"""Test UniFi Controller."""

from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

import aiounifi
import pytest

from openpeerpower.components.device_tracker import DOMAIN as TRACKER_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.components.unifi.const import (
    CONF_CONTROLLER,
    CONF_SITE_ID,
    DEFAULT_ALLOW_BANDWIDTH_SENSORS,
    DEFAULT_ALLOW_UPTIME_SENSORS,
    DEFAULT_DETECTION_TIME,
    DEFAULT_TRACK_CLIENTS,
    DEFAULT_TRACK_DEVICES,
    DEFAULT_TRACK_WIRED_CLIENTS,
    DOMAIN as UNIFI_DOMAIN,
    UNIFI_WIRELESS_CLIENTS,
)
from openpeerpower.components.unifi.controller import (
    SUPPORTED_PLATFORMS,
    get_controller,
)
from openpeerpower.components.unifi.errors import AuthenticationRequired, CannotConnect
from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    CONTENT_TYPE_JSON,
)
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry

DEFAULT_HOST = "1.2.3.4"
DEFAULT_SITE = "site_id"

CONTROLLER_HOST = {
    "hostname": "controller_host",
    "ip": DEFAULT_HOST,
    "is_wired": True,
    "last_seen": 1562600145,
    "mac": "10:00:00:00:00:01",
    "name": "Controller host",
    "oui": "Producer",
    "sw_mac": "00:00:00:00:01:01",
    "sw_port": 1,
    "wired-rx_bytes": 1234000000,
    "wired-tx_bytes": 5678000000,
    "uptime": 1562600160,
}

CONTROLLER_DATA = {
    CONF_HOST: DEFAULT_HOST,
    CONF_USERNAME: "username",
    CONF_PASSWORD: "password",
    CONF_PORT: 1234,
    CONF_SITE_ID: DEFAULT_SITE,
    CONF_VERIFY_SSL: False,
}

ENTRY_CONFIG = {**CONTROLLER_DATA, CONF_CONTROLLER: CONTROLLER_DATA}
ENTRY_OPTIONS = {}

CONFIGURATION = []

SITE = [{"desc": "Site name", "name": "site_id", "role": "admin", "_id": "1"}]
DESCRIPTION = [{"name": "username", "site_name": "site_id", "site_role": "admin"}]


