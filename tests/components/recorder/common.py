"""Common test utils for working with recorder."""
from datetime import timedelta

from openpeerpower import core as ha
from openpeerpower.components import recorder
from openpeerpower.core import OpenPeerPower
from openpeerpower.util import dt as dt_util

from tests.common import async_fire_time_changed, fire_time_changed

DEFAULT_PURGE_TASKS = 3


def wait_recording_done(opp: OpenPeerPower) -> None:
    """Block till recording is done."""
    opp.block_till_done()
    trigger_db_commit(opp)
    opp.block_till_done()
    opp.data[recorder.DATA_INSTANCE].block_till_done()
    opp.block_till_done()


async def async_wait_recording_done_without_instance(opp: OpenPeerPower) -> None:
    """Block till recording is done."""
    await opp.loop.run_in_executor(None, wait_recording_done, opp)


def trigger_db_commit(opp: OpenPeerPower) -> None:
    """Force the recorder to commit."""
    for _ in range(recorder.DEFAULT_COMMIT_INTERVAL):
        # We only commit on time change
        fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=1))


async def async_wait_recording_done(
    opp: OpenPeerPower,
    instance: recorder.Recorder,
) -> None:
    """Async wait until recording is done."""
    await opp.async_block_till_done()
    async_trigger_db_commit(opp)
    await opp.async_block_till_done()
    await async_recorder_block_till_done(opp, instance)
    await opp.async_block_till_done()


async def async_wait_purge_done(
    opp: OpenPeerPower, instance: recorder.Recorder, max: int = None
) -> None:
    """Wait for max number of purge events.

    Because a purge may insert another PurgeTask into
    the queue after the WaitTask finishes, we need up to
    a maximum number of WaitTasks that we will put into the
    queue.
    """
    if not max:
        max = DEFAULT_PURGE_TASKS
    for _ in range(max + 1):
        await async_wait_recording_done(opp, instance)


@ha.callback
def async_trigger_db_commit(opp: OpenPeerPower) -> None:
    """Fore the recorder to commit. Async friendly."""
    for _ in range(recorder.DEFAULT_COMMIT_INTERVAL):
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=1))


async def async_recorder_block_till_done(
    opp: OpenPeerPower,
    instance: recorder.Recorder,
) -> None:
    """Non blocking version of recorder.block_till_done()."""
    await opp.async_add_executor_job(instance.block_till_done)


def corrupt_db_file(test_db_file):
    """Corrupt an sqlite3 database file."""
    with open(test_db_file, "w+") as fhandle:
        fhandle.seek(200)
        fhandle.write("I am a corrupt db" * 100)
