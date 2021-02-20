"""Tests Open Peer Power temperature helpers."""
import pytest

from openpeerpower.const import (
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from openpeerpowerr.helpers.temperature import display_temp

TEMP = 24.636626


def test_temperature_not_a_number.opp):
    """Test that temperature is a number."""
    temp = "Temperature"
    with pytest.raises(Exception) as exception:
        display_temp.opp, temp, TEMP_CELSIUS, PRECISION_HALVES)

    assert f"Temperature is not a number: {temp}" in str(exception.value)


def test_celsius_op.ves.opp):
    """Test temperature to celsius rounding to halves."""
    assert display_temp.opp, TEMP, TEMP_CELSIUS, PRECISION_HALVES) == 24.5


def test_celsius_tenths.opp):
    """Test temperature to celsius rounding to tenths."""
    assert display_temp.opp, TEMP, TEMP_CELSIUS, PRECISION_TENTHS) == 24.6


def test_fahrenheit_wholes.opp):
    """Test temperature to fahrenheit rounding to wholes."""
    assert display_temp.opp, TEMP, TEMP_FAHRENHEIT, PRECISION_WHOLE) == -4
