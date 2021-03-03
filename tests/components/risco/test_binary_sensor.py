"""Tests for the Risco binary sensors."""
from unittest.mock import PropertyMock, patch

from openpeerpower.components.risco import CannotConnectError, UnauthorizedError
from openpeerpower.components.risco.const import DOMAIN
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.helpers.entity_component import async_update_entity

from .util import TEST_CONFIG, TEST_SITE_UUID, setup_risco
from .util import two_zone_alarm  # noqa: F401

from tests.common import MockConfigEntry

FIRST_ENTITY_ID = "binary_sensor.zone_0"
SECOND_ENTITY_ID = "binary_sensor.zone_1"


async def test_cannot_connect(opp):
    """Test connection error."""

    with patch(
        "openpeerpower.components.risco.RiscoAPI.login",
        side_effect=CannotConnectError,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=TEST_CONFIG)
        config_entry.add_to_opp(opp)
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        registry = await opp.helpers.entity_registry.async_get_registry()
        assert not registry.async_is_registered(FIRST_ENTITY_ID)
        assert not registry.async_is_registered(SECOND_ENTITY_ID)


async def test_unauthorized(opp):
    """Test unauthorized error."""

    with patch(
        "openpeerpower.components.risco.RiscoAPI.login",
        side_effect=UnauthorizedError,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=TEST_CONFIG)
        config_entry.add_to_opp(opp)
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        registry = await opp.helpers.entity_registry.async_get_registry()
        assert not registry.async_is_registered(FIRST_ENTITY_ID)
        assert not registry.async_is_registered(SECOND_ENTITY_ID)


async def test_setup(opp, two_zone_alarm):  # noqa: F811
    """Test entity setup."""
    registry = await opp.helpers.entity_registry.async_get_registry()

    assert not registry.async_is_registered(FIRST_ENTITY_ID)
    assert not registry.async_is_registered(SECOND_ENTITY_ID)

    await setup_risco(opp)

    assert registry.async_is_registered(FIRST_ENTITY_ID)
    assert registry.async_is_registered(SECOND_ENTITY_ID)

    registry = await opp.helpers.device_registry.async_get_registry()
    device = registry.async_get_device({(DOMAIN, TEST_SITE_UUID + "_zone_0")})
    assert device is not None
    assert device.manufacturer == "Risco"

    device = registry.async_get_device({(DOMAIN, TEST_SITE_UUID + "_zone_1")})
    assert device is not None
    assert device.manufacturer == "Risco"


async def _check_state(opp, alarm, triggered, bypassed, entity_id, zone_id):
    with patch.object(
        alarm.zones[zone_id],
        "triggered",
        new_callable=PropertyMock(return_value=triggered),
    ), patch.object(
        alarm.zones[zone_id],
        "bypassed",
        new_callable=PropertyMock(return_value=bypassed),
    ):
        await async_update_entity(opp, entity_id)
        await opp.async_block_till_done()

        expected_triggered = STATE_ON if triggered else STATE_OFF
        assert opp.states.get(entity_id).state == expected_triggered
        assert opp.states.get(entity_id).attributes["bypassed"] == bypassed
        assert opp.states.get(entity_id).attributes["zone_id"] == zone_id


async def test_states(opp, two_zone_alarm):  # noqa: F811
    """Test the various alarm states."""
    await setup_risco(opp)

    await _check_state(opp, two_zone_alarm, True, True, FIRST_ENTITY_ID, 0)
    await _check_state(opp, two_zone_alarm, True, False, FIRST_ENTITY_ID, 0)
    await _check_state(opp, two_zone_alarm, False, True, FIRST_ENTITY_ID, 0)
    await _check_state(opp, two_zone_alarm, False, False, FIRST_ENTITY_ID, 0)
    await _check_state(opp, two_zone_alarm, True, True, SECOND_ENTITY_ID, 1)
    await _check_state(opp, two_zone_alarm, True, False, SECOND_ENTITY_ID, 1)
    await _check_state(opp, two_zone_alarm, False, True, SECOND_ENTITY_ID, 1)
    await _check_state(opp, two_zone_alarm, False, False, SECOND_ENTITY_ID, 1)


async def test_bypass(opp, two_zone_alarm):  # noqa: F811
    """Test bypassing a zone."""
    await setup_risco(opp)
    with patch("openpeerpower.components.risco.RiscoAPI.bypass_zone") as mock:
        data = {"entity_id": FIRST_ENTITY_ID}

        await opp.services.async_call(
            DOMAIN, "bypass_zone", service_data=data, blocking=True
        )

        mock.assert_awaited_once_with(0, True)


async def test_unbypass(opp, two_zone_alarm):  # noqa: F811
    """Test unbypassing a zone."""
    await setup_risco(opp)
    with patch("openpeerpower.components.risco.RiscoAPI.bypass_zone") as mock:
        data = {"entity_id": FIRST_ENTITY_ID}

        await opp.services.async_call(
            DOMAIN, "unbypass_zone", service_data=data, blocking=True
        )

        mock.assert_awaited_once_with(0, False)
