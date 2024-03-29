"""Component to interface with cameras."""
from __future__ import annotations

import asyncio
import base64
import collections
from collections.abc import Awaitable, Mapping
from contextlib import suppress
from datetime import datetime, timedelta
import hashlib
import logging
import os
from random import SystemRandom
from typing import Callable, Final, cast, final

from aiohttp import web
import async_timeout
import attr
import voluptuous as vol

from openpeerpower.components import websocket_api
from openpeerpower.components.http import KEY_AUTHENTICATED, OpenPeerPowerView
from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_EXTRA,
    DOMAIN as DOMAIN_MP,
    SERVICE_PLAY_MEDIA,
)
from openpeerpower.components.stream import Stream, create_stream
from openpeerpower.components.stream.const import FORMAT_CONTENT_TYPE, OUTPUT_FORMATS
from openpeerpower.components.websocket_api import ActiveConnection
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_FILENAME,
    CONTENT_TYPE_MULTIPART,
    EVENT_OPENPEERPOWER_START,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.core import Event, OpenPeerPower, ServiceCall, callback
from openpeerpower.exceptions import OpenPeerPowerError
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
)
from openpeerpower.helpers.entity import Entity, entity_sources
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.network import get_url
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.loader import bind_opp

from .const import (
    CAMERA_IMAGE_TIMEOUT,
    CAMERA_STREAM_SOURCE_TIMEOUT,
    CONF_DURATION,
    CONF_LOOKBACK,
    DATA_CAMERA_PREFS,
    DOMAIN,
    SERVICE_RECORD,
)
from .prefs import CameraPreferences

# mypy: allow-untyped-calls

_LOGGER = logging.getLogger(__name__)

SERVICE_ENABLE_MOTION: Final = "enable_motion_detection"
SERVICE_DISABLE_MOTION: Final = "disable_motion_detection"
SERVICE_SNAPSHOT: Final = "snapshot"
SERVICE_PLAY_STREAM: Final = "play_stream"

SCAN_INTERVAL: Final = timedelta(seconds=30)
ENTITY_ID_FORMAT: Final = DOMAIN + ".{}"

ATTR_FILENAME: Final = "filename"
ATTR_MEDIA_PLAYER: Final = "media_player"
ATTR_FORMAT: Final = "format"

STATE_RECORDING: Final = "recording"
STATE_STREAMING: Final = "streaming"
STATE_IDLE: Final = "idle"

# Bitfield of features supported by the camera entity
SUPPORT_ON_OFF: Final = 1
SUPPORT_STREAM: Final = 2

DEFAULT_CONTENT_TYPE: Final = "image/jpeg"
ENTITY_IMAGE_URL: Final = "/api/camera_proxy/{0}?token={1}"

TOKEN_CHANGE_INTERVAL: Final = timedelta(minutes=5)
_RND: Final = SystemRandom()

MIN_STREAM_INTERVAL: Final = 0.5  # seconds

CAMERA_SERVICE_SNAPSHOT: Final = {vol.Required(ATTR_FILENAME): cv.template}

CAMERA_SERVICE_PLAY_STREAM: Final = {
    vol.Required(ATTR_MEDIA_PLAYER): cv.entities_domain(DOMAIN_MP),
    vol.Optional(ATTR_FORMAT, default="hls"): vol.In(OUTPUT_FORMATS),
}

CAMERA_SERVICE_RECORD: Final = {
    vol.Required(CONF_FILENAME): cv.template,
    vol.Optional(CONF_DURATION, default=30): vol.Coerce(int),
    vol.Optional(CONF_LOOKBACK, default=0): vol.Coerce(int),
}

WS_TYPE_CAMERA_THUMBNAIL: Final = "camera_thumbnail"
SCHEMA_WS_CAMERA_THUMBNAIL: Final = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_CAMERA_THUMBNAIL,
        vol.Required("entity_id"): cv.entity_id,
    }
)


@attr.s
class Image:
    """Represent an image."""

    content_type: str = attr.ib()
    content: bytes = attr.ib()


@bind_opp
async def async_request_stream(opp: OpenPeerPower, entity_id: str, fmt: str) -> str:
    """Request a stream for a camera entity."""
    camera = _get_camera_from_entity_id(opp, entity_id)
    return await _async_stream_endpoint_url(opp, camera, fmt)


