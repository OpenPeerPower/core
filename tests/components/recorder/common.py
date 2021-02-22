"""Common test utils for working with recorder."""

from datetime import timedelta

from openpeerpower.components import recorder
from openpeerpower.util import dt as dt_util

from tests.common import fire_time_changed


def wait_recording_done.opp):
    """Block till recording is done."""
   .opp.block_till_done()
    trigger_db_commit.opp)
   .opp.block_till_done()
   .opp.data[recorder.DATA_INSTANCE].block_till_done()
   .opp.block_till_done()


async def async_wait_recording_done.opp):
    """Block till recording is done."""
    await.opp.loop.run_in_executor(None, wait_recording_done,.opp)


def trigger_db_commit.opp):
    """Force the recorder to commit."""
    for _ in range(recorder.DEFAULT_COMMIT_INTERVAL):
        # We only commit on time change
        fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=1))


def corrupt_db_file(test_db_file):
    """Corrupt an sqlite3 database file."""
    with open(test_db_file, "w+") as fhandle:
        fhandle.seek(200)
        fhandle.write("I am a corrupt db" * 100)
