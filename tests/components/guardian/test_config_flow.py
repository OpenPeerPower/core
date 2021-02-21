"""Define tests for the Elexa Guardian config flow."""
from unittest.mock import patch

from aioguardian.errors import GuardianError

from openpeerpower import data_entry_flow
from openpeerpower.components.guardian import CONF_UID, DOMAIN
from openpeerpower.components.guardian.config_flow import (
    async_get_pin_from_discovery_hostname,
    async_get_pin_from_uid,
)
from openpeerpower.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from openpeerpower.const import CONF_IP_ADDRESS, CONF_PORT

from tests.common import MockConfigEntry


async def test_duplicate_error.opp, ping_client):
    """Test that errors are shown when duplicate entries are added."""
    conf = {CONF_IP_ADDRESS: "192.168.1.100", CONF_PORT: 7777}

    MockConfigEntry(domain=DOMAIN, unique_id="guardian_3456", data=conf).add_to.opp(
       .opp
    )

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_connect_error.opp):
    """Test that the config entry errors out if the device cannot connect."""
    conf = {CONF_IP_ADDRESS: "192.168.1.100", CONF_PORT: 7777}

    with patch(
        "aioguardian.client.Client.connect",
        side_effect=GuardianError,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {CONF_IP_ADDRESS: "cannot_connect"}


async def test_get_pin_from_discovery_hostname():
    """Test getting a device PIN from the zeroconf-discovered hostname."""
    pin = async_get_pin_from_discovery_hostname("GVC1-3456.local.")
    assert pin == "3456"


async def test_get_pin_from_uid():
    """Test getting a device PIN from its UID."""
    pin = async_get_pin_from_uid("ABCDEF123456")
    assert pin == "3456"


async def test_step_user.opp, ping_client):
    """Test the user step."""
    conf = {CONF_IP_ADDRESS: "192.168.1.100", CONF_PORT: 7777}

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "ABCDEF123456"
    assert result["data"] == {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_PORT: 7777,
        CONF_UID: "ABCDEF123456",
    }


async def test_step_zeroconf.opp, ping_client):
    """Test the zeroconf step."""
    zeroconf_data = {
        "host": "192.168.1.100",
        "port": 7777,
        "hostname": "GVC1-ABCD.local.",
        "type": "_api._udp.local.",
        "name": "Guardian Valve Controller API._api._udp.local.",
        "properties": {"_raw": {}},
    }

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zeroconf_confirm"

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "ABCDEF123456"
    assert result["data"] == {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_PORT: 7777,
        CONF_UID: "ABCDEF123456",
    }


async def test_step_zeroconf_already_in_progress.opp):
    """Test the zeroconf step aborting because it's already in progress."""
    zeroconf_data = {
        "host": "192.168.1.100",
        "port": 7777,
        "hostname": "GVC1-ABCD.local.",
        "type": "_api._udp.local.",
        "name": "Guardian Valve Controller API._api._udp.local.",
        "properties": {"_raw": {}},
    }

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zeroconf_confirm"

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_in_progress"


async def test_step_zeroconf_no_discovery_info.opp):
    """Test the zeroconf step aborting because no discovery info came along."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "cannot_connect"
