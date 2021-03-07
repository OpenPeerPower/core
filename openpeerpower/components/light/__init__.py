"""Provides functionality to interact with lights."""
from __future__ import annotations

import csv
import dataclasses
from datetime import timedelta
import logging
import os
from typing import Dict, List, Optional, Tuple, cast

import voluptuous as vol

from openpeerpower.const import (
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
    make_entity_service_schema,
)
from openpeerpower.helpers.entity import ToggleEntity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.loader import bind_opp
import openpeerpower.util.color as color_util

# mypy: allow-untyped-defs, no-check-untyped-defs

DOMAIN = "light"
SCAN_INTERVAL = timedelta(seconds=30)
DATA_PROFILES = "light_profiles"

ENTITY_ID_FORMAT = DOMAIN + ".{}"

# Bitfield of features supported by the light entity
SUPPORT_BRIGHTNESS = 1
SUPPORT_COLOR_TEMP = 2
SUPPORT_EFFECT = 4
SUPPORT_FLASH = 8
SUPPORT_COLOR = 16
SUPPORT_TRANSITION = 32
SUPPORT_WHITE_VALUE = 128

# Float that represents transition time in seconds to make change.
ATTR_TRANSITION = "transition"

# Lists holding color values
ATTR_RGB_COLOR = "rgb_color"
ATTR_XY_COLOR = "xy_color"
ATTR_HS_COLOR = "hs_color"
ATTR_COLOR_TEMP = "color_temp"
ATTR_KELVIN = "kelvin"
ATTR_MIN_MIREDS = "min_mireds"
ATTR_MAX_MIREDS = "max_mireds"
ATTR_COLOR_NAME = "color_name"
ATTR_WHITE_VALUE = "white_value"

# Brightness of the light, 0..255 or percentage
ATTR_BRIGHTNESS = "brightness"
ATTR_BRIGHTNESS_PCT = "brightness_pct"
ATTR_BRIGHTNESS_STEP = "brightness_step"
ATTR_BRIGHTNESS_STEP_PCT = "brightness_step_pct"

# String representing a profile (built-in ones or external defined).
ATTR_PROFILE = "profile"

# If the light should flash, can be FLASH_SHORT or FLASH_LONG.
ATTR_FLASH = "flash"
FLASH_SHORT = "short"
FLASH_LONG = "long"

# List of possible effects
ATTR_EFFECT_LIST = "effect_list"

# Apply an effect to the light, can be EFFECT_COLORLOOP.
ATTR_EFFECT = "effect"
EFFECT_COLORLOOP = "colorloop"
EFFECT_RANDOM = "random"
EFFECT_WHITE = "white"

COLOR_GROUP = "Color descriptors"

LIGHT_PROFILES_FILE = "light_profiles.csv"

# Service call validation schemas
VALID_TRANSITION = vol.All(vol.Coerce(float), vol.Clamp(min=0, max=6553))
VALID_BRIGHTNESS = vol.All(vol.Coerce(int), vol.Clamp(min=0, max=255))
VALID_BRIGHTNESS_PCT = vol.All(vol.Coerce(float), vol.Range(min=0, max=100))
VALID_BRIGHTNESS_STEP = vol.All(vol.Coerce(int), vol.Clamp(min=-255, max=255))
VALID_BRIGHTNESS_STEP_PCT = vol.All(vol.Coerce(float), vol.Clamp(min=-100, max=100))
VALID_FLASH = vol.In([FLASH_SHORT, FLASH_LONG])

