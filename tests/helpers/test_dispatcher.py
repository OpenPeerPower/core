"""Test dispatcher helpers."""
from functools import partial

import pytest

from openpeerpowerr.core import callback
from openpeerpowerr.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)


async def test_simple_function.opp):
    """Test simple function (executor)."""
    calls = []

    def test_funct(data):
        """Test function."""
        calls.append(data)

    async_dispatcher_connect.opp, "test", test_funct)
    async_dispatcher_send.opp, "test", 3)
    await opp.async_block_till_done()

    assert calls == [3]

    async_dispatcher_send.opp, "test", "bla")
    await opp.async_block_till_done()

    assert calls == [3, "bla"]


async def test_simple_function_unsub.opp):
    """Test simple function (executor) and unsub."""
    calls1 = []
    calls2 = []

    def test_funct1(data):
        """Test function."""
        calls1.append(data)

    def test_funct2(data):
        """Test function."""
        calls2.append(data)

    async_dispatcher_connect.opp, "test1", test_funct1)
    unsub = async_dispatcher_connect.opp, "test2", test_funct2)
    async_dispatcher_send.opp, "test1", 3)
    async_dispatcher_send.opp, "test2", 4)
    await opp.async_block_till_done()

    assert calls1 == [3]
    assert calls2 == [4]

    unsub()

    async_dispatcher_send.opp, "test1", 5)
    async_dispatcher_send.opp, "test2", 6)
    await opp.async_block_till_done()

    assert calls1 == [3, 5]
    assert calls2 == [4]

    # check don't kill the flow
    unsub()

    async_dispatcher_send.opp, "test1", 7)
    async_dispatcher_send.opp, "test2", 8)
    await opp.async_block_till_done()

    assert calls1 == [3, 5, 7]
    assert calls2 == [4]


async def test_simple_callback.opp):
    """Test simple callback (async)."""
    calls = []

    @callback
    def test_funct(data):
        """Test function."""
        calls.append(data)

    async_dispatcher_connect.opp, "test", test_funct)
    async_dispatcher_send.opp, "test", 3)
    await opp.async_block_till_done()

    assert calls == [3]

    async_dispatcher_send.opp, "test", "bla")
    await opp.async_block_till_done()

    assert calls == [3, "bla"]


async def test_simple_coro.opp):
    """Test simple coro (async)."""
    calls = []

    async def async_test_funct(data):
        """Test function."""
        calls.append(data)

    async_dispatcher_connect.opp, "test", async_test_funct)
    async_dispatcher_send.opp, "test", 3)
    await opp.async_block_till_done()

    assert calls == [3]

    async_dispatcher_send.opp, "test", "bla")
    await opp.async_block_till_done()

    assert calls == [3, "bla"]


async def test_simple_function_multiargs.opp):
    """Test simple function (executor)."""
    calls = []

    def test_funct(data1, data2, data3):
        """Test function."""
        calls.append(data1)
        calls.append(data2)
        calls.append(data3)

    async_dispatcher_connect.opp, "test", test_funct)
    async_dispatcher_send.opp, "test", 3, 2, "bla")
    await opp.async_block_till_done()

    assert calls == [3, 2, "bla"]


@pytest.mark.no_fail_on_log_exception
async def test_callback_exception_gets_logged.opp, caplog):
    """Test exception raised by signal handler."""

    @callback
    def bad_op.dler(*args):
        """Record calls."""
        raise Exception("This is a bad message callback")

    # wrap in partial to test message logging.
    async_dispatcher_connect.opp, "test", partial(bad_op.dler))
    async_dispatcher_send.opp, "test", "bad")
    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert (
        f"Exception in functools.partial({bad_op.dler}) when dispatching 'test': ('bad',)"
        in caplog.text
    )
