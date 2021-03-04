"""Test discovery helpers."""
from unittest.mock import patch

from openpeerpower import setup
from openpeerpower.core import callback
from openpeerpower.helpers import discovery
from openpeerpower.helpers.dispatcher import dispatcher_send
from openpeerpower.util.async_ import run_callback_threadsafe

from tests.common import (
    MockModule,
    MockPlatform,
    get_test_open_peer_power,
    mock_coro,
    mock_entity_platform,
    mock_integration,
)


class TestHelpersDiscovery:
    """Tests for discovery helper methods."""

    def setup_method(self, method):
        """Set up things to be run when tests are started."""
        self.opp = get_test_open_peer_power()

    def teardown_method(self, method):
        """Stop everything that was started."""
        self.opp.stop()

    @patch("openpeerpower.setup.async_setup_component", return_value=mock_coro())
    def test_listen(self, mock_setup_component):
        """Test discovery listen/discover combo."""
        helpers = self.opp.helpers
        calls_single = []

        @callback
        def callback_single(service, info):
            """Service discovered callback."""
            calls_single.append((service, info))

        self.opp.add_job(
            helpers.discovery.async_listen, "test service", callback_single
        )

        self.opp.add_job(
            helpers.discovery.async_discover,
            "test service",
            "discovery info",
            "test_component",
            {},
        )
        self.opp.block_till_done()

        assert mock_setup_component.called
        assert mock_setup_component.call_args[0] == (self.opp, "test_component", {})
        assert len(calls_single) == 1
        assert calls_single[0] == ("test service", "discovery info")

    @patch("openpeerpower.setup.async_setup_component", return_value=mock_coro(True))
    def test_platform(self, mock_setup_component):
        """Test discover platform method."""
        calls = []

        @callback
        def platform_callback(platform, info):
            """Platform callback method."""
            calls.append((platform, info))

        run_callback_threadsafe(
            self.opp.loop,
            discovery.async_listen_platform,
            self.opp,
            "test_component",
            platform_callback,
        ).result()

        discovery.load_platform(
            self.opp,
            "test_component",
            "test_platform",
            "discovery info",
            {"test_component": {}},
        )
        self.opp.block_till_done()
        assert mock_setup_component.called
        assert mock_setup_component.call_args[0] == (
            self.opp,
            "test_component",
            {"test_component": {}},
        )
        self.opp.block_till_done()

        discovery.load_platform(
            self.opp,
            "test_component_2",
            "test_platform",
            "discovery info",
            {"test_component": {}},
        )
        self.opp.block_till_done()

        assert len(calls) == 1
        assert calls[0] == ("test_platform", "discovery info")

        dispatcher_send(
            self.opp,
            discovery.SIGNAL_PLATFORM_DISCOVERED,
            {"service": discovery.EVENT_LOAD_PLATFORM.format("test_component")},
        )
        self.opp.block_till_done()

        assert len(calls) == 1

    def test_circular_import(self):
        """Test we don't break doing circular import.

        This test will have test_component discover the switch.test_circular
        component while setting up.

        The supplied config will load test_component and will load
        switch.test_circular.

        That means that after startup, we will have test_component and switch
        setup. The test_circular platform has been loaded twice.
        """
        component_calls = []
        platform_calls = []

        def component_setup(opp, config):
            """Set up mock component."""
            discovery.load_platform(opp, "switch", "test_circular", "disc", config)
            component_calls.append(1)
            return True

        def setup_platform(opp, config, add_entities_callback, discovery_info=None):
            """Set up mock platform."""
            platform_calls.append("disc" if discovery_info else "component")

        mock_integration(self.opp, MockModule("test_component", setup=component_setup))

        # dependencies are only set in component level
        # since we are using manifest to hold them
        mock_integration(
            self.opp, MockModule("test_circular", dependencies=["test_component"])
        )
        mock_entity_platform(
            self.opp, "switch.test_circular", MockPlatform(setup_platform)
        )

        setup.setup_component(
            self.opp,
            "test_component",
            {"test_component": None, "switch": [{"platform": "test_circular"}]},
        )

        self.opp.block_till_done()

        # test_component will only be setup once
        assert len(component_calls) == 1
        # The platform will be setup once via the config in `setup_component`
        # and once via the discovery inside test_component.
        assert len(platform_calls) == 2
        assert "test_component" in self.opp.config.components
        assert "switch" in self.opp.config.components

    @patch("openpeerpower.helpers.signal.async_register_signal_handling")
    def test_1st_discovers_2nd_component(self, mock_signal):
        """Test that we don't break if one component discovers the other.

        If the first component fires a discovery event to set up the
        second component while the second component is about to be set up,
        it should not set up the second component twice.
        """
        component_calls = []

        async def component1_setup(opp, config):
            """Set up mock component."""
            print("component1 setup")
            await discovery.async_discover(
                opp, "test_component2", {}, "test_component2", {}
            )
            return True

        def component2_setup(opp, config):
            """Set up mock component."""
            component_calls.append(1)
            return True

        mock_integration(
            self.opp, MockModule("test_component1", async_setup=component1_setup)
        )

        mock_integration(
            self.opp, MockModule("test_component2", setup=component2_setup)
        )

        @callback
        def do_setup():
            """Set up 2 components."""
            self.opp.async_add_job(
                setup.async_setup_component(self.opp, "test_component1", {})
            )
            self.opp.async_add_job(
                setup.async_setup_component(self.opp, "test_component2", {})
            )

        self.opp.add_job(do_setup)
        self.opp.block_till_done()

        # test_component will only be setup once
        assert len(component_calls) == 1
