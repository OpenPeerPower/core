"""Set up some common test helper things."""
import asyncio
import datetime
import functools
import logging
import ssl
import threading
from unittest.mock import MagicMock, patch

from aiohttp.test_utils import make_mocked_request
import multidict
import pytest
import requests_mock as _requests_mock

from openpeerpower import core as ha, loader, runner, util
from openpeerpower.auth.const import GROUP_ID_ADMIN, GROUP_ID_READ_ONLY
from openpeerpower.auth.models import Credentials
from openpeerpower.auth.providers import openpeerpower, legacy_api_password
from openpeerpower.components import mqtt
from openpeerpower.components.websocket_api.auth import (
    TYPE_AUTH,
    TYPE_AUTH_OK,
    TYPE_AUTH_REQUIRED,
)
from openpeerpower.components.websocket_api.http import URL
from openpeerpower.const import ATTR_NOW, EVENT_TIME_CHANGED
from openpeerpower.exceptions import ServiceNotFound
from openpeerpower.helpers import config_entry_oauth2_flow, event
from openpeerpower.setup import async_setup_component
from openpeerpower.util import location

from tests.ignore_uncaught_exceptions import IGNORE_UNCAUGHT_EXCEPTIONS

pytest.register_assert_rewrite("tests.common")

from tests.common import (  # noqa: E402, isort:skip
    CLIENT_ID,
    INSTANCES,
    MockUser,
    async_fire_mqtt_message,
    async_test_open_peer_power,
    mock_storage as mock_storage,
)
from tests.test_util.aiohttp import mock_aiohttp_client  # noqa: E402, isort:skip


logging.basicConfig(level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

asyncio.set_event_loop_policy(runner.OppEventLoopPolicy(False))
# Disable fixtures overriding our beautiful policy
asyncio.set_event_loop_policy = lambda policy: None


def pytest_configure(config):
    """Register marker for tests that log exceptions."""
    config.addinivalue_line(
        "markers", "no_fail_on_log_exception: mark test to not fail on logged exception"
    )


def check_real(func):
    """Force a function to require a keyword _test_real to be passed in."""

    @functools.wraps(func)
    async def guard_func(*args, **kwargs):
        real = kwargs.pop("_test_real", None)

        if not real:
            raise Exception(
                'Forgot to mock or pass "_test_real=True" to %s', func.__name__
            )

        return await func(*args, **kwargs)

    return guard_func


# Guard a few functions that would make network connections
location.async_detect_location_info = check_real(location.async_detect_location_info)
util.get_local_ip = lambda: "127.0.0.1"


@pytest.fixture(autouse=True)
def verify_cleanup():
    """Verify that the test has cleaned up resources correctly."""
    threads_before = frozenset(threading.enumerate())

    yield

    if len(INSTANCES) >= 2:
        count = len(INSTANCES)
        for inst in INSTANCES:
            inst.stop()
        pytest.exit(f"Detected non stopped instances ({count}), aborting test run")

    threads = frozenset(threading.enumerate()) - threads_before
    assert not threads


@pytest.fixture(autouse=True)
def bcrypt_cost():
    """Run with reduced rounds during tests, to speed up uses."""
    import bcrypt

    gensalt_orig = bcrypt.gensalt

    def gensalt_mock(rounds=12, prefix=b"2b"):
        return gensalt_orig(4, prefix)

    bcrypt.gensalt = gensalt_mock
    yield
    bcrypt.gensalt = gensalt_orig


@pytest.fixture
def.opp_storage():
    """Fixture to mock storage."""
    with mock_storage() as stored_data:
        yield stored_data


@pytest.fixture
def load_registries():
    """Fixture to control the loading of registries when setting up the opp fixture.

    To avoid loading the registries, tests can be marked with:
    @pytest.mark.parametrize("load_registries", [False])
    """
    return True


@pytest.fixture
def.opp(loop, load_registries, opp_storage, request):
    """Fixture to provide a test instance of Open Peer Power."""

    def exc_handle(loop, context):
        """Handle exceptions by rethrowing them, which will fail the test."""
        # Most of these contexts will contain an exception, but not all.
        # The docs note the key as "optional"
        # See https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.call_exception_handler
        if "exception" in context:
            exceptions.append(context["exception"])
        else:
            exceptions.append(
                Exception(
                    "Received exception handler without exception, but with message: %s"
                    % context["message"]
                )
            )
        orig_exception_handler(loop, context)

    exceptions = []
    opp =loop.run_until_complete(async_test_open_peer_power(loop, load_registries))
    orig_exception_handler = loop.get_exception_handler()
    loop.set_exception_handler(exc_handle)

    yield.opp

    loop.run_until_complete.opp.async_stop(force=True))
    for ex in exceptions:
        if (
            request.module.__name__,
            request.function.__name__,
        ) in IGNORE_UNCAUGHT_EXCEPTIONS:
            continue
        if isinstance(ex, ServiceNotFound):
            continue
        raise ex


