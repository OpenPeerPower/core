"""Code to handle a Hue bridge."""
from __future__ import annotations

import asyncio
from functools import partial
import logging

from aiohttp import client_exceptions
import aiohue
import async_timeout
import slugify as unicode_slug

from openpeerpower import core
from openpeerpower.const import HTTP_INTERNAL_SERVER_ERROR
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client

from .const import (
    ATTR_GROUP_NAME,
    ATTR_SCENE_NAME,
    ATTR_TRANSITION,
    CONF_ALLOW_HUE_GROUPS,
    CONF_ALLOW_UNREACHABLE,
    DEFAULT_ALLOW_HUE_GROUPS,
    DEFAULT_ALLOW_UNREACHABLE,
    DOMAIN,
    LOGGER,
)
from .errors import AuthenticationRequired, CannotConnect
from .helpers import create_config_flow
from .sensor_base import SensorManager

# How long should we sleep if the hub is busy
HUB_BUSY_SLEEP = 0.5

PLATFORMS = ["light", "binary_sensor", "sensor"]

_LOGGER = logging.getLogger(__name__)


class HueBridge:
    """Manages a single Hue bridge."""

    def __init__(self, opp, config_entry):
        """Initialize the system."""
        self.config_entry = config_entry
        self.opp = opp
        self.available = True
        self.authorized = False
        self.api = None
        self.parallel_updates_semaphore = None
        # Jobs to be executed when API is reset.
        self.reset_jobs = []
        self.sensor_manager = None
        self._update_callbacks = {}

    @property
    def host(self):
        """Return the host of this bridge."""
        return self.config_entry.data["host"]

    @property
    def allow_unreachable(self):
        """Allow unreachable light bulbs."""
        return self.config_entry.options.get(
            CONF_ALLOW_UNREACHABLE, DEFAULT_ALLOW_UNREACHABLE
        )

    @property
    def allow_groups(self):
        """Allow groups defined in the Hue bridge."""
        return self.config_entry.options.get(
            CONF_ALLOW_HUE_GROUPS, DEFAULT_ALLOW_HUE_GROUPS
        )

    async def async_setup(self, tries=0):
        """Set up a phue bridge based on host parameter."""
        host = self.host
        opp = self.opp

        bridge = aiohue.Bridge(
            host,
            username=self.config_entry.data["username"],
            websession=aiohttp_client.async_get_clientsession(opp),
        )

        try:
            await authenticate_bridge(opp, bridge)

        except AuthenticationRequired:
            # Usernames can become invalid if hub is reset or user removed.
            # We are going to fail the config entry setup and initiate a new
            # linking procedure. When linking succeeds, it will remove the
            # old config entry.
            create_config_flow(opp, host)
            return False

        except CannotConnect as err:
            raise ConfigEntryNotReady(
                f"Error connecting to the Hue bridge at {host}"
            ) from err

        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unknown error connecting with Hue bridge at %s", host)
            return False

        self.api = bridge
        if bridge.sensors is not None:
            self.sensor_manager = SensorManager(self)

        opp.data.setdefault(DOMAIN, {})[self.config_entry.entry_id] = self
        opp.config_entries.async_setup_platforms(self.config_entry, PLATFORMS)

        self.parallel_updates_semaphore = asyncio.Semaphore(
            3 if self.api.config.modelid == "BSB001" else 10
        )

        self.reset_jobs.append(self.config_entry.add_update_listener(_update_listener))
        self.reset_jobs.append(asyncio.create_task(self._subscribe_events()).cancel)

        self.authorized = True
        return True

    async def async_request_call(self, task):
        """Limit parallel requests to Hue hub.

        The Hue hub can only handle a certain amount of parallel requests, total.
        Although we limit our parallel requests, we still will run into issues because
        other products are hitting up Hue.

        ClientOSError means hub closed the socket on us.
        ContentResponseError means hub raised an error.
        Since we don't make bad requests, this is on them.
        """
        async with self.parallel_updates_semaphore:
            for tries in range(4):
                try:
                    return await task()
                except (
                    client_exceptions.ClientOSError,
                    client_exceptions.ClientResponseError,
                    client_exceptions.ServerDisconnectedError,
                ) as err:
                    if tries == 3:
                        _LOGGER.error("Request failed %s times, giving up", tries)
                        raise

                    # We only retry if it's a server error. So raise on all 4XX errors.
                    if (
                        isinstance(err, client_exceptions.ClientResponseError)
                        and err.status < HTTP_INTERNAL_SERVER_ERROR
                    ):
                        raise

                    await asyncio.sleep(HUB_BUSY_SLEEP * tries)

    async def async_reset(self):
        """Reset this bridge to default state.

        Will cancel any scheduled setup retry and will unload
        the config entry.
        """
        # The bridge can be in 3 states:
        #  - Setup was successful, self.api is not None
        #  - Authentication was wrong, self.api is None, not retrying setup.

        # If the authentication was wrong.
        if self.api is None:
            return True

        while self.reset_jobs:
            self.reset_jobs.pop()()

        self._update_callbacks = {}

        # If setup was successful, we set api variable, forwarded entry and
        # register service
        unload_success = await self.opp.config_entries.async_unload_platforms(
            self.config_entry, PLATFORMS
        )

        if unload_success:
            self.opp.data[DOMAIN].pop(self.config_entry.entry_id)

        return unload_success

    async def hue_activate_scene(self, data, skip_reload=False, hide_warnings=False):
        """Service to call directly into bridge to set scenes."""
        if self.api.scenes is None:
            _LOGGER.warning("Hub %s does not support scenes", self.api.host)
            return

        group_name = data[ATTR_GROUP_NAME]
        scene_name = data[ATTR_SCENE_NAME]
        transition = data.get(ATTR_TRANSITION)

        group = next(
            (group for group in self.api.groups.values() if group.name == group_name),
            None,
        )

        # Additional scene logic to handle duplicate scene names across groups
        scene = next(
            (
                scene
                for scene in self.api.scenes.values()
                if scene.name == scene_name
                and group is not None
                and sorted(scene.lights) == sorted(group.lights)
            ),
            None,
        )

        # If we can't find it, fetch latest info.
        if not skip_reload and (group is None or scene is None):
            await self.async_request_call(self.api.groups.update)
            await self.async_request_call(self.api.scenes.update)
            return await self.hue_activate_scene(data, skip_reload=True)

        if group is None:
            if not hide_warnings:
                LOGGER.warning(
                    "Unable to find group %s" " on bridge %s", group_name, self.host
                )
            return False

        if scene is None:
            LOGGER.warning("Unable to find scene %s", scene_name)
            return False

        return await self.async_request_call(
            partial(group.set_action, scene=scene.id, transitiontime=transition)
        )

    async def handle_unauthorized_error(self):
        """Create a new config flow when the authorization is no longer valid."""
        if not self.authorized:
            # we already created a new config flow, no need to do it again
            return
        LOGGER.error(
            "Unable to authorize to bridge %s, setup the linking again", self.host
        )
        self.authorized = False
        create_config_flow(self.opp, self.host)

    async def _subscribe_events(self):
        """Subscribe to Hue events."""
        try:
            async for updated_object in self.api.listen_events():
                key = (updated_object.ITEM_TYPE, updated_object.id)

                if key in self._update_callbacks:
                    for callback in self._update_callbacks[key]:
                        callback()

        except GeneratorExit:
            pass

    @core.callback
    def listen_updates(self, item_type, item_id, update_callback):
        """Listen to updates."""
        key = (item_type, item_id)
        callbacks: list[core.CALLBACK_TYPE] | None = self._update_callbacks.get(key)

        if callbacks is None:
            callbacks = self._update_callbacks[key] = []

        callbacks.append(update_callback)

        @core.callback
        def unsub():
            try:
                callbacks.remove(update_callback)
            except ValueError:
                pass

        return unsub


async def authenticate_bridge(opp: core.OpenPeerPower, bridge: aiohue.Bridge):
    """Create a bridge object and verify authentication."""
    try:
        with async_timeout.timeout(10):
            # Create username if we don't have one
            if not bridge.username:
                device_name = unicode_slug.slugify(
                    opp.config.location_name, max_length=19
                )
                await bridge.create_user(f"open-peer-power#{device_name}")

            # Initialize bridge (and validate our username)
            await bridge.initialize()

    except (aiohue.LinkButtonNotPressed, aiohue.Unauthorized) as err:
        raise AuthenticationRequired from err
    except (
        asyncio.TimeoutError,
        client_exceptions.ClientOSError,
        client_exceptions.ServerDisconnectedError,
        client_exceptions.ContentTypeError,
    ) as err:
        raise CannotConnect from err
    except aiohue.AiohueException as err:
        LOGGER.exception("Unknown Hue linking error occurred")
        raise AuthenticationRequired from err


async def _update_listener(opp, entry):
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)
