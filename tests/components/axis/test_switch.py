"""Axis switch platform tests."""

from copy import deepcopy
from unittest.mock import AsyncMock, patch

from openpeerpower.components.axis.const import DOMAIN as AXIS_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.setup import async_setup_component

from .test_device import (
    API_DISCOVERY_PORT_MANAGEMENT,
    API_DISCOVERY_RESPONSE,
    NAME,
    setup_axis_integration,
)

EVENTS = [
    {
        "operation": "Initialized",
        "topic": "tns1:Device/Trigger/Relay",
        "source": "RelayToken",
        "source_idx": "0",
        "type": "LogicalState",
        "value": "inactive",
    },
    {
        "operation": "Initialized",
        "topic": "tns1:Device/Trigger/Relay",
        "source": "RelayToken",
        "source_idx": "1",
        "type": "LogicalState",
        "value": "active",
    },
]


async def test_platform_manually_configured.opp):
    """Test that nothing happens when platform is manually configured."""
    assert await async_setup_component(
       .opp, SWITCH_DOMAIN, {SWITCH_DOMAIN: {"platform": AXIS_DOMAIN}}
    )

    assert AXIS_DOMAIN not in.opp.data


async def test_no_switches.opp):
    """Test that no output events in Axis results in no switch entities."""
    await setup_axis_integration.opp)

    assert not.opp.states.async_entity_ids(SWITCH_DOMAIN)


async def test_switches_with_port_cgi.opp):
    """Test that switches are loaded properly using port.cgi."""
    config_entry = await setup_axis_integration.opp)
    device =.opp.data[AXIS_DOMAIN][config_entry.unique_id]

    device.api.vapix.ports = {"0": AsyncMock(), "1": AsyncMock()}
    device.api.vapix.ports["0"].name = "Doorbell"
    device.api.vapix.ports["0"].open = AsyncMock()
    device.api.vapix.ports["0"].close = AsyncMock()
    device.api.vapix.ports["1"].name = ""

    device.api.event.update(EVENTS)
    await.opp.async_block_till_done()

    assert len.opp.states.async_entity_ids(SWITCH_DOMAIN)) == 2

    relay_1 =.opp.states.get(f"{SWITCH_DOMAIN}.{NAME}_relay_1")
    assert relay_1.state == STATE_ON
    assert relay_1.name == f"{NAME} Relay 1"

    entity_id = f"{SWITCH_DOMAIN}.{NAME}_doorbell"

    relay_0 =.opp.states.get(entity_id)
    assert relay_0.state == STATE_OFF
    assert relay_0.name == f"{NAME} Doorbell"

    await.opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    device.api.vapix.ports["0"].close.assert_called_once()

    await.opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    device.api.vapix.ports["0"].open.assert_called_once()


async def test_switches_with_port_management.opp):
    """Test that switches are loaded properly using port management."""
    api_discovery = deepcopy(API_DISCOVERY_RESPONSE)
    api_discovery["data"]["apiList"].append(API_DISCOVERY_PORT_MANAGEMENT)

    with patch.dict(API_DISCOVERY_RESPONSE, api_discovery):
        config_entry = await setup_axis_integration.opp)
        device =.opp.data[AXIS_DOMAIN][config_entry.unique_id]

    device.api.vapix.ports = {"0": AsyncMock(), "1": AsyncMock()}
    device.api.vapix.ports["0"].name = "Doorbell"
    device.api.vapix.ports["0"].open = AsyncMock()
    device.api.vapix.ports["0"].close = AsyncMock()
    device.api.vapix.ports["1"].name = ""

    device.api.event.update(EVENTS)
    await.opp.async_block_till_done()

    assert len.opp.states.async_entity_ids(SWITCH_DOMAIN)) == 2

    relay_1 =.opp.states.get(f"{SWITCH_DOMAIN}.{NAME}_relay_1")
    assert relay_1.state == STATE_ON
    assert relay_1.name == f"{NAME} Relay 1"

    entity_id = f"{SWITCH_DOMAIN}.{NAME}_doorbell"

    relay_0 =.opp.states.get(entity_id)
    assert relay_0.state == STATE_OFF
    assert relay_0.name == f"{NAME} Doorbell"

    await.opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    device.api.vapix.ports["0"].close.assert_called_once()

    await.opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    device.api.vapix.ports["0"].open.assert_called_once()
