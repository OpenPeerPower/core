"""The tests for the input_boolean component."""
# pylint: disable=protected-access
import logging
from unittest.mock import patch

import pytest

from openpeerpower.components.input_boolean import CONF_INITIAL, DOMAIN, is_on
from openpeerpower.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_NAME,
    SERVICE_RELOAD,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpowerr.core import Context, CoreState, State
from openpeerpowerr.helpers import entity_registry
from openpeerpowerr.setup import async_setup_component

from tests.common import mock_component, mock_restore_cache

_LOGGER = logging.getLogger(__name__)


@pytest.fixture
def storage_setup.opp,.opp_storage):
    """Storage setup."""

    async def _storage(items=None, config=None):
        if items is None:
           .opp_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": [{"id": "from_storage", "name": "from storage"}]},
            }
        else:
           .opp_storage[DOMAIN] = items
        if config is None:
            config = {DOMAIN: {}}
        return await async_setup_component.opp, DOMAIN, config)

    return _storage


async def test_config.opp):
    """Test config."""
    invalid_configs = [None, 1, {}, {"name with space": None}]

    for cfg in invalid_configs:
        assert not await async_setup_component.opp, DOMAIN, {DOMAIN: cfg})


async def test_methods.opp):
    """Test is_on, turn_on, turn_off methods."""
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {"test_1": None}})
    entity_id = "input_boolean.test_1"

    assert not is_on.opp, entity_id)

    await.opp.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    assert is_on.opp, entity_id)

    await.opp.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    assert not is_on.opp, entity_id)

    await.opp.services.async_call(
        DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    assert is_on.opp, entity_id)


async def test_config_options.opp):
    """Test configuration options."""
    count_start = len.opp.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s",.opp.states.async_entity_ids())

    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": None,
                "test_2": {"name": "Hello World", "icon": "mdi:work", "initial": True},
            }
        },
    )

    _LOGGER.debug("ENTITIES: %s",.opp.states.async_entity_ids())

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_boolean.test_1")
    state_2 = opp.states.get("input_boolean.test_2")

    assert state_1 is not None
    assert state_2 is not None

    assert STATE_OFF == state_1.state
    assert ATTR_ICON not in state_1.attributes
    assert ATTR_FRIENDLY_NAME not in state_1.attributes

    assert STATE_ON == state_2.state
    assert "Hello World" == state_2.attributes.get(ATTR_FRIENDLY_NAME)
    assert "mdi:work" == state_2.attributes.get(ATTR_ICON)


async def test_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
       .opp,
        (
            State("input_boolean.b1", "on"),
            State("input_boolean.b2", "off"),
            State("input_boolean.b3", "on"),
        ),
    )

   .opp.state = CoreState.starting
    mock_component.opp, "recorder")

    await async_setup_component.opp, DOMAIN, {DOMAIN: {"b1": None, "b2": None}})

    state = opp.states.get("input_boolean.b1")
    assert state
    assert state.state == "on"

    state = opp.states.get("input_boolean.b2")
    assert state
    assert state.state == "off"


async def test_initial_state_overrules_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
       .opp, (State("input_boolean.b1", "on"), State("input_boolean.b2", "off"))
    )

   .opp.state = CoreState.starting

    await async_setup_component(
       .opp,
        DOMAIN,
        {DOMAIN: {"b1": {CONF_INITIAL: False}, "b2": {CONF_INITIAL: True}}},
    )

    state = opp.states.get("input_boolean.b1")
    assert state
    assert state.state == "off"

    state = opp.states.get("input_boolean.b2")
    assert state
    assert state.state == "on"


async def test_input_boolean_context.opp,.opp_admin_user):
    """Test that input_boolean context works."""
    assert await async_setup_component(
       .opp, "input_boolean", {"input_boolean": {"ac": {CONF_INITIAL: True}}}
    )

    state = opp.states.get("input_boolean.ac")
    assert state is not None

    await.opp.services.async_call(
        "input_boolean",
        "turn_off",
        {"entity_id": state.entity_id},
        True,
        Context(user_id.opp_admin_user.id),
    )

    state2 = opp.states.get("input_boolean.ac")
    assert state2 is not None
    assert state.state != state2.state
    assert state2.context.user_id == opp_admin_user.id


async def test_reload.opp,.opp_admin_user):
    """Test reload service."""
    count_start = len.opp.states.async_entity_ids())
    ent_reg = await entity_registry.async_get_registry.opp)

    _LOGGER.debug("ENTITIES @ start: %s",.opp.states.async_entity_ids())

    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": None,
                "test_2": {"name": "Hello World", "icon": "mdi:work", "initial": True},
            }
        },
    )

    _LOGGER.debug("ENTITIES: %s",.opp.states.async_entity_ids())

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_boolean.test_1")
    state_2 = opp.states.get("input_boolean.test_2")
    state_3 = opp.states.get("input_boolean.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert STATE_ON == state_2.state

    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is None

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {
                    "name": "Hello World reloaded",
                    "icon": "mdi:work_reloaded",
                    "initial": False,
                },
                "test_3": None,
            }
        },
    ):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_boolean.test_1")
    state_2 = opp.states.get("input_boolean.test_2")
    state_3 = opp.states.get("input_boolean.test_3")

    assert state_1 is None
    assert state_2 is not None
    assert state_3 is not None

    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is not None

    assert STATE_ON == state_2.state  # reload is not supposed to change entity state
    assert "Hello World reloaded" == state_2.attributes.get(ATTR_FRIENDLY_NAME)
    assert "mdi:work_reloaded" == state_2.attributes.get(ATTR_ICON)


async def test_load_from_storage.opp, storage_setup):
    """Test set up from storage."""
    assert await storage_setup()
    state = opp.states.get(f"{DOMAIN}.from_storage")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "from storage"
    assert state.attributes.get(ATTR_EDITABLE)


async def test_editable_state_attribute.opp, storage_setup):
    """Test editable attribute."""
    assert await storage_setup(config={DOMAIN: {"from_yaml": None}})

    state = opp.states.get(f"{DOMAIN}.from_storage")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "from storage"
    assert state.attributes.get(ATTR_EDITABLE)

    state = opp.states.get(f"{DOMAIN}.from_yaml")
    assert state.state == STATE_OFF
    assert not state.attributes.get(ATTR_EDITABLE)


async def test_ws_list.opp,.opp_ws_client, storage_setup):
    """Test listing via WS."""
    assert await storage_setup(config={DOMAIN: {"from_yaml": None}})

    client = await.opp_ws_client.opp)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    storage_ent = "from_storage"
    yaml_ent = "from_yaml"
    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 1
    assert storage_ent in result
    assert yaml_ent not in result
    assert result[storage_ent][ATTR_NAME] == "from storage"


async def test_ws_delete.opp,.opp_ws_client, storage_setup):
    """Test WS delete cleans up entity registry."""
    assert await storage_setup()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await.opp_ws_client.opp)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/delete", f"{DOMAIN}_id": f"{input_id}"}
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None


async def test_setup_no_config.opp,.opp_admin_user):
    """Test component setup with no config."""
    count_start = len.opp.states.async_entity_ids())
    assert await async_setup_component.opp, DOMAIN, {})

    with patch(
        "openpeerpower.config.load_yaml_config_file", autospec=True, return_value={}
    ):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )

    assert count_start == len.opp.states.async_entity_ids())
