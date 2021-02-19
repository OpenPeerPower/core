"""Common test utils for working with recorder."""

from datetime import timedelta

from openpeerpower.components import recorder
from openpeerpowerr.util import dt as dt_util

from tests.common import fire_time_changed


def wait_recording_done.opp):
    """Block till recording is done."""
    trigger_db_commit.opp)
   .opp.block_till_done()
   .opp.data[recorder.DATA_INSTANCE].block_till_done()
   .opp.block_till_done()


def trigger_db_commit.opp):
    """Force the recorder to commit."""
    for _ in range(recorder.DEFAULT_COMMIT_INTERVAL):
        # We only commit on time change
        fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=1))
