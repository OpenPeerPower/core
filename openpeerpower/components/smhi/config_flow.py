"""Config flow to configure SMHI component."""
from __future__ import annotations

from typing import Any

from smhi.smhi_lib import Smhi, SmhiForecastException
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.data_entry_flow import FlowResult
from openpeerpower.helpers import aiohttp_client
import openpeerpower.helpers.config_validation as cv
from openpeerpower.util import slugify

from .const import DOMAIN, HOME_LOCATION_NAME


@callback
def smhi_locations(opp: OpenPeerPower) -> set[str]:
    """Return configurations of SMHI component."""
    return {
        slugify(entry.data[CONF_NAME])
        for entry in opp.config_entries.async_entries(DOMAIN)
    }


class SmhiFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SMHI component."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize SMHI forecast configuration flow."""
        self._errors: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            is_ok = await self._check_location(
                user_input[CONF_LONGITUDE], user_input[CONF_LATITUDE]
            )
            if is_ok:
                name = slugify(user_input[CONF_NAME])
                if not self._name_in_configuration_exists(name):
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], data=user_input
                    )

                self._errors[CONF_NAME] = "name_exists"
            else:
                self._errors["base"] = "wrong_location"

        # If opp.config has the location set and is a valid coordinate the
        # default location is set as default values in the form
        if not smhi_locations(self.opp) and await self._openpeerpower_location_exists():
            return await self._show_config_form(
                name=HOME_LOCATION_NAME,
                latitude=self.opp.config.latitude,
                longitude=self.opp.config.longitude,
            )

        return await self._show_config_form()

    async def _openpeerpower_location_exists(self) -> bool:
        """Return true if default location is set and is valid."""
        # Return true if valid location
        return (
            self.opp.config.latitude != 0.0
            and self.opp.config.longitude != 0.0
            and await self._check_location(
                self.opp.config.longitude, self.opp.config.latitude
            )
        )

    def _name_in_configuration_exists(self, name: str) -> bool:
        """Return True if name exists in configuration."""
        return name in smhi_locations(self.opp)

    async def _show_config_form(
        self,
        name: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> FlowResult:
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=name): str,
                    vol.Required(CONF_LATITUDE, default=latitude): cv.latitude,
                    vol.Required(CONF_LONGITUDE, default=longitude): cv.longitude,
                }
            ),
            errors=self._errors,
        )

    async def _check_location(self, longitude: float, latitude: float) -> bool:
        """Return true if location is ok."""
        try:
            session = aiohttp_client.async_get_clientsession(self.opp)
            smhi_api = Smhi(longitude, latitude, session=session)

            await smhi_api.async_get_forecast()

            return True
        except SmhiForecastException:
            # The API will throw an exception if faulty location
            pass

        return False