LIGHT_TURN_ON_SCHEMA = {
    vol.Exclusive(ATTR_PROFILE, COLOR_GROUP): cv.string,
    ATTR_TRANSITION: VALID_TRANSITION,
    vol.Exclusive(ATTR_BRIGHTNESS, ATTR_BRIGHTNESS): VALID_BRIGHTNESS,
    vol.Exclusive(ATTR_BRIGHTNESS_PCT, ATTR_BRIGHTNESS): VALID_BRIGHTNESS_PCT,
    vol.Exclusive(ATTR_BRIGHTNESS_STEP, ATTR_BRIGHTNESS): VALID_BRIGHTNESS_STEP,
    vol.Exclusive(ATTR_BRIGHTNESS_STEP_PCT, ATTR_BRIGHTNESS): VALID_BRIGHTNESS_STEP_PCT,
    vol.Exclusive(ATTR_COLOR_NAME, COLOR_GROUP): cv.string,
    vol.Exclusive(ATTR_RGB_COLOR, COLOR_GROUP): vol.All(
        vol.ExactSequence((cv.byte, cv.byte, cv.byte)), vol.Coerce(tuple)
    ),
    vol.Exclusive(ATTR_XY_COLOR, COLOR_GROUP): vol.All(
        vol.ExactSequence((cv.small_float, cv.small_float)), vol.Coerce(tuple)
    ),
    vol.Exclusive(ATTR_HS_COLOR, COLOR_GROUP): vol.All(
        vol.ExactSequence(
            (
                vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
                vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
            )
        ),
        vol.Coerce(tuple),
    ),
    vol.Exclusive(ATTR_COLOR_TEMP, COLOR_GROUP): vol.All(
        vol.Coerce(int), vol.Range(min=1)
    ),
    vol.Exclusive(ATTR_KELVIN, COLOR_GROUP): cv.positive_int,
    ATTR_WHITE_VALUE: vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    ATTR_FLASH: VALID_FLASH,
    ATTR_EFFECT: cv.string,
}


_LOGGER = logging.getLogger(__name__)


@bind_opp
def is_on(opp, entity_id):
    """Return if the lights are on based on the statemachine."""
    return opp.states.is_state(entity_id, STATE_ON)


def preprocess_turn_on_alternatives(opp, params):
    """Process extra data for turn light on request.

    Async friendly.
    """
    # Bail out, we process this later.
    if ATTR_BRIGHTNESS_STEP in params or ATTR_BRIGHTNESS_STEP_PCT in params:
        return

    if ATTR_PROFILE in params:
        opp.data[DATA_PROFILES].apply_profile(params.pop(ATTR_PROFILE), params)

    color_name = params.pop(ATTR_COLOR_NAME, None)
    if color_name is not None:
        try:
            params[ATTR_RGB_COLOR] = color_util.color_name_to_rgb(color_name)
        except ValueError:
            _LOGGER.warning("Got unknown color %s, falling back to white", color_name)
            params[ATTR_RGB_COLOR] = (255, 255, 255)

    kelvin = params.pop(ATTR_KELVIN, None)
    if kelvin is not None:
        mired = color_util.color_temperature_kelvin_to_mired(kelvin)
        params[ATTR_COLOR_TEMP] = int(mired)

    brightness_pct = params.pop(ATTR_BRIGHTNESS_PCT, None)
    if brightness_pct is not None:
        params[ATTR_BRIGHTNESS] = round(255 * brightness_pct / 100)

    xy_color = params.pop(ATTR_XY_COLOR, None)
    if xy_color is not None:
        params[ATTR_HS_COLOR] = color_util.color_xy_to_hs(*xy_color)

    rgb_color = params.pop(ATTR_RGB_COLOR, None)
    if rgb_color is not None:
        params[ATTR_HS_COLOR] = color_util.color_RGB_to_hs(*rgb_color)


def filter_turn_off_params(params):
    """Filter out params not used in turn off."""
    return {k: v for k, v in params.items() if k in (ATTR_TRANSITION, ATTR_FLASH)}