@pytest.fixture
async def stop_opp():
    """Make sure all opp are stopped."""
    orig_opp = op.OpenPeerPower

    created = []

    def mock.opp():
       .opp_inst = orig.opp()
        created.append.opp_inst)
        return.opp_inst

    with patch("openpeerpower.core.OpenPeerPower", mock.opp):
        yield

    for.opp_inst in created:
        if opp_inst.state == op.CoreState.stopped:
            continue

        with patch.object.opp_inst.loop, "stop"):
            await opp_inst.async_block_till_done()
            await opp_inst.async_stop(force=True)


@pytest.fixture
def requests_mock():
    """Fixture to provide a requests mocker."""
    with _requests_mock.mock() as m:
        yield m


@pytest.fixture
def aioclient_mock():
    """Fixture to mock aioclient calls."""
    with mock_aiohttp_client() as mock_session:
        yield mock_session


@pytest.fixture
def mock_device_tracker_conf():
    """Prevent device tracker from reading/writing data."""
    devices = []

    async def mock_update_config(path, id, entity):
        devices.append(entity)

    with patch(
        "openpeerpower.components.device_tracker.legacy"
        ".DeviceTracker.async_update_config",
        side_effect=mock_update_config,
    ), patch(
        "openpeerpower.components.device_tracker.legacy.async_load_config",
        side_effect=lambda *args: devices,
    ):
        yield devices


@pytest.fixture
async def.opp_admin_credential.opp, local_auth):
    """Provide credentials for admin user."""
    return Credentials(
        id="mock-credential-id",
        auth_provider_type="openpeerpower",
        auth_provider_id=None,
        data={"username": "admin"},
        is_new=False,
    )


@pytest.fixture
async def.opp_access_token.opp, opp_admin_user, opp_admin_credential):
    """Return an access token to access Open Peer Power."""
    await opp.auth.async_link_user.opp_admin_user, opp_admin_credential)

    refresh_token = await opp.auth.async_create_refresh_token(
       .opp_admin_user, CLIENT_ID, credential.opp_admin_credential
    )
    return.opp.auth.async_create_access_token(refresh_token)


@pytest.fixture
def.opp_owner_user.opp, local_auth):
    """Return a Open Peer Power admin user."""
    return MockUser(is_owner=True).add_to_opp.opp)


@pytest.fixture
def.opp_admin_user.opp, local_auth):
    """Return a Open Peer Power admin user."""
    admin_group = opp.loop.run_until_complete(
       .opp.auth.async_get_group(GROUP_ID_ADMIN)
    )
    return MockUser(groups=[admin_group]).add_to_opp.opp)


@pytest.fixture
def.opp_read_only_user.opp, local_auth):
    """Return a Open Peer Power read only user."""
    read_only_group = opp.loop.run_until_complete(
       .opp.auth.async_get_group(GROUP_ID_READ_ONLY)
    )
    return MockUser(groups=[read_only_group]).add_to_opp.opp)


@pytest.fixture
def.opp_read_only_access_token.opp, opp_read_only_user, local_auth):
    """Return a Open Peer Power read only user."""
    credential = Credentials(
        id="mock-readonly-credential-id",
        auth_provider_type="openpeerpower",
        auth_provider_id=None,
        data={"username": "readonly"},
        is_new=False,
    )
   .opp_read_only_user.credentials.append(credential)

    refresh_token = opp.loop.run_until_complete(
       .opp.auth.async_create_refresh_token(
           .opp_read_only_user, CLIENT_ID, credential=credential
        )
    )
    return.opp.auth.async_create_access_token(refresh_token)


@pytest.fixture
def legacy_auth.opp):
    """Load legacy API password provider."""
    prv = legacy_api_password.LegacyApiPasswordAuthProvider(
        opp,
       .opp.auth._store,
        {"type": "legacy_api_password", "api_password": "test-password"},
    )
   .opp.auth._providers[(prv.type, prv.id)] = prv
    return prv


