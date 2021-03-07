"""Tests for Philips Hue config flow."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from aiohttp import client_exceptions
import aiohue
from aiohue.discovery import URL_NUPNP
import pytest
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components import ssdp
from openpeerpower.components.hue import config_flow, const

from tests.common import MockConfigEntry


@pytest.fixture(name="hue_setup", autouse=True)
def hue_setup_fixture():
    """Mock hue entry setup."""
    with patch("openpeerpower.components.hue.async_setup_entry", return_value=True):
        yield


def get_mock_bridge(
    bridge_id="aabbccddeeff", host="1.2.3.4", mock_create_user=None, username=None
):
    """Return a mock bridge."""
    mock_bridge = Mock()
    mock_bridge.host = host
    mock_bridge.username = username
    mock_bridge.config.name = "Mock Bridge"
    mock_bridge.id = bridge_id

    if not mock_create_user:

        async def create_user(username):
            mock_bridge.username = username

        mock_create_user = create_user

    mock_bridge.create_user = mock_create_user
    mock_bridge.initialize = AsyncMock()

    return mock_bridge


async def test_flow_works(opp):
    """Test config flow ."""
    mock_bridge = get_mock_bridge()

    with patch(
        "openpeerpower.components.hue.config_flow.discover_nupnp",
        return_value=[mock_bridge],
    ):
        result = await opp.config_entries.flow.async_init(
            const.DOMAIN, context={"source": "user"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={"id": mock_bridge.id}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "link"

    flow = next(
        flow
        for flow in opp.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert flow["context"]["unique_id"] == "aabbccddeeff"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Mock Bridge"
    assert result["data"] == {
        "host": "1.2.3.4",
        "username": "open-peer-power#test-home",
    }

    assert len(mock_bridge.initialize.mock_calls) == 1


async def test_manual_flow_works(opp, aioclient_mock):
    """Test config flow discovers only already configured bridges."""
    mock_bridge = get_mock_bridge()

    MockConfigEntry(
        domain="hue", source=config_entries.SOURCE_IGNORE, unique_id="bla"
    ).add_to_opp(opp)

    with patch(
        "openpeerpower.components.hue.config_flow.discover_nupnp",
        return_value=[mock_bridge],
    ):
        result = await opp.config_entries.flow.async_init(
            const.DOMAIN, context={"source": "user"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={"id": "manual"}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"

    bridge = get_mock_bridge(
        bridge_id="id-1234", host="2.2.2.2", username="username-abc"
    )

    with patch(
        "aiohue.Bridge",
        return_value=bridge,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], {"host": "2.2.2.2"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "link"

    with patch("openpeerpower.components.hue.config_flow.authenticate_bridge"), patch(
        "openpeerpower.components.hue.async_unload_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] == "create_entry"
    assert result["title"] == "Mock Bridge"
    assert result["data"] == {
        "host": "2.2.2.2",
        "username": "username-abc",
    }
    entries = opp.config_entries.async_entries("hue")
    assert len(entries) == 2
    entry = entries[-1]
    assert entry.unique_id == "id-1234"


async def test_manual_flow_bridge_exist(opp, aioclient_mock):
    """Test config flow discovers only already configured bridges."""
    MockConfigEntry(
        domain="hue", unique_id="id-1234", data={"host": "2.2.2.2"}
    ).add_to_opp(opp)

    with patch(
        "openpeerpower.components.hue.config_flow.discover_nupnp",
        return_value=[],
    ):
        result = await opp.config_entries.flow.async_init(
            const.DOMAIN, context={"source": "user"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"

    bridge = get_mock_bridge(
        bridge_id="id-1234", host="2.2.2.2", username="username-abc"
    )

    with patch(
        "aiohue.Bridge",
        return_value=bridge,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], {"host": "2.2.2.2"}
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_manual_flow_no_discovered_bridges(opp, aioclient_mock):
    """Test config flow discovers no bridges."""
    aioclient_mock.get(URL_NUPNP, json=[])

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "manual"


async def test_flow_all_discovered_bridges_exist(opp, aioclient_mock):
    """Test config flow discovers only already configured bridges."""
    aioclient_mock.get(URL_NUPNP, json=[{"internalipaddress": "1.2.3.4", "id": "bla"}])
    MockConfigEntry(domain="hue", unique_id="bla", data={"host": "1.2.3.4"}).add_to_opp(
        opp
    )

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "user"}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"


async def test_flow_bridges_discovered(opp, aioclient_mock):
    """Test config flow discovers two bridges."""
    # Add ignored config entry. Should still show up as option.
    MockConfigEntry(
        domain="hue", source=config_entries.SOURCE_IGNORE, unique_id="bla"
    ).add_to_opp(opp)

    aioclient_mock.get(
        URL_NUPNP,
        json=[
            {"internalipaddress": "1.2.3.4", "id": "bla"},
            {"internalipaddress": "5.6.7.8", "id": "beer"},
        ],
    )

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    with pytest.raises(vol.Invalid):
        assert result["data_schema"]({"id": "not-discovered"})

    result["data_schema"]({"id": "bla"})
    result["data_schema"]({"id": "beer"})
    result["data_schema"]({"id": "manual"})


async def test_flow_two_bridges_discovered_one_new(opp, aioclient_mock):
    """Test config flow discovers two bridges."""
    aioclient_mock.get(
        URL_NUPNP,
        json=[
            {"internalipaddress": "1.2.3.4", "id": "bla"},
            {"internalipaddress": "5.6.7.8", "id": "beer"},
        ],
    )
    MockConfigEntry(domain="hue", unique_id="bla", data={"host": "1.2.3.4"}).add_to_opp(
        opp
    )

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "user"}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert result["data_schema"]({"id": "beer"})
    assert result["data_schema"]({"id": "manual"})
    with pytest.raises(vol.error.MultipleInvalid):
        assert not result["data_schema"]({"id": "bla"})


async def test_flow_timeout_discovery(opp):
    """Test config flow ."""
    with patch(
        "openpeerpower.components.hue.config_flow.discover_nupnp",
        side_effect=asyncio.TimeoutError,
    ):
        result = await opp.config_entries.flow.async_init(
            const.DOMAIN, context={"source": "user"}
        )

    assert result["type"] == "abort"
    assert result["reason"] == "discover_timeout"


async def test_flow_link_timeout(opp):
    """Test config flow."""
    mock_bridge = get_mock_bridge(
        mock_create_user=AsyncMock(side_effect=asyncio.TimeoutError),
    )
    with patch(
        "openpeerpower.components.hue.config_flow.discover_nupnp",
        return_value=[mock_bridge],
    ):
        result = await opp.config_entries.flow.async_init(
            const.DOMAIN, context={"source": "user"}
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={"id": mock_bridge.id}
    )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_flow_link_unknown_error(opp):
    """Test if a unknown error happened during the linking processes."""
    mock_bridge = get_mock_bridge(
        mock_create_user=AsyncMock(side_effect=OSError),
    )
    with patch(
        "openpeerpower.components.hue.config_flow.discover_nupnp",
        return_value=[mock_bridge],
    ):
        result = await opp.config_entries.flow.async_init(
            const.DOMAIN, context={"source": "user"}
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={"id": mock_bridge.id}
    )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "link"
    assert result["errors"] == {"base": "linking"}


async def test_flow_link_button_not_pressed(opp):
    """Test config flow ."""
    mock_bridge = get_mock_bridge(
        mock_create_user=AsyncMock(side_effect=aiohue.LinkButtonNotPressed),
    )
    with patch(
        "openpeerpower.components.hue.config_flow.discover_nupnp",
        return_value=[mock_bridge],
    ):
        result = await opp.config_entries.flow.async_init(
            const.DOMAIN, context={"source": "user"}
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={"id": mock_bridge.id}
    )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "link"
    assert result["errors"] == {"base": "register_failed"}


async def test_flow_link_unknown_host(opp):
    """Test config flow ."""
    mock_bridge = get_mock_bridge(
        mock_create_user=AsyncMock(side_effect=client_exceptions.ClientOSError),
    )
    with patch(
        "openpeerpower.components.hue.config_flow.discover_nupnp",
        return_value=[mock_bridge],
    ):
        result = await opp.config_entries.flow.async_init(
            const.DOMAIN, context={"source": "user"}
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={"id": mock_bridge.id}
    )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_bridge_ssdp(opp):
    """Test a bridge being discovered."""
    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "ssdp"},
        data={
            ssdp.ATTR_SSDP_LOCATION: "http://0.0.0.0/",
            ssdp.ATTR_UPNP_MANUFACTURER_URL: config_flow.HUE_MANUFACTURERURL,
            ssdp.ATTR_UPNP_SERIAL: "1234",
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "link"


async def test_bridge_ssdp_discover_other_bridge(opp):
    """Test that discovery ignores other bridges."""
    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "ssdp"},
        data={ssdp.ATTR_UPNP_MANUFACTURER_URL: "http://www.notphilips.com"},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_hue_bridge"


async def test_bridge_ssdp_emulated_hue(opp):
    """Test if discovery info is from an emulated hue instance."""
    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "ssdp"},
        data={
            ssdp.ATTR_SSDP_LOCATION: "http://0.0.0.0/",
            ssdp.ATTR_UPNP_FRIENDLY_NAME: "Open Peer Power Bridge",
            ssdp.ATTR_UPNP_MANUFACTURER_URL: config_flow.HUE_MANUFACTURERURL,
            ssdp.ATTR_UPNP_SERIAL: "1234",
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_hue_bridge"


async def test_bridge_ssdp_missing_location(opp):
    """Test if discovery info is missing a location attribute."""
    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "ssdp"},
        data={
            ssdp.ATTR_UPNP_MANUFACTURER_URL: config_flow.HUE_MANUFACTURERURL,
            ssdp.ATTR_UPNP_SERIAL: "1234",
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_hue_bridge"


async def test_bridge_ssdp_missing_serial(opp):
    """Test if discovery info is a serial attribute."""
    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "ssdp"},
        data={
            ssdp.ATTR_SSDP_LOCATION: "http://0.0.0.0/",
            ssdp.ATTR_UPNP_MANUFACTURER_URL: config_flow.HUE_MANUFACTURERURL,
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_hue_bridge"


async def test_bridge_ssdp_espalexa(opp):
    """Test if discovery info is from an Espalexa based device."""
    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "ssdp"},
        data={
            ssdp.ATTR_SSDP_LOCATION: "http://0.0.0.0/",
            ssdp.ATTR_UPNP_FRIENDLY_NAME: "Espalexa (0.0.0.0)",
            ssdp.ATTR_UPNP_MANUFACTURER_URL: config_flow.HUE_MANUFACTURERURL,
            ssdp.ATTR_UPNP_SERIAL: "1234",
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_hue_bridge"


async def test_bridge_ssdp_already_configured(opp):
    """Test if a discovered bridge has already been configured."""
    MockConfigEntry(
        domain="hue", unique_id="1234", data={"host": "0.0.0.0"}
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "ssdp"},
        data={
            ssdp.ATTR_SSDP_LOCATION: "http://0.0.0.0/",
            ssdp.ATTR_UPNP_MANUFACTURER_URL: config_flow.HUE_MANUFACTURERURL,
            ssdp.ATTR_UPNP_SERIAL: "1234",
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_import_with_no_config(opp):
    """Test importing a host without an existing config file."""
    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "import"},
        data={"host": "0.0.0.0"},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "link"


async def test_creating_entry_removes_entries_for_same_host_or_bridge(opp):
    """Test that we clean up entries for same host and bridge.

    An IP can only hold a single bridge and a single bridge can only be
    accessible via a single IP. So when we create a new entry, we'll remove
    all existing entries that either have same IP or same bridge_id.
    """
    orig_entry = MockConfigEntry(
        domain="hue",
        data={"host": "0.0.0.0", "username": "aaaa"},
        unique_id="id-1234",
    )
    orig_entry.add_to_opp(opp)

    MockConfigEntry(
        domain="hue",
        data={"host": "1.2.3.4", "username": "bbbb"},
        unique_id="id-5678",
    ).add_to_opp(opp)

    assert len(opp.config_entries.async_entries("hue")) == 2

    bridge = get_mock_bridge(
        bridge_id="id-1234", host="2.2.2.2", username="username-abc"
    )

    with patch(
        "aiohue.Bridge",
        return_value=bridge,
    ):
        result = await opp.config_entries.flow.async_init(
            "hue", data={"host": "2.2.2.2"}, context={"source": "import"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "link"

    with patch("openpeerpower.components.hue.config_flow.authenticate_bridge"), patch(
        "openpeerpower.components.hue.async_unload_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] == "create_entry"
    assert result["title"] == "Mock Bridge"
    assert result["data"] == {
        "host": "2.2.2.2",
        "username": "username-abc",
    }
    entries = opp.config_entries.async_entries("hue")
    assert len(entries) == 2
    new_entry = entries[-1]
    assert orig_entry.entry_id != new_entry.entry_id
    assert new_entry.unique_id == "id-1234"


async def test_bridge_homekit(opp, aioclient_mock):
    """Test a bridge being discovered via HomeKit."""
    aioclient_mock.get(URL_NUPNP, json=[{"internalipaddress": "1.2.3.4", "id": "bla"}])

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "homekit"},
        data={
            "host": "0.0.0.0",
            "serial": "1234",
            "manufacturerURL": config_flow.HUE_MANUFACTURERURL,
            "properties": {"id": "aa:bb:cc:dd:ee:ff"},
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_bridge_import_already_configured(opp):
    """Test if a import flow aborts if host is already configured."""
    MockConfigEntry(
        domain="hue", unique_id="aabbccddeeff", data={"host": "0.0.0.0"}
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "import"},
        data={"host": "0.0.0.0", "properties": {"id": "aa:bb:cc:dd:ee:ff"}},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_bridge_homekit_already_configured(opp):
    """Test if a HomeKit discovered bridge has already been configured."""
    MockConfigEntry(
        domain="hue", unique_id="aabbccddeeff", data={"host": "0.0.0.0"}
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "homekit"},
        data={"host": "0.0.0.0", "properties": {"id": "aa:bb:cc:dd:ee:ff"}},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_ssdp_discovery_update_configuration(opp):
    """Test if a discovered bridge is configured and updated with new host."""
    entry = MockConfigEntry(
        domain="hue", unique_id="aabbccddeeff", data={"host": "0.0.0.0"}
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": "ssdp"},
        data={
            ssdp.ATTR_SSDP_LOCATION: "http://1.1.1.1/",
            ssdp.ATTR_UPNP_MANUFACTURER_URL: config_flow.HUE_MANUFACTURERURL,
            ssdp.ATTR_UPNP_SERIAL: "aabbccddeeff",
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "1.1.1.1"


async def test_options_flow(opp):
    """Test options config flow."""
    entry = MockConfigEntry(
        domain="hue",
        unique_id="aabbccddeeff",
        data={"host": "0.0.0.0"},
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert (
        _get_schema_default(schema, const.CONF_ALLOW_HUE_GROUPS)
        == const.DEFAULT_ALLOW_HUE_GROUPS
    )
    assert (
        _get_schema_default(schema, const.CONF_ALLOW_UNREACHABLE)
        == const.DEFAULT_ALLOW_UNREACHABLE
    )

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            const.CONF_ALLOW_HUE_GROUPS: True,
            const.CONF_ALLOW_UNREACHABLE: True,
        },
    )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        const.CONF_ALLOW_HUE_GROUPS: True,
        const.CONF_ALLOW_UNREACHABLE: True,
    }


def _get_schema_default(schema, key_name):
    """Iterate schema to find a key."""
    for schema_key in schema:
        if schema_key == key_name:
            return schema_key.default()
    raise KeyError(f"{key_name} not found in schema")
