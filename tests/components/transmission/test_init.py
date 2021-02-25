"""Tests for Transmission init."""

from unittest.mock import patch

import pytest
from transmissionrpc.error import TransmissionError

from openpeerpower.components import transmission
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry, mock_coro

MOCK_ENTRY = MockConfigEntry(
    domain=transmission.DOMAIN,
    data={
        transmission.CONF_NAME: "Transmission",
        transmission.CONF_HOST: "0.0.0.0",
        transmission.CONF_USERNAME: "user",
        transmission.CONF_PASSWORD: "pass",
        transmission.CONF_PORT: 9091,
    },
)


@pytest.fixture(name="api")
def mock_transmission_api():
    """Mock an api."""
    with patch("transmissionrpc.Client"):
        yield


@pytest.fixture(name="auth_error")
def mock_api_authentication_error():
    """Mock an api."""
    with patch(
        "transmissionrpc.Client", side_effect=TransmissionError("401: Unauthorized")
    ):
        yield


@pytest.fixture(name="unknown_error")
def mock_api_unknown_error():
    """Mock an api."""
    with patch("transmissionrpc.Client", side_effect=TransmissionError):
        yield


async def test_setup_with_no_config(opp):
    """Test that we do not discover anything or try to set up a Transmission client."""
    assert await async_setup_component(opp, transmission.DOMAIN, {}) is True
    assert transmission.DOMAIN not in opp.data


async def test_setup_with_config(opp, api):
    """Test that we import the config and setup the client."""
    config = {
        transmission.DOMAIN: {
            transmission.CONF_NAME: "Transmission",
            transmission.CONF_HOST: "0.0.0.0",
            transmission.CONF_USERNAME: "user",
            transmission.CONF_PASSWORD: "pass",
            transmission.CONF_PORT: 9091,
        },
        transmission.DOMAIN: {
            transmission.CONF_NAME: "Transmission2",
            transmission.CONF_HOST: "0.0.0.1",
            transmission.CONF_USERNAME: "user",
            transmission.CONF_PASSWORD: "pass",
            transmission.CONF_PORT: 9091,
        },
    }
    assert await async_setup_component(opp, transmission.DOMAIN, config) is True


async def test_successful_config_entry(opp, api):
    """Test that configured transmission is configured successfully."""

    entry = MOCK_ENTRY
    entry.add_to_opp(opp)

    assert await transmission.async_setup_entry(opp, entry) is True
    assert entry.options == {
        transmission.CONF_SCAN_INTERVAL: transmission.DEFAULT_SCAN_INTERVAL,
        transmission.CONF_LIMIT: transmission.DEFAULT_LIMIT,
        transmission.CONF_ORDER: transmission.DEFAULT_ORDER,
    }


async def test_setup_failed.opp):
    """Test transmission failed due to an error."""

    entry = MOCK_ENTRY
    entry.add_to_opp(opp)

    # test connection error raising ConfigEntryNotReady
    with patch(
        "transmissionrpc.Client",
        side_effect=TransmissionError("111: Connection refused"),
    ), pytest.raises(ConfigEntryNotReady):

        await transmission.async_setup_entry(opp, entry)

    # test Authentication error returning false

    with patch(
        "transmissionrpc.Client", side_effect=TransmissionError("401: Unauthorized")
    ):

        assert await transmission.async_setup_entry(opp, entry) is False


async def test_unload_entry(opp, api):
    """Test removing transmission client."""
    entry = MOCK_ENTRY
    entry.add_to_opp(opp)

    with patch.object(
        opp.config_entries, "async_forward_entry_unload", return_value=mock_coro(True)
    ) as unload_entry:
        assert await transmission.async_setup_entry(opp, entry)

        assert await transmission.async_unload_entry(opp, entry)
        assert unload_entry.call_count == 2
        assert entry.entry_id not in opp.data[transmission.DOMAIN]