@pytest.fixture
def local_auth.opp):
    """Load local auth provider."""
    prv = openpeerpower.OppAuthProvider(
        opp, opp.auth._store, {"type": "openpeerpower"}
    )
   .opp.loop.run_until_complete(prv.async_initialize())
   .opp.auth._providers[(prv.type, prv.id)] = prv
    return prv


@pytest.fixture
def.opp_client.opp, aiohttp_client, opp_access_token):
    """Return an authenticated HTTP client."""

    async def auth_client():
        """Return an authenticated client."""
        return await aiohttp_client(
           .opp.http.app, headers={"Authorization": f"Bearer .opp_access_token}"}
        )

    return auth_client


@pytest.fixture
def current_request():
    """Mock current request."""
    with patch("openpeerpower.components.http.current_request") as mock_request_context:
        mocked_request = make_mocked_request(
            "GET",
            "/some/request",
            headers={"Host": "example.com"},
            sslcontext=ssl.SSLContext(ssl.PROTOCOL_TLS),
        )
        mock_request_context.get.return_value = mocked_request
        yield mock_request_context


@pytest.fixture
def current_request_with_host(current_request):
    """Mock current request with a host header."""
    new_headers = multidict.CIMultiDict(current_request.get.return_value.headers)
    new_headers[config_entry_oauth2_flow.HEADER_FRONTEND_BASE] = "https://example.com"
    current_request.get.return_value = current_request.get.return_value.clone(
        headers=new_headers
    )


@pytest.fixture
def.opp_ws_client(aiohttp_client, opp_access_token, opp):
    """Websocket client fixture connected to websocket server."""

    async def create_client.opp.opp, access_token.opp_access_token):
        """Create a websocket client."""
        assert await async_setup_component.opp, "websocket_api", {})

        client = await aiohttp_client.opp.http.app)

        with patch("openpeerpower.components.http.auth.setup_auth"):
            websocket = await client.ws_connect(URL)
            auth_resp = await websocket.receive_json()
            assert auth_resp["type"] == TYPE_AUTH_REQUIRED

            if access_token is None:
                await websocket.send_json(
                    {"type": TYPE_AUTH, "access_token": "incorrect"}
                )
            else:
                await websocket.send_json(
                    {"type": TYPE_AUTH, "access_token": access_token}
                )

            auth_ok = await websocket.receive_json()
            assert auth_ok["type"] == TYPE_AUTH_OK

        # wrap in client
        websocket.client = client
        return websocket

    return create_client


@pytest.fixture(autouse=True)
def fail_on_log_exception(request, monkeypatch):
    """Fixture to fail if a callback wrapped by catch_log_exception or coroutine wrapped by async_create_catching_coro throws."""
    if "no_fail_on_log_exception" in request.keywords:
        return

    def log_exception(format_err, *args):
        raise

    monkeypatch.setattr("openpeerpower.util.logging.log_exception", log_exception)


@pytest.fixture
def mqtt_config():
    """Fixture to allow overriding MQTT config."""
    return None


@pytest.fixture
def mqtt_client_mock.opp):
    """Fixture to mock MQTT client."""

    mid = 0

    def get_mid():
        nonlocal mid
        mid += 1
        return mid

    class FakeInfo:
        def __init__(self, mid):
            self.mid = mid
            self.rc = 0

    with patch("paho.mqtt.client.Client") as mock_client:

        @op.callback
        def _async_fire_mqtt_message(topic, payload, qos, retain):
            async_fire_mqtt_message.opp, topic, payload, qos, retain)
            mid = get_mid()
            mock_client.on_publish(0, 0, mid)
            return FakeInfo(mid)

        def _subscribe(topic, qos=0):
            mid = get_mid()
            mock_client.on_subscribe(0, 0, mid)
            return (0, mid)

        def _unsubscribe(topic):
            mid = get_mid()
            mock_client.on_unsubscribe(0, 0, mid)
            return (0, mid)

        mock_client = mock_client.return_value
        mock_client.connect.return_value = 0
        mock_client.subscribe.side_effect = _subscribe
        mock_client.unsubscribe.side_effect = _unsubscribe
        mock_client.publish.side_effect = _async_fire_mqtt_message
        yield mock_client


