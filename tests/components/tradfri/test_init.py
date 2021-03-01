"""Tests for Tradfri setup."""
from unittest.mock import patch

from openpeerpower.components import tradfri
from openpeerpower.helpers.device_registry import (
    async_entries_for_config_entry,
    async_get_registry as async_get_device_registry,
)
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_config_yaml_host_not_imported(opp):
    """Test that we don't import a configured host."""
    MockConfigEntry(domain="tradfri", data={"host": "mock-host"}).add_to_opp(opp)

    with patch(
        "openpeerpower.components.tradfri.load_json", return_value={}
    ), patch.object.opp.config_entries.flow, "async_init") as mock_init:
        assert await async_setup_component(
            opp, "tradfri", {"tradfri": {"host": "mock-host"}}
        )
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 0


async def test_config_yaml_host_imported(opp):
    """Test that we import a configured host."""
    with patch("openpeerpower.components.tradfri.load_json", return_value={}):
        assert await async_setup_component(
            opp, "tradfri", {"tradfri": {"host": "mock-host"}}
        )
        await opp.async_block_till_done()

    progress = opp.config_entries.flow.async_progress()
    assert len(progress) == 1
    assert progress[0]["handler"] == "tradfri"
    assert progress[0]["context"] == {"source": "import"}


async def test_config_json_host_not_imported(opp):
    """Test that we don't import a configured host."""
    MockConfigEntry(domain="tradfri", data={"host": "mock-host"}).add_to_opp(opp)

    with patch(
        "openpeerpower.components.tradfri.load_json",
        return_value={"mock-host": {"key": "some-info"}},
    ), patch.object.opp.config_entries.flow, "async_init") as mock_init:
        assert await async_setup_component(opp, "tradfri", {"tradfri": {}})
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 0


async def test_config_json_host_imported(
    opp, mock_gateway_info, mock_entry_setup, gateway_id
):
    """Test that we import a configured host."""
    mock_gateway_info.side_effect = lambda.opp, host, identity, key: {
        "host": host,
        "identity": identity,
        "key": key,
        "gateway_id": gateway_id,
    }

    with patch(
        "openpeerpower.components.tradfri.load_json",
        return_value={"mock-host": {"key": "some-info"}},
    ):
        assert await async_setup_component(opp, "tradfri", {"tradfri": {}})
        await opp.async_block_till_done()

    config_entry = mock_entry_setup.mock_calls[0][1][1]
    assert config_entry.domain == "tradfri"
    assert config_entry.source == "import"
    assert config_entry.title == "mock-host"


async def test_entry_setup_unload(opp, api_factory, gateway_id):
    """Test config entry setup and unload."""
    entry = MockConfigEntry(
        domain=tradfri.DOMAIN,
        data={
            tradfri.CONF_HOST: "mock-host",
            tradfri.CONF_IDENTITY: "mock-identity",
            tradfri.CONF_KEY: "mock-key",
            tradfri.CONF_IMPORT_GROUPS: True,
            tradfri.CONF_GATEWAY_ID: gateway_id,
        },
    )

    entry.add_to_opp(opp)
    with patch.object(
        opp.config_entries, "async_forward_entry_setup", return_value=True
    ) as setup:
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        assert setup.call_count == len(tradfri.PLATFORMS)

    dev_reg = await async_get_device_registry(opp)
    dev_entries = async_entries_for_config_entry(dev_reg, entry.entry_id)

    assert dev_entries
    dev_entry = dev_entries[0]
    assert dev_entry.identifiers == {
        (tradfri.DOMAIN, entry.data[tradfri.CONF_GATEWAY_ID])
    }
    assert dev_entry.manufacturer == tradfri.ATTR_TRADFRI_MANUFACTURER
    assert dev_entry.name == tradfri.ATTR_TRADFRI_GATEWAY
    assert dev_entry.model == tradfri.ATTR_TRADFRI_GATEWAY_MODEL

    with patch.object(
        opp.config_entries, "async_forward_entry_unload", return_value=True
    ) as unload:
        assert await opp.config_entries.async_unload(entry.entry_id)
        await opp.async_block_till_done()
        assert unload.call_count == len(tradfri.PLATFORMS)
        assert api_factory.shutdown.call_count == 1
