"""The tests for hls streams."""
from __future__ import annotations

import asyncio
from collections import deque
from datetime import timedelta
from io import BytesIO
import logging
import os
import threading
from unittest.mock import patch

import async_timeout
import av
import pytest

from openpeerpower.components.stream import create_stream
from openpeerpower.components.stream.const import HLS_PROVIDER, RECORDER_PROVIDER
from openpeerpower.components.stream.core import Segment
from openpeerpower.components.stream.fmp4utils import get_init_and_moof_data
from openpeerpower.components.stream.recorder import recorder_save_worker
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.stream.common import generate_h264_video

TEST_TIMEOUT = 7.0  # Lower than 9s open peer power timeout
MAX_ABORT_SEGMENTS = 20  # Abort test to avoid looping forever


class SaveRecordWorkerSync:
    """
    Test fixture to manage RecordOutput thread for recorder_save_worker.

    This is used to assert that the worker is started and stopped cleanly
    to avoid thread leaks in tests.
    """

    def __init__(self):
        """Initialize SaveRecordWorkerSync."""
        self.reset()
        self._segments = None
        self._save_thread = None

    def recorder_save_worker(self, file_out: str, segments: deque[Segment]):
        """Mock method for patch."""
        logging.debug("recorder_save_worker thread started")
        assert self._save_thread is None
        self._segments = segments
        self._save_thread = threading.current_thread()
        self._save_event.set()

    async def get_segments(self):
        """Return the recorded video segments."""
        with async_timeout.timeout(TEST_TIMEOUT):
            await self._save_event.wait()
        return self._segments

    async def join(self):
        """Verify save worker was invoked and block on shutdown."""
        with async_timeout.timeout(TEST_TIMEOUT):
            await self._save_event.wait()
        self._save_thread.join(timeout=TEST_TIMEOUT)
        assert not self._save_thread.is_alive()

    def reset(self):
        """Reset callback state for reuse in tests."""
        self._save_thread = None
        self._save_event = asyncio.Event()


@pytest.fixture()
def record_worker_sync(opp):
    """Patch recorder_save_worker for clean thread shutdown for test."""
    sync = SaveRecordWorkerSync()
    with patch(
        "openpeerpower.components.stream.recorder.recorder_save_worker",
        side_effect=sync.recorder_save_worker,
        autospec=True,
    ):
        yield sync


async def test_record_stream(opp, opp_client, record_worker_sync):
    """
    Test record stream.

    Tests full integration with the stream component, and captures the
    stream worker and save worker to allow for clean shutdown of background
    threads.  The actual save logic is tested in test_recorder_save below.
    """
    await async_setup_component(opp, "stream", {"stream": {}})

    # Setup demo track
    source = generate_h264_video()
    stream = create_stream(opp, source)
    with patch.object(opp.config, "is_allowed_path", return_value=True):
        await stream.async_record("/example/path")

    # After stream decoding finishes, the record worker thread starts
    segments = await record_worker_sync.get_segments()
    assert len(segments) >= 1

    # Verify that the save worker was invoked, then block until its
    # thread completes and is shutdown completely to avoid thread leaks.
    await record_worker_sync.join()

    stream.stop()


async def test_record_lookback(opp, opp_client, stream_worker_sync, record_worker_sync):
    """Exercise record with loopback."""
    await async_setup_component(opp, "stream", {"stream": {}})

    source = generate_h264_video()
    stream = create_stream(opp, source)

    # Start an HLS feed to enable lookback
    stream.add_provider(HLS_PROVIDER)
    stream.start()

    with patch.object(opp.config, "is_allowed_path", return_value=True):
        await stream.async_record("/example/path", lookback=4)

    # This test does not need recorder cleanup since it is not fully exercised

    stream.stop()


