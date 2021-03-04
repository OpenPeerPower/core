"""The tests for the litejet component."""
from openpeerpower.components import litejet
from openpeerpower.components.litejet.const import DOMAIN
from openpeerpower.const import CONF_PORT
from openpeerpower.setup import async_setup_component

from . import async_init_integration


async def test_setup_with_no_config(opp):
    """Test that nothing happens."""
    assert await async_setup_component(opp, DOMAIN, {}) is True
    assert DOMAIN not in opp.data


async def test_setup_with_config_to_import(opp, mock_litejet):
    """Test that import happens."""
    assert (
        await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PORT: "/dev/hello"}})
        is True
    )
    assert DOMAIN in opp.data


async def test_unload_entry(opp, mock_litejet):
    """Test being able to unload an entry."""
    entry = await async_init_integration(opp, use_switch=True, use_scene=True)

    assert await litejet.async_unload_entry(opp, entry)
    assert DOMAIN not in opp.data
