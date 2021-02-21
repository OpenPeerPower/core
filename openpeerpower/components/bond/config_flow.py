"""Config flow for Bond integration."""
import logging
from typing import Any, Dict, Optional, Tuple

from aiohttp import ClientConnectionError, ClientResponseError
from bond_api import Bond
import voluptuous as vol

from openpeerpower import config_entries, exceptions
from openpeerpower.const import (
    CONF_ACCESS_TOKEN,
    CONF_HOST,
    CONF_NAME,
    HTTP_UNAUTHORIZED,
)

from .const import CONF_BOND_ID
from .const import DOMAIN  # pylint:disable=unused-import
from .utils import BondHub

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_USER = vol.Schema(
    {vol.Required(CONF_HOST): str, vol.Required(CONF_ACCESS_TOKEN): str}
)
DATA_SCHEMA_DISCOVERY = vol.Schema({vol.Required(CONF_ACCESS_TOKEN): str})


async def _validate_input(data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Validate the user input allows us to connect."""

    bond = Bond(data[CONF_HOST], data[CONF_ACCESS_TOKEN])
    try:
        hub = BondHub(bond)
        await hub.setup(max_devices=1)
    except ClientConnectionError as error:
        raise InputValidationError("cannot_connect") from error
    except ClientResponseError as error:
        if error.status == HTTP_UNAUTHORIZED:
            raise InputValidationError("invalid_auth") from error
        raise InputValidationError("unknown") from error
    except Exception as error:
        _LOGGER.exception("Unexpected exception")
        raise InputValidationError("unknown") from error

    # Return unique ID from the hub to be stored in the config entry.
    if not hub.bond_id:
        raise InputValidationError("old_firmware")

    return hub.bond_id, hub.name


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bond."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    _discovered: dict = None

    async def async_step_zeroconf(
        self, discovery_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle a flow initialized by zeroconf discovery."""
        name: str = discovery_info[CONF_NAME]
        host: str = discovery_info[CONF_HOST]
        bond_id = name.partition(".")[0]
        await self.async_set_unique_id(bond_id)
        self._abort_if_unique_id_configured({CONF_HOST: host})

        self._discovered = {
            CONF_HOST: host,
            CONF_BOND_ID: bond_id,
        }
        self.context.update({"title_placeholders": self._discovered})

        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle confirmation flow for discovered bond hub."""
        errors = {}
        if user_input is not None:
            data = user_input.copy()
            data[CONF_HOST] = self._discovered[CONF_HOST]
            try:
                return await self._try_create_entry(data)
            except InputValidationError as error:
                errors["base"] = error.base

        return self.async_show_form(
            step_id="confirm",
            data_schema=DATA_SCHEMA_DISCOVERY,
            errors=errors,
            description_placeholders=self._discovered,
        )

    async def async_step_user(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            try:
                return await self._try_create_entry(user_input)
            except InputValidationError as error:
                errors["base"] = error.base

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA_USER, errors=errors
        )

    async def _try_create_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        bond_id, name = await _validate_input(data)
        await self.async_set_unique_id(bond_id)
        self._abort_if_unique_id_configured()
        hub_name = name or bond_id
        return self.async_create_entry(title=hub_name, data=data)


class InputValidationError(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot proceed due to invalid input."""

    def __init__(self, base: str):
        """Initialize with error base."""
        super().__init__()
        self.base = base
