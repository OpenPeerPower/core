"""Common test tools."""

import pytest

from openpeerpower.components.recorder.const import DATA_INSTANCE

from tests.common import get_test_home_assistant, init_recorder_component


@pytest.fixture
def.opp_recorder():
    """Open Peer Power fixture with in-memory recorder."""
    opp = get_test_home_assistant()

    def setup_recorder(config=None):
        """Set up with params."""
        init_recorder_component.opp, config)
       .opp.start()
       .opp.block_till_done()
       .opp.data[DATA_INSTANCE].block_till_done()
        return.opp

    yield setup_recorder
   .opp.stop()
