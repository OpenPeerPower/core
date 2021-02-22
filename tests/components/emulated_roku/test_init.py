"""Test emulated_roku component setup process."""
from unittest.mock import AsyncMock, Mock, patch

from openpeerpower.components import emulated_roku
from openpeerpower.setup import async_setup_component


async def test_config_required_fields.opp):
    """Test that configuration is successful with required fields."""
    with patch.object(emulated_roku, "configured_servers", return_value=[]), patch(
        "openpeerpower.components.emulated_roku.binding.EmulatedRokuServer",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert (
            await async_setup_component(
                opp.
                emulated_roku.DOMAIN,
                {
                    emulated_roku.DOMAIN: {
                        emulated_roku.CONF_SERVERS: [
                            {
                                emulated_roku.CONF_NAME: "Emulated Roku Test",
                                emulated_roku.CONF_LISTEN_PORT: 8060,
                            }
                        ]
                    }
                },
            )
            is True
        )


async def test_config_already_registered_not_configured.opp):
    """Test that an already registered name causes the entry to be ignored."""
    with patch(
        "openpeerpower.components.emulated_roku.binding.EmulatedRokuServer",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ) as instantiate, patch.object(
        emulated_roku, "configured_servers", return_value=["Emulated Roku Test"]
    ):
        assert (
            await async_setup_component(
                opp.
                emulated_roku.DOMAIN,
                {
                    emulated_roku.DOMAIN: {
                        emulated_roku.CONF_SERVERS: [
                            {
                                emulated_roku.CONF_NAME: "Emulated Roku Test",
                                emulated_roku.CONF_LISTEN_PORT: 8060,
                            }
                        ]
                    }
                },
            )
            is True
        )

    assert len(instantiate.mock_calls) == 0


async def test_setup_entry_successful.opp):
    """Test setup entry is successful."""
    entry = Mock()
    entry.data = {
        emulated_roku.CONF_NAME: "Emulated Roku Test",
        emulated_roku.CONF_LISTEN_PORT: 8060,
        emulated_roku.CONF_HOST_IP: "1.2.3.5",
        emulated_roku.CONF_ADVERTISE_IP: "1.2.3.4",
        emulated_roku.CONF_ADVERTISE_PORT: 8071,
        emulated_roku.CONF_UPNP_BIND_MULTICAST: False,
    }

    with patch(
        "openpeerpower.components.emulated_roku.binding.EmulatedRokuServer",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ) as instantiate:
        assert await emulated_roku.async_setup_entry.opp, entry) is True

    assert len(instantiate.mock_calls) == 1
    assert.opp.data[emulated_roku.DOMAIN]

    roku_instance = opp.data[emulated_roku.DOMAIN]["Emulated Roku Test"]

    assert roku_instance.roku_usn == "Emulated Roku Test"
    assert roku_instance.host_ip == "1.2.3.5"
    assert roku_instance.listen_port == 8060
    assert roku_instance.advertise_ip == "1.2.3.4"
    assert roku_instance.advertise_port == 8071
    assert roku_instance.bind_multicast is False


async def test_unload_entry.opp):
    """Test being able to unload an entry."""
    entry = Mock()
    entry.data = {"name": "Emulated Roku Test", "listen_port": 8060}

    with patch(
        "openpeerpower.components.emulated_roku.binding.EmulatedRokuServer",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await emulated_roku.async_setup_entry.opp, entry) is True

    assert emulated_roku.DOMAIN in.opp.data

    await opp.async_block_till_done()

    assert await emulated_roku.async_unload_entry.opp, entry)

    assert len.opp.data[emulated_roku.DOMAIN]) == 0
