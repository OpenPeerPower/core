"""The tests for Core components."""
# pylint: disable=protected-access
import asyncio
import unittest
from unittest.mock import Mock, patch

import pytest
import voluptuous as vol
import yaml

from openpeerpower import config
import openpeerpower.components as comps
from openpeerpower.components.openpeerpowerr import (
    SERVICE_CHECK_CONFIG,
    SERVICE_RELOAD_CORE_CONFIG,
    SERVICE_SET_LOCATION,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    ENTITY_MATCH_NONE,
    EVENT_CORE_CONFIG_UPDATE,
    SERVICE_OPENPEERPOWER_RESTART,
    SERVICE_OPENPEERPOWER_STOP,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
import openpeerpowerr.core as ha
from openpeerpowerr.exceptions import OpenPeerPowerError, Unauthorized
from openpeerpowerr.helpers import entity
from openpeerpowerr.setup import async_setup_component

from tests.common import (
    async_capture_events,
    async_mock_service,
    get_test_home_assistant,
    mock_service,
    patch_yaml_files,
)


def turn_on.opp, entity_id=None, **service_data):
    """Turn specified entity on if possible.

    This is a legacy helper method. Do not use it for new tests.
    """
    if entity_id is not None:
        service_data[ATTR_ENTITY_ID] = entity_id

   .opp.services.call(op.DOMAIN, SERVICE_TURN_ON, service_data)


def turn_off.opp, entity_id=None, **service_data):
    """Turn specified entity off.

    This is a legacy helper method. Do not use it for new tests.
    """
    if entity_id is not None:
        service_data[ATTR_ENTITY_ID] = entity_id

   .opp.services.call(op.DOMAIN, SERVICE_TURN_OFF, service_data)


def toggle.opp, entity_id=None, **service_data):
    """Toggle specified entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    if entity_id is not None:
        service_data[ATTR_ENTITY_ID] = entity_id

   .opp.services.call(op.DOMAIN, SERVICE_TOGGLE, service_data)


def stop.opp):
    """Stop Home Assistant.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.services.call(op.DOMAIN, SERVICE_OPENPEERPOWER_STOP)


def restart.opp):
    """Stop Home Assistant.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.services.call(op.DOMAIN, SERVICE_OPENPEERPOWER_RESTART)


def check_config.opp):
    """Check the config files.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.services.call(op.DOMAIN, SERVICE_CHECK_CONFIG)


