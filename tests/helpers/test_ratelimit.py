"""Tests for ratelimit."""
import asyncio
from datetime import timedelta

from openpeerpower.core import callback
from openpeerpower.helpers import ratelimit
from openpeerpower.util import dt as dt_util


async def test_hit(opp):
    """Test hitting the rate limit."""

    refresh_called = False

    @callback
    def _refresh():
        nonlocal refresh_called
        refresh_called = True
        return

    rate_limiter = ratelimit.KeyedRateLimit(opp)
    rate_limiter.async_triggered("key1", dt_util.utcnow())

    assert (
        rate_limiter.async_schedule_action(
            "key1", timedelta(seconds=0.001), dt_util.utcnow(), _refresh
        )
        is not None
    )

    assert not refresh_called

    assert rate_limiter.async_has_timer("key1")

    await asyncio.sleep(0.002)
    assert refresh_called

    assert (
        rate_limiter.async_schedule_action(
            "key2", timedelta(seconds=0.001), dt_util.utcnow(), _refresh
        )
        is None
    )
    rate_limiter.async_remove()


async def test_miss(opp):
    """Test missing the rate limit."""

    refresh_called = False

    @callback
    def _refresh():
        nonlocal refresh_called
        refresh_called = True
        return

    rate_limiter = ratelimit.KeyedRateLimit(opp)
    assert (
        rate_limiter.async_schedule_action(
            "key1", timedelta(seconds=0.1), dt_util.utcnow(), _refresh
        )
        is None
    )
    assert not refresh_called
    assert not rate_limiter.async_has_timer("key1")

    assert (
        rate_limiter.async_schedule_action(
            "key1", timedelta(seconds=0.1), dt_util.utcnow(), _refresh
        )
        is None
    )
    assert not refresh_called
    assert not rate_limiter.async_has_timer("key1")
    rate_limiter.async_remove()


async def test_no_limit(opp):
    """Test async_schedule_action always return None when there is no rate limit."""

    refresh_called = False

    @callback
    def _refresh():
        nonlocal refresh_called
        refresh_called = True
        return

    rate_limiter = ratelimit.KeyedRateLimit(opp)
    rate_limiter.async_triggered("key1", dt_util.utcnow())

    assert (
        rate_limiter.async_schedule_action("key1", None, dt_util.utcnow(), _refresh)
        is None
    )
    assert not refresh_called
    assert not rate_limiter.async_has_timer("key1")

    rate_limiter.async_triggered("key1", dt_util.utcnow())

    assert (
        rate_limiter.async_schedule_action("key1", None, dt_util.utcnow(), _refresh)
        is None
    )
    assert not refresh_called
    assert not rate_limiter.async_has_timer("key1")
    rate_limiter.async_remove()
