"""Tests for the Freebox config flow."""
from unittest.mock import Mock, patch

from openpeerpower.components.device_tracker import DOMAIN as DT_DOMAIN
from openpeerpower.components.freebox.const import DOMAIN as DOMAIN, SERVICE_REBOOT
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_LOADED, ENTRY_STATE_NOT_LOADED
from openpeerpower.const import CONF_HOST, CONF_PORT, STATE_UNAVAILABLE
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.setup import async_setup_component

from .const import MOCK_HOST, MOCK_PORT

from tests.common import MockConfigEntry


async def test_setup(opp: OpenPeerPowerType, router: Mock):
    """Test setup of integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
        unique_id=MOCK_HOST,
    )
    entry.add_to_opp(opp)
    assert await async_setup_component(opp, DOMAIN, {})
    await opp.async_block_till_done()
    assert opp.config_entries.async_entries() == [entry]

    assert router.call_count == 1
    assert router().open.call_count == 1

    assert opp.services.has_service(DOMAIN, SERVICE_REBOOT)

    with patch(
        "openpeerpower.components.freebox.router.FreeboxRouter.reboot"
    ) as mock_service:
        await opp.services.async_call(
            DOMAIN,
            SERVICE_REBOOT,
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_service.assert_called_once()


async def test_setup_import(opp: OpenPeerPowerType, router: Mock):
    """Test setup of integration from import."""
    await async_setup_component(opp, "persistent_notification", {})

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
        unique_id=MOCK_HOST,
    )
    entry.add_to_opp(opp)
    assert await async_setup_component(
        opp, DOMAIN, {DOMAIN: {CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT}}
    )
    await opp.async_block_till_done()
    assert opp.config_entries.async_entries() == [entry]

    assert router.call_count == 1
    assert router().open.call_count == 1

    assert opp.services.has_service(DOMAIN, SERVICE_REBOOT)


async def test_unload_remove(opp: OpenPeerPowerType, router: Mock):
    """Test unload and remove of integration."""
    entity_id_dt = f"{DT_DOMAIN}.freebox_server_r2"
    entity_id_sensor = f"{SENSOR_DOMAIN}.freebox_download_speed"
    entity_id_switch = f"{SWITCH_DOMAIN}.freebox_wifi"

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )
    entry.add_to_opp(opp)

    config_entries = opp.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    assert entry is config_entries[0]

    assert await async_setup_component(opp, DOMAIN, {}) is True
    await opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_LOADED
    state_dt = opp.states.get(entity_id_dt)
    assert state_dt
    state_sensor = opp.states.get(entity_id_sensor)
    assert state_sensor
    state_switch = opp.states.get(entity_id_switch)
    assert state_switch

    await opp.config_entries.async_unload(entry.entry_id)

    assert entry.state == ENTRY_STATE_NOT_LOADED
    state_dt = opp.states.get(entity_id_dt)
    assert state_dt.state == STATE_UNAVAILABLE
    state_sensor = opp.states.get(entity_id_sensor)
    assert state_sensor.state == STATE_UNAVAILABLE
    state_switch = opp.states.get(entity_id_switch)
    assert state_switch.state == STATE_UNAVAILABLE

    assert router().close.call_count == 1
    assert not opp.services.has_service(DOMAIN, SERVICE_REBOOT)

    await opp.config_entries.async_remove(entry.entry_id)
    await opp.async_block_till_done()

    assert router().close.call_count == 1
    assert entry.state == ENTRY_STATE_NOT_LOADED
    state_dt = opp.states.get(entity_id_dt)
    assert state_dt is None
    state_sensor = opp.states.get(entity_id_sensor)
    assert state_sensor is None
    state_switch = opp.states.get(entity_id_switch)
    assert state_switch is None
