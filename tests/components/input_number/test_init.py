"""The tests for the Input number component."""
# pylint: disable=protected-access
from unittest.mock import patch

import pytest
import voluptuous as vol

from openpeerpower.components.input_number import (
    ATTR_VALUE,
    DOMAIN,
    SERVICE_DECREMENT,
    SERVICE_INCREMENT,
    SERVICE_RELOAD,
    SERVICE_SET_VALUE,
)
from openpeerpower.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_NAME,
)
from openpeerpower.core import Context, CoreState, State
from openpeerpower.exceptions import Unauthorized
from openpeerpower.helpers import entity_registry
from openpeerpower.setup import async_setup_component

from tests.common import mock_restore_cache


@pytest.fixture
def storage_setup_opp, opp_storage):
    """Storage setup."""

    async def _storage(items=None, config=None):
        if items is None:
            opp.storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {
                    "items": [
                        {
                            "id": "from_storage",
                            "initial": 10,
                            "name": "from storage",
                            "max": 100,
                            "min": 0,
                            "step": 1,
                            "mode": "slider",
                        }
                    ]
                },
            }
        else:
            opp.storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": items},
            }
        if config is None:
            config = {DOMAIN: {}}
        return await async_setup_component.opp, DOMAIN, config)

    return _storage


async def set_value.opp, entity_id, value):
    """Set input_number to value.

    This is a legacy helper method. Do not use it for new tests.
    """
    await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )


async def increment.opp, entity_id):
    """Increment value of entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    await opp.services.async_call(
        DOMAIN, SERVICE_INCREMENT, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )


async def decrement.opp, entity_id):
    """Decrement value of entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    await opp.services.async_call(
        DOMAIN, SERVICE_DECREMENT, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )


async def test_config(opp):
    """Test config."""
    invalid_configs = [
        None,
        {},
        {"name with space": None},
        {"test_1": {"min": 50, "max": 50}},
    ]
    for cfg in invalid_configs:
        assert not await async_setup_component.opp, DOMAIN, {DOMAIN: cfg})


async def test_set_value.opp, caplog):
    """Test set_value method."""
    assert await async_setup_component(
        opp. DOMAIN, {DOMAIN: {"test_1": {"initial": 50, "min": 0, "max": 100}}}
    )
    entity_id = "input_number.test_1"

    state = opp.states.get(entity_id)
    assert 50 == float(state.state)

    await set_value.opp, entity_id, "30.4")

    state = opp.states.get(entity_id)
    assert 30.4 == float(state.state)

    await set_value.opp, entity_id, "70")

    state = opp.states.get(entity_id)
    assert 70 == float(state.state)

    with pytest.raises(vol.Invalid) as excinfo:
        await set_value.opp, entity_id, "110")

    assert "Invalid value for input_number.test_1: 110.0 (range 0.0 - 100.0)" in str(
        excinfo.value
    )

    state = opp.states.get(entity_id)
    assert 70 == float(state.state)


async def test_increment.opp):
    """Test increment method."""
    assert await async_setup_component(
        opp. DOMAIN, {DOMAIN: {"test_2": {"initial": 50, "min": 0, "max": 51}}}
    )
    entity_id = "input_number.test_2"

    state = opp.states.get(entity_id)
    assert 50 == float(state.state)

    await increment.opp, entity_id)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert 51 == float(state.state)

    await increment.opp, entity_id)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert 51 == float(state.state)


async def test_decrement.opp):
    """Test decrement method."""
    assert await async_setup_component(
        opp. DOMAIN, {DOMAIN: {"test_3": {"initial": 50, "min": 49, "max": 100}}}
    )
    entity_id = "input_number.test_3"

    state = opp.states.get(entity_id)
    assert 50 == float(state.state)

    await decrement.opp, entity_id)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert 49 == float(state.state)

    await decrement.opp, entity_id)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert 49 == float(state.state)


async def test_mode.opp):
    """Test mode settings."""
    assert await async_setup_component(
        opp.
        DOMAIN,
        {
            DOMAIN: {
                "test_default_slider": {"min": 0, "max": 100},
                "test_explicit_box": {"min": 0, "max": 100, "mode": "box"},
                "test_explicit_slider": {"min": 0, "max": 100, "mode": "slider"},
            }
        },
    )

    state = opp.states.get("input_number.test_default_slider")
    assert state
    assert "slider" == state.attributes["mode"]

    state = opp.states.get("input_number.test_explicit_box")
    assert state
    assert "box" == state.attributes["mode"]

    state = opp.states.get("input_number.test_explicit_slider")
    assert state
    assert "slider" == state.attributes["mode"]


async def test_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
        opp. (State("input_number.b1", "70"), State("input_number.b2", "200"))
    )

    opp.state = CoreState.starting

    await async_setup_component(
        opp.
        DOMAIN,
        {DOMAIN: {"b1": {"min": 0, "max": 100}, "b2": {"min": 10, "max": 100}}},
    )

    state = opp.states.get("input_number.b1")
    assert state
    assert float(state.state) == 70

    state = opp.states.get("input_number.b2")
    assert state
    assert float(state.state) == 10


