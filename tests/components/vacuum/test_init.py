"""The tests for Vacuum."""
from openpeerpower.components import vacuum


def test_deprecated_base_class(caplog):
    """Test deprecated base class."""

    class CustomVacuum(vacuum.VacuumDevice):
        pass

    class CustomStateVacuum(vacuum.StateVacuumDevice):
        pass

    CustomVacuum()
    assert "VacuumDevice is deprecated, modify CustomVacuum" in caplog.text

    CustomStateVacuum()
    assert "StateVacuumDevice is deprecated, modify CustomStateVacuum" in caplog.text
