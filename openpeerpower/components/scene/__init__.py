"""Allow users to set and activate scenes."""
import functools as ft
import importlib
import logging
from typing import Any, Optional

import voluptuous as vol

from openpeerpower.components.light import ATTR_TRANSITION
from openpeerpower.const import CONF_PLATFORM, SERVICE_TURN_ON
from openpeerpower.core import DOMAIN as HA_DOMAIN
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.entity_component import EntityComponent

# mypy: allow-untyped-defs, no-check-untyped-defs

DOMAIN = "scene"
STATE = "scening"
STATES = "states"


def _opp_domain_validator(config):
    """Validate platform in config for openpeerpower domain."""
    if CONF_PLATFORM not in config:
        config = {CONF_PLATFORM: HA_DOMAIN, STATES: config}

    return config


def _platform_validator(config):
    """Validate it is a valid  platform."""
    try:
        platform = importlib.import_module(
            ".{}".format(config[CONF_PLATFORM]), __name__
        )
    except ImportError:
        try:
            platform = importlib.import_module(
                "openpeerpower.components.{}.scene".format(config[CONF_PLATFORM])
            )
        except ImportError:
            raise vol.Invalid("Invalid platform specified") from None

    if not hasattr(platform, "PLATFORM_SCHEMA"):
        return config

    return platform.PLATFORM_SCHEMA(config)


PLATFORM_SCHEMA = vol.Schema(
    vol.All(
        _opp_domain_validator,
        vol.Schema({vol.Required(CONF_PLATFORM): str}, extra=vol.ALLOW_EXTRA),
        _platform_validator,
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the scenes."""
    component = opp.data[DOMAIN] = EntityComponent(
        logging.getLogger(__name__), DOMAIN, opp
    )

    await component.async_setup(config)
    # Ensure Open Peer Power platform always loaded.
    await component.async_setup_platform(HA_DOMAIN, {"platform": HA_DOMAIN, STATES: []})
    component.async_register_entity_service(
        SERVICE_TURN_ON,
        {ATTR_TRANSITION: vol.All(vol.Coerce(float), vol.Clamp(min=0, max=6553))},
        "async_activate",
    )

    return True


async def async_setup_entry(opp, entry):
    """Set up a config entry."""
    return await opp.data[DOMAIN].async_setup_entry(entry)


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.data[DOMAIN].async_unload_entry(entry)


class Scene(Entity):
    """A scene is a group of entities and the states we want them to be."""

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def state(self) -> Optional[str]:
        """Return the state of the scene."""
        return STATE

    def activate(self, **kwargs: Any) -> None:
        """Activate scene. Try to get entities into requested state."""
        raise NotImplementedError()

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate scene. Try to get entities into requested state."""
        assert self.opp
        task = self.opp.async_add_job(ft.partial(self.activate, **kwargs))
        if task:
            await task
