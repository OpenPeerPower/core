"""The tests for the Input select component."""
# pylint: disable=protected-access
from unittest.mock import patch

import pytest

from openpeerpower.components.input_select import (
    ATTR_OPTION,
    ATTR_OPTIONS,
    CONF_INITIAL,
    DOMAIN,
    SERVICE_SELECT_FIRST,
    SERVICE_SELECT_LAST,
    SERVICE_SELECT_NEXT,
    SERVICE_SELECT_OPTION,
    SERVICE_SELECT_PREVIOUS,
    SERVICE_SET_OPTIONS,
)
from openpeerpower.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_NAME,
    SERVICE_RELOAD,
)
from openpeerpowerr.core import Context, State
from openpeerpowerr.exceptions import Unauthorized
from openpeerpowerr.helpers import entity_registry
from openpeerpowerr.loader import bind_opp
from openpeerpowerr.setup import async_setup_component

from tests.common import mock_restore_cache


@pytest.fixture
def storage_setup.opp,.opp_storage):
    """Storage setup."""

    async def _storage(items=None, config=None):
        if items is None:
           .opp_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {
                    "items": [
                        {
                            "id": "from_storage",
                            "name": "from storage",
                            "options": ["storage option 1", "storage option 2"],
                        }
                    ]
                },
            }
        else:
           .opp_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": items},
            }
        if config is None:
            config = {DOMAIN: {}}
        return await async_setup_component.opp, DOMAIN, config)

    return _storage


@bind_opp
def select_option.opp, entity_id, option):
    """Set value of input_select.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.async_create_task(
       .opp.services.async_call(
            DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
        )
    )


@bind_opp
def select_next.opp, entity_id):
    """Set next value of input_select.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.async_create_task(
       .opp.services.async_call(
            DOMAIN, SERVICE_SELECT_NEXT, {ATTR_ENTITY_ID: entity_id}
        )
    )


@bind_opp
def select_previous.opp, entity_id):
    """Set previous value of input_select.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.async_create_task(
       .opp.services.async_call(
            DOMAIN, SERVICE_SELECT_PREVIOUS, {ATTR_ENTITY_ID: entity_id}
        )
    )


@bind_opp
def select_first.opp, entity_id):
    """Set first value of input_select.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.async_create_task(
       .opp.services.async_call(
            DOMAIN, SERVICE_SELECT_FIRST, {ATTR_ENTITY_ID: entity_id}
        )
    )


@bind_opp
def select_last.opp, entity_id):
    """Set last value of input_select.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.async_create_task(
       .opp.services.async_call(
            DOMAIN, SERVICE_SELECT_LAST, {ATTR_ENTITY_ID: entity_id}
        )
    )


async def test_config.opp):
    """Test config."""
    invalid_configs = [
        None,
        {},
        {"name with space": None},
        # {'bad_options': {'options': None}},
        {"bad_initial": {"options": [1, 2], "initial": 3}},
    ]

    for cfg in invalid_configs:
        assert not await async_setup_component.opp, DOMAIN, {DOMAIN: cfg})


async def test_select_option.opp):
    """Test select_option methods."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {DOMAIN: {"test_1": {"options": ["some option", "another option"]}}},
    )
    entity_id = "input_select.test_1"

    state = opp.states.get(entity_id)
    assert "some option" == state.state

    select_option.opp, entity_id, "another option")
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "another option" == state.state

    select_option.opp, entity_id, "non existing option")
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "another option" == state.state


async def test_select_next.opp):
    """Test select_next methods."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {
                    "options": ["first option", "middle option", "last option"],
                    "initial": "middle option",
                }
            }
        },
    )
    entity_id = "input_select.test_1"

    state = opp.states.get(entity_id)
    assert "middle option" == state.state

    select_next.opp, entity_id)
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "last option" == state.state

    select_next.opp, entity_id)
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "first option" == state.state


async def test_select_previous.opp):
    """Test select_previous methods."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {
                    "options": ["first option", "middle option", "last option"],
                    "initial": "middle option",
                }
            }
        },
    )
    entity_id = "input_select.test_1"

    state = opp.states.get(entity_id)
    assert "middle option" == state.state

    select_previous.opp, entity_id)
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "first option" == state.state

    select_previous.opp, entity_id)
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "last option" == state.state


