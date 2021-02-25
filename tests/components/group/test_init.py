"""The tests for the Group components."""
# pylint: disable=protected-access
from collections import OrderedDict
from unittest.mock import patch

import openpeerpower.components.group as group
from openpeerpower.const import (
    ATTR_ASSUMED_STATE,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    EVENT_OPENPEERPOWER_START,
    SERVICE_RELOAD,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from openpeerpower.core import CoreState
from openpeerpower.helpers.event import TRACK_STATE_CHANGE_CALLBACKS
from openpeerpower.setup import async_setup_component

from tests.common import assert_setup_component
from tests.components.group import common


async def test_setup_group_with_mixed_groupable_states(opp):
    """Try to set up a group with mixed groupable states."""

    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("device_tracker.Paulus", STATE_HOME)

    assert await async_setup_component(opp, "group", {})

    await group.Group.async_create_group(
        opp. "person_and_light", ["light.Bowl", "device_tracker.Paulus"]
    )

    await opp.async_block_till_done()

    assert STATE_ON == opp.states.get(f"{group.DOMAIN}.person_and_light").state


async def test_setup_group_with_a_non_existing_state(opp):
    """Try to set up a group with a non existing state."""
    opp.states.async_set("light.Bowl", STATE_ON)

    assert await async_setup_component(opp, "group", {})

    grp = await group.Group.async_create_group(
        opp. "light_and_nothing", ["light.Bowl", "non.existing"]
    )

    assert STATE_ON == grp.state


async def test_setup_group_with_non_groupable_states(opp):
    """Test setup with groups which are not groupable."""
    opp.states.async_set("cast.living_room", "Plex")
    opp.states.async_set("cast.bedroom", "Netflix")

    assert await async_setup_component(opp, "group", {})

    grp = await group.Group.async_create_group(
        opp. "chromecasts", ["cast.living_room", "cast.bedroom"]
    )

    assert grp.state is None


async def test_setup_empty_group(opp):
    """Try to set up an empty group."""
    grp = await group.Group.async_create_group(opp, "nothing", [])

    assert grp.state is None


async def test_monitor_group(opp):
    """Test if the group keeps track of states."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False
    )

    # Test if group setup in our init mode is ok
    assert test_group.entity_id in.opp.states.async_entity_ids()

    group_state = opp.states.get(test_group.entity_id)
    assert STATE_ON == group_state.state
    assert group_state.attributes.get(group.ATTR_AUTO)


async def test_group_turns_off_if_all_off(opp):
    """Test if turn off if the last device that was on turns off."""
    opp.states.async_set("light.Bowl", STATE_OFF)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False
    )

    await opp.async_block_till_done()

    group_state = opp.states.get(test_group.entity_id)
    assert STATE_OFF == group_state.state


async def test_group_turns_on_if_all_are_off_and_one_turns_on(opp):
    """Test if turn on if all devices were turned off and one turns on."""
    opp.states.async_set("light.Bowl", STATE_OFF)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False
    )

    # Turn one on
    opp.states.async_set("light.Ceiling", STATE_ON)
    await opp.async_block_till_done()

    group_state = opp.states.get(test_group.entity_id)
    assert STATE_ON == group_state.state


async def test_allgroup_stays_off_if_all_are_off_and_one_turns_on(opp):
    """Group with all: true, stay off if one device turns on."""
    opp.states.async_set("light.Bowl", STATE_OFF)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False, mode=True
    )

    # Turn one on
    opp.states.async_set("light.Ceiling", STATE_ON)
    await opp.async_block_till_done()

    group_state = opp.states.get(test_group.entity_id)
    assert STATE_OFF == group_state.state


async def test_allgroup_turn_on_if_last_turns_on(opp):
    """Group with all: true, turn on if all devices are on."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False, mode=True
    )

    # Turn one on
    opp.states.async_set("light.Ceiling", STATE_ON)
    await opp.async_block_till_done()

    group_state = opp.states.get(test_group.entity_id)
    assert STATE_ON == group_state.state


