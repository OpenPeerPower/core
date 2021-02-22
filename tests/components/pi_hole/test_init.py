"""Test pi_hole component."""
import logging
from unittest.mock import AsyncMock

from hole.exceptions import HoleError

from openpeerpower.components import pi_hole, switch
from openpeerpower.components.pi_hole.const import (
    CONF_LOCATION,
    CONF_STATISTICS_ONLY,
    DEFAULT_LOCATION,
    DEFAULT_NAME,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    SERVICE_DISABLE,
    SERVICE_DISABLE_ATTR_DURATION,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from openpeerpower.setup import async_setup_component

from . import (
    CONF_CONFIG_ENTRY,
    CONF_DATA,
    SWITCH_ENTITY_ID,
    _create_mocked_hole,
    _patch_config_flow_hole,
    _patch_init_hole,
)

from tests.common import MockConfigEntry


async def test_setup_minimal_config.opp):
    """Tests component setup with minimal config."""
    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        assert await async_setup_component(
           .opp, pi_hole.DOMAIN, {pi_hole.DOMAIN: [{"host": "pi.hole"}]}
        )

    await.opp.async_block_till_done()

    assert (
       .opp.states.get("sensor.pi_hole_ads_blocked_today").name
        == "Pi-Hole Ads Blocked Today"
    )
    assert (
       .opp.states.get("sensor.pi_hole_ads_percentage_blocked_today").name
        == "Pi-Hole Ads Percentage Blocked Today"
    )
    assert (
       .opp.states.get("sensor.pi_hole_dns_queries_cached").name
        == "Pi-Hole DNS Queries Cached"
    )
    assert (
       .opp.states.get("sensor.pi_hole_dns_queries_forwarded").name
        == "Pi-Hole DNS Queries Forwarded"
    )
    assert (
       .opp.states.get("sensor.pi_hole_dns_queries_today").name
        == "Pi-Hole DNS Queries Today"
    )
    assert (
       .opp.states.get("sensor.pi_hole_dns_unique_clients").name
        == "Pi-Hole DNS Unique Clients"
    )
    assert (
       .opp.states.get("sensor.pi_hole_dns_unique_domains").name
        == "Pi-Hole DNS Unique Domains"
    )
    assert (
       .opp.states.get("sensor.pi_hole_domains_blocked").name
        == "Pi-Hole Domains Blocked"
    )
    assert.opp.states.get("sensor.pi_hole_seen_clients").name == "Pi-Hole Seen Clients"

    assert.opp.states.get("sensor.pi_hole_ads_blocked_today").state == "0"
    assert.opp.states.get("sensor.pi_hole_ads_percentage_blocked_today").state == "0"
    assert.opp.states.get("sensor.pi_hole_dns_queries_cached").state == "0"
    assert.opp.states.get("sensor.pi_hole_dns_queries_forwarded").state == "0"
    assert.opp.states.get("sensor.pi_hole_dns_queries_today").state == "0"
    assert.opp.states.get("sensor.pi_hole_dns_unique_clients").state == "0"
    assert.opp.states.get("sensor.pi_hole_dns_unique_domains").state == "0"
    assert.opp.states.get("sensor.pi_hole_domains_blocked").state == "0"
    assert.opp.states.get("sensor.pi_hole_seen_clients").state == "0"

    assert.opp.states.get("binary_sensor.pi_hole").name == "Pi-Hole"
    assert.opp.states.get("binary_sensor.pi_hole").state == "off"


async def test_setup_name_config.opp):
    """Tests component setup with a custom name."""
    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        assert await async_setup_component(
           .opp,
            pi_hole.DOMAIN,
            {pi_hole.DOMAIN: [{"host": "pi.hole", "name": "Custom"}]},
        )

    await.opp.async_block_till_done()

    assert (
       .opp.states.get("sensor.custom_ads_blocked_today").name
        == "Custom Ads Blocked Today"
    )


