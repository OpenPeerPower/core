"""The tests for the geolocation trigger."""
import pytest

from openpeerpower.components import automation, zone
from openpeerpower.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from openpeerpowerr.core import Context
from openpeerpowerr.setup import async_setup_component

from tests.common import async_mock_service, mock_component
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service.opp, "test", "automation")


@pytest.fixture(autouse=True)
def setup_comp.opp):
    """Initialize components."""
    mock_component.opp, "group")
   .opp.loop.run_until_complete(
        async_setup_component(
           .opp,
            zone.DOMAIN,
            {
                "zone": {
                    "name": "test",
                    "latitude": 32.880837,
                    "longitude": -117.237561,
                    "radius": 250,
                }
            },
        )
    )


async def test_if_fires_on_zone_enter.opp, calls):
    """Test for firing on zone enter."""
    context = Context()
   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758, "source": "test_source"},
    )
    await opp..async_block_till_done()

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "geo_location",
                    "source": "test_source",
                    "zone": "zone.test",
                    "event": "enter",
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.%s }}"
                        % "}} - {{ trigger.".join(
                            (
                                "platform",
                                "entity_id",
                                "from_state.state",
                                "to_state.state",
                                "zone.name",
                            )
                        )
                    },
                },
            }
        },
    )

   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
        context=context,
    )
    await opp..async_block_till_done()

    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id
    assert (
        calls[0].data["some"]
        == "geo_location - geo_location.entity - hello - hello - test"
    )

    # Set out of zone again so we can trigger call
   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758},
    )
    await opp..async_block_till_done()

    await opp..services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
    )
    await opp..async_block_till_done()

    assert len(calls) == 1


async def test_if_not_fires_for_enter_on_zone_leave.opp, calls):
    """Test for not firing on zone leave."""
   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
    )
    await opp..async_block_till_done()

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "geo_location",
                    "source": "test_source",
                    "zone": "zone.test",
                    "event": "enter",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758},
    )
    await opp..async_block_till_done()

    assert len(calls) == 0


async def test_if_fires_on_zone_leave.opp, calls):
    """Test for firing on zone leave."""
   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
    )
    await opp..async_block_till_done()

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "geo_location",
                    "source": "test_source",
                    "zone": "zone.test",
                    "event": "leave",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758, "source": "test_source"},
    )
    await opp..async_block_till_done()

    assert len(calls) == 1


async def test_if_not_fires_for_leave_on_zone_enter.opp, calls):
    """Test for not firing on zone enter."""
   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758, "source": "test_source"},
    )
    await opp..async_block_till_done()

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "geo_location",
                    "source": "test_source",
                    "zone": "zone.test",
                    "event": "leave",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
    )
    await opp..async_block_till_done()

    assert len(calls) == 0


async def test_if_fires_on_zone_appear.opp, calls):
    """Test for firing if entity appears in zone."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "geo_location",
                    "source": "test_source",
                    "zone": "zone.test",
                    "event": "enter",
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.%s }}"
                        % "}} - {{ trigger.".join(
                            (
                                "platform",
                                "entity_id",
                                "from_state.state",
                                "to_state.state",
                                "zone.name",
                            )
                        )
                    },
                },
            }
        },
    )

    # Entity appears in zone without previously existing outside the zone.
    context = Context()
   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
        context=context,
    )
    await opp..async_block_till_done()

    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id
    assert (
        calls[0].data["some"] == "geo_location - geo_location.entity -  - hello - test"
    )


async def test_if_fires_on_zone_disappear.opp, calls):
    """Test for firing if entity disappears from zone."""
   .opp.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
    )
    await opp..async_block_till_done()

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "geo_location",
                    "source": "test_source",
                    "zone": "zone.test",
                    "event": "leave",
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.%s }}"
                        % "}} - {{ trigger.".join(
                            (
                                "platform",
                                "entity_id",
                                "from_state.state",
                                "to_state.state",
                                "zone.name",
                            )
                        )
                    },
                },
            }
        },
    )

    # Entity disappears from zone without new coordinates outside the zone.
   .opp.states.async_remove("geo_location.entity")
    await opp..async_block_till_done()

    assert len(calls) == 1
    assert (
        calls[0].data["some"] == "geo_location - geo_location.entity - hello -  - test"
    )
