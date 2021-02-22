"""The tests for the Foobot sensor platform."""

import asyncio
import re
from unittest.mock import MagicMock

import pytest

from openpeerpower.components.foobot import sensor as foobot
import openpeerpower.components.sensor as sensor
from openpeerpower.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    HTTP_FORBIDDEN,
    HTTP_INTERNAL_SERVER_ERROR,
    PERCENTAGE,
    TEMP_CELSIUS,
)
from openpeerpower.exceptions import PlatformNotReady
from openpeerpower.setup import async_setup_component

from tests.common import load_fixture

VALID_CONFIG = {
    "platform": "foobot",
    "token": "adfdsfasd",
    "username": "example@example.com",
}


async def test_default_setup_opp, aioclient_mock):
    """Test the default setup."""
    aioclient_mock.get(
        re.compile("api.foobot.io/v2/owner/.*"),
        text=load_fixture("foobot_devices.json"),
    )
    aioclient_mock.get(
        re.compile("api.foobot.io/v2/device/.*"), text=load_fixture("foobot_data.json")
    )
    assert await async_setup_component.opp, sensor.DOMAIN, {"sensor": VALID_CONFIG})
    await opp.async_block_till_done()

    metrics = {
        "co2": ["1232.0", CONCENTRATION_PARTS_PER_MILLION],
        "temperature": ["21.1", TEMP_CELSIUS],
        "humidity": ["49.5", PERCENTAGE],
        "pm2_5": ["144.8", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER],
        "voc": ["340.7", CONCENTRATION_PARTS_PER_BILLION],
        "index": ["138.9", PERCENTAGE],
    }

    for name, value in metrics.items():
        state = opp.states.get("sensor.foobot_happybot_%s" % name)
        assert state.state == value[0]
        assert state.attributes.get("unit_of_measurement") == value[1]


async def test_setup_timeout_error(opp, aioclient_mock):
    """Expected failures caused by a timeout in API response."""
    fake_async_add_entities = MagicMock()

    aioclient_mock.get(
        re.compile("api.foobot.io/v2/owner/.*"), exc=asyncio.TimeoutError()
    )
    with pytest.raises(PlatformNotReady):
        await foobot.async_setup_platform(
           .opp, {"sensor": VALID_CONFIG}, fake_async_add_entities
        )


async def test_setup_permanent_error(opp, aioclient_mock):
    """Expected failures caused by permanent errors in API response."""
    fake_async_add_entities = MagicMock()

    errors = [400, 401, HTTP_FORBIDDEN]
    for error in errors:
        aioclient_mock.get(re.compile("api.foobot.io/v2/owner/.*"), status=error)
        result = await foobot.async_setup_platform(
           .opp, {"sensor": VALID_CONFIG}, fake_async_add_entities
        )
        assert result is None


async def test_setup_temporary_error(opp, aioclient_mock):
    """Expected failures caused by temporary errors in API response."""
    fake_async_add_entities = MagicMock()

    errors = [429, HTTP_INTERNAL_SERVER_ERROR]
    for error in errors:
        aioclient_mock.get(re.compile("api.foobot.io/v2/owner/.*"), status=error)
        with pytest.raises(PlatformNotReady):
            await foobot.async_setup_platform(
               .opp, {"sensor": VALID_CONFIG}, fake_async_add_entities
            )
