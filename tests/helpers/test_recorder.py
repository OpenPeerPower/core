"""The tests for the recorder helpers."""

from unittest.mock import patch

from openpeerpower.helpers import recorder

from tests.common import async_init_recorder_component


async def test_async_migration_in_progress(opp):
    """Test async_migration_in_progress wraps the recorder."""
    with patch(
        "openpeerpower.components.recorder.async_migration_in_progress",
        return_value=False,
    ):
        assert await recorder.async_migration_in_progress(opp) is False

    # The recorder is not loaded
    with patch(
        "openpeerpower.components.recorder.async_migration_in_progress",
        return_value=True,
    ):
        assert await recorder.async_migration_in_progress(opp) is False

    await async_init_recorder_component(opp)

    # The recorder is now loaded
    with patch(
        "openpeerpower.components.recorder.async_migration_in_progress",
        return_value=True,
    ):
        assert await recorder.async_migration_in_progress(opp) is True
