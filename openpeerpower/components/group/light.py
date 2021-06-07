"""This platform allows several lights to be grouped into one light."""
from __future__ import annotations

import asyncio
from collections import Counter
from collections.abc import Iterator
import itertools
from typing import Any, Callable, cast

import voluptuous as vol

from openpeerpower.components import light
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_EFFECT_LIST,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_MAX_MIREDS,
    ATTR_MIN_MIREDS,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_TRANSITION,
    ATTR_WHITE_VALUE,
    ATTR_XY_COLOR,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_ONOFF,
    PLATFORM_SCHEMA,
    SUPPORT_EFFECT,
    SUPPORT_FLASH,
    SUPPORT_TRANSITION,
    SUPPORT_WHITE_VALUE,
    color_supported,
    color_temp_supported,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    CONF_ENTITIES,
    CONF_NAME,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from openpeerpower.core import CoreState, OpenPeerPower, State
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.event import async_track_state_change_event
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.util import color as color_util

from . import GroupEntity

# mypy: allow-incomplete-defs, allow-untyped-calls, allow-untyped-defs
# mypy: no-check-untyped-defs

DEFAULT_NAME = "Light Group"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_ENTITIES): cv.entities_domain(light.DOMAIN),
    }
)

SUPPORT_GROUP_LIGHT = (
    SUPPORT_EFFECT | SUPPORT_FLASH | SUPPORT_TRANSITION | SUPPORT_WHITE_VALUE
)


async def async_setup_platform(
    opp: OpenPeerPower, config: ConfigType, async_add_entities, discovery_info=None
) -> None:
    """Initialize light.group platform."""
    async_add_entities(
        [LightGroup(cast(str, config.get(CONF_NAME)), config[CONF_ENTITIES])]
    )


