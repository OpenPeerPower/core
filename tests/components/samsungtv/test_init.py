"""Tests for the Samsung TV Integration."""
from unittest.mock import Mock, call, patch

from openpeerpower.components.media_player.const import DOMAIN, SUPPORT_TURN_ON
from openpeerpower.components.samsungtv.const import (
    CONF_ON_ACTION,
    DOMAIN as SAMSUNGTV_DOMAIN,
    METHOD_WEBSOCKET,
)
from openpeerpower.components.samsungtv.media_player import SUPPORT_SAMSUNGTV
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    CONF_HOST,
    CONF_METHOD,
    CONF_NAME,
    SERVICE_VOLUME_UP,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.setup import async_setup_component

ENTITY_ID = f"{DOMAIN}.fake_name"
MOCK_CONFIG = {
    SAMSUNGTV_DOMAIN: [
        {
            CONF_HOST: "fake_host",
            CONF_NAME: "fake_name",
            CONF_ON_ACTION: [{"delay": "00:00:01"}],
            CONF_METHOD: METHOD_WEBSOCKET,
        }
    ]
}
REMOTE_CALL = {
    "name": "OpenPeerPower",
    "description": "OpenPeerPower",
    "id": "ha.component.samsung",
    "host": MOCK_CONFIG[SAMSUNGTV_DOMAIN][0][CONF_HOST],
    "method": "legacy",
    "port": None,
    "timeout": 1,
}


async def test_setup(opp: OpenPeerPower, remote: Mock):
    """Test Samsung TV integration is setup."""
    with patch("openpeerpower.components.samsungtv.bridge.Remote") as remote, patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        with patch("openpeerpower.components.samsungtv.bridge.Remote") as remote:
            await async_setup_component(opp, SAMSUNGTV_DOMAIN, MOCK_CONFIG)
            await opp.async_block_till_done()
        state = opp.states.get(ENTITY_ID)

        # test name and turn_on
        assert state
        assert state.name == "fake_name"
        assert (
            state.attributes[ATTR_SUPPORTED_FEATURES]
            == SUPPORT_SAMSUNGTV | SUPPORT_TURN_ON
        )

        # test host and port
        assert await opp.services.async_call(
            DOMAIN, SERVICE_VOLUME_UP, {ATTR_ENTITY_ID: ENTITY_ID}, True
        )
        assert remote.call_args == call(REMOTE_CALL)


async def test_setup_duplicate_config(opp: OpenPeerPower, remote: Mock, caplog):
    """Test duplicate setup of platform."""
    DUPLICATE = {
        SAMSUNGTV_DOMAIN: [
            MOCK_CONFIG[SAMSUNGTV_DOMAIN][0],
            MOCK_CONFIG[SAMSUNGTV_DOMAIN][0],
        ]
    }
    await async_setup_component(opp, SAMSUNGTV_DOMAIN, DUPLICATE)
    await opp.async_block_till_done()
    assert opp.states.get(ENTITY_ID) is None
    assert len(opp.states.async_all()) == 0
    assert "duplicate host entries found" in caplog.text


async def test_setup_duplicate_entries(opp: OpenPeerPower, remote: Mock, caplog):
    """Test duplicate setup of platform."""
    await async_setup_component(opp, SAMSUNGTV_DOMAIN, MOCK_CONFIG)
    await opp.async_block_till_done()
    assert opp.states.get(ENTITY_ID)
    assert len(opp.states.async_all()) == 1
    await async_setup_component(opp, SAMSUNGTV_DOMAIN, MOCK_CONFIG)
    assert len(opp.states.async_all()) == 1
