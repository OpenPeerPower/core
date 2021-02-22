"""The tests for the Entity component helper."""
# pylint: disable=protected-access
from collections import OrderedDict
from datetime import timedelta
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
import voluptuous as vol

from openpeerpower.const import ENTITY_MATCH_ALL, ENTITY_MATCH_NONE
import openpeerpower.core as ha
from openpeerpower.exceptions import PlatformNotReady
from openpeerpower.helpers import discovery
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockModule,
    MockPlatform,
    async_fire_time_changed,
    mock_entity_platform,
    mock_integration,
)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "test_domain"


async def test_setup_loads_platforms.opp):
    """Test the loading of the platforms."""
    component_setup = Mock(return_value=True)
    platform_setup = Mock(return_value=None)

    mock_integration.opp, MockModule("test_component", setup=component_setup))
    # mock the dependencies
    mock_integration.opp, MockModule("mod2", dependencies=["test_component"]))
    mock_entity_platform.opp, "test_domain.mod2", MockPlatform(platform_setup))

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    assert not component_setup.called
    assert not platform_setup.called

    component.setup({DOMAIN: {"platform": "mod2"}})

    await.opp.async_block_till_done()
    assert component_setup.called
    assert platform_setup.called


async def test_setup_recovers_when_setup_raises.opp):
    """Test the setup if exceptions are happening."""
    platform1_setup = Mock(side_effect=Exception("Broken"))
    platform2_setup = Mock(return_value=None)

    mock_entity_platform.opp, "test_domain.mod1", MockPlatform(platform1_setup))
    mock_entity_platform.opp, "test_domain.mod2", MockPlatform(platform2_setup))

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    assert not platform1_setup.called
    assert not platform2_setup.called

    component.setup(
        OrderedDict(
            [
                (DOMAIN, {"platform": "mod1"}),
                (f"{DOMAIN} 2", {"platform": "non_exist"}),
                (f"{DOMAIN} 3", {"platform": "mod2"}),
            ]
        )
    )

    await.opp.async_block_till_done()
    assert platform1_setup.called
    assert platform2_setup.called


@patch(
    "openpeerpower.helpers.entity_component.EntityComponent.async_setup_platform",
)
@patch("openpeerpower.setup.async_setup_component", return_value=True)
async def test_setup_does_discovery(mock_setup_component, mock_setup,.opp):
    """Test setup for discovery."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    component.setup({})

    discovery.load_platform(
       .opp, DOMAIN, "platform_test", {"msg": "discovery_info"}, {DOMAIN: {}}
    )

    await.opp.async_block_till_done()

    assert mock_setup.called
    assert ("platform_test", {}, {"msg": "discovery_info"}) == mock_setup.call_args[0]


@patch("openpeerpower.helpers.entity_platform.async_track_time_interval")
async def test_set_scan_interval_via_config(mock_track,.opp):
    """Test the setting of the scan interval via configuration."""

    def platform_setup_opp, config, add_entities, discovery_info=None):
        """Test the platform setup."""
        add_entities([MockEntity(should_poll=True)])

    mock_entity_platform.opp, "test_domain.platform", MockPlatform(platform_setup))

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    component.setup(
        {DOMAIN: {"platform": "platform", "scan_interval": timedelta(seconds=30)}}
    )

    await.opp.async_block_till_done()
    assert mock_track.called
    assert timedelta(seconds=30) == mock_track.call_args[0][2]


async def test_set_entity_namespace_via_config.opp):
    """Test setting an entity namespace."""

    def platform_setup_opp, config, add_entities, discovery_info=None):
        """Test the platform setup."""
        add_entities([MockEntity(name="beer"), MockEntity(name=None)])

    platform = MockPlatform(platform_setup)

    mock_entity_platform.opp, "test_domain.platform", platform)

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    component.setup({DOMAIN: {"platform": "platform", "entity_namespace": "yummy"}})

    await.opp.async_block_till_done()

    assert sorted.opp.states.async_entity_ids()) == [
        "test_domain.yummy_beer",
        "test_domain.yummy_unnamed_device",
    ]


async def test_extract_from_service_available_device.opp):
    """Test the extraction of entity from service and device is available."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities(
        [
            MockEntity(name="test_1"),
            MockEntity(name="test_2", available=False),
            MockEntity(name="test_3"),
            MockEntity(name="test_4", available=False),
        ]
    )

    call_1 = ha.ServiceCall("test", "service", data={"entity_id": ENTITY_MATCH_ALL})

    assert ["test_domain.test_1", "test_domain.test_3"] == sorted(
        ent.entity_id for ent in (await component.async_extract_from_service(call_1))
    )

    call_2 = ha.ServiceCall(
        "test",
        "service",
        data={"entity_id": ["test_domain.test_3", "test_domain.test_4"]},
    )

    assert ["test_domain.test_3"] == sorted(
        ent.entity_id for ent in (await component.async_extract_from_service(call_2))
    )