@bind_opp
async def async_get_image(
    opp: OpenPeerPower, entity_id: str, timeout: int = 10
) -> Image:
    """Fetch an image from a camera entity."""
    camera = _get_camera_from_entity_id(opp, entity_id)

    with suppress(asyncio.CancelledError, asyncio.TimeoutError):
        async with async_timeout.timeout(timeout):
            image = await camera.async_camera_image()

            if image:
                return Image(camera.content_type, image)

    raise OpenPeerPowerError("Unable to get image")


@bind_opp
async def async_get_stream_source(opp: OpenPeerPower, entity_id: str) -> str | None:
    """Fetch the stream source for a camera entity."""
    camera = _get_camera_from_entity_id(opp, entity_id)

    return await camera.stream_source()


@bind_opp
async def async_get_mjpeg_stream(
    opp: OpenPeerPower, request: web.Request, entity_id: str
) -> web.StreamResponse | None:
    """Fetch an mjpeg stream from a camera entity."""
    camera = _get_camera_from_entity_id(opp, entity_id)

    return await camera.handle_async_mjpeg_stream(request)


async def async_get_still_stream(
    request: web.Request,
    image_cb: Callable[[], Awaitable[bytes | None]],
    content_type: str,
    interval: float,
) -> web.StreamResponse:
    """Generate an HTTP MJPEG stream from camera images.

    This method must be run in the event loop.
    """
    response = web.StreamResponse()
    response.content_type = CONTENT_TYPE_MULTIPART.format("--frameboundary")
    await response.prepare(request)

    async def write_to_mjpeg_stream(img_bytes: bytes) -> None:
        """Write image to stream."""
        await response.write(
            bytes(
                "--frameboundary\r\n"
                "Content-Type: {}\r\n"
                "Content-Length: {}\r\n\r\n".format(content_type, len(img_bytes)),
                "utf-8",
            )
            + img_bytes
            + b"\r\n"
        )

    last_image = None

    while True:
        img_bytes = await image_cb()
        if not img_bytes:
            break

        if img_bytes != last_image:
            await write_to_mjpeg_stream(img_bytes)

            # Chrome seems to always ignore first picture,
            # print it twice.
            if last_image is None:
                await write_to_mjpeg_stream(img_bytes)
            last_image = img_bytes

        await asyncio.sleep(interval)

    return response