def mock_default_unifi_requests(
    aioclient_mock,
    host,
    site_id,
    sites=None,
    description=None,
    clients_response=None,
    clients_all_response=None,
    devices_response=None,
    dpiapp_response=None,
    dpigroup_response=None,
    wlans_response=None,
):
    """Mock default UniFi requests responses."""
    aioclient_mock.get(f"https://{host}:1234", status=302)  # Check UniFi OS

    aioclient_mock.post(
        f"https://{host}:1234/api/login",
        json={"data": "login successful", "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        f"https://{host}:1234/api/self/sites",
        json={"data": sites or [], "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        f"https://{host}:1234/api/s/{site_id}/self",
        json={"data": description or [], "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        f"https://{host}:1234/api/s/{site_id}/stat/sta",
        json={"data": clients_response or [], "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"https://{host}:1234/api/s/{site_id}/rest/user",
        json={"data": clients_all_response or [], "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"https://{host}:1234/api/s/{site_id}/stat/device",
        json={"data": devices_response or [], "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"https://{host}:1234/api/s/{site_id}/rest/dpiapp",
        json={"data": dpiapp_response or [], "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"https://{host}:1234/api/s/{site_id}/rest/dpigroup",
        json={"data": dpigroup_response or [], "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"https://{host}:1234/api/s/{site_id}/rest/wlanconf",
        json={"data": wlans_response or [], "meta": {"rc": "ok"}},
        headers={"content-type": CONTENT_TYPE_JSON},
    )


async def setup_unifi_integration(
    opp,
    aioclient_mock=None,
    *,
    config=ENTRY_CONFIG,
    options=ENTRY_OPTIONS,
    sites=SITE,
    site_description=DESCRIPTION,
    clients_response=None,
    clients_all_response=None,
    devices_response=None,
    dpiapp_response=None,
    dpigroup_response=None,
    wlans_response=None,
    known_wireless_clients=None,
    controllers=None,
):
    """Create the UniFi controller."""
    assert await async_setup_component(opp, UNIFI_DOMAIN, {})

    config_entry = MockConfigEntry(
        domain=UNIFI_DOMAIN,
        data=deepcopy(config),
        options=deepcopy(options),
        entry_id=1,
        unique_id="1",
        version=1,
    )
    config_entry.add_to_opp(opp)

    if known_wireless_clients:
        opp.data[UNIFI_WIRELESS_CLIENTS].update_data(
            known_wireless_clients, config_entry
        )

    if aioclient_mock:
        mock_default_unifi_requests(
            aioclient_mock,
            host=config_entry.data[CONF_HOST],
            site_id=config_entry.data[CONF_SITE_ID],
            sites=sites,
            description=site_description,
            clients_response=clients_response,
            clients_all_response=clients_all_response,
            devices_response=devices_response,
            dpiapp_response=dpiapp_response,
            dpigroup_response=dpigroup_response,
            wlans_response=wlans_response,
        )

    with patch.object(aiounifi.websocket.WSClient, "start", return_value=True):
        await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()

    if config_entry.entry_id not in opp.data[UNIFI_DOMAIN]:
        return None

    return config_entry


async def test_controller_setup_opp, aioclient_mock):
    """Successful setup."""
    with patch(
        "openpeerpower.config_entries.ConfigEntries.async_forward_entry_setup",
        return_value=True,
    ) as forward_entry_setup:
        config_entry = await setup_unifi_integration(opp, aioclient_mock)
        controller = opp.data[UNIFI_DOMAIN][config_entry.entry_id]

    entry = controller.config_entry
    assert len(forward_entry_setup.mock_calls) == len(SUPPORTED_PLATFORMS)
    assert forward_entry_setup.mock_calls[0][1] == (entry, TRACKER_DOMAIN)
    assert forward_entry_setup.mock_calls[1][1] == (entry, SENSOR_DOMAIN)
    assert forward_entry_setup.mock_calls[2][1] == (entry, SWITCH_DOMAIN)

    assert controller.host == CONTROLLER_DATA[CONF_HOST]
    assert controller.site == CONTROLLER_DATA[CONF_SITE_ID]
    assert controller.site_name == SITE[0]["desc"]
    assert controller.site_role == SITE[0]["role"]

    assert controller.option_allow_bandwidth_sensors == DEFAULT_ALLOW_BANDWIDTH_SENSORS
    assert controller.option_allow_uptime_sensors == DEFAULT_ALLOW_UPTIME_SENSORS
    assert isinstance(controller.option_block_clients, list)
    assert controller.option_track_clients == DEFAULT_TRACK_CLIENTS
    assert controller.option_track_devices == DEFAULT_TRACK_DEVICES
    assert controller.option_track_wired_clients == DEFAULT_TRACK_WIRED_CLIENTS
    assert controller.option_detection_time == timedelta(seconds=DEFAULT_DETECTION_TIME)
    assert isinstance(controller.option_ssid_filter, set)

    assert controller.mac is None

    assert controller.signal_reachable == "unifi-reachable-1"
    assert controller.signal_update == "unifi-update-1"
    assert controller.signal_remove == "unifi-remove-1"
    assert controller.signal_options_update == "unifi-options-1"
    assert controller.signal_heartbeat_missed == "unifi-heartbeat-missed"


async def test_controller_mac(opp, aioclient_mock):
    """Test that it is possible to identify controller mac."""
    config_entry = await setup_unifi_integration(
        opp. aioclient_mock, clients_response=[CONTROLLER_HOST]
    )
    controller = opp.data[UNIFI_DOMAIN][config_entry.entry_id]
    assert controller.mac == CONTROLLER_HOST["mac"]


async def test_controller_not_accessible.opp):
    """Retry to login gets scheduled when connection fails."""
    with patch(
        "openpeerpower.components.unifi.controller.get_controller",
        side_effect=CannotConnect,
    ):
        await setup_unifi_integration.opp)
    assert opp.data[UNIFI_DOMAIN] == {}


async def test_controller_trigger_reauth_flow.opp):
    """Failed authentication trigger a reauthentication flow."""
    with patch(
        "openpeerpower.components.unifi.controller.get_controller",
        side_effect=AuthenticationRequired,
    ), patch.object.opp.config_entries.flow, "async_init") as mock_flow_init:
        await setup_unifi_integration.opp)
        mock_flow_init.assert_called_once()
    assert opp.data[UNIFI_DOMAIN] == {}


async def test_controller_unknown_error(opp):
    """Unknown errors are handled."""
    with patch(
        "openpeerpower.components.unifi.controller.get_controller",
        side_effect=Exception,
    ):
        await setup_unifi_integration.opp)
    assert opp.data[UNIFI_DOMAIN] == {}


async def test_reset_after_successful_setup_opp, aioclient_mock):
    """Calling reset when the entry has been setup."""
    config_entry = await setup_unifi_integration(opp, aioclient_mock)
    controller = opp.data[UNIFI_DOMAIN][config_entry.entry_id]

    assert len(controller.listeners) == 6

    result = await controller.async_reset()
    await opp.async_block_till_done()

    assert result is True
    assert len(controller.listeners) == 0