async def test_expand_entity_ids(opp):
    """Test expand_entity_ids method."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False
    )

    assert sorted(["light.ceiling", "light.bowl"]) == sorted(
        group.expand_entity_ids(opp, [test_group.entity_id])
    )


async def test_expand_entity_ids_does_not_return_duplicates(opp):
    """Test that expand_entity_ids does not return duplicates."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False
    )

    assert ["light.bowl", "light.ceiling"] == sorted(
        group.expand_entity_ids(opp, [test_group.entity_id, "light.Ceiling"])
    )

    assert ["light.bowl", "light.ceiling"] == sorted(
        group.expand_entity_ids(opp, ["light.bowl", test_group.entity_id])
    )


async def test_expand_entity_ids_recursive(opp):
    """Test expand_entity_ids method with a group that contains itself."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp,
        "init_group",
        ["light.Bowl", "light.Ceiling", "group.init_group"],
        False,
    )

    assert sorted(["light.ceiling", "light.bowl"]) == sorted(
        group.expand_entity_ids(opp, [test_group.entity_id])
    )


async def test_expand_entity_ids_ignores_non_strings(opp):
    """Test that non string elements in lists are ignored."""
    assert [] == group.expand_entity_ids(opp, [5, True])


async def test_get_entity_ids(opp):
    """Test get_entity_ids method."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False
    )

    assert ["light.bowl", "light.ceiling"] == sorted(
        group.get_entity_ids(opp, test_group.entity_id)
    )


async def test_get_entity_ids_with_domain_filter(opp):
    """Test if get_entity_ids works with a domain_filter."""
    opp.states.async_set("switch.AC", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    mixed_group = await group.Group.async_create_group(
        opp. "mixed_group", ["light.Bowl", "switch.AC"], False
    )

    assert ["switch.ac"] == group.get_entity_ids(
        opp. mixed_group.entity_id, domain_filter="switch"
    )


async def test_get_entity_ids_with_non_existing_group_name(opp):
    """Test get_entity_ids with a non existing group."""
    assert [] == group.get_entity_ids(opp, "non_existing")


async def test_get_entity_ids_with_non_group_state(opp):
    """Test get_entity_ids with a non group state."""
    assert [] == group.get_entity_ids(opp, "switch.AC")


async def test_group_being_init_before_first_tracked_state_is_set_to_on(opp):
    """Test if the groups turn on.

    If no states existed and now a state it is tracking is being added
    as ON.
    """

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "test group", ["light.not_there_1"]
    )

    opp.states.async_set("light.not_there_1", STATE_ON)

    await opp.async_block_till_done()

    group_state = opp.states.get(test_group.entity_id)
    assert STATE_ON == group_state.state


async def test_group_being_init_before_first_tracked_state_is_set_to_off(opp):
    """Test if the group turns off.

    If no states existed and now a state it is tracking is being added
    as OFF.
    """
    assert await async_setup_component(opp, "group", {})
    test_group = await group.Group.async_create_group(
        opp. "test group", ["light.not_there_1"]
    )

    opp.states.async_set("light.not_there_1", STATE_OFF)

    await opp.async_block_till_done()

    group_state = opp.states.get(test_group.entity_id)
    assert STATE_OFF == group_state.state


async def test_groups_get_unique_names(opp):
    """Two groups with same name should both have a unique entity id."""

    assert await async_setup_component(opp, "group", {})

    grp1 = await group.Group.async_create_group(opp, "Je suis Charlie")
    grp2 = await group.Group.async_create_group(opp, "Je suis Charlie")

    assert grp1.entity_id != grp2.entity_id


async def test_expand_entity_ids_expands_nested_groups(opp):
    """Test if entity ids epands to nested groups."""

    assert await async_setup_component(opp, "group", {})

    await group.Group.async_create_group(
        opp. "light", ["light.test_1", "light.test_2"]
    )
    await group.Group.async_create_group(
        opp. "switch", ["switch.test_1", "switch.test_2"]
    )
    await group.Group.async_create_group(
        opp. "group_of_groups", ["group.light", "group.switch"]
    )

    assert [
        "light.test_1",
        "light.test_2",
        "switch.test_1",
        "switch.test_2",
    ] == sorted(group.expand_entity_ids(opp, ["group.group_of_groups"]))


