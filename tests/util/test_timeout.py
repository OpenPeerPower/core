"""Test Open Peer Power timeout handler."""
import asyncio
import time

import pytest

from openpeerpower.util.timeout import TimeoutManager


async def test_simple_global_timeout():
    """Test a simple global timeout."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1):
            await asyncio.sleep(0.3)


async def test_simple_global_timeout_with_executor_job(opp):
    """Test a simple global timeout with executor job."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1):
            await opp.async_add_executor_job(lambda: time.sleep(0.2))


async def test_simple_global_timeout_freeze():
    """Test a simple global timeout freeze."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2):
        async with timeout.async_freeze():
            await asyncio.sleep(0.3)


async def test_simple_zone_timeout_freeze_inside_executor_job(opp):
    """Test a simple zone timeout freeze inside an executor job."""
    timeout = TimeoutManager()

    def _some_sync_work():
        with timeout.freeze("recorder"):
            time.sleep(0.3)

    async with timeout.async_timeout(1.0):
        async with timeout.async_timeout(0.2, zone_name="recorder"):
            await opp.async_add_executor_job(_some_sync_work)


async def test_simple_global_timeout_freeze_inside_executor_job(opp):
    """Test a simple global timeout freeze inside an executor job."""
    timeout = TimeoutManager()

    def _some_sync_work():
        with timeout.freeze():
            time.sleep(0.3)

    async with timeout.async_timeout(0.2):
        await opp.async_add_executor_job(_some_sync_work)


async def test_mix_global_timeout_freeze_and_zone_freeze_inside_executor_job(opp):
    """Test a simple global timeout freeze inside an executor job."""
    timeout = TimeoutManager()

    def _some_sync_work():
        with timeout.freeze("recorder"):
            time.sleep(0.3)

    async with timeout.async_timeout(0.1):
        async with timeout.async_timeout(0.2, zone_name="recorder"):
            await opp.async_add_executor_job(_some_sync_work)


async def test_mix_global_timeout_freeze_and_zone_freeze_different_order(opp):
    """Test a simple global timeout freeze inside an executor job before timeout was set."""
    timeout = TimeoutManager()

    def _some_sync_work():
        with timeout.freeze("recorder"):
            time.sleep(0.4)

    async with timeout.async_timeout(0.1):
        opp.async_add_executor_job(_some_sync_work)
        async with timeout.async_timeout(0.2, zone_name="recorder"):
            await asyncio.sleep(0.3)


async def test_mix_global_timeout_freeze_and_zone_freeze_other_zone_inside_executor_job(
    opp,
):
    """Test a simple global timeout freeze other zone inside an executor job."""
    timeout = TimeoutManager()

    def _some_sync_work():
        with timeout.freeze("not_recorder"):
            time.sleep(0.3)

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1):
            async with timeout.async_timeout(0.2, zone_name="recorder"):
                async with timeout.async_timeout(0.2, zone_name="not_recorder"):
                    await opp.async_add_executor_job(_some_sync_work)


async def test_mix_global_timeout_freeze_and_zone_freeze_inside_executor_job_second_job_outside_zone_context(
    opp,
):
    """Test a simple global timeout freeze inside an executor job with second job outside of zone context."""
    timeout = TimeoutManager()

    def _some_sync_work():
        with timeout.freeze("recorder"):
            time.sleep(0.3)

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1):
            async with timeout.async_timeout(0.2, zone_name="recorder"):
                await opp.async_add_executor_job(_some_sync_work)
            await opp.async_add_executor_job(lambda: time.sleep(0.2))


async def test_simple_global_timeout_freeze_with_executor_job(opp):
    """Test a simple global timeout freeze with executor job."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2):
        async with timeout.async_freeze():
            await opp.async_add_executor_job(lambda: time.sleep(0.3))


async def test_simple_global_timeout_freeze_reset():
    """Test a simple global timeout freeze reset."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.2):
            async with timeout.async_freeze():
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.2)


async def test_simple_zone_timeout():
    """Test a simple zone timeout."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1, "test"):
            await asyncio.sleep(0.3)


async def test_multiple_zone_timeout():
    """Test a simple zone timeout."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1, "test"):
            async with timeout.async_timeout(0.5, "test"):
                await asyncio.sleep(0.3)


async def test_different_zone_timeout():
    """Test a simple zone timeout."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1, "test"):
            async with timeout.async_timeout(0.5, "other"):
                await asyncio.sleep(0.3)


async def test_simple_zone_timeout_freeze():
    """Test a simple zone timeout freeze."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2, "test"):
        async with timeout.async_freeze("test"):
            await asyncio.sleep(0.3)


async def test_simple_zone_timeout_freeze_without_timeout():
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.1, "test"):
        async with timeout.async_freeze("test"):
            await asyncio.sleep(0.3)


async def test_simple_zone_timeout_freeze_reset():
    """Test a simple zone timeout freeze reset."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.2, "test"):
            async with timeout.async_freeze("test"):
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.2, "test")


async def test_mix_zone_timeout_freeze_and_global_freeze():
    """Test a mix zone timeout freeze and global freeze."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2, "test"):
        async with timeout.async_freeze("test"):
            async with timeout.async_freeze():
                await asyncio.sleep(0.3)


async def test_mix_global_and_zone_timeout_freeze_():
    """Test a mix zone timeout freeze and global freeze."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2, "test"):
        async with timeout.async_freeze():
            async with timeout.async_freeze("test"):
                await asyncio.sleep(0.3)


async def test_mix_zone_timeout_freeze():
    """Test a mix zone timeout global freeze."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2, "test"):
        async with timeout.async_freeze():
            await asyncio.sleep(0.3)


async def test_mix_zone_timeout():
    """Test a mix zone timeout global."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.1):
        try:
            async with timeout.async_timeout(0.2, "test"):
                await asyncio.sleep(0.4)
        except asyncio.TimeoutError:
            pass


async def test_mix_zone_timeout_trigger_global():
    """Test a mix zone timeout global with trigger it."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1):
            try:
                async with timeout.async_timeout(0.1, "test"):
                    await asyncio.sleep(0.3)
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.3)


async def test_mix_zone_timeout_trigger_global_cool_down():
    """Test a mix zone timeout global with trigger it with cool_down."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.1, cool_down=0.3):
        try:
            async with timeout.async_timeout(0.1, "test"):
                await asyncio.sleep(0.3)
        except asyncio.TimeoutError:
            pass

        await asyncio.sleep(0.2)


async def test_simple_zone_timeout_freeze_without_timeout_cleanup(opp):
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    async def background():
        async with timeout.async_freeze("test"):
            await asyncio.sleep(0.4)

    async with timeout.async_timeout(0.1):
        opp.async_create_task(background())
        await asyncio.sleep(0.2)


async def test_simple_zone_timeout_freeze_without_timeout_cleanup2(opp):
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    async def background():
        async with timeout.async_freeze("test"):
            await asyncio.sleep(0.2)

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1):
            opp.async_create_task(background())
            await asyncio.sleep(0.3)


async def test_simple_zone_timeout_freeze_without_timeout_exeption():
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1):
            try:
                async with timeout.async_freeze("test"):
                    raise RuntimeError()
            except RuntimeError:
                pass

            await asyncio.sleep(0.4)


async def test_simple_zone_timeout_zone_with_timeout_exeption():
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    with pytest.raises(asyncio.TimeoutError):
        async with timeout.async_timeout(0.1):
            try:
                async with timeout.async_timeout(0.3, "test"):
                    raise RuntimeError()
            except RuntimeError:
                pass

            await asyncio.sleep(0.3)
