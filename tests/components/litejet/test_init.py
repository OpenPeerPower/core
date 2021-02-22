"""The tests for the litejet component."""
import unittest

from openpeerpower.components import litejet

from tests.common import get_test_open_peer_power


class TestLiteJet(unittest.TestCase):
    """Test the litejet component."""

    def setup_method(self, method):
        """Set up things to be run when tests are started."""
        self opp =get_test_open_peer_power()
        self.opp.start()
        self.opp.block_till_done()

    def teardown_method(self, method):
        """Stop everything that was started."""
        self.opp.stop()

    def test_is_ignored_unspecified(self):
        """Ensure it is ignored when unspecified."""
        self.opp.data["litejet_config"] = {}
        assert not litejet.is_ignored(self.opp, "Test")

    def test_is_ignored_empty(self):
        """Ensure it is ignored when empty."""
        self.opp.data["litejet_config"] = {litejet.CONF_EXCLUDE_NAMES: []}
        assert not litejet.is_ignored(self.opp, "Test")

    def test_is_ignored_normal(self):
        """Test if usually ignored."""
        self.opp.data["litejet_config"] = {
            litejet.CONF_EXCLUDE_NAMES: ["Test", "Other One"]
        }
        assert litejet.is_ignored(self.opp, "Test")
        assert not litejet.is_ignored(self.opp, "Other one")
        assert not litejet.is_ignored(self.opp, "Other 0ne")
        assert litejet.is_ignored(self.opp, "Other One There")
        assert litejet.is_ignored(self.opp, "Other One")