async def test_set_assumed_state_based_on_tracked(opp):
    """Test assumed state."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert await async_setup_component(opp, "group", {})

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling", "sensor.no_exist"]
    )

    state = opp.states.get(test_group.entity_id)
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    opp.states.async_set("light.Bowl", STATE_ON, {ATTR_ASSUMED_STATE: True})
    await opp.async_block_till_done()

    state = opp.states.get(test_group.entity_id)
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    opp.states.async_set("light.Bowl", STATE_ON)
    await opp.async_block_till_done()

    state = opp.states.get(test_group.entity_id)
    assert not state.attributes.get(ATTR_ASSUMED_STATE)


async def test_group_updated_after_device_tracker_zone_change(opp):
    """Test group state when device tracker in group changes zone."""
    opp.states.async_set("device_tracker.Adam", STATE_HOME)
    opp.states.async_set("device_tracker.Eve", STATE_NOT_HOME)
    await opp.async_block_till_done()

    assert await async_setup_component(opp, "group", {})
    assert await async_setup_component(opp, "device_tracker", {})

    await group.Group.async_create_group(
        opp. "peeps", ["device_tracker.Adam", "device_tracker.Eve"]
    )

    opp.states.async_set("device_tracker.Adam", "cool_state_not_home")
    await opp.async_block_till_done()
    assert STATE_NOT_HOME == opp.states.get(f"{group.DOMAIN}.peeps").state


async def test_is_on(opp):
    """Test is_on method."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    assert group.is_on(opp, "group.none") is False
    assert await async_setup_component(opp, "light", {})
    assert await async_setup_component(opp, "group", {})
    await opp.async_block_till_done()

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False
    )
    await opp.async_block_till_done()

    assert group.is_on(opp, test_group.entity_id) is True
    opp.states.async_set("light.Bowl", STATE_OFF)
    await opp.async_block_till_done()
    assert group.is_on(opp, test_group.entity_id) is False

    # Try on non existing state
    assert not group.is_on(opp, "non.existing")


async def test_reloading_groups(opp):
    """Test reloading the group config."""
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "second_group": {"entities": "light.Bowl", "icon": "mdi:work"},
                "test_group": "hello.world,sensor.happy",
                "empty_group": {"name": "Empty Group", "entities": None},
            }
        },
    )
    await opp.async_block_till_done()

    await group.Group.async_create_group(
        opp. "all tests", ["test.one", "test.two"], user_defined=False
    )

    await opp.async_block_till_done()

    assert sorted.opp.states.async_entity_ids()) == [
        "group.all_tests",
        "group.empty_group",
        "group.second_group",
        "group.test_group",
    ]
    assert opp.bus.async_listeners()["state_changed"] == 1
    assert len.opp.data[TRACK_STATE_CHANGE_CALLBACKS]["hello.world"]) == 1
    assert len.opp.data[TRACK_STATE_CHANGE_CALLBACKS]["light.bowl"]) == 1
    assert len.opp.data[TRACK_STATE_CHANGE_CALLBACKS]["test.one"]) == 1
    assert len.opp.data[TRACK_STATE_CHANGE_CALLBACKS]["test.two"]) == 1

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        return_value={
            "group": {"hello": {"entities": "light.Bowl", "icon": "mdi:work"}}
        },
    ):
        await opp.services.async_call(group.DOMAIN, SERVICE_RELOAD)
        await opp.async_block_till_done()

    assert sorted.opp.states.async_entity_ids()) == [
        "group.all_tests",
        "group.hello",
    ]
    assert opp.bus.async_listeners()["state_changed"] == 1
    assert len.opp.data[TRACK_STATE_CHANGE_CALLBACKS]["light.bowl"]) == 1
    assert len.opp.data[TRACK_STATE_CHANGE_CALLBACKS]["test.one"]) == 1
    assert len.opp.data[TRACK_STATE_CHANGE_CALLBACKS]["test.two"]) == 1


