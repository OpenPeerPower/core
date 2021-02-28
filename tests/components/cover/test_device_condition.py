"""The tests for Cover device conditions."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.cover import DOMAIN
from openpeerpower.const import (
    CONF_PLATFORM,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from openpeerpower.helpers import device_registry
from openpeerpower.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automation_capabilities,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def device_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


@pytest.fixture
def entity_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_registry(opp)


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


async def test_get_conditions(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a cover."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[0]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_open",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_closed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_opening",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_closing",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
    ]
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_get_conditions_set_pos(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a cover."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[1]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_open",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_closed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_opening",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_closing",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_position",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
    ]
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_get_conditions_set_tilt_pos(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a cover."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[2]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_open",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_closed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_opening",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_closing",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_tilt_position",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_{ent.unique_id}",
        },
    ]
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_get_condition_capabilities(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a cover condition."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[0]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert len(conditions) == 4
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "condition", condition
        )
        assert capabilities == {"extra_fields": []}


async def test_get_condition_capabilities_set_pos(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a cover condition."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[1]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "above",
                "optional": True,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            },
            {
                "name": "below",
                "optional": True,
                "type": "integer",
                "default": 100,
                "valueMax": 100,
                "valueMin": 0,
            },
        ]
    }
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert len(conditions) == 5
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "condition", condition
        )
        if condition["type"] == "is_position":
            assert capabilities == expected_capabilities
        else:
            assert capabilities == {"extra_fields": []}


async def test_get_condition_capabilities_set_tilt_pos(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a cover condition."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[2]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "above",
                "optional": True,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            },
            {
                "name": "below",
                "optional": True,
                "type": "integer",
                "default": 100,
                "valueMax": 100,
                "valueMin": 0,
            },
        ]
    }
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert len(conditions) == 5
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "condition", condition
        )
        if condition["type"] == "is_tilt_position":
            assert capabilities == expected_capabilities
        else:
            assert capabilities == {"extra_fields": []}


async def test_if_state(opp, calls):
    """Test for turn_on and turn_off conditions."""
    opp.states.async_set("cover.entity", STATE_OPEN)

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "cover.entity",
                            "type": "is_open",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_open - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "cover.entity",
                            "type": "is_closed",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_closed - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event3"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "cover.entity",
                            "type": "is_opening",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_opening - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event4"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "cover.entity",
                            "type": "is_closing",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_closing - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
            ]
        },
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "is_open - event - test_event1"

    opp.states.async_set("cover.entity", STATE_CLOSED)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "is_closed - event - test_event2"

    opp.states.async_set("cover.entity", STATE_OPENING)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()
    assert len(calls) == 3
    assert calls[2].data["some"] == "is_opening - event - test_event3"

    opp.states.async_set("cover.entity", STATE_CLOSING)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event4")
    await opp.async_block_till_done()
    assert len(calls) == 4
    assert calls[3].data["some"] == "is_closing - event - test_event4"


async def test_if_position(opp, calls):
    """Test for position conditions."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[1]
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": ent.entity_id,
                            "type": "is_position",
                            "above": 45,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_pos_gt_45 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": ent.entity_id,
                            "type": "is_position",
                            "below": 90,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_pos_lt_90 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event3"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": ent.entity_id,
                            "type": "is_position",
                            "above": 45,
                            "below": 90,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_pos_gt_45_lt_90 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
            ]
        },
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()
    assert len(calls) == 3
    assert calls[0].data["some"] == "is_pos_gt_45 - event - test_event1"
    assert calls[1].data["some"] == "is_pos_lt_90 - event - test_event2"
    assert calls[2].data["some"] == "is_pos_gt_45_lt_90 - event - test_event3"

    opp.states.async_set(
        ent.entity_id, STATE_CLOSED, attributes={"current_position": 45}
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()
    assert len(calls) == 4
    assert calls[3].data["some"] == "is_pos_lt_90 - event - test_event2"

    opp.states.async_set(
        ent.entity_id, STATE_CLOSED, attributes={"current_position": 90}
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()
    assert len(calls) == 5
    assert calls[4].data["some"] == "is_pos_gt_45 - event - test_event1"


async def test_if_tilt_position(opp, calls):
    """Test for tilt position conditions."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[2]
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": ent.entity_id,
                            "type": "is_tilt_position",
                            "above": 45,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_pos_gt_45 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": ent.entity_id,
                            "type": "is_tilt_position",
                            "below": 90,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_pos_lt_90 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event3"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": ent.entity_id,
                            "type": "is_tilt_position",
                            "above": 45,
                            "below": 90,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_pos_gt_45_lt_90 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
            ]
        },
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()
    assert len(calls) == 3
    assert calls[0].data["some"] == "is_pos_gt_45 - event - test_event1"
    assert calls[1].data["some"] == "is_pos_lt_90 - event - test_event2"
    assert calls[2].data["some"] == "is_pos_gt_45_lt_90 - event - test_event3"

    opp.states.async_set(
        ent.entity_id, STATE_CLOSED, attributes={"current_tilt_position": 45}
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()
    assert len(calls) == 4
    assert calls[3].data["some"] == "is_pos_lt_90 - event - test_event2"

    opp.states.async_set(
        ent.entity_id, STATE_CLOSED, attributes={"current_tilt_position": 90}
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()
    assert len(calls) == 5
    assert calls[4].data["some"] == "is_pos_gt_45 - event - test_event1"
