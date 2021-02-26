"""Test Axis config flow."""
from unittest.mock import patch

import pytest
import respx

from openpeerpower import data_entry_flow
from openpeerpower.components.axis import config_flow
from openpeerpower.components.axis.const import (
    CONF_EVENTS,
    CONF_MODEL,
    CONF_STREAM_PROFILE,
    CONF_VIDEO_SOURCE,
    DEFAULT_STREAM_PROFILE,
    DEFAULT_VIDEO_SOURCE,
    DOMAIN as AXIS_DOMAIN,
)
from openpeerpower.components.dhcp import HOSTNAME, IP_ADDRESS, MAC_ADDRESS
from openpeerpower.config_entries import (
    SOURCE_DHCP,
    SOURCE_IGNORE,
    SOURCE_REAUTH,
    SOURCE_SSDP,
    SOURCE_USER,
    SOURCE_ZEROCONF,
)
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from .test_device import (
    DEFAULT_HOST,
    MAC,
    MODEL,
    NAME,
    mock_default_vapix_requests,
    setup_axis_integration,
)

from tests.common import MockConfigEntry


async def test_flow_manual_configuration(opp):
    """Test that config flow works."""
    MockConfigEntry(domain=AXIS_DOMAIN, source=SOURCE_IGNORE).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with respx.mock:
        mock_default_vapix_requests(respx)
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
                CONF_PORT: 80,
            },
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == f"M1065-LW - {MAC}"
    assert result["data"] == {
        CONF_HOST: "1.2.3.4",
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pass",
        CONF_PORT: 80,
        CONF_MODEL: "M1065-LW",
        CONF_NAME: "M1065-LW 0",
    }


async def test_manual_configuration_update_configuration(opp):
    """Test that config flow fails on already configured device."""
    config_entry = await setup_axis_integration(opp)
    device = opp.data[AXIS_DOMAIN][config_entry.unique_id]

    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with patch(
        "openpeerpower.components.axis.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, respx.mock:
        mock_default_vapix_requests(respx, "2.3.4.5")
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "2.3.4.5",
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
                CONF_PORT: 80,
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    assert device.host == "2.3.4.5"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_flow_fails_faulty_credentials(opp):
    """Test that config flow fails on faulty credentials."""
    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with patch(
        "openpeerpower.components.axis.config_flow.get_device",
        side_effect=config_flow.AuthenticationRequired,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
                CONF_PORT: 80,
            },
        )

    assert result["errors"] == {"base": "invalid_auth"}


async def test_flow_fails_cannot_connect(opp):
    """Test that config flow fails on cannot connect."""
    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with patch(
        "openpeerpower.components.axis.config_flow.get_device",
        side_effect=config_flow.CannotConnect,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
                CONF_PORT: 80,
            },
        )

    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_create_entry_multiple_existing_entries_of_same_model(opp):
    """Test that create entry can generate a name with other entries."""
    entry = MockConfigEntry(
        domain=AXIS_DOMAIN,
        data={CONF_NAME: "M1065-LW 0", CONF_MODEL: "M1065-LW"},
    )
    entry.add_to_opp(opp)
    entry2 = MockConfigEntry(
        domain=AXIS_DOMAIN,
        data={CONF_NAME: "M1065-LW 1", CONF_MODEL: "M1065-LW"},
    )
    entry2.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with respx.mock:
        mock_default_vapix_requests(respx)
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
                CONF_PORT: 80,
            },
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == f"M1065-LW - {MAC}"
    assert result["data"] == {
        CONF_HOST: "1.2.3.4",
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pass",
        CONF_PORT: 80,
        CONF_MODEL: "M1065-LW",
        CONF_NAME: "M1065-LW 2",
    }

    assert result["data"][CONF_NAME] == "M1065-LW 2"


async def test_reauth_flow_update_configuration(opp):
    """Test that config flow fails on already configured device."""
    config_entry = await setup_axis_integration(opp)
    device = opp.data[AXIS_DOMAIN][config_entry.unique_id]

    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN,
        context={"source": SOURCE_REAUTH},
        data=config_entry.data,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with respx.mock:
        mock_default_vapix_requests(respx, "2.3.4.5")
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "2.3.4.5",
                CONF_USERNAME: "user2",
                CONF_PASSWORD: "pass2",
                CONF_PORT: 80,
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    assert device.host == "2.3.4.5"
    assert device.username == "user2"
    assert device.password == "pass2"


