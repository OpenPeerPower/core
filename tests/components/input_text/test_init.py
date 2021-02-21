"""The tests for the Input text component."""
# pylint: disable=protected-access
from unittest.mock import patch

import pytest

from openpeerpower.components.input_text import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_VALUE,
    CONF_INITIAL,
    CONF_MAX_VALUE,
    CONF_MIN_VALUE,
    DOMAIN,
    MODE_TEXT,
    SERVICE_SET_VALUE,
)
from openpeerpower.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_NAME,
    SERVICE_RELOAD,
)
from openpeerpowerr.core import Context, CoreState, State
from openpeerpowerr.exceptions import Unauthorized
from openpeerpowerr.helpers import entity_registry
from openpeerpowerr.loader import bind_opp
from openpeerpowerr.setup import async_setup_component

from tests.common import mock_restore_cache

TEST_VAL_MIN = 2
TEST_VAL_MAX = 22


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
                            "initial": "loaded from storage",
                            ATTR_MAX: TEST_VAL_MAX,
                            ATTR_MIN: TEST_VAL_MIN,
                            ATTR_MODE: MODE_TEXT,
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
def set_value.opp, entity_id, value):
    """Set input_text to value.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.async_create_task(
       .opp.services.async_call(
            DOMAIN, SERVICE_SET_VALUE, {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value}
        )
    )


async def test_config.opp):
    """Test config."""
    invalid_configs = [
        None,
        {},
        {"name with space": None},
        {"test_1": {"min": 50, "max": 50}},
    ]
    for cfg in invalid_configs:
        assert not await async_setup_component.opp, DOMAIN, {DOMAIN: cfg})


async def test_set_value.opp):
    """Test set_value method."""
    assert await async_setup_component(
       .opp, DOMAIN, {DOMAIN: {"test_1": {"initial": "test", "min": 3, "max": 10}}}
    )
    entity_id = "input_text.test_1"

    state = opp.states.get(entity_id)
    assert str(state.state) == "test"

    set_value.opp, entity_id, "testing")
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert str(state.state) == "testing"

    set_value.opp, entity_id, "testing too long")
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert str(state.state) == "testing"


async def test_mode.opp):
    """Test mode settings."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_default_text": {"initial": "test", "min": 3, "max": 10},
                "test_explicit_text": {
                    "initial": "test",
                    "min": 3,
                    "max": 10,
                    "mode": "text",
                },
                "test_explicit_password": {
                    "initial": "test",
                    "min": 3,
                    "max": 10,
                    "mode": "password",
                },
            }
        },
    )

    state = opp.states.get("input_text.test_default_text")
    assert state
    assert state.attributes["mode"] == "text"

    state = opp.states.get("input_text.test_explicit_text")
    assert state
    assert state.attributes["mode"] == "text"

    state = opp.states.get("input_text.test_explicit_password")
    assert state
    assert state.attributes["mode"] == "password"


async def test_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
       .opp,
        (State("input_text.b1", "test"), State("input_text.b2", "testing too long")),
    )

   .opp.state = CoreState.starting

    assert await async_setup_component(
       .opp, DOMAIN, {DOMAIN: {"b1": None, "b2": {"min": 0, "max": 10}}}
    )

    state = opp.states.get("input_text.b1")
    assert state
    assert str(state.state) == "test"

    state = opp.states.get("input_text.b2")
    assert state
    assert str(state.state) == "unknown"


async def test_initial_state_overrules_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
       .opp,
        (State("input_text.b1", "testing"), State("input_text.b2", "testing too long")),
    )

   .opp.state = CoreState.starting

    await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "b1": {"initial": "test", "min": 0, "max": 10},
                "b2": {"initial": "test", "min": 0, "max": 10},
            }
        },
    )

    state = opp.states.get("input_text.b1")
    assert state
    assert str(state.state) == "test"

    state = opp.states.get("input_text.b2")
    assert state
    assert str(state.state) == "test"


async def test_no_initial_state_and_no_restore_state.opp):
    """Ensure that entity is create without initial and restore feature."""
   .opp.state = CoreState.starting

    await async_setup_component.opp, DOMAIN, {DOMAIN: {"b1": {"min": 0, "max": 100}}})

    state = opp.states.get("input_text.b1")
    assert state
    assert str(state.state) == "unknown"


async def test_input_text_context.opp,.opp_admin_user):
    """Test that input_text context works."""
    assert await async_setup_component(
       .opp, "input_text", {"input_text": {"t1": {"initial": "bla"}}}
    )

    state = opp.states.get("input_text.t1")
    assert state is not None

    await.opp.services.async_call(
        "input_text",
        "set_value",
        {"entity_id": state.entity_id, "value": "new_value"},
        True,
        Context(user_id.opp_admin_user.id),
    )

    state2 = opp.states.get("input_text.t1")
    assert state2 is not None
    assert state.state != state2.state
    assert state2.context.user_id == opp_admin_user.id