class LightGroup(GroupEntity, light.LightEntity):
    """Representation of a light group."""

    def __init__(self, name: str, entity_ids: list[str]) -> None:
        """Initialize a light group."""
        self._name = name
        self._entity_ids = entity_ids
        self._is_on = False
        self._available = False
        self._icon = "mdi:lightbulb-group"
        self._brightness: int | None = None
        self._color_mode: str | None = None
        self._hs_color: tuple[float, float] | None = None
        self._rgb_color: tuple[int, int, int] | None = None
        self._rgbw_color: tuple[int, int, int, int] | None = None
        self._rgbww_color: tuple[int, int, int, int, int] | None = None
        self._xy_color: tuple[float, float] | None = None
        self._color_temp: int | None = None
        self._min_mireds: int = 154
        self._max_mireds: int = 500
        self._white_value: int | None = None
        self._effect_list: list[str] | None = None
        self._effect: str | None = None
        self._supported_color_modes: set[str] | None = None
        self._supported_features: int = 0

    async def async_added_to_opp(self) -> None:
        """Register callbacks."""

        async def async_state_changed_listener(event):
            """Handle child updates."""
            self.async_set_context(event.context)
            await self.async_defer_or_update_op_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.opp, self._entity_ids, async_state_changed_listener
            )
        )

        if self.opp.state == CoreState.running:
            await self.async_update()
            return

        await super().async_added_to_opp()

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return the on/off state of the light group."""
        return self._is_on

    @property
    def available(self) -> bool:
        """Return whether the light group is available."""
        return self._available

    @property
    def icon(self):
        """Return the light group icon."""
        return self._icon

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light group between 0..255."""
        return self._brightness

    @property
    def color_mode(self) -> str | None:
        """Return the color mode of the light."""
        return self._color_mode

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the HS color value [float, float]."""
        return self._hs_color

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value [int, int, int]."""
        return self._rgb_color

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the rgbw color value [int, int, int, int]."""
        return self._rgbw_color

    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        """Return the rgbww color value [int, int, int, int, int]."""
        return self._rgbww_color

    @property
    def xy_color(self) -> tuple[float, float] | None:
        """Return the xy color value [float, float]."""
        return self._xy_color

    @property
    def color_temp(self) -> int | None:
        """Return the CT color value in mireds."""
        return self._color_temp

    @property
    def min_mireds(self) -> int:
        """Return the coldest color_temp that this light group supports."""
        return self._min_mireds

    @property
    def max_mireds(self) -> int:
        """Return the warmest color_temp that this light group supports."""
        return self._max_mireds

    @property
    def white_value(self) -> int | None:
        """Return the white value of this light group between 0..255."""
        return self._white_value

    @property
    def effect_list(self) -> list[str] | None:
        """Return the list of supported effects."""
        return self._effect_list

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self._effect

    @property
    def supported_color_modes(self) -> set | None:
        """Flag supported color modes."""
        return self._supported_color_modes

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features

    @property
    def should_poll(self) -> bool:
        """No polling needed for a light group."""
        return False

    @property
    def extra_state_attributes(self):
        """Return the state attributes for the light group."""
        return {ATTR_ENTITY_ID: self._entity_ids}

    async def async_turn_on(self, **kwargs):
        """Forward the turn_on command to all lights in the light group."""
        data = {ATTR_ENTITY_ID: self._entity_ids}
        emulate_color_temp_entity_ids = []

        if ATTR_BRIGHTNESS in kwargs:
            data[ATTR_BRIGHTNESS] = kwargs[ATTR_BRIGHTNESS]

        if ATTR_HS_COLOR in kwargs:
            data[ATTR_HS_COLOR] = kwargs[ATTR_HS_COLOR]

        if ATTR_RGB_COLOR in kwargs:
            data[ATTR_RGB_COLOR] = kwargs[ATTR_RGB_COLOR]

        if ATTR_RGBW_COLOR in kwargs:
            data[ATTR_RGBW_COLOR] = kwargs[ATTR_RGBW_COLOR]

        if ATTR_RGBWW_COLOR in kwargs:
            data[ATTR_RGBWW_COLOR] = kwargs[ATTR_RGBWW_COLOR]

        if ATTR_XY_COLOR in kwargs:
            data[ATTR_XY_COLOR] = kwargs[ATTR_XY_COLOR]

        if ATTR_COLOR_TEMP in kwargs:
            data[ATTR_COLOR_TEMP] = kwargs[ATTR_COLOR_TEMP]

            # Create a new entity list to mutate
            updated_entities = list(self._entity_ids)

            # Walk through initial entity ids, split entity lists by support
            for entity_id in self._entity_ids:
                state = self.opp.states.get(entity_id)
                if not state:
                    continue
                support = state.attributes.get(ATTR_SUPPORTED_COLOR_MODES)
                # Only pass color temperature to supported entity_ids
                if color_supported(support) and not color_temp_supported(support):
                    emulate_color_temp_entity_ids.append(entity_id)
                    updated_entities.remove(entity_id)
                    data[ATTR_ENTITY_ID] = updated_entities

        if ATTR_WHITE_VALUE in kwargs:
            data[ATTR_WHITE_VALUE] = kwargs[ATTR_WHITE_VALUE]

        if ATTR_EFFECT in kwargs:
            data[ATTR_EFFECT] = kwargs[ATTR_EFFECT]

        if ATTR_TRANSITION in kwargs:
            data[ATTR_TRANSITION] = kwargs[ATTR_TRANSITION]

        if ATTR_FLASH in kwargs:
            data[ATTR_FLASH] = kwargs[ATTR_FLASH]

        if not emulate_color_temp_entity_ids:
            await self.opp.services.async_call(
                light.DOMAIN,
                light.SERVICE_TURN_ON,
                data,
                blocking=True,
                context=self._context,
            )
            return

        emulate_color_temp_data = data.copy()
        temp_k = color_util.color_temperature_mired_to_kelvin(
            emulate_color_temp_data[ATTR_COLOR_TEMP]
        )
        hs_color = color_util.color_temperature_to_hs(temp_k)
        emulate_color_temp_data[ATTR_HS_COLOR] = hs_color
        del emulate_color_temp_data[ATTR_COLOR_TEMP]

        emulate_color_temp_data[ATTR_ENTITY_ID] = emulate_color_temp_entity_ids

        await asyncio.gather(
            self.opp.services.async_call(
                light.DOMAIN,
                light.SERVICE_TURN_ON,
                data,
                blocking=True,
                context=self._context,
            ),
            self.opp.services.async_call(
                light.DOMAIN,
                light.SERVICE_TURN_ON,
                emulate_color_temp_data,
                blocking=True,
                context=self._context,
            ),
        )

    async def async_turn_off(self, **kwargs):
        """Forward the turn_off command to all lights in the light group."""
        data = {ATTR_ENTITY_ID: self._entity_ids}

        if ATTR_TRANSITION in kwargs:
            data[ATTR_TRANSITION] = kwargs[ATTR_TRANSITION]

        await self.opp.services.async_call(
            light.DOMAIN,
            light.SERVICE_TURN_OFF,
            data,
            blocking=True,
            context=self._context,
        )

    async def async_update(self):
        """Query all members and determine the light group state."""
        all_states = [self.opp.states.get(x) for x in self._entity_ids]
        states: list[State] = list(filter(None, all_states))
        on_states = [state for state in states if state.state == STATE_ON]

        self._is_on = len(on_states) > 0
        self._available = any(state.state != STATE_UNAVAILABLE for state in states)

        self._brightness = _reduce_attribute(on_states, ATTR_BRIGHTNESS)

        self._hs_color = _reduce_attribute(on_states, ATTR_HS_COLOR, reduce=_mean_tuple)
        self._rgb_color = _reduce_attribute(
            on_states, ATTR_RGB_COLOR, reduce=_mean_tuple
        )
        self._rgbw_color = _reduce_attribute(
            on_states, ATTR_RGBW_COLOR, reduce=_mean_tuple
        )
        self._rgbww_color = _reduce_attribute(
            on_states, ATTR_RGBWW_COLOR, reduce=_mean_tuple
        )
        self._xy_color = _reduce_attribute(on_states, ATTR_XY_COLOR, reduce=_mean_tuple)

        self._white_value = _reduce_attribute(on_states, ATTR_WHITE_VALUE)

        self._color_temp = _reduce_attribute(on_states, ATTR_COLOR_TEMP)
        self._min_mireds = _reduce_attribute(
            states, ATTR_MIN_MIREDS, default=154, reduce=min
        )
        self._max_mireds = _reduce_attribute(
            states, ATTR_MAX_MIREDS, default=500, reduce=max
        )

        self._effect_list = None
        all_effect_lists = list(_find_state_attributes(states, ATTR_EFFECT_LIST))
        if all_effect_lists:
            # Merge all effects from all effect_lists with a union merge.
            self._effect_list = list(set().union(*all_effect_lists))
            self._effect_list.sort()
            if "None" in self._effect_list:
                self._effect_list.remove("None")
                self._effect_list.insert(0, "None")

        self._effect = None
        all_effects = list(_find_state_attributes(on_states, ATTR_EFFECT))
        if all_effects:
            # Report the most common effect.
            effects_count = Counter(itertools.chain(all_effects))
            self._effect = effects_count.most_common(1)[0][0]

        self._color_mode = None
        all_color_modes = list(_find_state_attributes(on_states, ATTR_COLOR_MODE))
        if all_color_modes:
            # Report the most common color mode, select brightness and onoff last
            color_mode_count = Counter(itertools.chain(all_color_modes))
            if COLOR_MODE_ONOFF in color_mode_count:
                color_mode_count[COLOR_MODE_ONOFF] = -1
            if COLOR_MODE_BRIGHTNESS in color_mode_count:
                color_mode_count[COLOR_MODE_BRIGHTNESS] = 0
            self._color_mode = color_mode_count.most_common(1)[0][0]

        self._supported_color_modes = None
        all_supported_color_modes = list(
            _find_state_attributes(states, ATTR_SUPPORTED_COLOR_MODES)
        )
        if all_supported_color_modes:
            # Merge all color modes.
            self._supported_color_modes = set().union(*all_supported_color_modes)

        self._supported_features = 0
        for support in _find_state_attributes(states, ATTR_SUPPORTED_FEATURES):
            # Merge supported features by emulating support for every feature
            # we find.
            self._supported_features |= support
        # Bitwise-and the supported features with the GroupedLight's features
        # so that we don't break in the future when a new feature is added.
        self._supported_features &= SUPPORT_GROUP_LIGHT


def _find_state_attributes(states: list[State], key: str) -> Iterator[Any]:
    """Find attributes with matching key from states."""
    for state in states:
        value = state.attributes.get(key)
        if value is not None:
            yield value


def _mean_int(*args):
    """Return the mean of the supplied values."""
    return int(sum(args) / len(args))


def _mean_tuple(*args):
    """Return the mean values along the columns of the supplied values."""
    return tuple(sum(x) / len(x) for x in zip(*args))


def _reduce_attribute(
    states: list[State],
    key: str,
    default: Any | None = None,
    reduce: Callable[..., Any] = _mean_int,
) -> Any:
    """Find the first attribute matching key from states.

    If none are found, return default.
    """
    attrs = list(_find_state_attributes(states, key))

    if not attrs:
        return default

    if len(attrs) == 1:
        return attrs[0]

    return reduce(*attrs)