@pytest.mark.parametrize(
    "source,discovery_info",
    [
        (
            SOURCE_DHCP,
            {
                HOSTNAME: f"axis-{MAC}",
                IP_ADDRESS: DEFAULT_HOST,
                MAC_ADDRESS: MAC,
            },
        ),
        (
            SOURCE_SSDP,
            {
                "st": "urn:axis-com:service:BasicService:1",
                "usn": f"uuid:Upnp-BasicDevice-1_0-{MAC}::urn:axis-com:service:BasicService:1",
                "ext": "",
                "server": "Linux/4.14.173-axis8, UPnP/1.0, Portable SDK for UPnP devices/1.8.7",
                "deviceType": "urn:schemas-upnp-org:device:Basic:1",
                "friendlyName": f"AXIS M1065-LW - {MAC}",
                "manufacturer": "AXIS",
                "manufacturerURL": "http://www.axis.com/",
                "modelDescription": "AXIS M1065-LW Network Camera",
                "modelName": "AXIS M1065-LW",
                "modelNumber": "M1065-LW",
                "modelURL": "http://www.axis.com/",
                "serialNumber": MAC,
                "UDN": f"uuid:Upnp-BasicDevice-1_0-{MAC}",
                "serviceList": {
                    "service": {
                        "serviceType": "urn:axis-com:service:BasicService:1",
                        "serviceId": "urn:axis-com:serviceId:BasicServiceId",
                        "controlURL": "/upnp/control/BasicServiceId",
                        "eventSubURL": "/upnp/event/BasicServiceId",
                        "SCPDURL": "/scpd_basic.xml",
                    }
                },
                "presentationURL": f"http://{DEFAULT_HOST}:80/",
            },
        ),
        (
            SOURCE_ZEROCONF,
            {
                "host": DEFAULT_HOST,
                "port": 80,
                "hostname": f"axis-{MAC.lower()}.local.",
                "type": "_axis-video._tcp.local.",
                "name": f"AXIS M1065-LW - {MAC}._axis-video._tcp.local.",
                "properties": {
                    "_raw": {"macaddress": MAC.encode()},
                    "macaddress": MAC,
                },
            },
        ),
    ],
)
async def test_discovery_flow(opp, source: str, discovery_info: dict):
    """Test the different discovery flows for new devices work."""
    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, data=discovery_info, context={"source": source}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with respx.mock:
        mock_default_vapix_requests(respx)
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
                CONF_PORT: 80,
            },
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == f"M1065-LW - {MAC}"
    assert result["data"] == {
        CONF_HOST: "1.2.3.4",
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pass",
        CONF_PORT: 80,
        CONF_MODEL: "M1065-LW",
        CONF_NAME: "M1065-LW 0",
    }

    assert result["data"][CONF_NAME] == "M1065-LW 0"


@pytest.mark.parametrize(
    "source,discovery_info",
    [
        (
            SOURCE_DHCP,
            {
                HOSTNAME: f"axis-{MAC}",
                IP_ADDRESS: DEFAULT_HOST,
                MAC_ADDRESS: MAC,
            },
        ),
        (
            SOURCE_SSDP,
            {
                "friendlyName": f"AXIS M1065-LW - {MAC}",
                "serialNumber": MAC,
                "presentationURL": f"http://{DEFAULT_HOST}:80/",
            },
        ),
        (
            SOURCE_ZEROCONF,
            {
                CONF_HOST: DEFAULT_HOST,
                CONF_PORT: 80,
                "name": f"AXIS M1065-LW - {MAC}._axis-video._tcp.local.",
                "properties": {"macaddress": MAC},
            },
        ),
    ],
)
async def test_discovered_device_already_configured(
    opp, source: str, discovery_info: dict
):
    """Test that discovery doesn't setup already configured devices."""
    config_entry = await setup_axis_integration(opp)
    assert config_entry.data[CONF_HOST] == DEFAULT_HOST

    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, data=discovery_info, context={"source": source}
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data[CONF_HOST] == DEFAULT_HOST