async def test_config_none.opp):
    """Set up input_text without any config."""
    await async_setup_component.opp, DOMAIN, {DOMAIN: {"b1": None}})

    state = opp.states.get("input_text.b1")
    assert state
    assert str(state.state) == "unknown"

    # with empty config we still should have the defaults
    assert state.attributes[ATTR_MODE] == MODE_TEXT
    assert state.attributes[ATTR_MAX] == CONF_MAX_VALUE
    assert state.attributes[ATTR_MIN] == CONF_MIN_VALUE


async def test_reload.opp,.opp_admin_user,.opp_read_only_user):
    """Test reload service."""
    count_start = len.opp.states.async_entity_ids())

    assert await async_setup_component(
       .opp,
        DOMAIN,
        {DOMAIN: {"test_1": {"initial": "test 1"}, "test_2": {"initial": "test 2"}}},
    )

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_text.test_1")
    state_2 = opp.states.get("input_text.test_2")
    state_3 = opp.states.get("input_text.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert state_1.state == "test 1"
    assert state_2.state == "test 2"
    assert state_1.attributes[ATTR_MIN] == 0
    assert state_2.attributes[ATTR_MAX] == 100

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {"initial": "test reloaded", ATTR_MIN: 12},
                "test_3": {"initial": "test 3", ATTR_MAX: 21},
            }
        },
    ):
        with pytest.raises(Unauthorized):
            await.opp.services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                blocking=True,
                context=Context(user_id.opp_read_only_user.id),
            )
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )
        await opp.async_block_till_done()

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_text.test_1")
    state_2 = opp.states.get("input_text.test_2")
    state_3 = opp.states.get("input_text.test_3")

    assert state_1 is None
    assert state_2 is not None
    assert state_3 is not None
    assert state_2.attributes[ATTR_MIN] == 12
    assert state_3.attributes[ATTR_MAX] == 21


async def test_load_from_storage.opp, storage_setup):
    """Test set up from storage."""
    assert await storage_setup()
    state = opp.states.get(f"{DOMAIN}.from_storage")
    assert state.state == "loaded from storage"
    assert state.attributes.get(ATTR_EDITABLE)
    assert state.attributes[ATTR_MAX] == TEST_VAL_MAX
    assert state.attributes[ATTR_MIN] == TEST_VAL_MIN


async def test_editable_state_attribute.opp, storage_setup):
    """Test editable attribute."""
    assert await storage_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    "initial": "yaml initial value",
                    ATTR_MODE: MODE_TEXT,
                    ATTR_MAX: 33,
                    ATTR_MIN: 3,
                    ATTR_NAME: "yaml friendly name",
                }
            }
        }
    )

    state = opp.states.get(f"{DOMAIN}.from_storage")
    assert state.state == "loaded from storage"
    assert state.attributes.get(ATTR_EDITABLE)
    assert state.attributes[ATTR_MAX] == TEST_VAL_MAX
    assert state.attributes[ATTR_MIN] == TEST_VAL_MIN

    state = opp.states.get(f"{DOMAIN}.from_yaml")
    assert state.state == "yaml initial value"
    assert not state.attributes[ATTR_EDITABLE]
    assert state.attributes[ATTR_MAX] == 33
    assert state.attributes[ATTR_MIN] == 3


async def test_ws_list.opp,.opp_ws_client, storage_setup):
    """Test listing via WS."""
    assert await storage_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    "initial": "yaml initial value",
                    ATTR_MODE: MODE_TEXT,
                    ATTR_MAX: 33,
                    ATTR_MIN: 3,
                    ATTR_NAME: "yaml friendly name",
                }
            }
        }
    )

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


async def test_update.opp,.opp_ws_client, storage_setup):
    """Test updating min/max updates the state."""

    assert await storage_setup()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state.attributes[ATTR_FRIENDLY_NAME] == "from storage"
    assert state.attributes[ATTR_MODE] == MODE_TEXT
    assert state.state == "loaded from storage"
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await.opp_ws_client.opp)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            ATTR_NAME: "even newer name",
            CONF_INITIAL: "newer option",
            ATTR_MIN: 6,
            ATTR_MODE: "password",
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state.state == "loaded from storage"
    assert state.attributes[ATTR_FRIENDLY_NAME] == "even newer name"
    assert state.attributes[ATTR_MODE] == "password"
    assert state.attributes[ATTR_MIN] == 6
    assert state.attributes[ATTR_MAX] == TEST_VAL_MAX


async def test_ws_create.opp,.opp_ws_client, storage_setup):
    """Test create WS."""
    assert await storage_setup(items=[])

    input_id = "new_input"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None

    client = await.opp_ws_client.opp)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            "name": "New Input",
            "initial": "even newer option",
            ATTR_MAX: 44,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state.state == "even newer option"
    assert state.attributes[ATTR_FRIENDLY_NAME] == "New Input"
    assert state.attributes[ATTR_EDITABLE]
    assert state.attributes[ATTR_MAX] == 44
    assert state.attributes[ATTR_MIN] == 0


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
        await opp.async_block_till_done()

    assert count_start == len.opp.states.async_entity_ids())