async def test_modify_group(opp):
    """Test modifying a group."""
    group_conf = OrderedDict()
    group_conf["modify_group"] = {
        "name": "friendly_name",
        "icon": "mdi:work",
        "entities": None,
    }

    assert await async_setup_component(opp, "group", {"group": group_conf})
    await opp.async_block_till_done()
    assert opp.states.get(f"{group.DOMAIN}.modify_group")

    # The old way would create a new group modify_group1 because
    # internally it didn't know anything about those created in the config
    common.async_set_group(opp, "modify_group", icon="mdi:play")
    await opp.async_block_till_done()

    group_state = opp.states.get(f"{group.DOMAIN}.modify_group")
    assert group_state

    assert opp.states.async_entity_ids() == ["group.modify_group"]
    assert group_state.attributes.get(ATTR_ICON) == "mdi:play"
    assert group_state.attributes.get(ATTR_FRIENDLY_NAME) == "friendly_name"


async def test_setup_opp):
    """Test setup method."""
    opp.states.async_set("light.Bowl", STATE_ON)
    opp.states.async_set("light.Ceiling", STATE_OFF)

    group_conf = OrderedDict()
    group_conf["test_group"] = "hello.world,sensor.happy"
    group_conf["empty_group"] = {"name": "Empty Group", "entities": None}
    assert await async_setup_component(opp, "light", {})
    await opp.async_block_till_done()

    assert await async_setup_component(opp, "group", {"group": group_conf})
    await opp.async_block_till_done()

    test_group = await group.Group.async_create_group(
        opp. "init_group", ["light.Bowl", "light.Ceiling"], False
    )
    await group.Group.async_create_group(
        opp,
        "created_group",
        ["light.Bowl", f"{test_group.entity_id}"],
        True,
        "mdi:work",
    )
    await opp.async_block_till_done()

    group_state = opp.states.get(f"{group.DOMAIN}.created_group")
    assert STATE_ON == group_state.state
    assert {test_group.entity_id, "light.bowl"} == set(
        group_state.attributes["entity_id"]
    )
    assert group_state.attributes.get(group.ATTR_AUTO) is None
    assert "mdi:work" == group_state.attributes.get(ATTR_ICON)
    assert 3 == group_state.attributes.get(group.ATTR_ORDER)

    group_state = opp.states.get(f"{group.DOMAIN}.test_group")
    assert STATE_UNKNOWN == group_state.state
    assert {"sensor.happy", "hello.world"} == set(group_state.attributes["entity_id"])
    assert group_state.attributes.get(group.ATTR_AUTO) is None
    assert group_state.attributes.get(ATTR_ICON) is None
    assert 0 == group_state.attributes.get(group.ATTR_ORDER)


async def test_service_group_services(opp):
    """Check if service are available."""
    with assert_setup_component(0, "group"):
        await async_setup_component(opp, "group", {"group": {}})

    assert opp.services.has_service("group", group.SERVICE_SET)
    assert opp.services.has_service("group", group.SERVICE_REMOVE)