def reload_core_config.opp):
    """Reload the core config.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.services.call(op.DOMAIN, SERVICE_RELOAD_CORE_CONFIG)


class TestComponentsCore(unittest.TestCase):
    """Test openpeerpower.components module."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()
        assert asyncio.run_coroutine_threadsafe(
            async_setup_component(self.opp, "openpeerpowerr", {}), self.opp.loop
        ).result()

        self.opp.states.set("light.Bowl", STATE_ON)
        self.opp.states.set("light.Ceiling", STATE_OFF)
        self.addCleanup(self.opp.stop)

    def test_is_on(self):
        """Test is_on method."""
        assert comps.is_on(self.opp, "light.Bowl")
        assert not comps.is_on(self.opp, "light.Ceiling")
        assert comps.is_on(self.opp)
        assert not comps.is_on(self.opp, "non_existing.entity")

    def test_turn_on_without_entities(self):
        """Test turn_on method without entities."""
        calls = mock_service(self.opp, "light", SERVICE_TURN_ON)
        turn_on(self.opp)
        self.opp.block_till_done()
        assert 0 == len(calls)

    def test_turn_on(self):
        """Test turn_on method."""
        calls = mock_service(self.opp, "light", SERVICE_TURN_ON)
        turn_on(self.opp, "light.Ceiling")
        self.opp.block_till_done()
        assert 1 == len(calls)

    def test_turn_off(self):
        """Test turn_off method."""
        calls = mock_service(self.opp, "light", SERVICE_TURN_OFF)
        turn_off(self.opp, "light.Bowl")
        self.opp.block_till_done()
        assert 1 == len(calls)

    def test_toggle(self):
        """Test toggle method."""
        calls = mock_service(self.opp, "light", SERVICE_TOGGLE)
        toggle(self.opp, "light.Bowl")
        self.opp.block_till_done()
        assert 1 == len(calls)

    @patch("openpeerpower.config.os.path.isfile", Mock(return_value=True))
    def test_reload_core_conf(self):
        """Test reload core conf service."""
        ent = entity.Entity()
        ent.entity_id = "test.entity"
        ent.opp = self.opp
        ent.schedule_update_op.state()
        self.opp.block_till_done()

        state = self.opp.states.get("test.entity")
        assert state is not None
        assert state.state == "unknown"
        assert state.attributes == {}

        files = {
            config.YAML_CONFIG_FILE: yaml.dump(
                {
                    op.DOMAIN: {
                        "latitude": 10,
                        "longitude": 20,
                        "customize": {"test.Entity": {"hello": "world"}},
                    }
                }
            )
        }
        with patch_yaml_files(files, True):
            reload_core_config(self.opp)
            self.opp.block_till_done()

        assert self.opp.config.latitude == 10
        assert self.opp.config.longitude == 20

        ent.schedule_update_op.state()
        self.opp.block_till_done()

        state = self.opp.states.get("test.entity")
        assert state is not None
        assert state.state == "unknown"
        assert state.attributes.get("hello") == "world"

    @patch("openpeerpower.config.os.path.isfile", Mock(return_value=True))
    @patch("openpeerpower.components.openpeerpowerr._LOGGER.error")
    @patch("openpeerpower.config.async_process_op.core_config")
    def test_reload_core_with_wrong_conf(self, mock_process, mock_error):
        """Test reload core conf service."""
        files = {config.YAML_CONFIG_FILE: yaml.dump(["invalid", "config"])}
        with patch_yaml_files(files, True):
            reload_core_config(self.opp)
            self.opp.block_till_done()

        assert mock_error.called
        assert mock_process.called is False

    @patch("openpeerpowerr.core.OpenPeerPower.async_stop", return_value=None)
    def test_stop_openpeerpowerr(self, mock_stop):
        """Test stop service."""
        stop(self.opp)
        self.opp.block_till_done()
        assert mock_stop.called

    @patch("openpeerpowerr.core.OpenPeerPower.async_stop", return_value=None)
    @patch("openpeerpower.config.async_check_op.config_file", return_value=None)
    def test_restart_openpeerpowerr(self, mock_check, mock_restart):
        """Test stop service."""
        restart(self.opp)
        self.opp.block_till_done()
        assert mock_restart.called
        assert mock_check.called

    @patch("openpeerpowerr.core.OpenPeerPower.async_stop", return_value=None)
    @patch(
        "openpeerpower.config.async_check_op.config_file",
        side_effect=OpenPeerPowerError("Test error"),
    )
    def test_restart_openpeerpowerr_wrong_conf(self, mock_check, mock_restart):
        """Test stop service."""
        restart(self.opp)
        self.opp.block_till_done()
        assert mock_check.called
        assert not mock_restart.called

    @patch("openpeerpowerr.core.OpenPeerPower.async_stop", return_value=None)
    @patch("openpeerpower.config.async_check_op.config_file", return_value=None)
    def test_check_config(self, mock_check, mock_stop):
        """Test stop service."""
        check_config(self.opp)
        self.opp.block_till_done()
        assert mock_check.called
        assert not mock_stop.called


