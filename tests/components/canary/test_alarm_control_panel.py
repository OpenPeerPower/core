"""The tests for the Canary alarm_control_panel platform."""
from unittest.mock import PropertyMock, patch

from canary.api import LOCATION_MODE_AWAY, LOCATION_MODE_HOME, LOCATION_MODE_NIGHT

from openpeerpower.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from openpeerpower.components.canary import DOMAIN
from openpeerpower.const import (
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_DISARM,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_UNKNOWN,
)
from openpeerpowerr.setup import async_setup_component

from . import mock_device, mock_location, mock_mode

from tests.common import mock_registry


async def test_alarm_control_panel.opp, canary) -> None:
    """Test the creation and values of the alarm_control_panel for Canary."""
    await async_setup_component.opp, "persistent_notification", {})

    registry = mock_registry.opp)
    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    mocked_location = mock_location(
        location_id=100,
        name="Home",
        is_celsius=True,
        is_private=False,
        mode=mock_mode(7, "standby"),
        devices=[online_device_at_home],
    )

    instance = canary.return_value
    instance.get_locations.return_value = [mocked_location]

    config = {DOMAIN: {"username": "test-username", "password": "test-password"}}
    with patch("openpeerpower.components.canary.PLATFORMS", ["alarm_control_panel"]):
        assert await async_setup_component.opp, DOMAIN, config)
        await opp.async_block_till_done()

    entity_id = "alarm_control_panel.home"
    entity_entry = registry.async_get(entity_id)
    assert entity_entry
    assert entity_entry.unique_id == "100"

    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert not state.attributes["private"]

    # test private system
    type(mocked_location).is_private = PropertyMock(return_value=True)

    await.opp.helpers.entity_component.async_update_entity(entity_id)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_ALARM_DISARMED
    assert state.attributes["private"]

    type(mocked_location).is_private = PropertyMock(return_value=False)

    # test armed home
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(4, LOCATION_MODE_HOME)
    )

    await.opp.helpers.entity_component.async_update_entity(entity_id)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_ALARM_ARMED_HOME

    # test armed away
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(5, LOCATION_MODE_AWAY)
    )

    await.opp.helpers.entity_component.async_update_entity(entity_id)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_ALARM_ARMED_AWAY

    # test armed night
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(6, LOCATION_MODE_NIGHT)
    )

    await.opp.helpers.entity_component.async_update_entity(entity_id)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_ALARM_ARMED_NIGHT


async def test_alarm_control_panel_services.opp, canary) -> None:
    """Test the services of the alarm_control_panel for Canary."""
    await async_setup_component.opp, "persistent_notification", {})

    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    mocked_location = mock_location(
        location_id=100,
        name="Home",
        is_celsius=True,
        mode=mock_mode(1, "disarmed"),
        devices=[online_device_at_home],
    )

    instance = canary.return_value
    instance.get_locations.return_value = [mocked_location]

    config = {DOMAIN: {"username": "test-username", "password": "test-password"}}
    with patch("openpeerpower.components.canary.PLATFORMS", ["alarm_control_panel"]):
        assert await async_setup_component.opp, DOMAIN, config)
        await opp.async_block_till_done()

    entity_id = "alarm_control_panel.home"

    # test arm away
    await.opp.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        service_data={"entity_id": entity_id},
        blocking=True,
    )
    instance.set_location_mode.assert_called_with(100, LOCATION_MODE_AWAY)

    # test arm home
    await.opp.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_HOME,
        service_data={"entity_id": entity_id},
        blocking=True,
    )
    instance.set_location_mode.assert_called_with(100, LOCATION_MODE_HOME)

    # test arm night
    await.opp.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_NIGHT,
        service_data={"entity_id": entity_id},
        blocking=True,
    )
    instance.set_location_mode.assert_called_with(100, LOCATION_MODE_NIGHT)

    # test disarm
    await.opp.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        service_data={"entity_id": entity_id},
        blocking=True,
    )
    instance.set_location_mode.assert_called_with(100, "disarmed", True)