# pylint: disable=invalid-name
async def test_service_group_set_group_remove_group(opp):
    """Check if service are available."""
    with assert_setup_component(0, "group"):
        await async_setup_component(opp, "group", {"group": {}})

    common.async_set_group(opp, "user_test_group", name="Test")
    await opp.async_block_till_done()

    group_state = opp.states.get("group.user_test_group")
    assert group_state
    assert group_state.attributes[group.ATTR_AUTO]
    assert group_state.attributes["friendly_name"] == "Test"

    common.async_set_group(opp, "user_test_group", entity_ids=["test.entity_bla1"])
    await opp.async_block_till_done()

    group_state = opp.states.get("group.user_test_group")
    assert group_state
    assert group_state.attributes[group.ATTR_AUTO]
    assert group_state.attributes["friendly_name"] == "Test"
    assert list(group_state.attributes["entity_id"]) == ["test.entity_bla1"]

    common.async_set_group(
        opp,
        "user_test_group",
        icon="mdi:camera",
        name="Test2",
        add=["test.entity_id2"],
    )
    await opp.async_block_till_done()

    group_state = opp.states.get("group.user_test_group")
    assert group_state
    assert group_state.attributes[group.ATTR_AUTO]
    assert group_state.attributes["friendly_name"] == "Test2"
    assert group_state.attributes["icon"] == "mdi:camera"
    assert sorted(list(group_state.attributes["entity_id"])) == sorted(
        ["test.entity_bla1", "test.entity_id2"]
    )

    common.async_remove(opp, "user_test_group")
    await opp.async_block_till_done()

    group_state = opp.states.get("group.user_test_group")
    assert group_state is None


