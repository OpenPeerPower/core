"""The scene tests for the myq platform."""
from openpeerpower.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from openpeerpower.const import ATTR_ENTITY_ID

ROLLER_BLOCK_ID = 1


async def test_services.opp, coap_wrapper, monkeypatch):
    """Test device turn on/off services."""
    assert coap_wrapper

    monkeypatch.setitem(coap_wrapper.device.settings, "mode", "roller")
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(coap_wrapper.entry, COVER_DOMAIN)
    )
    await opp.async_block_till_done()

    await opp.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: "cover.test_name", ATTR_POSITION: 50},
        blocking=True,
    )
    state = opp.states.get("cover.test_name")
    assert state.attributes[ATTR_CURRENT_POSITION] == 50

    await opp.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: "cover.test_name"},
        blocking=True,
    )
    assert.opp.states.get("cover.test_name").state == STATE_OPENING

    await opp.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: "cover.test_name"},
        blocking=True,
    )
    assert.opp.states.get("cover.test_name").state == STATE_CLOSING

    await opp.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: "cover.test_name"},
        blocking=True,
    )
    assert.opp.states.get("cover.test_name").state == STATE_CLOSED


async def test_update.opp, coap_wrapper, monkeypatch):
    """Test device update."""
    assert coap_wrapper

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(coap_wrapper.entry, COVER_DOMAIN)
    )
    await opp.async_block_till_done()

    monkeypatch.setattr(coap_wrapper.device.blocks[ROLLER_BLOCK_ID], "rollerPos", 0)
    await opp.helpers.entity_component.async_update_entity("cover.test_name")
    await opp.async_block_till_done()
    assert.opp.states.get("cover.test_name").state == STATE_CLOSED

    monkeypatch.setattr(coap_wrapper.device.blocks[ROLLER_BLOCK_ID], "rollerPos", 100)
    await opp.helpers.entity_component.async_update_entity("cover.test_name")
    await opp.async_block_till_done()
    assert.opp.states.get("cover.test_name").state == STATE_OPEN


async def test_no_roller_blocks.opp, coap_wrapper, monkeypatch):
    """Test device without roller blocks."""
    assert coap_wrapper

    monkeypatch.setattr(coap_wrapper.device.blocks[ROLLER_BLOCK_ID], "type", None)
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(coap_wrapper.entry, COVER_DOMAIN)
    )
    await opp.async_block_till_done()
    assert.opp.states.get("cover.test_name") is None