@pytest.mark.parametrize(
    "source,discovery_info,expected_port",
    [
        (
            SOURCE_DHCP,
            {
                HOSTNAME: f"axis-{MAC}",
                IP_ADDRESS: "2.3.4.5",
                MAC_ADDRESS: MAC,
            },
            80,
        ),
        (
            SOURCE_SSDP,
            {
                "friendlyName": f"AXIS M1065-LW - {MAC}",
                "serialNumber": MAC,
                "presentationURL": "http://2.3.4.5:8080/",
            },
            8080,
        ),
        (
            SOURCE_ZEROCONF,
            {
                CONF_HOST: "2.3.4.5",
                CONF_PORT: 8080,
                "name": f"AXIS M1065-LW - {MAC}._axis-video._tcp.local.",
                "properties": {"macaddress": MAC},
            },
            8080,
        ),
    ],
)
async def test_discovery_flow_updated_configuration(
    opp, source: str, discovery_info: dict, expected_port: int
):
    """Test that discovery flow update configuration with new parameters."""
    config_entry = await setup_axis_integration(opp)
    assert config_entry.data == {
        CONF_HOST: DEFAULT_HOST,
        CONF_PORT: 80,
        CONF_USERNAME: "root",
        CONF_PASSWORD: "pass",
        CONF_MODEL: MODEL,
        CONF_NAME: NAME,
    }

    with patch(
        "openpeerpower.components.axis.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, respx.mock:
        mock_default_vapix_requests(respx, "2.3.4.5")
        result = await opp.config_entries.flow.async_init(
            AXIS_DOMAIN, data=discovery_info, context={"source": source}
        )
        await opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data == {
        CONF_HOST: "2.3.4.5",
        CONF_PORT: expected_port,
        CONF_USERNAME: "root",
        CONF_PASSWORD: "pass",
        CONF_MODEL: MODEL,
        CONF_NAME: NAME,
    }
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    "source,discovery_info",
    [
        (
            SOURCE_DHCP,
            {
                HOSTNAME: "",
                IP_ADDRESS: "",
                MAC_ADDRESS: "01234567890",
            },
        ),
        (
            SOURCE_SSDP,
            {
                "friendlyName": "",
                "serialNumber": "01234567890",
                "presentationURL": "",
            },
        ),
        (
            SOURCE_ZEROCONF,
            {
                CONF_HOST: "",
                CONF_PORT: 0,
                "name": "",
                "properties": {"macaddress": "01234567890"},
            },
        ),
    ],
)
async def test_discovery_flow_ignore_non_axis_device(
    opp, source: str, discovery_info: dict
):
    """Test that discovery flow ignores devices with non Axis OUI."""
    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, data=discovery_info, context={"source": source}
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "not_axis_device"


@pytest.mark.parametrize(
    "source,discovery_info",
    [
        (
            SOURCE_DHCP,
            {HOSTNAME: f"axis-{MAC}", IP_ADDRESS: "169.254.3.4", MAC_ADDRESS: MAC},
        ),
        (
            SOURCE_SSDP,
            {
                "friendlyName": f"AXIS M1065-LW - {MAC}",
                "serialNumber": MAC,
                "presentationURL": "http://169.254.3.4:80/",
            },
        ),
        (
            SOURCE_ZEROCONF,
            {
                CONF_HOST: "169.254.3.4",
                CONF_PORT: 80,
                "name": f"AXIS M1065-LW - {MAC}._axis-video._tcp.local.",
                "properties": {"macaddress": MAC},
            },
        ),
    ],
)
async def test_discovery_flow_ignore_link_local_address(
    opp, source: str, discovery_info: dict
):
    """Test that discovery flow ignores devices with link local addresses."""
    result = await opp.config_entries.flow.async_init(
        AXIS_DOMAIN, data=discovery_info, context={"source": source}
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "link_local_address"


async def test_option_flow(opp):
    """Test config flow options."""
    config_entry = await setup_axis_integration(opp)
    device = opp.data[AXIS_DOMAIN][config_entry.unique_id]
    assert device.option_stream_profile == DEFAULT_STREAM_PROFILE
    assert device.option_video_source == DEFAULT_VIDEO_SOURCE

    with respx.mock:
        mock_default_vapix_requests(respx)
        result = await opp.config_entries.options.async_init(
            device.config_entry.entry_id
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "configure_stream"
    assert set(result["data_schema"].schema[CONF_STREAM_PROFILE].container) == {
        DEFAULT_STREAM_PROFILE,
        "profile_1",
        "profile_2",
    }
    assert set(result["data_schema"].schema[CONF_VIDEO_SOURCE].container) == {
        DEFAULT_VIDEO_SOURCE,
        1,
    }

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_STREAM_PROFILE: "profile_1", CONF_VIDEO_SOURCE: 1},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["data"] == {
        CONF_EVENTS: True,
        CONF_STREAM_PROFILE: "profile_1",
        CONF_VIDEO_SOURCE: 1,
    }
    assert device.option_stream_profile == "profile_1"
    assert device.option_video_source == 1