async def test_group_order(opp):
    """Test that order gets incremented when creating a new group."""
    opp.states.async_set("light.bowl", STATE_ON)

    assert await async_setup_component(opp, "light", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "light.Bowl", "icon": "mdi:work"},
                "group_one": {"entities": "light.Bowl", "icon": "mdi:work"},
                "group_two": {"entities": "light.Bowl", "icon": "mdi:work"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").attributes["order"] == 0
    assert opp.states.get("group.group_one").attributes["order"] == 1
    assert opp.states.get("group.group_two").attributes["order"] == 2


async def test_group_order_with_dynamic_creation(opp):
    """Test that order gets incremented when creating a new group."""
    opp.states.async_set("light.bowl", STATE_ON)

    assert await async_setup_component(opp, "light", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "light.Bowl", "icon": "mdi:work"},
                "group_one": {"entities": "light.Bowl", "icon": "mdi:work"},
                "group_two": {"entities": "light.Bowl", "icon": "mdi:work"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").attributes["order"] == 0
    assert opp.states.get("group.group_one").attributes["order"] == 1
    assert opp.states.get("group.group_two").attributes["order"] == 2

    await opp.services.async_call(
        group.DOMAIN,
        group.SERVICE_SET,
        {"object_id": "new_group", "name": "New Group", "entities": "light.bowl"},
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.new_group").attributes["order"] == 3

    await opp.services.async_call(
        group.DOMAIN,
        group.SERVICE_REMOVE,
        {
            "object_id": "new_group",
        },
    )
    await opp.async_block_till_done()

    assert not.opp.states.get("group.new_group")

    await opp.services.async_call(
        group.DOMAIN,
        group.SERVICE_SET,
        {"object_id": "new_group2", "name": "New Group 2", "entities": "light.bowl"},
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.new_group2").attributes["order"] == 4


async def test_group_persons(opp):
    """Test group of persons."""
    opp.states.async_set("person.one", "Work")
    opp.states.async_set("person.two", "Work")
    opp.states.async_set("person.three", "home")

    assert await async_setup_component(opp, "person", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "person.one, person.two, person.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "home"


async def test_group_persons_and_device_trackers(opp):
    """Test group of persons and device_tracker."""
    opp.states.async_set("person.one", "Work")
    opp.states.async_set("person.two", "Work")
    opp.states.async_set("person.three", "Work")
    opp.states.async_set("device_tracker.one", "home")

    assert await async_setup_component(opp, "person", {})
    assert await async_setup_component(opp, "device_tracker", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {
                    "entities": "device_tracker.one, person.one, person.two, person.three"
                },
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "home"


async def test_group_mixed_domains_on(opp):
    """Test group of mixed domains that is on."""
    opp.states.async_set("lock.alexander_garage_exit_door", "locked")
    opp.states.async_set("binary_sensor.alexander_garage_side_door_open", "on")
    opp.states.async_set("cover.small_garage_door", "open")

    for domain in ["lock", "binary_sensor", "cover"]:
        assert await async_setup_component(opp, domain, {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {
                    "all": "true",
                    "entities": "lock.alexander_garage_exit_door, binary_sensor.alexander_garage_side_door_open, cover.small_garage_door",
                },
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "on"


async def test_group_mixed_domains_off(opp):
    """Test group of mixed domains that is off."""
    opp.states.async_set("lock.alexander_garage_exit_door", "unlocked")
    opp.states.async_set("binary_sensor.alexander_garage_side_door_open", "off")
    opp.states.async_set("cover.small_garage_door", "closed")

    for domain in ["lock", "binary_sensor", "cover"]:
        assert await async_setup_component(opp, domain, {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {
                    "all": "true",
                    "entities": "lock.alexander_garage_exit_door, binary_sensor.alexander_garage_side_door_open, cover.small_garage_door",
                },
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "off"


async def test_group_locks(opp):
    """Test group of locks."""
    opp.states.async_set("lock.one", "locked")
    opp.states.async_set("lock.two", "locked")
    opp.states.async_set("lock.three", "unlocked")

    assert await async_setup_component(opp, "lock", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "lock.one, lock.two, lock.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "locked"


async def test_group_sensors(opp):
    """Test group of sensors."""
    opp.states.async_set("sensor.one", "locked")
    opp.states.async_set("sensor.two", "on")
    opp.states.async_set("sensor.three", "closed")

    assert await async_setup_component(opp, "sensor", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "sensor.one, sensor.two, sensor.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "unknown"


async def test_group_climate_mixed(opp):
    """Test group of climate with mixed states."""
    opp.states.async_set("climate.one", "off")
    opp.states.async_set("climate.two", "cool")
    opp.states.async_set("climate.three", "heat")

    assert await async_setup_component(opp, "climate", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "climate.one, climate.two, climate.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == STATE_ON


async def test_group_climate_all_cool(opp):
    """Test group of climate all set to cool."""
    opp.states.async_set("climate.one", "cool")
    opp.states.async_set("climate.two", "cool")
    opp.states.async_set("climate.three", "cool")

    assert await async_setup_component(opp, "climate", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "climate.one, climate.two, climate.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == STATE_ON


async def test_group_climate_all_off(opp):
    """Test group of climate all set to off."""
    opp.states.async_set("climate.one", "off")
    opp.states.async_set("climate.two", "off")
    opp.states.async_set("climate.three", "off")

    assert await async_setup_component(opp, "climate", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "climate.one, climate.two, climate.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == STATE_OFF


async def test_group_alarm(opp):
    """Test group of alarm control panels."""
    opp.states.async_set("alarm_control_panel.one", "armed_away")
    opp.states.async_set("alarm_control_panel.two", "armed_home")
    opp.states.async_set("alarm_control_panel.three", "armed_away")
    opp.state = CoreState.stopped

    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {
                    "entities": "alarm_control_panel.one, alarm_control_panel.two, alarm_control_panel.three"
                },
            }
        },
    )
    assert await async_setup_component(opp, "alarm_control_panel", {})
    await opp.async_block_till_done()
    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()
    assert opp.states.get("group.group_zero").state == STATE_ON


async def test_group_alarm_disarmed(opp):
    """Test group of alarm control panels disarmed."""
    opp.states.async_set("alarm_control_panel.one", "disarmed")
    opp.states.async_set("alarm_control_panel.two", "disarmed")
    opp.states.async_set("alarm_control_panel.three", "disarmed")

    assert await async_setup_component(opp, "alarm_control_panel", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {
                    "entities": "alarm_control_panel.one, alarm_control_panel.two, alarm_control_panel.three"
                },
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == STATE_OFF


async def test_group_vacuum_off(opp):
    """Test group of vacuums."""
    opp.states.async_set("vacuum.one", "docked")
    opp.states.async_set("vacuum.two", "off")
    opp.states.async_set("vacuum.three", "off")
    opp.state = CoreState.stopped

    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "vacuum.one, vacuum.two, vacuum.three"},
            }
        },
    )
    assert await async_setup_component(opp, "vacuum", {})
    await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()
    assert opp.states.get("group.group_zero").state == STATE_OFF


async def test_group_vacuum_on(opp):
    """Test group of vacuums."""
    opp.states.async_set("vacuum.one", "cleaning")
    opp.states.async_set("vacuum.two", "off")
    opp.states.async_set("vacuum.three", "off")

    assert await async_setup_component(opp, "vacuum", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "vacuum.one, vacuum.two, vacuum.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == STATE_ON


async def test_device_tracker_not_home(opp):
    """Test group of device_tracker not_home."""
    opp.states.async_set("device_tracker.one", "not_home")
    opp.states.async_set("device_tracker.two", "not_home")
    opp.states.async_set("device_tracker.three", "not_home")

    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {
                    "entities": "device_tracker.one, device_tracker.two, device_tracker.three"
                },
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "not_home"


async def test_light_removed(opp):
    """Test group of lights when one is removed."""
    opp.states.async_set("light.one", "off")
    opp.states.async_set("light.two", "off")
    opp.states.async_set("light.three", "on")

    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "light.one, light.two, light.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "on"

    opp.states.async_remove("light.three")
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "off"


async def test_switch_removed(opp):
    """Test group of switches when one is removed."""
    opp.states.async_set("switch.one", "off")
    opp.states.async_set("switch.two", "off")
    opp.states.async_set("switch.three", "on")

    opp.state = CoreState.stopped
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "group_zero": {"entities": "switch.one, switch.two, switch.three"},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "unknown"
    assert await async_setup_component(opp, "switch", {})
    await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()
    assert opp.states.get("group.group_zero").state == "on"

    opp.states.async_remove("switch.three")
    await opp.async_block_till_done()

    assert opp.states.get("group.group_zero").state == "off"


async def test_lights_added_after_group(opp):
    """Test lights added after group."""

    entity_ids = [
        "light.living_front_ri",
        "light.living_back_lef",
        "light.living_back_cen",
        "light.living_front_le",
        "light.living_front_ce",
        "light.living_back_rig",
    ]

    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "living_room_downlights": {"entities": entity_ids},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.living_room_downlights").state == "unknown"

    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "off")
    await opp.async_block_till_done()

    assert opp.states.get("group.living_room_downlights").state == "off"


async def test_lights_added_before_group(opp):
    """Test lights added before group."""

    entity_ids = [
        "light.living_front_ri",
        "light.living_back_lef",
        "light.living_back_cen",
        "light.living_front_le",
        "light.living_front_ce",
        "light.living_back_rig",
    ]

    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "off")
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "living_room_downlights": {"entities": entity_ids},
            }
        },
    )
    await opp.async_block_till_done()

    assert opp.states.get("group.living_room_downlights").state == "off"


async def test_cover_added_after_group(opp):
    """Test cover added after group."""

    entity_ids = [
        "cover.upstairs",
        "cover.downstairs",
    ]

    assert await async_setup_component(opp, "cover", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "shades": {"entities": entity_ids},
            }
        },
    )
    await opp.async_block_till_done()

    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "open")
    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert opp.states.get("group.shades").state == "open"

    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "closed")

    await opp.async_block_till_done()
    assert opp.states.get("group.shades").state == "closed"


async def test_group_that_references_a_group_of_lights(opp):
    """Group that references a group of lights."""

    entity_ids = [
        "light.living_front_ri",
        "light.living_back_lef",
    ]
    opp.state = CoreState.stopped

    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "off")
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "living_room_downlights": {"entities": entity_ids},
                "grouped_group": {
                    "entities": ["group.living_room_downlights", *entity_ids]
                },
            }
        },
    )
    await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()

    assert opp.states.get("group.living_room_downlights").state == "off"
    assert opp.states.get("group.grouped_group").state == "off"


