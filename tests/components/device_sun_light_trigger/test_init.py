"""The tests device sun light trigger component."""
# pylint: disable=protected-access
from datetime import datetime
from unittest.mock import patch

import pytest

from openpeerpower.components import (
    device_sun_light_trigger,
    device_tracker,
    group,
    light,
)
from openpeerpower.components.device_tracker.const import DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_PLATFORM,
    EVENT_OPENPEERPOWER_START,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.core import CoreState
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt as dt_util

from tests.common import async_fire_time_changed


@pytest.fixture
def scanner.opp):
    """Initialize components."""
    scanner = getattr.opp.components, "test.device_tracker").get_scanner(None, None)

    scanner.reset()
    scanner.come_home("DEV1")

    getattr.opp.components, "test.light").init()

    with patch(
        "openpeerpower.components.device_tracker.legacy.load_yaml_config_file",
        return_value={
            "device_1": {
                "mac": "DEV1",
                "name": "Unnamed Device",
                "picture": "http://example.com/dev1.jpg",
                "track": True,
                "vendor": None,
            },
            "device_2": {
                "mac": "DEV2",
                "name": "Unnamed Device",
                "picture": "http://example.com/dev2.jpg",
                "track": True,
                "vendor": None,
            },
        },
    ):
        assert opp.loop.run_until_complete(
            async_setup_component(
                opp,
                device_tracker.DOMAIN,
                {device_tracker.DOMAIN: {CONF_PLATFORM: "test"}},
            )
        )

    assert opp.loop.run_until_complete(
        async_setup_component(
            opp. light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
        )
    )

    return scanner


async def test_lights_on_when_sun_sets(opp, scanner):
    """Test lights go on when there is someone home and the sun sets."""
    test_time = datetime(2017, 4, 5, 1, 2, 3, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=test_time):
        assert await async_setup_component(
            opp. device_sun_light_trigger.DOMAIN, {device_sun_light_trigger.DOMAIN: {}}
        )

    await opp.services.async_call(
        light.DOMAIN,
        light.SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "test.light"},
        blocking=True,
    )

    test_time = test_time.replace(hour=3)
    with patch("openpeerpower.util.dt.utcnow", return_value=test_time):
        async_fire_time_changed(opp, test_time)
        await opp.async_block_till_done()

    assert all(
        opp.states.get(ent_id).state == STATE_ON
        for ent_id in.opp.states.async_entity_ids("light")
    )


async def test_lights_turn_off_when_everyone_leaves.opp):
    """Test lights turn off when everyone leaves the house."""
    assert await async_setup_component(
        opp. "light", {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await opp.services.async_call(
        light.DOMAIN,
        light.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "test.light"},
        blocking=True,
    )
    opp.states.async_set("device_tracker.bla", STATE_HOME)

    assert await async_setup_component(
        opp. device_sun_light_trigger.DOMAIN, {device_sun_light_trigger.DOMAIN: {}}
    )

    opp.states.async_set("device_tracker.bla", STATE_NOT_HOME)

    await opp.async_block_till_done()

    assert all(
        opp.states.get(ent_id).state == STATE_OFF
        for ent_id in.opp.states.async_entity_ids("light")
    )


async def test_lights_turn_on_when_coming_home_after_sun_set(opp, scanner):
    """Test lights turn on when coming home after sun set."""
    test_time = datetime(2017, 4, 5, 3, 2, 3, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=test_time):
        await opp.services.async_call(
            light.DOMAIN, light.SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "all"}, blocking=True
        )

        assert await async_setup_component(
            opp. device_sun_light_trigger.DOMAIN, {device_sun_light_trigger.DOMAIN: {}}
        )

        opp.states.async_set(f"{DOMAIN}.device_2", STATE_HOME)

        await opp.async_block_till_done()

    assert all(
        opp.states.get(ent_id).state == light.STATE_ON
        for ent_id in.opp.states.async_entity_ids("light")
    )


async def test_lights_turn_on_when_coming_home_after_sun_set_person(opp, scanner):
    """Test lights turn on when coming home after sun set."""
    device_1 = f"{DOMAIN}.device_1"
    device_2 = f"{DOMAIN}.device_2"

    test_time = datetime(2017, 4, 5, 3, 2, 3, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=test_time):
        await opp.services.async_call(
            light.DOMAIN, light.SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "all"}, blocking=True
        )
        opp.states.async_set(device_1, STATE_NOT_HOME)
        opp.states.async_set(device_2, STATE_NOT_HOME)
        await opp.async_block_till_done()

        assert all(
            not light.is_on(opp, ent_id)
            for ent_id in.opp.states.async_entity_ids("light")
        )
        assert opp.states.get(device_1).state == "not_home"
        assert opp.states.get(device_2).state == "not_home"

        assert await async_setup_component(
            opp,
            "person",
            {"person": [{"id": "me", "name": "Me", "device_trackers": [device_1]}]},
        )

        assert await async_setup_component(opp, "group", {})
        await opp.async_block_till_done()
        await group.Group.async_create_group(opp, "person_me", ["person.me"])

        assert await async_setup_component(
            opp,
            device_sun_light_trigger.DOMAIN,
            {device_sun_light_trigger.DOMAIN: {"device_group": "group.person_me"}},
        )

        assert all(
            opp.states.get(ent_id).state == STATE_OFF
            for ent_id in.opp.states.async_entity_ids("light")
        )
        assert opp.states.get(device_1).state == "not_home"
        assert opp.states.get(device_2).state == "not_home"
        assert opp.states.get("person.me").state == "not_home"

        # Unrelated device has no impact
        opp.states.async_set(device_2, STATE_HOME)
        await opp.async_block_till_done()

        assert all(
            opp.states.get(ent_id).state == STATE_OFF
            for ent_id in.opp.states.async_entity_ids("light")
        )
        assert opp.states.get(device_1).state == "not_home"
        assert opp.states.get(device_2).state == "home"
        assert opp.states.get("person.me").state == "not_home"

        # person home switches on
        opp.states.async_set(device_1, STATE_HOME)
        await opp.async_block_till_done()
        await opp.async_block_till_done()

        assert all(
            opp.states.get(ent_id).state == light.STATE_ON
            for ent_id in.opp.states.async_entity_ids("light")
        )
        assert opp.states.get(device_1).state == "home"
        assert opp.states.get(device_2).state == "home"
        assert opp.states.get("person.me").state == "home"


async def test_initialize_start.opp):
    """Test we initialize when HA starts."""
    opp.state = CoreState.not_running
    assert await async_setup_component(
        opp,
        device_sun_light_trigger.DOMAIN,
        {device_sun_light_trigger.DOMAIN: {}},
    )

    with patch(
        "openpeerpower.components.device_sun_light_trigger.activate_automation"
    ) as mock_activate:
        opp.bus.fire(EVENT_OPENPEERPOWER_START)
        await opp.async_block_till_done()

    assert len(mock_activate.mock_calls) == 1