async def async_setup(opp, config):
    """Expose light control via state machine and services."""
    component = opp.data[DOMAIN] = EntityComponent(_LOGGER, DOMAIN, opp, SCAN_INTERVAL)
    await component.async_setup(config)

    profiles = opp.data[DATA_PROFILES] = Profiles(opp)
    await profiles.async_initialize()

    def preprocess_data(data):
        """Preprocess the service data."""
        base = {
            entity_field: data.pop(entity_field)
            for entity_field in cv.ENTITY_SERVICE_FIELDS
            if entity_field in data
        }

        preprocess_turn_on_alternatives(opp, data)
        base["params"] = data
        return base

    async def async_handle_light_on_service(light, call):
        """Handle turning a light on.

        If brightness is set to 0, this service will turn the light off.
        """
        params = call.data["params"]

        # Only process params once we processed brightness step
        if params and (
            ATTR_BRIGHTNESS_STEP in params or ATTR_BRIGHTNESS_STEP_PCT in params
        ):
            brightness = light.brightness if light.is_on else 0

            if ATTR_BRIGHTNESS_STEP in params:
                brightness += params.pop(ATTR_BRIGHTNESS_STEP)

            else:
                brightness += round(params.pop(ATTR_BRIGHTNESS_STEP_PCT) / 100 * 255)

            params[ATTR_BRIGHTNESS] = max(0, min(255, brightness))

            preprocess_turn_on_alternatives(opp, params)

        if ATTR_PROFILE not in params:
            profiles.apply_default(light.entity_id, params)

        # Zero brightness: Light will be turned off
        if params.get(ATTR_BRIGHTNESS) == 0:
            await light.async_turn_off(**filter_turn_off_params(params))
        else:
            await light.async_turn_on(**params)

    async def async_handle_toggle_service(light, call):
        """Handle toggling a light."""
        if light.is_on:
            off_params = filter_turn_off_params(call.data["params"])
            await light.async_turn_off(**off_params)
        else:
            await async_handle_light_on_service(light, call)

    # Listen for light on and light off service calls.

    component.async_register_entity_service(
        SERVICE_TURN_ON,
        vol.All(cv.make_entity_service_schema(LIGHT_TURN_ON_SCHEMA), preprocess_data),
        async_handle_light_on_service,
    )

    component.async_register_entity_service(
        SERVICE_TURN_OFF,
        {ATTR_TRANSITION: VALID_TRANSITION, ATTR_FLASH: VALID_FLASH},
        "async_turn_off",
    )

    component.async_register_entity_service(
        SERVICE_TOGGLE,
        vol.All(cv.make_entity_service_schema(LIGHT_TURN_ON_SCHEMA), preprocess_data),
        async_handle_toggle_service,
    )

    return True


async def async_setup_entry(opp, entry):
    """Set up a config entry."""
    return await opp.data[DOMAIN].async_setup_entry(entry)


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.data[DOMAIN].async_unload_entry(entry)


def _coerce_none(value: str) -> None:
    """Coerce an empty string as None."""

    if not isinstance(value, str):
        raise vol.Invalid("Expected a string")

    if value:
        raise vol.Invalid("Not an empty string")


@dataclasses.dataclass
class Profile:
    """Representation of a profile."""

    name: str
    color_x: Optional[float] = dataclasses.field(repr=False)
    color_y: Optional[float] = dataclasses.field(repr=False)
    brightness: Optional[int]
    transition: Optional[int] = None
    hs_color: Optional[Tuple[float, float]] = dataclasses.field(init=False)

    SCHEMA = vol.Schema(  # pylint: disable=invalid-name
        vol.Any(
            vol.ExactSequence(
                (
                    str,
                    vol.Any(cv.small_float, _coerce_none),
                    vol.Any(cv.small_float, _coerce_none),
                    vol.Any(cv.byte, _coerce_none),
                )
            ),
            vol.ExactSequence(
                (
                    str,
                    vol.Any(cv.small_float, _coerce_none),
                    vol.Any(cv.small_float, _coerce_none),
                    vol.Any(cv.byte, _coerce_none),
                    vol.Any(VALID_TRANSITION, _coerce_none),
                )
            ),
        )
    )

    def __post_init__(self) -> None:
        """Convert xy to hs color."""
        if None in (self.color_x, self.color_y):
            self.hs_color = None
            return

        self.hs_color = color_util.color_xy_to_hs(
            cast(float, self.color_x), cast(float, self.color_y)
        )

    @classmethod
    def from_csv_row(cls, csv_row: List[str]) -> Profile:
        """Create profile from a CSV row tuple."""
        return cls(*cls.SCHEMA(csv_row))


