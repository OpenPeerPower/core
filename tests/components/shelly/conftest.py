"""Test configuration for Shelly."""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from openpeerpower.components.shelly import ShellyDeviceWrapper
from openpeerpower.components.shelly.const import (
    COAP,
    DATA_CONFIG_ENTRY,
    DOMAIN,
    EVENT_SHELLY_CLICK,
)
from openpeerpower.core import callback as op_callback
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry, async_mock_service, mock_device_registry

MOCK_SETTINGS = {
    "name": "Test name",
    "mode": "relay",
    "device": {
        "mac": "test-mac",
        "hostname": "test-host",
        "type": "SHSW-25",
        "num_outputs": 2,
    },
    "coiot": {"update_period": 15},
    "fw": "20201124-092159/v1.9.0@57ac4ad8",
    "relays": [{"btn_type": "momentary"}, {"btn_type": "toggle"}],
    "rollers": [{"positioning": True}],
}

MOCK_BLOCKS = [
    Mock(
        sensor_ids={"inputEvent": "S", "inputEventCnt": 2},
        channel="0",
        type="relay",
        set_state=AsyncMock(side_effect=lambda turn: {"ison": turn == "on"}),
    ),
    Mock(
        sensor_ids={"roller": "stop", "rollerPos": 0},
        channel="1",
        type="roller",
        set_state=AsyncMock(
            side_effect=lambda go, roller_pos=0: {
                "current_pos": roller_pos,
                "state": go,
            }
        ),
    ),
]


MOCK_SHELLY = {
    "mac": "test-mac",
    "auth": False,
    "fw": "20201124-092854/v1.9.0@57ac4ad8",
    "num_outputs": 2,
}


@pytest.fixture(autouse=True)
def mock_coap():
    """Mock out coap."""
    with patch("openpeerpower.components.shelly.get_coap_context"):
        yield


@pytest.fixture
def device_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


@pytest.fixture
def events.opp):
    """Yield caught shelly_click events."""
    op_events = []
    opp.bus.async_listen(EVENT_SHELLY_CLICK, op_callback(op_events.append))
    yield op_events


@pytest.fixture
async def coap_wrapper(opp):
    """Setups a coap wrapper with mocked device."""
    await async_setup_component(opp, "shelly", {})

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"sleep_period": 0, "model": "SHSW-25"},
        unique_id="12345678",
    )
    config_entry.add_to_opp(opp)

    device = Mock(
        blocks=MOCK_BLOCKS,
        settings=MOCK_SETTINGS,
        shelly=MOCK_SHELLY,
        update=AsyncMock(),
        initialized=True,
    )

    opp.data[DOMAIN] = {DATA_CONFIG_ENTRY: {}}
    opp.data[DOMAIN][DATA_CONFIG_ENTRY][config_entry.entry_id] = {}
    wrapper = opp.data[DOMAIN][DATA_CONFIG_ENTRY][config_entry.entry_id][
        COAP
    ] = ShellyDeviceWrapper.opp, config_entry, device)

    await wrapper.async_setup()

    return wrapper
