"""The sensor tests for the griddy platform."""

from unittest.mock import patch

from pydexcom import SessionError

from openpeerpower.components.dexcom.const import MMOL_L
from openpeerpower.const import (
    CONF_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)

from tests.components.dexcom import GLUCOSE_READING, init_integration


async def test_sensors(opp):
    """Test we get sensor data."""
    await init_integration(opp)

    test_username_glucose_value = opp.states.get(
        "sensor.dexcom_test_username_glucose_value"
    )
    assert test_username_glucose_value.state == str(GLUCOSE_READING.value)
    test_username_glucose_trend = opp.states.get(
        "sensor.dexcom_test_username_glucose_trend"
    )
    assert test_username_glucose_trend.state == GLUCOSE_READING.trend_description


async def test_sensors_unknown(opp):
    """Test we handle sensor state unknown."""
    await init_integration(opp)

    with patch(
        "openpeerpower.components.dexcom.Dexcom.get_current_glucose_reading",
        return_value=None,
    ):
        await opp.helpers.entity_component.async_update_entity(
            "sensor.dexcom_test_username_glucose_value"
        )
        await opp.helpers.entity_component.async_update_entity(
            "sensor.dexcom_test_username_glucose_trend"
        )

    test_username_glucose_value = opp.states.get(
        "sensor.dexcom_test_username_glucose_value"
    )
    assert test_username_glucose_value.state == STATE_UNKNOWN
    test_username_glucose_trend = opp.states.get(
        "sensor.dexcom_test_username_glucose_trend"
    )
    assert test_username_glucose_trend.state == STATE_UNKNOWN


async def test_sensors_update_failed(opp):
    """Test we handle sensor update failed."""
    await init_integration(opp)

    with patch(
        "openpeerpower.components.dexcom.Dexcom.get_current_glucose_reading",
        side_effect=SessionError,
    ):
        await opp.helpers.entity_component.async_update_entity(
            "sensor.dexcom_test_username_glucose_value"
        )
        await opp.helpers.entity_component.async_update_entity(
            "sensor.dexcom_test_username_glucose_trend"
        )

    test_username_glucose_value = opp.states.get(
        "sensor.dexcom_test_username_glucose_value"
    )
    assert test_username_glucose_value.state == STATE_UNAVAILABLE
    test_username_glucose_trend = opp.states.get(
        "sensor.dexcom_test_username_glucose_trend"
    )
    assert test_username_glucose_trend.state == STATE_UNAVAILABLE


async def test_sensors_options_changed(opp):
    """Test we handle sensor unavailable."""
    entry = await init_integration(opp)

    test_username_glucose_value = opp.states.get(
        "sensor.dexcom_test_username_glucose_value"
    )
    assert test_username_glucose_value.state == str(GLUCOSE_READING.value)
    test_username_glucose_trend = opp.states.get(
        "sensor.dexcom_test_username_glucose_trend"
    )
    assert test_username_glucose_trend.state == GLUCOSE_READING.trend_description

    with patch(
        "openpeerpower.components.dexcom.Dexcom.get_current_glucose_reading",
        return_value=GLUCOSE_READING,
    ), patch(
        "openpeerpower.components.dexcom.Dexcom.create_session",
        return_value="test_session_id",
    ):
        opp.config_entries.async_update_entry(
            entry=entry,
            options={CONF_UNIT_OF_MEASUREMENT: MMOL_L},
        )
        await opp.async_block_till_done()

    assert entry.options == {CONF_UNIT_OF_MEASUREMENT: MMOL_L}

    test_username_glucose_value = opp.states.get(
        "sensor.dexcom_test_username_glucose_value"
    )
    assert test_username_glucose_value.state == str(GLUCOSE_READING.mmol_l)
    test_username_glucose_trend = opp.states.get(
        "sensor.dexcom_test_username_glucose_trend"
    )
    assert test_username_glucose_trend.state == GLUCOSE_READING.trend_description