class Profiles:
    """Representation of available color profiles."""

    def __init__(self, opp: OpenPeerPowerType):
        """Initialize profiles."""
        self.opp = opp
        self.data: Dict[str, Profile] = {}

    def _load_profile_data(self) -> Dict[str, Profile]:
        """Load built-in profiles and custom profiles."""
        profile_paths = [
            os.path.join(os.path.dirname(__file__), LIGHT_PROFILES_FILE),
            self.opp.config.path(LIGHT_PROFILES_FILE),
        ]
        profiles = {}

        for profile_path in profile_paths:
            if not os.path.isfile(profile_path):
                continue
            with open(profile_path) as inp:
                reader = csv.reader(inp)

                # Skip the header
                next(reader, None)

                try:
                    for rec in reader:
                        profile = Profile.from_csv_row(rec)
                        profiles[profile.name] = profile

                except vol.MultipleInvalid as ex:
                    _LOGGER.error(
                        "Error parsing light profile row '%s' from %s: %s",
                        rec,
                        profile_path,
                        ex,
                    )
                    continue
        return profiles

    async def async_initialize(self) -> None:
        """Load and cache profiles."""
        self.data = await self.opp.async_add_executor_job(self._load_profile_data)

    @callback
    def apply_default(self, entity_id: str, params: Dict) -> None:
        """Return the default turn-on profile for the given light."""
        for _entity_id in (entity_id, "group.all_lights"):
            name = f"{_entity_id}.default"
            if name in self.data:
                self.apply_profile(name, params)
                return

    @callback
    def apply_profile(self, name: str, params: Dict) -> None:
        """Apply a profile."""
        profile = self.data.get(name)

        if profile is None:
            return

        if profile.hs_color is not None:
            params.setdefault(ATTR_HS_COLOR, profile.hs_color)
        if profile.brightness is not None:
            params.setdefault(ATTR_BRIGHTNESS, profile.brightness)
        if profile.transition is not None:
            params.setdefault(ATTR_TRANSITION, profile.transition)


class LightEntity(ToggleEntity):
    """Representation of a light."""

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return None

    @property
    def hs_color(self):
        """Return the hue and saturation color value [float, float]."""
        return None

    @property
    def color_temp(self):
        """Return the CT color value in mireds."""
        return None

    @property
    def min_mireds(self):
        """Return the coldest color_temp that this light supports."""
        # Default to the Philips Hue value that OP has always assumed
        # https://developers.meethue.com/documentation/core-concepts
        return 153

    @property
    def max_mireds(self):
        """Return the warmest color_temp that this light supports."""
        # Default to the Philips Hue value that OP has always assumed
        # https://developers.meethue.com/documentation/core-concepts
        return 500

    @property
    def white_value(self):
        """Return the white value of this light between 0..255."""
        return None

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return None

    @property
    def effect(self):
        """Return the current effect."""
        return None

    @property
    def capability_attributes(self):
        """Return capability attributes."""
        data = {}
        supported_features = self.supported_features

        if supported_features & SUPPORT_COLOR_TEMP:
            data[ATTR_MIN_MIREDS] = self.min_mireds
            data[ATTR_MAX_MIREDS] = self.max_mireds

        if supported_features & SUPPORT_EFFECT:
            data[ATTR_EFFECT_LIST] = self.effect_list

        return data

    @property
    def state_attributes(self):
        """Return state attributes."""
        if not self.is_on:
            return None

        data = {}
        supported_features = self.supported_features

        if supported_features & SUPPORT_BRIGHTNESS:
            data[ATTR_BRIGHTNESS] = self.brightness

        if supported_features & SUPPORT_COLOR_TEMP:
            data[ATTR_COLOR_TEMP] = self.color_temp

        if supported_features & SUPPORT_COLOR and self.hs_color:
            hs_color = self.hs_color
            data[ATTR_HS_COLOR] = (round(hs_color[0], 3), round(hs_color[1], 3))
            data[ATTR_RGB_COLOR] = color_util.color_hs_to_RGB(*hs_color)
            data[ATTR_XY_COLOR] = color_util.color_hs_to_xy(*hs_color)

        if supported_features & SUPPORT_WHITE_VALUE:
            data[ATTR_WHITE_VALUE] = self.white_value

        if supported_features & SUPPORT_EFFECT:
            data[ATTR_EFFECT] = self.effect

        return {key: val for key, val in data.items() if val is not None}

    @property
    def supported_features(self):
        """Flag supported features."""
        return 0


class Light(LightEntity):
    """Representation of a light (for backwards compatibility)."""

    def __init_subclass__(cls, **kwargs):
        """Print deprecation warning."""
        super().__init_subclass__(**kwargs)
        _LOGGER.warning(
            "Light is deprecated, modify %s to extend LightEntity",
            cls.__name__,
        )
