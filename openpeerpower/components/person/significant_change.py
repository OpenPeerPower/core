"""Helper to test significant Person state changes."""
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

    if new_state != old_state:
        return True

    return False