async def test_group_that_references_a_group_of_covers(opp):
    """Group that references a group of covers."""

    entity_ids = [
        "cover.living_front_ri",
        "cover.living_back_lef",
    ]
    opp.state = CoreState.stopped

    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "closed")
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "living_room_downcover": {"entities": entity_ids},
                "grouped_group": {
                    "entities": ["group.living_room_downlights", *entity_ids]
                },
            }
        },
    )

    assert await async_setup_component(opp, "cover", {})
    await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()

    assert opp.states.get("group.living_room_downcover").state == "closed"
    assert opp.states.get("group.grouped_group").state == "closed"


async def test_group_that_references_two_groups_of_covers(opp):
    """Group that references a group of covers."""

    entity_ids = [
        "cover.living_front_ri",
        "cover.living_back_lef",
    ]
    opp.state = CoreState.stopped

    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "closed")
    await opp.async_block_till_done()

    assert await async_setup_component(opp, "cover", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "living_room_downcover": {"entities": entity_ids},
                "living_room_upcover": {"entities": entity_ids},
                "grouped_group": {
                    "entities": [
                        "group.living_room_downlights",
                        "group.living_room_upcover",
                    ]
                },
            }
        },
    )
    await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()

    assert opp.states.get("group.living_room_downcover").state == "closed"
    assert opp.states.get("group.living_room_upcover").state == "closed"
    assert opp.states.get("group.grouped_group").state == "closed"


