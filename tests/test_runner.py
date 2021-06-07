"""Test the runner."""

import threading
from unittest.mock import patch

from openpeerpower import core, runner
from openpeerpower.util import executor, thread

# https://github.com/openpeerpower/supervisor/blob/main/supervisor/docker/openpeerpower.py
SUPERVISOR_HARD_TIMEOUT = 220

TIMEOUT_SAFETY_MARGIN = 10


async def test_cumulative_shutdown_timeout_less_than_supervisor():
    """Verify the cumulative shutdown timeout is at least 10s less than the supervisor."""
    assert (
        core.STAGE_1_SHUTDOWN_TIMEOUT
        + core.STAGE_2_SHUTDOWN_TIMEOUT
        + core.STAGE_3_SHUTDOWN_TIMEOUT
        + executor.EXECUTOR_SHUTDOWN_TIMEOUT
        + thread.THREADING_SHUTDOWN_TIMEOUT
        + TIMEOUT_SAFETY_MARGIN
        <= SUPERVISOR_HARD_TIMEOUT
    )


async def test_setup_and_run_opp(opp, tmpdir):
    """Test we can setup and run."""
    test_dir = tmpdir.mkdir("config")
    default_config = runner.RuntimeConfig(test_dir)

    with patch("openpeerpower.bootstrap.async_setup_opp., return_value=opp), patch(
        "threading._shutdown"
    ), patch("openpeerpower.core.OpenPeerPower.async_run") as mock_run:
        await runner.setup_and_run_opp(default_config)
        assert threading._shutdown == thread.deadlock_safe_shutdown

    assert mock_run.called