async def test_select_first_last.opp):
    """Test select_first and _last methods."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {
                    "options": ["first option", "middle option", "last option"],
                    "initial": "middle option",
                }
            }
        },
    )
    entity_id = "input_select.test_1"

    state = opp.states.get(entity_id)
    assert "middle option" == state.state

    select_first.opp, entity_id)
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "first option" == state.state

    select_last.opp, entity_id)
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "last option" == state.state


async def test_config_options.opp):
    """Test configuration options."""
    count_start = len.opp.states.async_entity_ids())

    test_2_options = ["Good Option", "Better Option", "Best Option"]

    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {"options": [1, 2]},
                "test_2": {
                    "name": "Hello World",
                    "icon": "mdi:work",
                    "options": test_2_options,
                    "initial": "Better Option",
                },
            }
        },
    )

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_select.test_1")
    state_2 = opp.states.get("input_select.test_2")

    assert state_1 is not None
    assert state_2 is not None

    assert "1" == state_1.state
    assert ["1", "2"] == state_1.attributes.get(ATTR_OPTIONS)
    assert ATTR_ICON not in state_1.attributes

    assert "Better Option" == state_2.state
    assert test_2_options == state_2.attributes.get(ATTR_OPTIONS)
    assert "Hello World" == state_2.attributes.get(ATTR_FRIENDLY_NAME)
    assert "mdi:work" == state_2.attributes.get(ATTR_ICON)


async def test_set_options_service.opp):
    """Test set_options service."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {
                    "options": ["first option", "middle option", "last option"],
                    "initial": "middle option",
                }
            }
        },
    )
    entity_id = "input_select.test_1"

    state = opp.states.get(entity_id)
    assert "middle option" == state.state

    data = {ATTR_OPTIONS: ["test1", "test2"], "entity_id": entity_id}
    await opp..services.async_call(DOMAIN, SERVICE_SET_OPTIONS, data)
    await opp..async_block_till_done()

    state = opp.states.get(entity_id)
    assert "test1" == state.state

    select_option.opp, entity_id, "first option")
    await opp..async_block_till_done()
    state = opp.states.get(entity_id)
    assert "test1" == state.state

    select_option.opp, entity_id, "test2")
    await opp..async_block_till_done()
    state = opp.states.get(entity_id)
    assert "test2" == state.state


async def test_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
       .opp,
        (
            State("input_select.s1", "last option"),
            State("input_select.s2", "bad option"),
        ),
    )

    options = {"options": ["first option", "middle option", "last option"]}

    await async_setup_component.opp, DOMAIN, {DOMAIN: {"s1": options, "s2": options}})

    state = opp.states.get("input_select.s1")
    assert state
    assert state.state == "last option"

    state = opp.states.get("input_select.s2")
    assert state
    assert state.state == "first option"


async def test_initial_state_overrules_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
       .opp,
        (
            State("input_select.s1", "last option"),
            State("input_select.s2", "bad option"),
        ),
    )

    options = {
        "options": ["first option", "middle option", "last option"],
        "initial": "middle option",
    }

    await async_setup_component.opp, DOMAIN, {DOMAIN: {"s1": options, "s2": options}})

    state = opp.states.get("input_select.s1")
    assert state
    assert state.state == "middle option"

    state = opp.states.get("input_select.s2")
    assert state
    assert state.state == "middle option"


async def test_input_select_context.opp,.opp_admin_user):
    """Test that input_select context works."""
    assert await async_setup_component(
       .opp,
        "input_select",
        {
            "input_select": {
                "s1": {"options": ["first option", "middle option", "last option"]}
            }
        },
    )

    state = opp.states.get("input_select.s1")
    assert state is not None

    await opp..services.async_call(
        "input_select",
        "select_next",
        {"entity_id": state.entity_id},
        True,
        Context(user_id.opp_admin_user.id),
    )

    state2 = opp.states.get("input_select.s1")
    assert state2 is not None
    assert state.state != state2.state
    assert state2.context.user_id == opp_admin_user.id


