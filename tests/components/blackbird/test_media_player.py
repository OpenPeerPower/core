"""The tests for the Monoprice Blackbird media player platform."""
from collections import defaultdict
import unittest
from unittest import mock

import pytest
import voluptuous as vol

from openpeerpower.components.blackbird.const import DOMAIN, SERVICE_SETALLZONES
from openpeerpower.components.blackbird.media_player import (
    DATA_BLACKBIRD,
    PLATFORM_SCHEMA,
    setup_platform,
)
from openpeerpower.components.media_player.const import (
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
)
from openpeerpower.const import STATE_OFF, STATE_ON

import tests.common


class AttrDict(dict):
    """Helper class for mocking attributes."""

    def __setattr__(self, name, value):
        """Set attribute."""
        self[name] = value

    def __getattr__(self, item):
        """Get attribute."""
        return self[item]


class MockBlackbird:
    """Mock for pyblackbird object."""

    def __init__(self):
        """Init mock object."""
        self.zones = defaultdict(lambda: AttrDict(power=True, av=1))

    def zone_status(self, zone_id):
        """Get zone status."""
        status = self.zones[zone_id]
        status.zone = zone_id
        return AttrDict(status)

    def set_zone_source(self, zone_id, source_idx):
        """Set source for zone."""
        self.zones[zone_id].av = source_idx

    def set_zone_power(self, zone_id, power):
        """Turn zone on/off."""
        self.zones[zone_id].power = power

    def set_all_zone_source(self, source_idx):
        """Set source for all zones."""
        self.zones[3].av = source_idx


class TestBlackbirdSchema(unittest.TestCase):
    """Test Blackbird schema."""

    def test_valid_serial_schema(self):
        """Test valid schema."""
        valid_schema = {
            "platform": "blackbird",
            "port": "/dev/ttyUSB0",
            "zones": {
                1: {"name": "a"},
                2: {"name": "a"},
                3: {"name": "a"},
                4: {"name": "a"},
                5: {"name": "a"},
                6: {"name": "a"},
                7: {"name": "a"},
                8: {"name": "a"},
            },
            "sources": {
                1: {"name": "a"},
                2: {"name": "a"},
                3: {"name": "a"},
                4: {"name": "a"},
                5: {"name": "a"},
                6: {"name": "a"},
                7: {"name": "a"},
                8: {"name": "a"},
            },
        }
        PLATFORM_SCHEMA(valid_schema)

    def test_valid_socket_schema(self):
        """Test valid schema."""
        valid_schema = {
            "platform": "blackbird",
            "host": "192.168.1.50",
            "zones": {
                1: {"name": "a"},
                2: {"name": "a"},
                3: {"name": "a"},
                4: {"name": "a"},
                5: {"name": "a"},
            },
            "sources": {
                1: {"name": "a"},
                2: {"name": "a"},
                3: {"name": "a"},
                4: {"name": "a"},
            },
        }
        PLATFORM_SCHEMA(valid_schema)

    def test_invalid_schemas(self):
        """Test invalid schemas."""
        schemas = (
            {},  # Empty
            None,  # None
            # Port and host used concurrently
            {
                "platform": "blackbird",
                "port": "/dev/ttyUSB0",
                "host": "192.168.1.50",
                "name": "Name",
                "zones": {1: {"name": "a"}},
                "sources": {1: {"name": "b"}},
            },
            # Port or host missing
            {
                "platform": "blackbird",
                "name": "Name",
                "zones": {1: {"name": "a"}},
                "sources": {1: {"name": "b"}},
            },
            # Invalid zone number
            {
                "platform": "blackbird",
                "port": "/dev/ttyUSB0",
                "name": "Name",
                "zones": {11: {"name": "a"}},
                "sources": {1: {"name": "b"}},
            },
            # Invalid source number
            {
                "platform": "blackbird",
                "port": "/dev/ttyUSB0",
                "name": "Name",
                "zones": {1: {"name": "a"}},
                "sources": {9: {"name": "b"}},
            },
            # Zone missing name
            {
                "platform": "blackbird",
                "port": "/dev/ttyUSB0",
                "name": "Name",
                "zones": {1: {}},
                "sources": {1: {"name": "b"}},
            },
            # Source missing name
            {
                "platform": "blackbird",
                "port": "/dev/ttyUSB0",
                "name": "Name",
                "zones": {1: {"name": "a"}},
                "sources": {1: {}},
            },
        )
        for value in schemas:
            with pytest.raises(vol.MultipleInvalid):
                PLATFORM_SCHEMA(value)


