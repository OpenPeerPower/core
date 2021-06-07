"""Common test tools."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Awaitable, Callable, cast
from unittest.mock import patch

import pytest

from openpeerpower.components import recorder
from openpeerpower.components.recorder import Recorder
from openpeerpower.components.recorder.const import DATA_INSTANCE
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.typing import ConfigType

from .common import async_recorder_block_till_done

from tests.common import async_init_recorder_component

SetupRecorderInstanceT = Callable[..., Awaitable[Recorder]]


@pytest.fixture
async def async_setup_recorder_instance(
    enable_statistics,
) -> AsyncGenerator[SetupRecorderInstanceT, None]:
    """Yield callable to setup recorder instance."""

    async def async_setup_recorder(
        opp: OpenPeerPower, config: ConfigType | None = None
    ) -> Recorder:
        """Setup and return recorder instance."""  # noqa: D401
        stats = recorder.Recorder.async_hourly_statistics if enable_statistics else None
        with patch(
            "openpeerpower.components.recorder.Recorder.async_hourly_statistics",
            side_effect=stats,
            autospec=True,
        ):
            await async_init_recorder_component(opp, config)
            await opp.async_block_till_done()
            instance = cast(Recorder, opp.data[DATA_INSTANCE])
            await async_recorder_block_till_done(opp, instance)
            assert isinstance(instance, Recorder)
            return instance

    yield async_setup_recorder
