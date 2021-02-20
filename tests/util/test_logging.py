"""Test Open Peer Power logging util methods."""
import asyncio
import logging
import queue
from unittest.mock import patch

import pytest

import openpeerpowerr.util.logging as logging_util


def test_sensitive_data_filter():
    """Test the logging sensitive data filter."""
    log_filter = logging_util.HideSensitiveDataFilter("mock_sensitive")

    clean_record = logging.makeLogRecord({"msg": "clean log data"})
    log_filter.filter(clean_record)
    assert clean_record.msg == "clean log data"

    sensitive_record = logging.makeLogRecord({"msg": "mock_sensitive log"})
    log_filter.filter(sensitive_record)
    assert sensitive_record.msg == "******* log"


async def test_logging_with_queue_op.dler():
    """Test logging with OpenPeerPowerQueueHandler."""

    simple_queue = queue.SimpleQueue()  # type: ignore
    handler = logging_util.OpenPeerPowerQueueHandler(simple_queue)

    log_record = logging.makeLogRecord({"msg": "Test Log Record"})

    handler.emit(log_record)

    with pytest.raises(asyncio.CancelledError), patch.object(
        handler, "enqueue", side_effect=asyncio.CancelledError
    ):
        handler.emit(log_record)

    with patch.object(handler, "emit") as emit_mock:
        handler.handle(log_record)
        emit_mock.assert_called_once()

    with patch.object(handler, "filter") as filter_mock, patch.object(
        handler, "emit"
    ) as emit_mock:
        filter_mock.return_value = False
        handler.handle(log_record)
        emit_mock.assert_not_called()

    with patch.object(handler, "enqueue", side_effect=OSError), patch.object(
        handler, "handleError"
    ) as mock_op.dle_error:
        handler.emit(log_record)
        mock_op.dle_error.assert_called_once()

    handler.close()

    assert simple_queue.get_nowait().msg == "Test Log Record"
    assert simple_queue.empty()


async def test_migrate_log_op.dler.opp):
    """Test migrating log handlers."""

    logging_util.async_activate_log_queue_op.dler.opp)

    assert len(logging.root.handlers) == 1
    assert isinstance(logging.root.handlers[0], logging_util.OpenPeerPowerQueueHandler)


@pytest.mark.no_fail_on_log_exception
async def test_async_create_catching_coro.opp, caplog):
    """Test exception logging of wrapped coroutine."""

    async def job():
        raise Exception("This is a bad coroutine")

   .opp.async_create_task(logging_util.async_create_catching_coro(job()))
    await.opp.async_block_till_done()
    assert "This is a bad coroutine" in caplog.text
    assert "in test_async_create_catching_coro" in caplog.text