async def test_wireless_client_event_calls_update_wireless_devices(
    opp. aioclient_mock
):
    """Call update_wireless_devices method when receiving wireless client event."""
    config_entry = await setup_unifi_integration(opp, aioclient_mock)
    controller = opp.data[UNIFI_DOMAIN][config_entry.entry_id]

    with patch(
        "openpeerpower.components.unifi.controller.UniFiController.update_wireless_clients",
        return_value=None,
    ) as wireless_clients_mock:
        controller.api.websocket._data = {
            "meta": {"rc": "ok", "message": "events"},
            "data": [
                {
                    "datetime": "2020-01-20T19:37:04Z",
                    "key": aiounifi.events.WIRELESS_CLIENT_CONNECTED,
                    "msg": "User[11:22:33:44:55:66] has connected to WLAN",
                    "time": 1579549024893,
                }
            ],
        }
        controller.api.session_handler("data")

        assert wireless_clients_mock.assert_called_once


async def test_get_controller.opp):
    """Successful call."""
    with patch("aiounifi.Controller.check_unifi_os", return_value=True), patch(
        "aiounifi.Controller.login", return_value=True
    ):
        assert await get_controller(opp, **CONTROLLER_DATA)


async def test_get_controller_verify_ssl_false.opp):
    """Successful call with verify ssl set to false."""
    controller_data = dict(CONTROLLER_DATA)
    controller_data[CONF_VERIFY_SSL] = False
    with patch("aiounifi.Controller.check_unifi_os", return_value=True), patch(
        "aiounifi.Controller.login", return_value=True
    ):
        assert await get_controller(opp, **controller_data)


async def test_get_controller_login_failed.opp):
    """Check that get_controller can handle a failed login."""
    with patch("aiounifi.Controller.check_unifi_os", return_value=True), patch(
        "aiounifi.Controller.login", side_effect=aiounifi.Unauthorized
    ), pytest.raises(AuthenticationRequired):
        await get_controller(opp, **CONTROLLER_DATA)


async def test_get_controller_controller_bad_gateway.opp):
    """Check that get_controller can handle controller being unavailable."""
    with patch("aiounifi.Controller.check_unifi_os", return_value=True), patch(
        "aiounifi.Controller.login", side_effect=aiounifi.BadGateway
    ), pytest.raises(CannotConnect):
        await get_controller(opp, **CONTROLLER_DATA)


async def test_get_controller_controller_service_unavailable.opp):
    """Check that get_controller can handle controller being unavailable."""
    with patch("aiounifi.Controller.check_unifi_os", return_value=True), patch(
        "aiounifi.Controller.login", side_effect=aiounifi.ServiceUnavailable
    ), pytest.raises(CannotConnect):
        await get_controller(opp, **CONTROLLER_DATA)


async def test_get_controller_controller_unavailable.opp):
    """Check that get_controller can handle controller being unavailable."""
    with patch("aiounifi.Controller.check_unifi_os", return_value=True), patch(
        "aiounifi.Controller.login", side_effect=aiounifi.RequestError
    ), pytest.raises(CannotConnect):
        await get_controller(opp, **CONTROLLER_DATA)


async def test_get_controller_login_required.opp):
    """Check that get_controller can handle unknown errors."""
    with patch("aiounifi.Controller.check_unifi_os", return_value=True), patch(
        "aiounifi.Controller.login", side_effect=aiounifi.LoginRequired
    ), pytest.raises(AuthenticationRequired):
        await get_controller(opp, **CONTROLLER_DATA)


async def test_get_controller_unknown_error(opp):
    """Check that get_controller can handle unknown errors."""
    with patch("aiounifi.Controller.check_unifi_os", return_value=True), patch(
        "aiounifi.Controller.login", side_effect=aiounifi.AiounifiException
    ), pytest.raises(AuthenticationRequired):
        await get_controller(opp, **CONTROLLER_DATA)
