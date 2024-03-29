"""Tests for Search integration."""
from openpeerpower.components import search
from openpeerpower.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401


async def test_search(opp):
    """Test that search works."""
    area_reg = ar.async_get(opp)
    device_reg = dr.async_get(opp)
    entity_reg = er.async_get(opp)

    living_room_area = area_reg.async_create("Living Room")

    # Light strip with 2 lights.
    wled_config_entry = MockConfigEntry(domain="wled")
    wled_config_entry.add_to_opp(opp)

    wled_device = device_reg.async_get_or_create(
        config_entry_id=wled_config_entry.entry_id,
        name="Light Strip",
        identifiers=({"wled", "wled-1"}),
    )

    device_reg.async_update_device(wled_device.id, area_id=living_room_area.id)

    wled_segment_1_entity = entity_reg.async_get_or_create(
        "light",
        "wled",
        "wled-1-seg-1",
        suggested_object_id="wled segment 1",
        config_entry=wled_config_entry,
        device_id=wled_device.id,
    )
    wled_segment_2_entity = entity_reg.async_get_or_create(
        "light",
        "wled",
        "wled-1-seg-2",
        suggested_object_id="wled segment 2",
        config_entry=wled_config_entry,
        device_id=wled_device.id,
    )

    # Non related info.
    kitchen_area = area_reg.async_create("Kitchen")

    hue_config_entry = MockConfigEntry(domain="hue")
    hue_config_entry.add_to_opp(opp)

    hue_device = device_reg.async_get_or_create(
        config_entry_id=hue_config_entry.entry_id,
        name="Light Strip",
        identifiers=({"hue", "hue-1"}),
    )

    device_reg.async_update_device(hue_device.id, area_id=kitchen_area.id)

    hue_segment_1_entity = entity_reg.async_get_or_create(
        "light",
        "hue",
        "hue-1-seg-1",
        suggested_object_id="hue segment 1",
        config_entry=hue_config_entry,
        device_id=hue_device.id,
    )
    hue_segment_2_entity = entity_reg.async_get_or_create(
        "light",
        "hue",
        "hue-1-seg-2",
        suggested_object_id="hue segment 2",
        config_entry=hue_config_entry,
        device_id=hue_device.id,
    )

    await async_setup_component(
        opp,
        "group",
        {
            "group": {
                "wled": {
                    "name": "wled",
                    "entities": [
                        wled_segment_1_entity.entity_id,
                        wled_segment_2_entity.entity_id,
                    ],
                },
                "hue": {
                    "name": "hue",
                    "entities": [
                        hue_segment_1_entity.entity_id,
                        hue_segment_2_entity.entity_id,
                    ],
                },
                "wled_hue": {
                    "name": "wled and hue",
                    "entities": [
                        wled_segment_1_entity.entity_id,
                        wled_segment_2_entity.entity_id,
                        hue_segment_1_entity.entity_id,
                        hue_segment_2_entity.entity_id,
                    ],
                },
            }
        },
    )

    await async_setup_component(
        opp,
        "scene",
        {
            "scene": [
                {
                    "name": "scene_wled_seg_1",
                    "entities": {wled_segment_1_entity.entity_id: "on"},
                },
                {
                    "name": "scene_hue_seg_1",
                    "entities": {hue_segment_1_entity.entity_id: "on"},
                },
                {
                    "name": "scene_wled_hue",
                    "entities": {
                        wled_segment_1_entity.entity_id: "on",
                        wled_segment_2_entity.entity_id: "on",
                        hue_segment_1_entity.entity_id: "on",
                        hue_segment_2_entity.entity_id: "on",
                    },
                },
            ]
        },
    )

    await async_setup_component(
        opp,
        "script",
        {
            "script": {
                "wled": {
                    "sequence": [
                        {
                            "service": "test.script",
                            "data": {"entity_id": wled_segment_1_entity.entity_id},
                        },
                    ]
                },
                "hue": {
                    "sequence": [
                        {
                            "service": "test.script",
                            "data": {"entity_id": hue_segment_1_entity.entity_id},
                        },
                    ]
                },
            }
        },
    )

    assert await async_setup_component(
        opp,
        "automation",
        {
            "automation": [
                {
                    "alias": "wled_entity",
                    "trigger": {"platform": "template", "value_template": "true"},
                    "action": [
                        {
                            "service": "test.script",
                            "data": {"entity_id": wled_segment_1_entity.entity_id},
                        },
                    ],
                },
                {
                    "alias": "wled_device",
                    "trigger": {"platform": "template", "value_template": "true"},
                    "action": [
                        {
                            "domain": "light",
                            "device_id": wled_device.id,
                            "entity_id": wled_segment_1_entity.entity_id,
                            "type": "turn_on",
                        },
                    ],
                },
            ]
        },
    )

    # Ensure automations set up correctly.
    assert opp.states.get("automation.wled_entity") is not None
    assert opp.states.get("automation.wled_device") is not None

    # Explore the graph from every node and make sure we find the same results
    expected = {
        "config_entry": {wled_config_entry.entry_id},
        "area": {living_room_area.id},
        "device": {wled_device.id},
        "entity": {wled_segment_1_entity.entity_id, wled_segment_2_entity.entity_id},
        "scene": {"scene.scene_wled_seg_1", "scene.scene_wled_hue"},
        "group": {"group.wled", "group.wled_hue"},
        "script": {"script.wled"},
        "automation": {"automation.wled_entity", "automation.wled_device"},
    }

    for search_type, search_id in (
        ("config_entry", wled_config_entry.entry_id),
        ("area", living_room_area.id),
        ("device", wled_device.id),
        ("entity", wled_segment_1_entity.entity_id),
        ("entity", wled_segment_2_entity.entity_id),
        ("scene", "scene.scene_wled_seg_1"),
        ("group", "group.wled"),
        ("script", "script.wled"),
        ("automation", "automation.wled_entity"),
        ("automation", "automation.wled_device"),
    ):
        searcher = search.Searcher(opp, device_reg, entity_reg)
        results = searcher.async_search(search_type, search_id)
        # Add the item we searched for, it's omitted from results
        results.setdefault(search_type, set()).add(search_id)

        assert (
            results == expected
        ), f"Results for {search_type}/{search_id} do not match up"

    # For combined things, needs to return everything.
    expected_combined = {
        "config_entry": {wled_config_entry.entry_id, hue_config_entry.entry_id},
        "area": {living_room_area.id, kitchen_area.id},
        "device": {wled_device.id, hue_device.id},
        "entity": {
            wled_segment_1_entity.entity_id,
            wled_segment_2_entity.entity_id,
            hue_segment_1_entity.entity_id,
            hue_segment_2_entity.entity_id,
        },
        "scene": {
            "scene.scene_wled_seg_1",
            "scene.scene_hue_seg_1",
            "scene.scene_wled_hue",
        },
        "group": {"group.wled", "group.hue", "group.wled_hue"},
        "script": {"script.wled", "script.hue"},
        "automation": {"automation.wled_entity", "automation.wled_device"},
    }
    for search_type, search_id in (
        ("scene", "scene.scene_wled_hue"),
        ("group", "group.wled_hue"),
    ):
        searcher = search.Searcher(opp, device_reg, entity_reg)
        results = searcher.async_search(search_type, search_id)
        # Add the item we searched for, it's omitted from results
        results.setdefault(search_type, set()).add(search_id)
        assert (
            results == expected_combined
        ), f"Results for {search_type}/{search_id} do not match up"

    for search_type, search_id in (
        ("entity", "automation.non_existing"),
        ("entity", "scene.non_existing"),
        ("entity", "group.non_existing"),
        ("entity", "script.non_existing"),
        ("entity", "light.non_existing"),
        ("area", "non_existing"),
        ("config_entry", "non_existing"),
        ("device", "non_existing"),
        ("group", "group.non_existing"),
        ("scene", "scene.non_existing"),
        ("script", "script.non_existing"),
        ("automation", "automation.non_existing"),
    ):
        searcher = search.Searcher(opp, device_reg, entity_reg)
        assert searcher.async_search(search_type, search_id) == {}