async def test_platform_not_ready.opp, legacy_patchable_time):
    """Test that we retry when platform not ready."""
    platform1_setup = Mock(side_effect=[PlatformNotReady, PlatformNotReady, None])
    mock_integration.opp, MockModule("mod1"))
    mock_entity_platform.opp, "test_domain.mod1", MockPlatform(platform1_setup))

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    await component.async_setup({DOMAIN: {"platform": "mod1"}})
    await.opp.async_block_till_done()
    assert len(platform1_setup.mock_calls) == 1
    assert "test_domain.mod1" not in.opp.config.components

    utcnow = dt_util.utcnow()

    with patch("openpeerpower.util.dt.utcnow", return_value=utcnow):
        # Should not trigger attempt 2
        async_fire_time_changed.opp, utcnow + timedelta(seconds=29))
        await.opp.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 1

        # Should trigger attempt 2
        async_fire_time_changed.opp, utcnow + timedelta(seconds=30))
        await.opp.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 2
        assert "test_domain.mod1" not in.opp.config.components

        # This should not trigger attempt 3
        async_fire_time_changed.opp, utcnow + timedelta(seconds=59))
        await.opp.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 2

        # Trigger attempt 3, which succeeds
        async_fire_time_changed.opp, utcnow + timedelta(seconds=60))
        await.opp.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 3
        assert "test_domain.mod1" in.opp.config.components


async def test_extract_from_service_fails_if_no_entity_id.opp):
    """Test the extraction of everything from service."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities(
        [MockEntity(name="test_1"), MockEntity(name="test_2")]
    )

    assert (
        await component.async_extract_from_service(ha.ServiceCall("test", "service"))
        == []
    )
    assert (
        await component.async_extract_from_service(
            ha.ServiceCall("test", "service", {"entity_id": ENTITY_MATCH_NONE})
        )
        == []
    )
    assert (
        await component.async_extract_from_service(
            ha.ServiceCall("test", "service", {"area_id": ENTITY_MATCH_NONE})
        )
        == []
    )


async def test_extract_from_service_filter_out_non_existing_entities.opp):
    """Test the extraction of non existing entities from service."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities(
        [MockEntity(name="test_1"), MockEntity(name="test_2")]
    )

    call = ha.ServiceCall(
        "test",
        "service",
        {"entity_id": ["test_domain.test_2", "test_domain.non_exist"]},
    )

    assert ["test_domain.test_2"] == [
        ent.entity_id for ent in await component.async_extract_from_service(call)
    ]


async def test_extract_from_service_no_group_expand.opp):
    """Test not expanding a group."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities([MockEntity(entity_id="group.test_group")])

    call = ha.ServiceCall("test", "service", {"entity_id": ["group.test_group"]})

    extracted = await component.async_extract_from_service(call, expand_group=False)
    assert len(extracted) == 1
    assert extracted[0].entity_id == "group.test_group"


async def test_setup_dependencies_platform.opp):
    """Test we setup the dependencies of a platform.

    We're explicitly testing that we process dependencies even if a component
    with the same name has already been loaded.
    """
    mock_integration(
       .opp, MockModule("test_component", dependencies=["test_component2"])
    )
    mock_integration.opp, MockModule("test_component2"))
    mock_entity_platform.opp, "test_domain.test_component", MockPlatform())

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    await component.async_setup({DOMAIN: {"platform": "test_component"}})
    await.opp.async_block_till_done()
    assert "test_component" in.opp.config.components
    assert "test_component2" in.opp.config.components
    assert "test_domain.test_component" in.opp.config.components


async def test_setup_entry.opp):
    """Test setup entry calls async_setup_entry on platform."""
    mock_setup_entry = AsyncMock(return_value=True)
    mock_entity_platform(
       .opp,
        "test_domain.entry_domain",
        MockPlatform(
            async_setup_entry=mock_setup_entry, scan_interval=timedelta(seconds=5)
        ),
    )

    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    entry = MockConfigEntry(domain="entry_domain")

    assert await component.async_setup_entry(entry)
    assert len(mock_setup_entry.mock_calls) == 1
    p.opp, p_entry, _ = mock_setup_entry.mock_calls[0][1]
    assert p.opp is.opp
    assert p_entry is entry

    assert component._platforms[entry.entry_id].scan_interval == timedelta(seconds=5)


async def test_setup_entry_platform_not_exist.opp):
    """Test setup entry fails if platform does not exist."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    entry = MockConfigEntry(domain="non_existing")

    assert (await component.async_setup_entry(entry)) is False