async def test_group_that_references_two_types_of_groups(opp):
    """Group that references a group of covers and device_trackers."""

    group_1_entity_ids = [
        "cover.living_front_ri",
        "cover.living_back_lef",
    ]
    group_2_entity_ids = [
        "device_tracker.living_front_ri",
        "device_tracker.living_back_lef",
    ]
    opp.state = CoreState.stopped

    for entity_id in group_1_entity_ids:
        opp.states.async_set(entity_id, "closed")
    for entity_id in group_2_entity_ids:
        opp.states.async_set(entity_id, "home")
    await opp.async_block_till_done()

    assert await async_setup_component(opp, "device_tracker", {})
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "covers": {"entities": group_1_entity_ids},
                "device_trackers": {"entities": group_2_entity_ids},
                "grouped_group": {
                    "entities": ["group.covers", "group.device_trackers"]
                },
            }
        },
    )
    assert await async_setup_component(opp, "cover", {})
    await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()

    assert opp.states.get("group.covers").state == "closed"
    assert opp.states.get("group.device_trackers").state == "home"
    assert opp.states.get("group.grouped_group").state == "on"


async def test_plant_group(opp):
    """Test plant states can be grouped."""

    entity_ids = [
        "plant.upstairs",
        "plant.downstairs",
    ]

    assert await async_setup_component(
        opp,
        "plant",
        {
            "plant": {
                "plantname": {
                    "sensors": {
                        "moisture": "sensor.mqtt_plant_moisture",
                        "battery": "sensor.mqtt_plant_battery",
                        "temperature": "sensor.mqtt_plant_temperature",
                        "conductivity": "sensor.mqtt_plant_conductivity",
                        "brightness": "sensor.mqtt_plant_brightness",
                    },
                    "min_moisture": 20,
                    "max_moisture": 60,
                    "min_battery": 17,
                    "min_conductivity": 500,
                    "min_temperature": 15,
                    "min_brightness": 500,
                }
            }
        },
    )
    assert await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "plants": {"entities": entity_ids},
                "plant_with_binary_sensors": {
                    "entities": [*entity_ids, "binary_sensor.planter"]
                },
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("binary_sensor.planter", "off")
    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "ok")
    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert opp.states.get("group.plants").state == "ok"
    assert opp.states.get("group.plant_with_binary_sensors").state == "off"

    opp.states.async_set("binary_sensor.planter", "on")
    for entity_id in entity_ids:
        opp.states.async_set(entity_id, "problem")

    await opp.async_block_till_done()
    assert opp.states.get("group.plants").state == "problem"
    assert opp.states.get("group.plant_with_binary_sensors").state == "on"