def _get_camera_from_entity_id(opp: OpenPeerPower, entity_id: str) -> Camera:
    """Get camera component from entity_id."""
    component = opp.data.get(DOMAIN)

    if component is None:
        raise OpenPeerPowerError("Camera integration not set up")

    camera = component.get_entity(entity_id)

    if camera is None:
        raise OpenPeerPowerError("Camera not found")

    if not camera.is_on:
        raise OpenPeerPowerError("Camera is off")

    return cast(Camera, camera)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the camera component."""
    component = opp.data[DOMAIN] = EntityComponent(_LOGGER, DOMAIN, opp, SCAN_INTERVAL)

    prefs = CameraPreferences(opp)
    await prefs.async_initialize()
    opp.data[DATA_CAMERA_PREFS] = prefs

    opp.http.register_view(CameraImageView(component))
    opp.http.register_view(CameraMjpegStream(component))
    opp.components.websocket_api.async_register_command(
        WS_TYPE_CAMERA_THUMBNAIL, websocket_camera_thumbnail, SCHEMA_WS_CAMERA_THUMBNAIL
    )
    opp.components.websocket_api.async_register_command(ws_camera_stream)
    opp.components.websocket_api.async_register_command(websocket_get_prefs)
    opp.components.websocket_api.async_register_command(websocket_update_prefs)

    await component.async_setup(config)

    async def preload_stream(_event: Event) -> None:
        for camera in component.entities:
            camera = cast(Camera, camera)
            camera_prefs = prefs.get(camera.entity_id)
            if not camera_prefs.preload_stream:
                continue
            stream = await camera.create_stream()
            if not stream:
                continue
            stream.keepalive = True
            stream.add_provider("hls")
            stream.start()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_START, preload_stream)

    @callback
    def update_tokens(time: datetime) -> None:
        """Update tokens of the entities."""
        for entity in component.entities:
            entity = cast(Camera, entity)
            entity.async_update_token()
            entity.async_write_op_state()

    opp.helpers.event.async_track_time_interval(update_tokens, TOKEN_CHANGE_INTERVAL)

    component.async_register_entity_service(
        SERVICE_ENABLE_MOTION, {}, "async_enable_motion_detection"
    )
    component.async_register_entity_service(
        SERVICE_DISABLE_MOTION, {}, "async_disable_motion_detection"
    )
    component.async_register_entity_service(SERVICE_TURN_OFF, {}, "async_turn_off")
    component.async_register_entity_service(SERVICE_TURN_ON, {}, "async_turn_on")
    component.async_register_entity_service(
        SERVICE_SNAPSHOT, CAMERA_SERVICE_SNAPSHOT, async_handle_snapshot_service
    )
    component.async_register_entity_service(
        SERVICE_PLAY_STREAM,
        CAMERA_SERVICE_PLAY_STREAM,
        async_handle_play_stream_service,
    )
    component.async_register_entity_service(
        SERVICE_RECORD, CAMERA_SERVICE_RECORD, async_handle_record_service
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    component: EntityComponent = opp.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    component: EntityComponent = opp.data[DOMAIN]
    return await component.async_unload_entry(entry)


class Camera(Entity):
    """The base class for camera entities."""

    def __init__(self) -> None:
        """Initialize a camera."""
        self.is_streaming: bool = False
        self.stream: Stream | None = None
        self.stream_options: dict[str, str] = {}
        self.content_type: str = DEFAULT_CONTENT_TYPE
        self.access_tokens: collections.deque = collections.deque([], 2)
        self.async_update_token()

    @property
    def should_poll(self) -> bool:
        """No need to poll cameras."""
        return False

    @property
    def entity_picture(self) -> str:
        """Return a link to the camera feed as entity picture."""
        return ENTITY_IMAGE_URL.format(self.entity_id, self.access_tokens[-1])

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return 0

    @property
    def is_recording(self) -> bool:
        """Return true if the device is recording."""
        return False

    @property
    def brand(self) -> str | None:
        """Return the camera brand."""
        return None

    @property
    def motion_detection_enabled(self) -> bool:
        """Return the camera motion detection status."""
        return False

    @property
    def model(self) -> str | None:
        """Return the camera model."""
        return None

    @property
    def frame_interval(self) -> float:
        """Return the interval between frames of the mjpeg stream."""
        return MIN_STREAM_INTERVAL

    async def create_stream(self) -> Stream | None:
        """Create a Stream for stream_source."""
        # There is at most one stream (a decode worker) per camera
        if not self.stream:
            async with async_timeout.timeout(CAMERA_STREAM_SOURCE_TIMEOUT):
                source = await self.stream_source()
            if not source:
                return None
            self.stream = create_stream(self.opp, source, options=self.stream_options)
        return self.stream

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        return None

    def camera_image(self) -> bytes | None:
        """Return bytes of camera image."""
        raise NotImplementedError()

    async def async_camera_image(self) -> bytes | None:
        """Return bytes of camera image."""
        return await self.opp.async_add_executor_job(self.camera_image)

    async def handle_async_still_stream(
        self, request: web.Request, interval: float
    ) -> web.StreamResponse:
        """Generate an HTTP MJPEG stream from camera images."""
        return await async_get_still_stream(
            request, self.async_camera_image, self.content_type, interval
        )

    async def handle_async_mjpeg_stream(
        self, request: web.Request
    ) -> web.StreamResponse | None:
        """Serve an HTTP MJPEG stream from the camera.

        This method can be overridden by camera platforms to proxy
        a direct stream from the camera.
        """
        return await self.handle_async_still_stream(request, self.frame_interval)

    @property
    def state(self) -> str:
        """Return the camera state."""
        if self.is_recording:
            return STATE_RECORDING
        if self.is_streaming:
            return STATE_STREAMING
        return STATE_IDLE

    @property
    def is_on(self) -> bool:
        """Return true if on."""
        return True

    def turn_off(self) -> None:
        """Turn off camera."""
        raise NotImplementedError()

    async def async_turn_off(self) -> None:
        """Turn off camera."""
        await self.opp.async_add_executor_job(self.turn_off)

    def turn_on(self) -> None:
        """Turn off camera."""
        raise NotImplementedError()

    async def async_turn_on(self) -> None:
        """Turn off camera."""
        await self.opp.async_add_executor_job(self.turn_on)

    def enable_motion_detection(self) -> None:
        """Enable motion detection in the camera."""
        raise NotImplementedError()

    async def async_enable_motion_detection(self) -> None:
        """Call the job and enable motion detection."""
        await self.opp.async_add_executor_job(self.enable_motion_detection)

    def disable_motion_detection(self) -> None:
        """Disable motion detection in camera."""
        raise NotImplementedError()

    async def async_disable_motion_detection(self) -> None:
        """Call the job and disable motion detection."""
        await self.opp.async_add_executor_job(self.disable_motion_detection)

    @final
    @property
    def state_attributes(self) -> dict[str, str | None]:
        """Return the camera state attributes."""
        attrs = {"access_token": self.access_tokens[-1]}

        if self.model:
            attrs["model_name"] = self.model

        if self.brand:
            attrs["brand"] = self.brand

        if self.motion_detection_enabled:
            attrs["motion_detection"] = self.motion_detection_enabled

        return attrs

    @callback
    def async_update_token(self) -> None:
        """Update the used token."""
        self.access_tokens.append(
            hashlib.sha256(_RND.getrandbits(256).to_bytes(32, "little")).hexdigest()
        )


class CameraView(OpenPeerPowerView):
    """Base CameraView."""

    requires_auth = False

    def __init__(self, component: EntityComponent) -> None:
        """Initialize a basic camera view."""
        self.component = component

    async def get(self, request: web.Request, entity_id: str) -> web.StreamResponse:
        """Start a GET request."""
        camera = self.component.get_entity(entity_id)

        if camera is None:
            raise web.HTTPNotFound()

        camera = cast(Camera, camera)

        authenticated = (
            request[KEY_AUTHENTICATED]
            or request.query.get("token") in camera.access_tokens
        )

        if not authenticated:
            raise web.HTTPUnauthorized()

        if not camera.is_on:
            _LOGGER.debug("Camera is off")
            raise web.HTTPServiceUnavailable()

        return await self.handle(request, camera)

    async def handle(self, request: web.Request, camera: Camera) -> web.StreamResponse:
        """Handle the camera request."""
        raise NotImplementedError()


class CameraImageView(CameraView):
    """Camera view to serve an image."""

    url = "/api/camera_proxy/{entity_id}"
    name = "api:camera:image"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera image."""
        with suppress(asyncio.CancelledError, asyncio.TimeoutError):
            async with async_timeout.timeout(CAMERA_IMAGE_TIMEOUT):
                image = await camera.async_camera_image()

            if image:
                return web.Response(body=image, content_type=camera.content_type)

        raise web.HTTPInternalServerError()