class TestBlackbirdMediaPlayer(unittest.TestCase):
    """Test the media_player module."""

    def setUp(self):
        """Set up the test case."""
        self.blackbird = MockBlackbird()
        self.opp = tests.common.get_test_open_peer_power()
        self.opp.start()
        # Note, source dictionary is unsorted!
        with mock.patch(
            "openpeerpower.components.blackbird.media_player.get_blackbird",
            new=lambda *a: self.blackbird,
        ):
            setup_platform(
                self.opp,
                {
                    "platform": "blackbird",
                    "port": "/dev/ttyUSB0",
                    "zones": {3: {"name": "Zone name"}},
                    "sources": {
                        1: {"name": "one"},
                        3: {"name": "three"},
                        2: {"name": "two"},
                    },
                },
                lambda *args, **kwargs: None,
                {},
            )
            self.opp.block_till_done()
        self.media_player = self.opp.data[DATA_BLACKBIRD]["/dev/ttyUSB0-3"]
        self.media_player.opp = self.opp
        self.media_player.entity_id = "media_player.zone_3"
        self.addCleanup(self.tear_down_cleanup)

    def tear_down_cleanup(self):
        """Tear down the test case."""
        self.opp.stop()

    def test_setup_platform(self, *args):
        """Test setting up platform."""
        # One service must be registered
        assert self.opp.services.has_service(DOMAIN, SERVICE_SETALLZONES)
        assert len(self.opp.data[DATA_BLACKBIRD]) == 1
        assert self.opp.data[DATA_BLACKBIRD]["/dev/ttyUSB0-3"].name == "Zone name"

    def test_setallzones_service_call_with_entity_id(self):
        """Test set all zone source service call with entity id."""
        self.media_player.update()
        assert self.media_player.name == "Zone name"
        assert self.media_player.state == STATE_ON
        assert self.media_player.source == "one"

        # Call set all zones service
        self.opp.services.call(
            DOMAIN,
            SERVICE_SETALLZONES,
            {"entity_id": "media_player.zone_3", "source": "three"},
            blocking=True,
        )

        # Check that source was changed
        assert self.blackbird.zones[3].av == 3
        self.media_player.update()
        assert self.media_player.source == "three"

    def test_setallzones_service_call_without_entity_id(self):
        """Test set all zone source service call without entity id."""
        self.media_player.update()
        assert self.media_player.name == "Zone name"
        assert self.media_player.state == STATE_ON
        assert self.media_player.source == "one"

        # Call set all zones service
        self.opp.services.call(
            DOMAIN, SERVICE_SETALLZONES, {"source": "three"}, blocking=True
        )

        # Check that source was changed
        assert self.blackbird.zones[3].av == 3
        self.media_player.update()
        assert self.media_player.source == "three"

    def test_update(self):
        """Test updating values from blackbird."""
        assert self.media_player.state is None
        assert self.media_player.source is None

        self.media_player.update()

        assert self.media_player.state == STATE_ON
        assert self.media_player.source == "one"

    def test_name(self):
        """Test name property."""
        assert self.media_player.name == "Zone name"

    def test_state(self):
        """Test state property."""
        assert self.media_player.state is None

        self.media_player.update()
        assert self.media_player.state == STATE_ON

        self.blackbird.zones[3].power = False
        self.media_player.update()
        assert self.media_player.state == STATE_OFF

    def test_supported_features(self):
        """Test supported features property."""
        assert (
            SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE
            == self.media_player.supported_features
        )

    def test_source(self):
        """Test source property."""
        assert self.media_player.source is None
        self.media_player.update()
        assert self.media_player.source == "one"

    def test_media_title(self):
        """Test media title property."""
        assert self.media_player.media_title is None
        self.media_player.update()
        assert self.media_player.media_title == "one"

    def test_source_list(self):
        """Test source list property."""
        # Note, the list is sorted!
        assert self.media_player.source_list == ["one", "two", "three"]

    def test_select_source(self):
        """Test source selection methods."""
        self.media_player.update()

        assert self.media_player.source == "one"

        self.media_player.select_source("two")
        assert self.blackbird.zones[3].av == 2
        self.media_player.update()
        assert self.media_player.source == "two"

        # Trying to set unknown source.
        self.media_player.select_source("no name")
        assert self.blackbird.zones[3].av == 2
        self.media_player.update()
        assert self.media_player.source == "two"

    def test_turn_on(self):
        """Testing turning on the zone."""
        self.blackbird.zones[3].power = False
        self.media_player.update()
        assert self.media_player.state == STATE_OFF

        self.media_player.turn_on()
        assert self.blackbird.zones[3].power
        self.media_player.update()
        assert self.media_player.state == STATE_ON

    def test_turn_off(self):
        """Testing turning off the zone."""
        self.blackbird.zones[3].power = True
        self.media_player.update()
        assert self.media_player.state == STATE_ON

        self.media_player.turn_off()
        assert not self.blackbird.zones[3].power
        self.media_player.update()
        assert self.media_player.state == STATE_OFF