async def test_switch.opp, caplog):
    """Test Pi-hole switch."""
    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        assert await async_setup_component(
           .opp,
            pi_hole.DOMAIN,
            {pi_hole.DOMAIN: [{"host": "pi.hole1", "api_key": "1"}]},
        )

        await.opp.async_block_till_done()

        await.opp.services.async_call(
            switch.DOMAIN,
            switch.SERVICE_TURN_ON,
            {"entity_id": SWITCH_ENTITY_ID},
            blocking=True,
        )
        mocked_hole.enable.assert_called_once()

        await.opp.services.async_call(
            switch.DOMAIN,
            switch.SERVICE_TURN_OFF,
            {"entity_id": SWITCH_ENTITY_ID},
            blocking=True,
        )
        mocked_hole.disable.assert_called_once_with(True)

        # Failed calls
        type(mocked_hole).enable = AsyncMock(side_effect=HoleError("Error1"))
        await.opp.services.async_call(
            switch.DOMAIN,
            switch.SERVICE_TURN_ON,
            {"entity_id": SWITCH_ENTITY_ID},
            blocking=True,
        )
        type(mocked_hole).disable = AsyncMock(side_effect=HoleError("Error2"))
        await.opp.services.async_call(
            switch.DOMAIN,
            switch.SERVICE_TURN_OFF,
            {"entity_id": SWITCH_ENTITY_ID},
            blocking=True,
        )
        errors = [x for x in caplog.records if x.levelno == logging.ERROR]
        assert errors[-2].message == "Unable to enable Pi-hole: Error1"
        assert errors[-1].message == "Unable to disable Pi-hole: Error2"


async def test_disable_service_call.opp):
    """Test disable service call with no Pi-hole named."""
    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        assert await async_setup_component(
           .opp,
            pi_hole.DOMAIN,
            {
                pi_hole.DOMAIN: [
                    {"host": "pi.hole1", "api_key": "1"},
                    {"host": "pi.hole2", "name": "Custom"},
                ]
            },
        )

        await.opp.async_block_till_done()

        await.opp.services.async_call(
            pi_hole.DOMAIN,
            SERVICE_DISABLE,
            {ATTR_ENTITY_ID: "all", SERVICE_DISABLE_ATTR_DURATION: "00:00:01"},
            blocking=True,
        )

        await.opp.async_block_till_done()

        mocked_hole.disable.assert_called_once_with(1)


async def test_unload.opp):
    """Test unload entities."""
    entry = MockConfigEntry(
        domain=pi_hole.DOMAIN,
        data={
            CONF_NAME: DEFAULT_NAME,
            CONF_HOST: "pi.hole",
            CONF_LOCATION: DEFAULT_LOCATION,
            CONF_SSL: DEFAULT_SSL,
            CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
            CONF_STATISTICS_ONLY: True,
        },
    )
    entry.add_to.opp.opp)
    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()
    assert entry.entry_id in.opp.data[pi_hole.DOMAIN]

    assert await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()
    assert entry.entry_id not in.opp.data[pi_hole.DOMAIN]


async def test_migrate.opp):
    """Test migrate from old config entry."""
    entry = MockConfigEntry(domain=pi_hole.DOMAIN, data=CONF_DATA)
    entry.add_to.opp.opp)

    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    assert entry.data == CONF_CONFIG_ENTRY


async def test_migrate_statistics_only.opp):
    """Test migrate from old config entry with statistics only."""
    conf_data = {**CONF_DATA}
    conf_data[CONF_API_KEY] = ""
    entry = MockConfigEntry(domain=pi_hole.DOMAIN, data=conf_data)
    entry.add_to.opp.opp)

    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    config_entry_data = {**CONF_CONFIG_ENTRY}
    config_entry_data[CONF_STATISTICS_ONLY] = True
    config_entry_data[CONF_API_KEY] = ""
    assert entry.data == config_entry_data