async def test_setup_entry_fails_duplicate.opp):
    """Test we don't allow setting up a config entry twice."""
    mock_setup_entry = AsyncMock(return_value=True)
    mock_entity_platform(
       .opp,
        "test_domain.entry_domain",
        MockPlatform(async_setup_entry=mock_setup_entry),
    )

    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    entry = MockConfigEntry(domain="entry_domain")

    assert await component.async_setup_entry(entry)

    with pytest.raises(ValueError):
        await component.async_setup_entry(entry)


async def test_unload_entry_resets_platform.opp):
    """Test unloading an entry removes all entities."""
    mock_setup_entry = AsyncMock(return_value=True)
    mock_entity_platform(
       .opp,
        "test_domain.entry_domain",
        MockPlatform(async_setup_entry=mock_setup_entry),
    )

    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    entry = MockConfigEntry(domain="entry_domain")

    assert await component.async_setup_entry(entry)
    assert len(mock_setup_entry.mock_calls) == 1
    add_entities = mock_setup_entry.mock_calls[0][1][2]
    add_entities([MockEntity()])
    await.opp.async_block_till_done()

    assert len.opp.states.async_entity_ids()) == 1

    assert await component.async_unload_entry(entry)
    assert len.opp.states.async_entity_ids()) == 0


async def test_unload_entry_fails_if_never_loaded.opp):
    """."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    entry = MockConfigEntry(domain="entry_domain")

    with pytest.raises(ValueError):
        await component.async_unload_entry(entry)


async def test_update_entity.opp):
    """Test that we can update an entity with the helper."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    entity = MockEntity()
    entity.async_write_ha_state = Mock()
    entity.async_update_ha_state = AsyncMock(return_value=None)
    await component.async_add_entities([entity])

    # Called as part of async_add_entities
    assert len(entity.async_write_ha_state.mock_calls) == 1

    await.opp.helpers.entity_component.async_update_entity(entity.entity_id)

    assert len(entity.async_update_ha_state.mock_calls) == 1
    assert entity.async_update_ha_state.mock_calls[-1][1][0] is True


async def test_set_service_race.opp):
    """Test race condition on setting service."""
    exception = False

    def async_loop_exception_handler(_, _2) -> None:
        """Handle all exception inside the core loop."""
        nonlocal exception
        exception = True

   .opp.loop.set_exception_handler(async_loop_exception_handler)

    await async_setup_component.opp, "group", {})
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    for _ in range(2):
       .opp.async_create_task(component.async_add_entities([MockEntity()]))

    await.opp.async_block_till_done()
    assert not exception


async def test_extract_all_omit_entity_id.opp, caplog):
    """Test extract all with None and *."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities(
        [MockEntity(name="test_1"), MockEntity(name="test_2")]
    )

    call = ha.ServiceCall("test", "service")

    assert [] == sorted(
        ent.entity_id for ent in await component.async_extract_from_service(call)
    )


async def test_extract_all_use_match_all.opp, caplog):
    """Test extract all with None and *."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities(
        [MockEntity(name="test_1"), MockEntity(name="test_2")]
    )

    call = ha.ServiceCall("test", "service", {"entity_id": "all"})

    assert ["test_domain.test_1", "test_domain.test_2"] == sorted(
        ent.entity_id for ent in await component.async_extract_from_service(call)
    )
    assert (
        "Not passing an entity ID to a service to target all entities is deprecated"
    ) not in caplog.text


async def test_register_entity_service.opp):
    """Test not expanding a group."""
    entity = MockEntity(entity_id=f"{DOMAIN}.entity")
    calls = []

    @ha.callback
    def appender(**kwargs):
        calls.append(kwargs)

    entity.async_called_by_service = appender

    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities([entity])

    component.async_register_entity_service(
        "hello", {"some": str}, "async_called_by_service"
    )

    with pytest.raises(vol.Invalid):
        await.opp.services.async_call(
            DOMAIN,
            "hello",
            {"entity_id": entity.entity_id, "invalid": "data"},
            blocking=True,
        )
        assert len(calls) == 0

    await.opp.services.async_call(
        DOMAIN, "hello", {"entity_id": entity.entity_id, "some": "data"}, blocking=True
    )
    assert len(calls) == 1
    assert calls[0] == {"some": "data"}

    await.opp.services.async_call(
        DOMAIN, "hello", {"entity_id": ENTITY_MATCH_ALL, "some": "data"}, blocking=True
    )
    assert len(calls) == 2
    assert calls[1] == {"some": "data"}

    await.opp.services.async_call(
        DOMAIN, "hello", {"entity_id": ENTITY_MATCH_NONE, "some": "data"}, blocking=True
    )
    assert len(calls) == 2

    await.opp.services.async_call(
        DOMAIN, "hello", {"area_id": ENTITY_MATCH_NONE, "some": "data"}, blocking=True
    )
    assert len(calls) == 2
