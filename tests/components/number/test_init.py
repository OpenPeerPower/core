"""The tests for the Number component."""
from unittest.mock import MagicMock

from openpeerpower.components.number import NumberEntity


class MockDefaultNumberEntity(NumberEntity):
    """Mock NumberEntity device to use in tests."""

    @property
    def value(self):
        """Return the current value."""
        return 0.5


class MockNumberEntity(NumberEntity):
    """Mock NumberEntity device to use in tests."""

    @property
    def max_value(self) -> float:
        """Return the max value."""
        return 1.0

    @property
    def value(self):
        """Return the current value."""
        return 0.5


async def test_step.opp):
    """Test the step calculation."""
    number = MockDefaultNumberEntity()
    assert number.step == 1.0

    number_2 = MockNumberEntity()
    assert number_2.step == 0.1


async def test_sync_set_value.opp):
    """Test if async set_value calls sync set_value."""
    number = MockDefaultNumberEntity()
    number.opp =.opp

    number.set_value = MagicMock()
    await number.async_set_value(42)

    assert number.set_value.called
    assert number.set_value.call_args[0][0] == 42