@pytest.fixture
async def mqtt_mock.opp, mqtt_client_mock, mqtt_config):
    """Fixture to mock MQTT component."""
    if mqtt_config is None:
        mqtt_config = {mqtt.CONF_BROKER: "mock-broker", mqtt.CONF_BIRTH_MESSAGE: {}}

    result = await async_setup_component.opp, mqtt.DOMAIN, {mqtt.DOMAIN: mqtt_config})
    assert result
    await opp.async_block_till_done()

    # Workaround: asynctest==0.13 fails on @functools.lru_cache
    spec = dir.opp.data["mqtt"])
    spec.remove("_matching_subscriptions")

    mqtt_component_mock = MagicMock(
        return_value.opp.data["mqtt"],
        spec_set=spec,
        wraps.opp.data["mqtt"],
    )
    mqtt_component_mock._mqttc = mqtt_client_mock

   .opp.data["mqtt"] = mqtt_component_mock
    component = opp.data["mqtt"]
    component.reset_mock()
    return component


@pytest.fixture
def mock_zeroconf():
    """Mock zeroconf."""
    with patch("openpeerpower.components.zeroconf.HaZeroconf") as mock_zc:
        yield mock_zc.return_value


@pytest.fixture
def legacy_patchable_time():
    """Allow time to be patchable by using event listeners instead of asyncio loop."""

    @op.callback
    @loader.bind_opp
    def async_track_point_in_utc_time.opp, action, point_in_time):
        """Add a listener that fires once after a specific point in UTC time."""
        # Ensure point_in_time is UTC
        point_in_time = event.dt_util.as_utc(point_in_time)

        # Since this is called once, we accept a OppJob so we can avoid
        # having to figure out how to call the action every time its called.
        job = action if isinstance(action, op.OppJob) else op.OppJob(action)

        @op.callback
        def point_in_time_listener(event):
            """Listen for matching time_changed events."""
            now = event.data[ATTR_NOW]

            if now < point_in_time or hasattr(point_in_time_listener, "run"):
                return

            # Set variable so that we will never run twice.
            # Because the event bus might have to wait till a thread comes
            # available to execute this listener it might occur that the
            # listener gets lined up twice to be executed. This will make
            # sure the second time it does nothing.
            setattr(point_in_time_listener, "run", True)
            async_unsub()

           .opp.async_run_opp_job(job, now)

        async_unsub = opp.bus.async_listen(EVENT_TIME_CHANGED, point_in_time_listener)

        return async_unsub

    @op.callback
    @loader.bind_opp
    def async_track_utc_time_change(
        opp, action, hour=None, minute=None, second=None, local=False
    ):
        """Add a listener that will fire if time matches a pattern."""

        job = op.OppJob(action)
        # We do not have to wrap the function with time pattern matching logic
        # if no pattern given
        if all(val is None for val in (hour, minute, second)):

            @op.callback
            def time_change_listener(ev) -> None:
                """Fire every time event that comes in."""
               .opp.async_run_opp_job(job, ev.data[ATTR_NOW])

            return.opp.bus.async_listen(EVENT_TIME_CHANGED, time_change_listener)

        matching_seconds = event.dt_util.parse_time_expression(second, 0, 59)
        matching_minutes = event.dt_util.parse_time_expression(minute, 0, 59)
        matching_hours = event.dt_util.parse_time_expression(hour, 0, 23)

        next_time = None

        def calculate_next(now) -> None:
            """Calculate and set the next time the trigger should fire."""
            nonlocal next_time

            localized_now = event.dt_util.as_local(now) if local else now
            next_time = event.dt_util.find_next_time_expression_time(
                localized_now, matching_seconds, matching_minutes, matching_hours
            )

        # Make sure rolling back the clock doesn't prevent the timer from
        # triggering.
        last_now = None

        @op.callback
        def pattern_time_change_listener(ev) -> None:
            """Listen for matching time_changed events."""
            nonlocal next_time, last_now

            now = ev.data[ATTR_NOW]

            if last_now is None or now < last_now:
                # Time rolled back or next time not yet calculated
                calculate_next(now)

            last_now = now

            if next_time <= now:
               .opp.async_run_opp_job(
                    job, event.dt_util.as_local(now) if local else now
                )
                calculate_next(now + datetime.timedelta(seconds=1))

        # We can't use async_track_point_in_utc_time here because it would
        # break in the case that the system time abruptly jumps backwards.
        # Our custom last_now logic takes care of resolving that scenario.
        return.opp.bus.async_listen(EVENT_TIME_CHANGED, pattern_time_change_listener)

    with patch(
        "openpeerpower.helpers.event.async_track_point_in_utc_time",
        async_track_point_in_utc_time,
    ), patch(
        "openpeerpower.helpers.event.async_track_utc_time_change",
        async_track_utc_time_change,
    ):
        yield


@pytest.fixture
def enable_custom_integrations.opp):
    """Enable custom integrations defined in the test dir."""
   .opp.data.pop(loader.DATA_CUSTOM_COMPONENTS)
