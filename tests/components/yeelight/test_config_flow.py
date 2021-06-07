"""Test the Yeelight config flow."""
from unittest.mock import MagicMock, patch

import pytest

from openpeerpower import config_entries, setup
from openpeerpower.components.yeelight import (
    CONF_MODE_MUSIC,
    CONF_MODEL,
    CONF_NIGHTLIGHT_SWITCH,
    CONF_NIGHTLIGHT_SWITCH_TYPE,
    CONF_SAVE_ON_CHANGE,
    CONF_TRANSITION,
    DEFAULT_MODE_MUSIC,
    DEFAULT_NAME,
    DEFAULT_NIGHTLIGHT_SWITCH,
    DEFAULT_SAVE_ON_CHANGE,
    DEFAULT_TRANSITION,
    DOMAIN,
    NIGHTLIGHT_SWITCH_TYPE_LIGHT,
)
from openpeerpower.components.yeelight.config_flow import CannotConnect
from openpeerpower.const import CONF_DEVICE, CONF_HOST, CONF_ID, CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.data_entry_flow import RESULT_TYPE_ABORT, RESULT_TYPE_FORM

from . import (
    ID,
    IP_ADDRESS,
    MODULE,
    MODULE_CONFIG_FLOW,
    NAME,
    UNIQUE_NAME,
    _mocked_bulb,
    _patch_discovery,
)

from tests.common import MockConfigEntry

DEFAULT_CONFIG = {
    CONF_MODEL: "",
    CONF_TRANSITION: DEFAULT_TRANSITION,
    CONF_MODE_MUSIC: DEFAULT_MODE_MUSIC,
    CONF_SAVE_ON_CHANGE: DEFAULT_SAVE_ON_CHANGE,
    CONF_NIGHTLIGHT_SWITCH: DEFAULT_NIGHTLIGHT_SWITCH,
}


async def test_discovery(opp: OpenPeerPower):
    """Test setting up discovery."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert not result["errors"]

    with _patch_discovery(f"{MODULE_CONFIG_FLOW}.yeelight"):
        result2 = await opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2["type"] == "form"
    assert result2["step_id"] == "pick_device"
    assert not result2["errors"]

    with patch(f"{MODULE}.async_setup", return_value=True) as mock_setup, patch(
        f"{MODULE}.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result3 = await opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE: ID}
        )
    assert result3["type"] == "create_entry"
    assert result3["title"] == UNIQUE_NAME
    assert result3["data"] == {CONF_ID: ID}
    await opp.async_block_till_done()
    mock_setup.assert_called_once()
    mock_setup_entry.assert_called_once()

    # ignore configured devices
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert not result["errors"]

    with _patch_discovery(f"{MODULE_CONFIG_FLOW}.yeelight"):
        result2 = await opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2["type"] == "abort"
    assert result2["reason"] == "no_devices_found"


async def test_discovery_no_device(opp: OpenPeerPower):
    """Test discovery without device."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with _patch_discovery(f"{MODULE_CONFIG_FLOW}.yeelight", no_device=True):
        result2 = await opp.config_entries.flow.async_configure(result["flow_id"], {})

    assert result2["type"] == "abort"
    assert result2["reason"] == "no_devices_found"


async def test_import(opp: OpenPeerPower):
    """Test import from yaml."""
    config = {
        CONF_NAME: DEFAULT_NAME,
        CONF_HOST: IP_ADDRESS,
        CONF_TRANSITION: DEFAULT_TRANSITION,
        CONF_MODE_MUSIC: DEFAULT_MODE_MUSIC,
        CONF_SAVE_ON_CHANGE: DEFAULT_SAVE_ON_CHANGE,
        CONF_NIGHTLIGHT_SWITCH_TYPE: NIGHTLIGHT_SWITCH_TYPE_LIGHT,
    }

    # Cannot connect
    mocked_bulb = _mocked_bulb(cannot_connect=True)
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=config
        )
    type(mocked_bulb).get_capabilities.assert_called_once()
    type(mocked_bulb).get_properties.assert_called_once()
    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"

    # Success
    mocked_bulb = _mocked_bulb()
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb), patch(
        f"{MODULE}.async_setup", return_value=True
    ) as mock_setup, patch(
        f"{MODULE}.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=config
        )
    type(mocked_bulb).get_capabilities.assert_called_once()
    assert result["type"] == "create_entry"
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_HOST: IP_ADDRESS,
        CONF_TRANSITION: DEFAULT_TRANSITION,
        CONF_MODE_MUSIC: DEFAULT_MODE_MUSIC,
        CONF_SAVE_ON_CHANGE: DEFAULT_SAVE_ON_CHANGE,
        CONF_NIGHTLIGHT_SWITCH: True,
    }
    await opp.async_block_till_done()
    mock_setup.assert_called_once()
    mock_setup_entry.assert_called_once()

    # Duplicate
    mocked_bulb = _mocked_bulb()
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=config
        )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_manual(opp: OpenPeerPower):
    """Test manually setup."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert not result["errors"]

    # Cannot connect (timeout)
    mocked_bulb = _mocked_bulb(cannot_connect=True)
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
    assert result2["type"] == "form"
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}

    # Cannot connect (error)
    type(mocked_bulb).get_capabilities = MagicMock(side_effect=OSError)
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result3 = await opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
    assert result3["errors"] == {"base": "cannot_connect"}

    # Success
    mocked_bulb = _mocked_bulb()
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb), patch(
        f"{MODULE}.async_setup", return_value=True
    ), patch(f"{MODULE}.async_setup_entry", return_value=True):
        result4 = await opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
        await opp.async_block_till_done()
    assert result4["type"] == "create_entry"
    assert result4["title"] == "color 0x000000000015243f"
    assert result4["data"] == {CONF_HOST: IP_ADDRESS}

    # Duplicate
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mocked_bulb = _mocked_bulb()
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"


async def test_options(opp: OpenPeerPower):
    """Test options flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS, CONF_NAME: NAME}
    )
    config_entry.add_to_opp(opp)

    mocked_bulb = _mocked_bulb()
    with patch(f"{MODULE}.Bulb", return_value=mocked_bulb):
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    config = {
        CONF_NAME: NAME,
        CONF_MODEL: "",
        CONF_TRANSITION: DEFAULT_TRANSITION,
        CONF_MODE_MUSIC: DEFAULT_MODE_MUSIC,
        CONF_SAVE_ON_CHANGE: DEFAULT_SAVE_ON_CHANGE,
        CONF_NIGHTLIGHT_SWITCH: DEFAULT_NIGHTLIGHT_SWITCH,
    }
    assert config_entry.options == config
    assert opp.states.get(f"light.{NAME}_nightlight") is None

    result = await opp.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    config[CONF_NIGHTLIGHT_SWITCH] = True
    user_input = {**config}
    user_input.pop(CONF_NAME)
    with patch(f"{MODULE}.Bulb", return_value=mocked_bulb):
        result2 = await opp.config_entries.options.async_configure(
            result["flow_id"], user_input
        )
        await opp.async_block_till_done()
    assert result2["type"] == "create_entry"
    assert result2["data"] == config
    assert result2["data"] == config_entry.options
    assert opp.states.get(f"light.{NAME}_nightlight") is not None