async def test_initial_state_overrules_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
        opp. (State("input_number.b1", "70"), State("input_number.b2", "200"))
    )

    opp.state = CoreState.starting

    await async_setup_component(
        opp.
        DOMAIN,
        {
            DOMAIN: {
                "b1": {"initial": 50, "min": 0, "max": 100},
                "b2": {"initial": 60, "min": 0, "max": 100},
            }
        },
    )

    state = opp.states.get("input_number.b1")
    assert state
    assert float(state.state) == 50

    state = opp.states.get("input_number.b2")
    assert state
    assert float(state.state) == 60


async def test_no_initial_state_and_no_restore_state.opp):
    """Ensure that entity is create without initial and restore feature."""
    opp.state = CoreState.starting

    await async_setup_component.opp, DOMAIN, {DOMAIN: {"b1": {"min": 0, "max": 100}}})

    state = opp.states.get("input_number.b1")
    assert state
    assert float(state.state) == 0


async def test_input_number_context.opp, opp_admin_user):
    """Test that input_number context works."""
    assert await async_setup_component(
        opp. "input_number", {"input_number": {"b1": {"min": 0, "max": 100}}}
    )

    state = opp.states.get("input_number.b1")
    assert state is not None

    await opp.services.async_call(
        "input_number",
        "increment",
        {"entity_id": state.entity_id},
        True,
        Context(user_id.opp_admin_user.id),
    )

    state2 = opp.states.get("input_number.b1")
    assert state2 is not None
    assert state.state != state2.state
    assert state2.context.user_id == opp_admin_user.id


async def test_reload.opp, opp_admin_user, opp_read_only_user):
    """Test reload service."""
    count_start = len.opp.states.async_entity_ids())
    ent_reg = await entity_registry.async_get_registry.opp)

    assert await async_setup_component(
        opp.
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {"initial": 50, "min": 0, "max": 51},
                "test_3": {"initial": 10, "min": 0, "max": 15},
            }
        },
    )

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_number.test_1")
    state_2 = opp.states.get("input_number.test_2")
    state_3 = opp.states.get("input_number.test_3")

    assert state_1 is not None
    assert state_2 is None
    assert state_3 is not None
    assert 50 == float(state_1.state)
    assert 10 == float(state_3.state)
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is not None

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_1": {"initial": 40, "min": 0, "max": 51},
                "test_2": {"initial": 20, "min": 10, "max": 30},
            }
        },
    ):
        with pytest.raises(Unauthorized):
            await opp.services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                blocking=True,
                context=Context(user_id.opp_read_only_user.id),
            )
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )
        await opp.async_block_till_done()

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_number.test_1")
    state_2 = opp.states.get("input_number.test_2")
    state_3 = opp.states.get("input_number.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert 50 == float(state_1.state)
    assert 20 == float(state_2.state)
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is None


async def test_load_from_storage.opp, storage_setup):
    """Test set up from storage."""
    assert await storage_setup()
    state = opp.states.get(f"{DOMAIN}.from_storage")
    assert float(state.state) == 10
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "from storage"
    assert state.attributes.get(ATTR_EDITABLE)


async def test_editable_state_attribute.opp, storage_setup):
    """Test editable attribute."""
    assert await storage_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    "min": 1,
                    "max": 10,
                    "initial": 5,
                    "step": 1,
                    "mode": "slider",
                }
            }
        }
    )

    state = opp.states.get(f"{DOMAIN}.from_storage")
    assert float(state.state) == 10
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "from storage"
    assert state.attributes.get(ATTR_EDITABLE)

    state = opp.states.get(f"{DOMAIN}.from_yaml")
    assert float(state.state) == 5
    assert not state.attributes.get(ATTR_EDITABLE)


async def test_ws_list.opp, opp_ws_client, storage_setup):
    """Test listing via WS."""
    assert await storage_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    "min": 1,
                    "max": 10,
                    "initial": 5,
                    "step": 1,
                    "mode": "slider",
                }
            }
        }
    )

    client = await opp_ws_client.opp)

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


async def test_ws_delete.opp, opp_ws_client, storage_setup):
    """Test WS delete cleans up entity registry."""
    assert await storage_setup()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await opp_ws_client.opp)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/delete", f"{DOMAIN}_id": f"{input_id}"}
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None


async def test_update_min_max.opp, opp_ws_client, storage_setup):
    """Test updating min/max updates the state."""

    items = [
        {
            "id": "from_storage",
            "name": "from storage",
            "max": 100,
            "min": 0,
            "step": 1,
            "mode": "slider",
        }
    ]
    assert await storage_setup(items)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state is not None
    assert state.state
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await opp_ws_client.opp)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/update", f"{DOMAIN}_id": f"{input_id}", "min": 9}
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert float(state.state) == 9

    await client.send_json(
        {
            "id": 7,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            "max": 5,
            "min": 0,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert float(state.state) == 5


async def test_ws_create.opp, opp_ws_client, storage_setup):
    """Test create WS."""
    assert await storage_setup(items=[])

    input_id = "new_input"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None

    client = await opp_ws_client.opp)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            "name": "New Input",
            "max": 20,
            "min": 0,
            "initial": 10,
            "step": 1,
            "mode": "slider",
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert float(state.state) == 10


async def test_setup_no_config(opp, opp_admin_user):
    """Test component setup with no config."""
    count_start = len.opp.states.async_entity_ids())
    assert await async_setup_component.opp, DOMAIN, {})

    with patch(
        "openpeerpower.config.load_yaml_config_file", autospec=True, return_value={}
    ):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )
        await opp.async_block_till_done()

    assert count_start == len.opp.states.async_entity_ids())