async def test_recorder_timeout(opp, opp_client, stream_worker_sync):
    """
    Test recorder timeout.

    Mocks out the cleanup to assert that it is invoked after a timeout.
    This test does not start the recorder save thread.
    """
    await async_setup_component(opp, "stream", {"stream": {}})

    stream_worker_sync.pause()

    with patch("openpeerpower.components.stream.IdleTimer.fire") as mock_timeout:
        # Setup demo track
        source = generate_h264_video()

        stream = create_stream(opp, source)
        with patch.object(opp.config, "is_allowed_path", return_value=True):
            await stream.async_record("/example/path")
        recorder = stream.add_provider(RECORDER_PROVIDER)

        await recorder.recv()

        # Wait a minute
        future = dt_util.utcnow() + timedelta(minutes=1)
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        assert mock_timeout.called

        stream_worker_sync.resume()
        stream.stop()
        await opp.async_block_till_done()
        await opp.async_block_till_done()


async def test_record_path_not_allowed(opp, opp_client):
    """Test where the output path is not allowed by open peer power configuration."""
    await async_setup_component(opp, "stream", {"stream": {}})

    # Setup demo track
    source = generate_h264_video()
    stream = create_stream(opp, source)
    with patch.object(opp.config, "is_allowed_path", return_value=False), pytest.raises(
        OpenPeerPowerError
    ):
        await stream.async_record("/example/path")


async def test_recorder_save(tmpdir):
    """Test recorder save."""
    # Setup
    source = generate_h264_video()
    filename = f"{tmpdir}/test.mp4"

    # Run
    recorder_save_worker(
        filename, [Segment(1, *get_init_and_moof_data(source.getbuffer()), 4)]
    )

    # Assert
    assert os.path.exists(filename)


async def test_recorder_discontinuity(tmpdir):
    """Test recorder save across a discontinuity."""
    # Setup
    source = generate_h264_video()
    filename = f"{tmpdir}/test.mp4"

    # Run
    init, moof_data = get_init_and_moof_data(source.getbuffer())
    recorder_save_worker(
        filename,
        [
            Segment(1, init, moof_data, 4, 0),
            Segment(2, init, moof_data, 4, 1),
        ],
    )

    # Assert
    assert os.path.exists(filename)


async def test_recorder_no_segments(tmpdir):
    """Test recorder behavior with a stream failure which causes no segments."""
    # Setup
    filename = f"{tmpdir}/test.mp4"

    # Run
    recorder_save_worker("unused-file", [])

    # Assert
    assert not os.path.exists(filename)


async def test_record_stream_audio(
    opp, opp_client, stream_worker_sync, record_worker_sync
):
    """
    Test treatment of different audio inputs.

    Record stream output should have an audio channel when input has
    a valid codec and audio packets and no audio channel otherwise.
    """
    await async_setup_component(opp, "stream", {"stream": {}})

    for a_codec, expected_audio_streams in (
        ("aac", 1),  # aac is a valid mp4 codec
        ("pcm_mulaw", 0),  # G.711 is not a valid mp4 codec
        ("empty", 0),  # audio stream with no packets
        (None, 0),  # no audio stream
    ):
        record_worker_sync.reset()
        stream_worker_sync.pause()

        # Setup demo track
        source = generate_h264_video(
            container_format="mov", audio_codec=a_codec
        )  # mov can store PCM
        stream = create_stream(opp, source)
        with patch.object(opp.config, "is_allowed_path", return_value=True):
            await stream.async_record("/example/path")
        recorder = stream.add_provider(RECORDER_PROVIDER)

        while True:
            await recorder.recv()
            if not (segment := recorder.last_segment):
                break
            last_segment = segment
            stream_worker_sync.resume()

        result = av.open(
            BytesIO(last_segment.init + last_segment.moof_data), "r", format="mp4"
        )

        assert len(result.streams.audio) == expected_audio_streams
        result.close()
        stream.stop()
        await opp.async_block_till_done()

        # Verify that the save worker was invoked, then block until its
        # thread completes and is shutdown completely to avoid thread leaks.
        await record_worker_sync.join()


async def test_recorder_log(opp, caplog):
    """Test starting a stream to record logs the url without username and password."""
    await async_setup_component(opp, "stream", {"stream": {}})
    stream = create_stream(opp, "https://abcd:efgh@foo.bar")
    with patch.object(opp.config, "is_allowed_path", return_value=True):
        await stream.async_record("/example/path")
    assert "https://abcd:efgh@foo.bar" not in caplog.text
    assert "https://****:****@foo.bar" in caplog.text