async def test_manual_no_capabilities(opp: OpenPeerPower):
    """Test manually setup without successful get_capabilities."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert not result["errors"]

    mocked_bulb = _mocked_bulb()
    type(mocked_bulb).get_capabilities = MagicMock(return_value=None)
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb), patch(
        f"{MODULE}.async_setup", return_value=True
    ), patch(f"{MODULE}.async_setup_entry", return_value=True):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
    type(mocked_bulb).get_capabilities.assert_called_once()
    type(mocked_bulb).get_properties.assert_called_once()
    assert result["type"] == "create_entry"
    assert result["data"] == {CONF_HOST: IP_ADDRESS}


async def test_discovered_by_homekit_and_dhcp(opp):
    """Test we get the form with homekit and abort for dhcp source when we get both."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    mocked_bulb = _mocked_bulb()
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_HOMEKIT},
            data={"host": "1.2.3.4", "properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] is None

    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result2 = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={"ip": "1.2.3.4", "macaddress": "aa:bb:cc:dd:ee:ff"},
        )
    assert result2["type"] == RESULT_TYPE_ABORT
    assert result2["reason"] == "already_in_progress"

    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result3 = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={"ip": "1.2.3.4", "macaddress": "00:00:00:00:00:00"},
        )
    assert result3["type"] == RESULT_TYPE_ABORT
    assert result3["reason"] == "already_in_progress"

    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", side_effect=CannotConnect):
        result3 = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={"ip": "1.2.3.5", "macaddress": "00:00:00:00:00:01"},
        )
    assert result3["type"] == RESULT_TYPE_ABORT
    assert result3["reason"] == "cannot_connect"


@pytest.mark.parametrize(
    "source, data",
    [
        (
            config_entries.SOURCE_DHCP,
            {"ip": IP_ADDRESS, "macaddress": "aa:bb:cc:dd:ee:ff"},
        ),
        (
            config_entries.SOURCE_HOMEKIT,
            {"host": IP_ADDRESS, "properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        ),
    ],
)
async def test_discovered_by_dhcp_or_homekit(opp, source, data):
    """Test we can setup when discovered from dhcp or homekit."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    mocked_bulb = _mocked_bulb()
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": source}, data=data
        )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] is None

    with patch(f"{MODULE}.async_setup", return_value=True) as mock_async_setup, patch(
        f"{MODULE}.async_setup_entry", return_value=True
    ) as mock_async_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2["type"] == "create_entry"
    assert result2["data"] == {CONF_HOST: IP_ADDRESS, CONF_ID: "0x000000000015243f"}
    assert mock_async_setup.called
    assert mock_async_setup_entry.called


@pytest.mark.parametrize(
    "source, data",
    [
        (
            config_entries.SOURCE_DHCP,
            {"ip": IP_ADDRESS, "macaddress": "aa:bb:cc:dd:ee:ff"},
        ),
        (
            config_entries.SOURCE_HOMEKIT,
            {"host": IP_ADDRESS, "properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        ),
    ],
)
async def test_discovered_by_dhcp_or_homekit_failed_to_get_id(opp, source, data):
    """Test we abort if we cannot get the unique id when discovered from dhcp or homekit."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    mocked_bulb = _mocked_bulb()
    type(mocked_bulb).get_capabilities = MagicMock(return_value=None)
    with patch(f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": source}, data=data
        )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "cannot_connect"