async def test_reload.opp,.opp_admin_user,.opp_read_only_user):
    """Test reload service."""
    count_start = len.opp.states.async_entity_ids())
    ent_reg = await entity_registry.async_get_registry.opp)

    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {
                    "options": ["first option", "middle option", "last option"],
                    "initial": "middle option",
                },
                "test_2": {
                    "options": ["an option", "not an option"],
                    "initial": "an option",
                },
            }
        },
    )

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_select.test_1")
    state_2 = opp.states.get("input_select.test_2")
    state_3 = opp.states.get("input_select.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert "middle option" == state_1.state
    assert "an option" == state_2.state
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is None

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {
                    "options": ["an option", "reloaded option"],
                    "initial": "reloaded option",
                },
                "test_3": {
                    "options": ["new option", "newer option"],
                    "initial": "newer option",
                },
            }
        },
    ):
        with pytest.raises(Unauthorized):
            await opp..services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                blocking=True,
                context=Context(user_id.opp_read_only_user.id),
            )
        await opp..services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )
        await opp..async_block_till_done()

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_select.test_1")
    state_2 = opp.states.get("input_select.test_2")
    state_3 = opp.states.get("input_select.test_3")

    assert state_1 is None
    assert state_2 is not None
    assert state_3 is not None
    assert "an option" == state_2.state
    assert "newer option" == state_3.state
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is not None


async def test_load_from_storage.opp, storage_setup):
    """Test set up from storage."""
    assert await storage_setup()
    state = opp.states.get(f"{DOMAIN}.from_storage")
    assert state.state == "storage option 1"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "from storage"
    assert state.attributes.get(ATTR_EDITABLE)


async def test_editable_state_attribute.opp, storage_setup):
    """Test editable attribute."""
    assert await storage_setup(
        config={DOMAIN: {"from_yaml": {"options": ["yaml option", "other option"]}}}
    )

    state = opp.states.get(f"{DOMAIN}.from_storage")
    assert state.state == "storage option 1"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "from storage"
    assert state.attributes.get(ATTR_EDITABLE)

    state = opp.states.get(f"{DOMAIN}.from_yaml")
    assert state.state == "yaml option"
    assert not state.attributes.get(ATTR_EDITABLE)


async def test_ws_list.opp,.opp_ws_client, storage_setup):
    """Test listing via WS."""
    assert await storage_setup(
        config={DOMAIN: {"from_yaml": {"options": ["yaml option"]}}}
    )

    client = await opp._ws_client.opp)

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

    client = await opp._ws_client.opp)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/delete", f"{DOMAIN}_id": f"{input_id}"}
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None


async def test_update.opp,.opp_ws_client, storage_setup):
    """Test updating min/max updates the state."""

    items = [
        {
            "id": "from_storage",
            "name": "from storage",
            "options": ["yaml update 1", "yaml update 2"],
        }
    ]
    assert await storage_setup(items)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state.attributes[ATTR_OPTIONS] == ["yaml update 1", "yaml update 2"]
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await opp._ws_client.opp)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            "options": ["new option", "newer option"],
            CONF_INITIAL: "newer option",
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state.attributes[ATTR_OPTIONS] == ["new option", "newer option"]

    await client.send_json(
        {
            "id": 7,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            "options": ["new option", "no newer option"],
        }
    )
    resp = await client.receive_json()
    assert not resp["success"]


async def test_ws_create.opp,.opp_ws_client, storage_setup):
    """Test create WS."""
    assert await storage_setup(items=[])

    input_id = "new_input"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None

    client = await opp._ws_client.opp)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            "name": "New Input",
            "options": ["new option", "even newer option"],
            "initial": "even newer option",
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state.state == "even newer option"


async def test_setup_no_config.opp,.opp_admin_user):
    """Test component setup with no config."""
    count_start = len.opp.states.async_entity_ids())
    assert await async_setup_component.opp, DOMAIN, {})

    with patch(
        "openpeerpower.config.load_yaml_config_file", autospec=True, return_value={}
    ):
        await opp..services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )
        await opp..async_block_till_done()

    assert count_start == len.opp.states.async_entity_ids())