async def test_turn_on_skips_domains_without_service.opp, caplog):
    """Test if turn_on is blocking domain with no service."""
    await async_setup_component.opp, "openpeerpowerr", {})
    async_mock_service.opp, "light", SERVICE_TURN_ON)
   .opp.states.async_set("light.Bowl", STATE_ON)
   .opp.states.async_set("light.Ceiling", STATE_OFF)

    # We can't test if our service call results in services being called
    # because by mocking out the call service method, we mock out all
    # So we mimic how the service registry calls services
    service_call = op.ServiceCall(
        "openpeerpowerr",
        "turn_on",
        {"entity_id": ["light.test", "sensor.bla", "binary_sensor.blub", "light.bla"]},
    )
    service =.opp.services._services["openpeerpowerr"]["turn_on"]

    with patch(
        "openpeerpowerr.core.ServiceRegistry.async_call",
        return_value=None,
    ) as mock_call:
        await service.job.target(service_call)

    assert mock_call.call_count == 1
    assert mock_call.call_args_list[0][0] == (
        "light",
        "turn_on",
        {"entity_id": ["light.bla", "light.test"]},
    )
    assert mock_call.call_args_list[0][1] == {
        "blocking": True,
        "context": service_call.context,
    }
    assert (
        "The service openpeerpowerr.turn_on does not support entities binary_sensor.blub, sensor.bla"
        in caplog.text
    )


async def test_entity_update.opp):
    """Test being able to call entity update."""
    await async_setup_component.opp, "openpeerpowerr", {})

    with patch(
        "openpeerpowerr.helpers.entity_component.async_update_entity",
        return_value=None,
    ) as mock_update:
        await.opp.services.async_call(
            "openpeerpowerr",
            "update_entity",
            {"entity_id": ["light.kitchen"]},
            blocking=True,
        )

    assert len(mock_update.mock_calls) == 1
    assert mock_update.mock_calls[0][1][1] == "light.kitchen"


async def test_setting_location.opp):
    """Test setting the location."""
    await async_setup_component.opp, "openpeerpowerr", {})
    events = async_capture_events.opp, EVENT_CORE_CONFIG_UPDATE)
    # Just to make sure that we are updating values.
    assert.opp.config.latitude != 30
    assert.opp.config.longitude != 40
    await.opp.services.async_call(
        "openpeerpowerr",
        "set_location",
        {"latitude": 30, "longitude": 40},
        blocking=True,
    )
    assert len(events) == 1
    assert.opp.config.latitude == 30
    assert.opp.config.longitude == 40


async def test_require_admin.opp,.opp_read_only_user):
    """Test services requiring admin."""
    await async_setup_component.opp, "openpeerpowerr", {})

    for service in (
        SERVICE_OPENPEERPOWER_RESTART,
        SERVICE_OPENPEERPOWER_STOP,
        SERVICE_CHECK_CONFIG,
        SERVICE_RELOAD_CORE_CONFIG,
    ):
        with pytest.raises(Unauthorized):
            await.opp.services.async_call(
                op.DOMAIN,
                service,
                {},
                context=op.Context(user_id.opp_read_only_user.id),
                blocking=True,
            )
            assert False, f"Should have raises for {service}"

    with pytest.raises(Unauthorized):
        await.opp.services.async_call(
            op.DOMAIN,
            SERVICE_SET_LOCATION,
            {"latitude": 0, "longitude": 0},
            context=op.Context(user_id.opp_read_only_user.id),
            blocking=True,
        )


async def test_turn_on_off_toggle_schema.opp,.opp_read_only_user):
    """Test the schemas for the turn on/off/toggle services."""
    await async_setup_component.opp, "openpeerpowerr", {})

    for service in SERVICE_TURN_ON, SERVICE_TURN_OFF, SERVICE_TOGGLE:
        for invalid in None, "nothing", ENTITY_MATCH_ALL, ENTITY_MATCH_NONE:
            with pytest.raises(vol.Invalid):
                await.opp.services.async_call(
                    op.DOMAIN,
                    service,
                    {"entity_id": invalid},
                    context=op.Context(user_id.opp_read_only_user.id),
                    blocking=True,
                )


async def test_not_allowing_recursion.opp, caplog):
    """Test we do not allow recursion."""
    await async_setup_component.opp, "openpeerpowerr", {})

    for service in SERVICE_TURN_ON, SERVICE_TURN_OFF, SERVICE_TOGGLE:
        await.opp.services.async_call(
            op.DOMAIN,
            service,
            {"entity_id": "openpeerpowerr.light"},
            blocking=True,
        )
        assert (
            f"Called service openpeerpowerr.{service} with invalid entities openpeerpowerr.light"
            in caplog.text
        ), service
