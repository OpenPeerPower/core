"""Helper to test significant Switch state changes."""
from typing import Any, Optional

from openpeerpower.core import OpenPeerPower, callback


@callback
def async_check_significant_change(
    opp: OpenPeerPower,
    old_state: str,
    old_attrs: dict,
    new_state: str,
    new_attrs: dict,
    **kwargs: Any,
) -> Optional[bool]:
    """Test if state significantly changed."""
    return old_state != new_state
