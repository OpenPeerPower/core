# pylint: disable=redefined-outer-name
"""Tests for the Daikin config flow."""
import asyncio
from unittest.mock import PropertyMock, patch

from aiohttp import ClientError
from aiohttp.web_exceptions import HTTPForbidden
import pytest

from openpeerpower.components.daikin.const import KEY_IP, KEY_MAC
from openpeerpower.config_entries import (
    SOURCE_DISCOVERY,
    SOURCE_IMPORT,
    SOURCE_USER,
    SOURCE_ZEROCONF,
)
from openpeerpower.const import CONF_HOST
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from tests.common import MockConfigEntry

MAC = "AABBCCDDEEFF"
HOST = "127.0.0.1"


@pytest.fixture
def mock_daikin():
    """Mock pydaikin."""

    async def mock_daikin_factory(*args, **kwargs):
        """Mock the init function in pydaikin."""
        return Appliance

    with patch("openpeerpower.components.daikin.config_flow.Appliance") as Appliance:
        type(Appliance).mac = PropertyMock(return_value="AABBCCDDEEFF")
        Appliance.factory.side_effect = mock_daikin_factory
        yield Appliance


@pytest.fixture
def mock_daikin_discovery():
    """Mock pydaikin Discovery."""
    with patch("openpeerpower.components.daikin.config_flow.Discovery") as Discovery:
        Discovery().poll.return_value = {
            "127.0.01": {"mac": "AABBCCDDEEFF", "id": "test"}
        }.values()
        yield Discovery


async def test_user.opp, mock_daikin):
    """Test user config."""
    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST},
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][KEY_MAC] == MAC


async def test_abort_if_already_setup.opp, mock_daikin):
    """Test we abort if Daikin is already setup."""
    MockConfigEntry(domain="daikin", unique_id=MAC).add_to.opp.opp)
    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, KEY_MAC: MAC},
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_import.opp, mock_daikin):
    """Test import step."""
    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_IMPORT},
        data={},
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_IMPORT},
        data={CONF_HOST: HOST},
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][KEY_MAC] == MAC


@pytest.mark.parametrize(
    "s_effect,reason",
    [
        (asyncio.TimeoutError, "cannot_connect"),
        (HTTPForbidden, "invalid_auth"),
        (ClientError, "unknown"),
        (Exception, "unknown"),
    ],
)
async def test_device_abort.opp, mock_daikin, s_effect, reason):
    """Test device abort."""
    mock_daikin.factory.side_effect = s_effect

    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, KEY_MAC: MAC},
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": reason}
    assert result["step_id"] == "user"


@pytest.mark.parametrize(
    "source, data, unique_id",
    [
        (SOURCE_DISCOVERY, {KEY_IP: HOST, KEY_MAC: MAC}, MAC),
        (SOURCE_ZEROCONF, {CONF_HOST: HOST}, MAC),
    ],
)
async def test_discovery_zeroconf(
   .opp, mock_daikin, mock_daikin_discovery, source, data, unique_id
):
    """Test discovery/zeroconf step."""
    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": source},
        data=data,
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    MockConfigEntry(domain="daikin", unique_id=unique_id).add_to.opp.opp)
    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER, "unique_id": unique_id},
        data={CONF_HOST: HOST},
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    result = await.opp.config_entries.flow.async_init(
        "daikin",
        context={"source": source},
        data=data,
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_in_progress"