async def test_area_lookup(opp):
    """Test area based lookup."""
    area_reg = ar.async_get(opp)
    device_reg = dr.async_get(opp)
    entity_reg = er.async_get(opp)

    living_room_area = area_reg.async_create("Living Room")

    await async_setup_component(
        opp,
        "script",
        {
            "script": {
                "wled": {
                    "sequence": [
                        {
                            "service": "light.turn_on",
                            "target": {"area_id": living_room_area.id},
                        },
                    ]
                },
            }
        },
    )

    assert await async_setup_component(
        opp,
        "automation",
        {
            "automation": [
                {
                    "alias": "area_turn_on",
                    "trigger": {"platform": "template", "value_template": "true"},
                    "action": [
                        {
                            "service": "light.turn_on",
                            "data": {
                                "area_id": living_room_area.id,
                            },
                        },
                    ],
                },
            ]
        },
    )

    searcher = search.Searcher(opp, device_reg, entity_reg)
    assert searcher.async_search("area", living_room_area.id) == {
        "script": {"script.wled"},
        "automation": {"automation.area_turn_on"},
    }

    searcher = search.Searcher(opp, device_reg, entity_reg)
    assert searcher.async_search("automation", "automation.area_turn_on") == {
        "area": {living_room_area.id},
    }


async def test_ws_api(opp, opp_ws_client):
    """Test WS API."""
    assert await async_setup_component(opp, "search", {})

    area_reg = ar.async_get(opp)
    device_reg = dr.async_get(opp)

    kitchen_area = area_reg.async_create("Kitchen")

    hue_config_entry = MockConfigEntry(domain="hue")
    hue_config_entry.add_to_opp(opp)

    hue_device = device_reg.async_get_or_create(
        config_entry_id=hue_config_entry.entry_id,
        name="Light Strip",
        identifiers=({"hue", "hue-1"}),
    )

    device_reg.async_update_device(hue_device.id, area_id=kitchen_area.id)

    client = await opp_ws_client(opp)

    await client.send_json(
        {
            "id": 1,
            "type": "search/related",
            "item_type": "device",
            "item_id": hue_device.id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "config_entry": [hue_config_entry.entry_id],
        "area": [kitchen_area.id],
    }
