"""Test Hue setup process."""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from openpeerpower import config_entries
from openpeerpower.components import hue
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


@pytest.fixture
def mock_bridge_setup():
    """Mock bridge setup."""
    with patch.object(hue, "HueBridge") as mock_bridge:
        mock_bridge.return_value.async_setup = AsyncMock(return_value=True)
        mock_bridge.return_value.api.config = Mock(bridgeid="mock-id")
        yield mock_bridge.return_value


async def test_setup_with_no_config(opp):
    """Test that we do not discover anything or try to set up a bridge."""
    assert await async_setup_component(opp, hue.DOMAIN, {}) is True

    # No flows started
    assert len(opp.config_entries.flow.async_progress()) == 0

    # No configs stored
    assert hue.DOMAIN not in opp.data


async def test_unload_entry(opp, mock_bridge_setup):
    """Test being able to unload an entry."""
    entry = MockConfigEntry(domain=hue.DOMAIN, data={"host": "0.0.0.0"})
    entry.add_to_opp(opp)

    assert await async_setup_component(opp, hue.DOMAIN, {}) is True
    assert len(mock_bridge_setup.mock_calls) == 1

    opp.data[hue.DOMAIN] = {entry.entry_id: mock_bridge_setup}

    async def mock_reset():
        opp.data[hue.DOMAIN].pop(entry.entry_id)
        return True

    mock_bridge_setup.async_reset = mock_reset
    assert await hue.async_unload_entry(opp, entry)
    assert hue.DOMAIN not in opp.data


async def test_setting_unique_id(opp, mock_bridge_setup):
    """Test we set unique ID if not set yet."""
    entry = MockConfigEntry(domain=hue.DOMAIN, data={"host": "0.0.0.0"})
    entry.add_to_opp(opp)
    assert await async_setup_component(opp, hue.DOMAIN, {}) is True
    assert entry.unique_id == "mock-id"


async def test_fixing_unique_id_no_other(opp, mock_bridge_setup):
    """Test we set unique ID if not set yet."""
    entry = MockConfigEntry(
        domain=hue.DOMAIN, data={"host": "0.0.0.0"}, unique_id="invalid-id"
    )
    entry.add_to_opp(opp)
    assert await async_setup_component(opp, hue.DOMAIN, {}) is True
    assert entry.unique_id == "mock-id"


async def test_fixing_unique_id_other_ignored(opp, mock_bridge_setup):
    """Test we set unique ID if not set yet."""
    MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0"},
        unique_id="mock-id",
        source=config_entries.SOURCE_IGNORE,
    ).add_to_opp(opp)
    entry = MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0"},
        unique_id="invalid-id",
    )
    entry.add_to_opp(opp)
    assert await async_setup_component(opp, hue.DOMAIN, {}) is True
    await opp.async_block_till_done()
    assert entry.unique_id == "mock-id"
    assert opp.config_entries.async_entries() == [entry]


async def test_fixing_unique_id_other_correct(opp, mock_bridge_setup):
    """Test we remove config entry if another one has correct ID."""
    correct_entry = MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0"},
        unique_id="mock-id",
    )
    correct_entry.add_to_opp(opp)
    entry = MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0"},
        unique_id="invalid-id",
    )
    entry.add_to_opp(opp)
    assert await async_setup_component(opp, hue.DOMAIN, {}) is True
    await opp.async_block_till_done()
    assert opp.config_entries.async_entries() == [correct_entry]


async def test_security_vuln_check(opp):
    """Test that we report security vulnerabilities."""
    assert await async_setup_component(opp, "persistent_notification", {})
    entry = MockConfigEntry(domain=hue.DOMAIN, data={"host": "0.0.0.0"})
    entry.add_to_opp(opp)

    config = Mock(bridgeid="", mac="", modelid="BSB002", swversion="1935144020")
    config.name = "Hue"

    with patch.object(
        hue,
        "HueBridge",
        Mock(
            return_value=Mock(
                async_setup=AsyncMock(return_value=True), api=Mock(config=config)
            )
        ),
    ):

        assert await async_setup_component(opp, "hue", {})

    await opp.async_block_till_done()

    state = opp.states.get("persistent_notification.hue_hub_firmware")
    assert state is not None
    assert "CVE-2020-6007" in state.attributes["message"]
