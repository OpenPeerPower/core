"""Helper to test significant Light state changes."""
from typing import Any, Optional

from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.significant_change import (
    check_numeric_changed,
    either_one_none,
)

from . import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_WHITE_VALUE,
)


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
    if old_state != new_state:
        return True

    if old_attrs.get(ATTR_EFFECT) != new_attrs.get(ATTR_EFFECT):
        return True

    old_color = old_attrs.get(ATTR_HS_COLOR)
    new_color = new_attrs.get(ATTR_HS_COLOR)

    if either_one_none(old_color, new_color):
        return True

    if old_color and new_color:
        # Range 0..360
        if check_numeric_changed(old_color[0], new_color[0], 5):
            return True

        # Range 0..100
        if check_numeric_changed(old_color[1], new_color[1], 3):
            return True

    if check_numeric_changed(
        old_attrs.get(ATTR_BRIGHTNESS), new_attrs.get(ATTR_BRIGHTNESS), 3
    ):
        return True

    if check_numeric_changed(
        # Default range 153..500
        old_attrs.get(ATTR_COLOR_TEMP),
        new_attrs.get(ATTR_COLOR_TEMP),
        5,
    ):
        return True

    if check_numeric_changed(
        # Range 0..255
        old_attrs.get(ATTR_WHITE_VALUE),
        new_attrs.get(ATTR_WHITE_VALUE),
        5,
    ):
        return True

    return False
