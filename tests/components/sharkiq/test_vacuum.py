"""Test the Shark IQ vacuum entity."""
from __future__ import annotations

from copy import deepcopy
import enum
from typing import Any, Iterable
from unittest.mock import patch

import pytest
from sharkiqpy import AylaApi, SharkIqAuthError, SharkIqNotAuthedError, SharkIqVacuum

from openpeerpower.components.openpeerpower import SERVICE_UPDATE_ENTITY
from openpeerpower.components.sharkiq import DOMAIN
from openpeerpower.components.sharkiq.vacuum import (
    ATTR_ERROR_CODE,
    ATTR_ERROR_MSG,
    ATTR_LOW_LIGHT,
    ATTR_RECHARGE_RESUME,
    FAN_SPEEDS_MAP,
)
from openpeerpower.components.vacuum import (
    ATTR_BATTERY_LEVEL,
    ATTR_FAN_SPEED,
    ATTR_FAN_SPEED_LIST,
    SERVICE_LOCATE,
    SERVICE_PAUSE,
    SERVICE_RETURN_TO_BASE,
    SERVICE_SET_FAN_SPEED,
    SERVICE_START,
    SERVICE_STOP,
    STATE_CLEANING,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    SUPPORT_BATTERY,
    SUPPORT_FAN_SPEED,
    SUPPORT_LOCATE,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STATUS,
    SUPPORT_STOP,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_UNAVAILABLE,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import device_registry as dr, entity_registry as er
from openpeerpower.setup import async_setup_component

from .const import (
    CONFIG,
    ENTRY_ID,
    SHARK_DEVICE_DICT,
    SHARK_METADATA_DICT,
    SHARK_PROPERTIES_DICT,
    TEST_USERNAME,
)

from tests.common import MockConfigEntry

VAC_ENTITY_ID = f"vacuum.{SHARK_DEVICE_DICT['product_name'].lower()}"
EXPECTED_FEATURES = (
    SUPPORT_BATTERY
    | SUPPORT_FAN_SPEED
    | SUPPORT_PAUSE
    | SUPPORT_RETURN_HOME
    | SUPPORT_START
    | SUPPORT_STATE
    | SUPPORT_STATUS
    | SUPPORT_STOP
    | SUPPORT_LOCATE
)


class MockAyla(AylaApi):
    """Mocked AylaApi that doesn't do anything."""

    async def async_sign_in(self):
        """Instead of signing in, just return."""

    async def async_list_devices(self) -> list[dict]:
        """Return the device list."""
        return [SHARK_DEVICE_DICT]

    async def async_get_devices(self, update: bool = True) -> list[SharkIqVacuum]:
        """Get the list of devices."""
        shark = MockShark(self, SHARK_DEVICE_DICT)
        shark.properties_full = deepcopy(SHARK_PROPERTIES_DICT)
        shark._update_metadata(SHARK_METADATA_DICT)  # pylint: disable=protected-access
        return [shark]

    async def async_request(self, http_method: str, url: str, **kwargs):
        """Don't make an HTTP request."""


class MockShark(SharkIqVacuum):
    """Mocked SharkIqVacuum that won't hit the API."""

    async def async_update(self, property_list: Iterable[str] | None = None):
        """Don't do anything."""

    def set_property_value(self, property_name, value):
        """Set a property locally without hitting the API."""
        if isinstance(property_name, enum.Enum):
            property_name = property_name.value
        if isinstance(value, enum.Enum):
            value = value.value
        self.properties_full[property_name]["value"] = value

    async def async_set_property_value(self, property_name, value):
        """Set a property locally without hitting the API."""
        self.set_property_value(property_name, value)


@pytest.fixture(autouse=True)
@patch("sharkiqpy.ayla_api.AylaApi", MockAyla)
async def setup_integration(opp):
    """Build the mock integration."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=TEST_USERNAME, data=CONFIG, entry_id=ENTRY_ID
    )
    entry.add_to_opp(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()


async def test_simple_properties(opp: OpenPeerPower):
    """Test that simple properties work as intended."""
    state = opp.states.get(VAC_ENTITY_ID)
    registry = er.async_get(opp)
    entity = registry.async_get(VAC_ENTITY_ID)

    assert entity
    assert state
    assert state.state == STATE_CLEANING
    assert entity.unique_id == "AC000Wxxxxxxxxx"


@pytest.mark.parametrize(
    "attribute,target_value",
    [
        (ATTR_SUPPORTED_FEATURES, EXPECTED_FEATURES),
        (ATTR_BATTERY_LEVEL, 50),
        (ATTR_FAN_SPEED, "Eco"),
        (ATTR_FAN_SPEED_LIST, list(FAN_SPEEDS_MAP)),
        (ATTR_ERROR_CODE, 7),
        (ATTR_ERROR_MSG, "Cliff sensor is blocked"),
        (ATTR_LOW_LIGHT, False),
        (ATTR_RECHARGE_RESUME, True),
    ],
)
async def test_initial_attributes(
    opp: OpenPeerPower, attribute: str, target_value: Any
):
    """Test initial config attributes."""
    state = opp.states.get(VAC_ENTITY_ID)
    assert state.attributes.get(attribute) == target_value


@pytest.mark.parametrize(
    "service,target_state",
    [
        (SERVICE_STOP, STATE_IDLE),
        (SERVICE_PAUSE, STATE_PAUSED),
        (SERVICE_RETURN_TO_BASE, STATE_RETURNING),
        (SERVICE_START, STATE_CLEANING),
    ],
)
async def test_cleaning_states(opp: OpenPeerPower, service: str, target_state: str):
    """Test cleaning states."""
    service_data = {ATTR_ENTITY_ID: VAC_ENTITY_ID}
    await opp.services.async_call("vacuum", service, service_data, blocking=True)
    state = opp.states.get(VAC_ENTITY_ID)
    assert state.state == target_state


@pytest.mark.parametrize("fan_speed", list(FAN_SPEEDS_MAP))
async def test_fan_speed(opp: OpenPeerPower, fan_speed: str) -> None:
    """Test setting fan speeds."""
    service_data = {ATTR_ENTITY_ID: VAC_ENTITY_ID, ATTR_FAN_SPEED: fan_speed}
    await opp.services.async_call(
        "vacuum", SERVICE_SET_FAN_SPEED, service_data, blocking=True
    )
    state = opp.states.get(VAC_ENTITY_ID)
    assert state.attributes.get(ATTR_FAN_SPEED) == fan_speed


@pytest.mark.parametrize(
    "device_property,target_value",
    [
        ("manufacturer", "Shark"),
        ("model", "RV1001AE"),
        ("name", "Sharknado"),
        ("sw_version", "Dummy Firmware 1.0"),
    ],
)
async def test_device_properties(
    opp: OpenPeerPower, device_property: str, target_value: str
):
    """Test device properties."""
    registry = dr.async_get(opp)
    device = registry.async_get_device({(DOMAIN, "AC000Wxxxxxxxxx")})
    assert getattr(device, device_property) == target_value


async def test_locate(opp):
    """Test that the locate command works."""
    with patch.object(SharkIqVacuum, "async_find_device") as mock_locate:
        data = {ATTR_ENTITY_ID: VAC_ENTITY_ID}
        await opp.services.async_call("vacuum", SERVICE_LOCATE, data, blocking=True)
        mock_locate.assert_called_once()


@pytest.mark.parametrize(
    "side_effect,success",
    [
        (None, True),
        (SharkIqAuthError, False),
        (SharkIqNotAuthedError, False),
        (RuntimeError, False),
    ],
)
@patch("sharkiqpy.ayla_api.AylaApi", MockAyla)
async def test_coordinator_updates(
    opp: OpenPeerPower, side_effect: Exception | None, success: bool
) -> None:
    """Test the update coordinator update functions."""
    coordinator = opp.data[DOMAIN][ENTRY_ID]

    await async_setup_component(opp, "openpeerpower", {})

    with patch.object(
        MockShark, "async_update", side_effect=side_effect
    ) as mock_update:
        data = {ATTR_ENTITY_ID: [VAC_ENTITY_ID]}
        await opp.services.async_call(
            "openpeerpower", SERVICE_UPDATE_ENTITY, data, blocking=True
        )
        assert coordinator.last_update_success == success
        mock_update.assert_called_once()

    state = opp.states.get(VAC_ENTITY_ID)
    assert (state.state == STATE_UNAVAILABLE) != success
