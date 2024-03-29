"""Support for Plum Lightpad lights."""
from __future__ import annotations

import asyncio

from plumlightpad import Plum

from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    LightEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
import openpeerpower.util.color as color_util

from .const import DOMAIN


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plum Lightpad dimmer lights and glow rings."""

    plum: Plum = opp.data[DOMAIN][entry.entry_id]

    def setup_entities(device) -> None:
        entities = []

        if "lpid" in device:
            lightpad = plum.get_lightpad(device["lpid"])
            entities.append(GlowRing(lightpad=lightpad))

        if "llid" in device:
            logical_load = plum.get_load(device["llid"])
            entities.append(PlumLight(load=logical_load))

        if entities:
            async_add_entities(entities)

    async def new_load(device):
        setup_entities(device)

    async def new_lightpad(device):
        setup_entities(device)

    device_web_session = async_get_clientsession(opp, verify_ssl=False)
    asyncio.create_task(
        plum.discover(
            opp.loop,
            loadListener=new_load,
            lightpadListener=new_lightpad,
            websession=device_web_session,
        )
    )


class PlumLight(LightEntity):
    """Representation of a Plum Lightpad dimmer."""

    def __init__(self, load):
        """Initialize the light."""
        self._load = load
        self._brightness = load.level

    async def async_added_to_opp(self):
        """Subscribe to dimmerchange events."""
        self._load.add_event_listener("dimmerchange", self.dimmerchange)

    def dimmerchange(self, event):
        """Change event handler updating the brightness."""
        self._brightness = event["level"]
        self.schedule_update_op_state()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def unique_id(self):
        """Combine logical load ID with .light to guarantee it is unique."""
        return f"{self._load.llid}.light"

    @property
    def name(self):
        """Return the name of the switch if any."""
        return self._load.name

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "name": self.name,
            "identifiers": {(DOMAIN, self.unique_id)},
            "model": "Dimmer",
            "manufacturer": "Plum",
        }

    @property
    def brightness(self) -> int:
        """Return the brightness of this switch between 0..255."""
        return self._brightness

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._brightness > 0

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._load.dimmable:
            return SUPPORT_BRIGHTNESS
        return 0

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs:
            await self._load.turn_on(kwargs[ATTR_BRIGHTNESS])
        else:
            await self._load.turn_on()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._load.turn_off()


class GlowRing(LightEntity):
    """Representation of a Plum Lightpad dimmer glow ring."""

    def __init__(self, lightpad):
        """Initialize the light."""
        self._lightpad = lightpad
        self._name = f"{lightpad.friendly_name} Glow Ring"

        self._state = lightpad.glow_enabled
        self._glow_intensity = lightpad.glow_intensity

        self._red = lightpad.glow_color["red"]
        self._green = lightpad.glow_color["green"]
        self._blue = lightpad.glow_color["blue"]

    async def async_added_to_opp(self):
        """Subscribe to configchange events."""
        self._lightpad.add_event_listener("configchange", self.configchange_event)

    def configchange_event(self, event):
        """Handle Configuration change event."""
        config = event["changes"]

        self._state = config["glowEnabled"]
        self._glow_intensity = config["glowIntensity"]

        self._red = config["glowColor"]["red"]
        self._green = config["glowColor"]["green"]
        self._blue = config["glowColor"]["blue"]

        self.schedule_update_op_state()

    @property
    def hs_color(self):
        """Return the hue and saturation color value [float, float]."""
        return color_util.color_RGB_to_hs(self._red, self._green, self._blue)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def unique_id(self):
        """Combine LightPad ID with .glow to guarantee it is unique."""
        return f"{self._lightpad.lpid}.glow"

    @property
    def name(self):
        """Return the name of the switch if any."""
        return self._name

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "name": self.name,
            "identifiers": {(DOMAIN, self.unique_id)},
            "model": "Glow Ring",
            "manufacturer": "Plum",
        }

    @property
    def brightness(self) -> int:
        """Return the brightness of this switch between 0..255."""
        return min(max(int(round(self._glow_intensity * 255, 0)), 0), 255)

    @property
    def glow_intensity(self):
        """Brightness in float form."""
        return self._glow_intensity

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._state

    @property
    def icon(self):
        """Return the crop-portrait icon representing the glow ring."""
        return "mdi:crop-portrait"

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness_pct = kwargs[ATTR_BRIGHTNESS] / 255.0
            await self._lightpad.set_config({"glowIntensity": brightness_pct})
        elif ATTR_HS_COLOR in kwargs:
            hs_color = kwargs[ATTR_HS_COLOR]
            red, green, blue = color_util.color_hs_to_RGB(*hs_color)
            await self._lightpad.set_glow_color(red, green, blue, 0)
        else:
            await self._lightpad.set_config({"glowEnabled": True})

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness_pct = kwargs[ATTR_BRIGHTNESS] / 255.0
            await self._lightpad.set_config({"glowIntensity": brightness_pct})
        else:
            await self._lightpad.set_config({"glowEnabled": False})