class CameraMjpegStream(CameraView):
    """Camera View to serve an MJPEG stream."""

    url = "/api/camera_proxy_stream/{entity_id}"
    name = "api:camera:stream"

    async def handle(self, request: web.Request, camera: Camera) -> web.StreamResponse:
        """Serve camera stream, possibly with interval."""
        interval_str = request.query.get("interval")
        if interval_str is None:
            stream = await camera.handle_async_mjpeg_stream(request)
            if stream is None:
                raise web.HTTPBadGateway()
            return stream

        try:
            # Compose camera stream from stills
            interval = float(interval_str)
            if interval < MIN_STREAM_INTERVAL:
                raise ValueError(f"Stream interval must be be > {MIN_STREAM_INTERVAL}")
            return await camera.handle_async_still_stream(request, interval)
        except ValueError as err:
            raise web.HTTPBadRequest() from err


@websocket_api.async_response
async def websocket_camera_thumbnail(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Handle get camera thumbnail websocket command.

    Async friendly.
    """
    _LOGGER.warning("The websocket command 'camera_thumbnail' has been deprecated")
    try:
        image = await async_get_image(opp, msg["entity_id"])
        await connection.send_big_result(
            msg["id"],
            {
                "content_type": image.content_type,
                "content": base64.b64encode(image.content).decode("utf-8"),
            },
        )
    except OpenPeerPowerError:
        connection.send_message(
            websocket_api.error_message(
                msg["id"], "image_fetch_failed", "Unable to fetch image"
            )
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "camera/stream",
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("format", default="hls"): vol.In(OUTPUT_FORMATS),
    }
)
@websocket_api.async_response
async def ws_camera_stream(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Handle get camera stream websocket command.

    Async friendly.
    """
    try:
        entity_id = msg["entity_id"]
        camera = _get_camera_from_entity_id(opp, entity_id)
        url = await _async_stream_endpoint_url(opp, camera, fmt=msg["format"])
        connection.send_result(msg["id"], {"url": url})
    except OpenPeerPowerError as ex:
        _LOGGER.error("Error requesting stream: %s", ex)
        connection.send_error(msg["id"], "start_stream_failed", str(ex))
    except asyncio.TimeoutError:
        _LOGGER.error("Timeout getting stream source")
        connection.send_error(
            msg["id"], "start_stream_failed", "Timeout getting stream source"
        )


@websocket_api.websocket_command(
    {vol.Required("type"): "camera/get_prefs", vol.Required("entity_id"): cv.entity_id}
)
@websocket_api.async_response
async def websocket_get_prefs(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Handle request for account info."""
    prefs = opp.data[DATA_CAMERA_PREFS].get(msg["entity_id"])
    connection.send_result(msg["id"], prefs.as_dict())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "camera/update_prefs",
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("preload_stream"): bool,
    }
)
@websocket_api.async_response
async def websocket_update_prefs(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Handle request for account info."""
    prefs = opp.data[DATA_CAMERA_PREFS]

    changes = dict(msg)
    changes.pop("id")
    changes.pop("type")
    entity_id = changes.pop("entity_id")
    await prefs.async_update(entity_id, **changes)

    connection.send_result(msg["id"], prefs.get(entity_id).as_dict())


async def async_handle_snapshot_service(
    camera: Camera, service_call: ServiceCall
) -> None:
    """Handle snapshot services calls."""
    opp = camera.opp
    filename = service_call.data[ATTR_FILENAME]
    filename.opp = opp

    snapshot_file = filename.async_render(variables={ATTR_ENTITY_ID: camera})

    # check if we allow to access to that file
    if not opp.config.is_allowed_path(snapshot_file):
        _LOGGER.error("Can't write %s, no access to path!", snapshot_file)
        return

    image = await camera.async_camera_image()

    def _write_image(to_file: str, image_data: bytes | None) -> None:
        """Executor helper to write image."""
        if image_data is None:
            return
        if not os.path.exists(os.path.dirname(to_file)):
            os.makedirs(os.path.dirname(to_file), exist_ok=True)
        with open(to_file, "wb") as img_file:
            img_file.write(image_data)

    try:
        await opp.async_add_executor_job(_write_image, snapshot_file, image)
    except OSError as err:
        _LOGGER.error("Can't write image to file: %s", err)


async def async_handle_play_stream_service(
    camera: Camera, service_call: ServiceCall
) -> None:
    """Handle play stream services calls."""
    fmt = service_call.data[ATTR_FORMAT]
    url = await _async_stream_endpoint_url(camera.opp, camera, fmt)

    opp = camera.opp
    data: Mapping[str, str] = {
        ATTR_MEDIA_CONTENT_ID: f"{get_url(opp)}{url}",
        ATTR_MEDIA_CONTENT_TYPE: FORMAT_CONTENT_TYPE[fmt],
    }

    # It is required to send a different payload for cast media players
    entity_ids = service_call.data[ATTR_MEDIA_PLAYER]
    sources = entity_sources(opp)
    cast_entity_ids = [
        entity
        for entity in entity_ids
        # All entities should be in sources. This extra guard is to
        # avoid people writing to the state machine and breaking it.
        if entity in sources and sources[entity]["domain"] == "cast"
    ]
    other_entity_ids = list(set(entity_ids) - set(cast_entity_ids))

    if cast_entity_ids:
        await opp.services.async_call(
            DOMAIN_MP,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: cast_entity_ids,
                **data,
                ATTR_MEDIA_EXTRA: {
                    "stream_type": "LIVE",
                    "media_info": {
                        "hlsVideoSegmentFormat": "fmp4",
                    },
                },
            },
            blocking=True,
            context=service_call.context,
        )

    if other_entity_ids:
        await opp.services.async_call(
            DOMAIN_MP,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: other_entity_ids,
                **data,
            },
            blocking=True,
            context=service_call.context,
        )


async def _async_stream_endpoint_url(
    opp: OpenPeerPower, camera: Camera, fmt: str
) -> str:
    stream = await camera.create_stream()
    if not stream:
        raise OpenPeerPowerError(
            f"{camera.entity_id} does not support play stream service"
        )

    # Update keepalive setting which manages idle shutdown
    camera_prefs = opp.data[DATA_CAMERA_PREFS].get(camera.entity_id)
    stream.keepalive = camera_prefs.preload_stream

    stream.add_provider(fmt)
    stream.start()
    return stream.endpoint_url(fmt)


async def async_handle_record_service(
    camera: Camera, service_call: ServiceCall
) -> None:
    """Handle stream recording service calls."""
    stream = await camera.create_stream()

    if not stream:
        raise OpenPeerPowerError(f"{camera.entity_id} does not support record service")

    opp = camera.opp
    filename = service_call.data[CONF_FILENAME]
    filename.opp = opp
    video_path = filename.async_render(variables={ATTR_ENTITY_ID: camera})

    await stream.async_record(
        video_path,
        duration=service_call.data[CONF_DURATION],
        lookback=service_call.data[CONF_LOOKBACK],
    )
