"""Test Open Peer Power remote methods and classes."""
import pytest

from openpeerpower import core
from openpeerpower.helpers.json import JSONEncoder
from openpeerpower.util import dt as dt_util


def test_json_encoder(opp):
    """Test the JSON Encoder."""
    op_json_enc = JSONEncoder()
    state = core.State("test.test", "hello")

    assert op_json_enc.default(state) == state.as_dict()

    # Default method raises TypeError if non HA object
    with pytest.raises(TypeError):
        op_json_enc.default(1)

    now = dt_util.utcnow()
    assert op_json_enc.default(now) == now.isoformat()
