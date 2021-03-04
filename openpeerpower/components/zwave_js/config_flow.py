"""Config flow for Z-Wave JS integration."""
import asyncio
import logging
from typing import Any, Dict, Optional, cast

import aiohttp
from async_timeout import timeout
import voluptuous as vol
from zwave_js_server.version import VersionInfo, get_server_version

from openpeerpower import config_entries, exceptions
from openpeerpower.components.oppio import is_oppio
from openpeerpower.const import CONF_URL
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.data_entry_flow import AbortFlow
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .addon import AddonError, AddonManager, get_addon_manager
from .const import (  # pylint:disable=unused-import
    CONF_ADDON_DEVICE,
    CONF_ADDON_NETWORK_KEY,
    CONF_INTEGRATION_CREATED_ADDON,
    CONF_NETWORK_KEY,
    CONF_USB_PATH,
    CONF_USE_ADDON,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_URL = "ws://localhost:3000"
TITLE = "Z-Wave JS"

ADDON_SETUP_TIMEOUT = 5
ADDON_SETUP_TIMEOUT_ROUNDS = 4
SERVER_VERSION_TIMEOUT = 10

ON_SUPERVISOR_SCHEMA = vol.Schema({vol.Optional(CONF_USE_ADDON, default=True): bool})
STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_URL, default=DEFAULT_URL): str})


async def validate_input(opp: OpenPeerPower, user_input: dict) -> VersionInfo:
    """Validate if the user input allows us to connect."""
    ws_address = user_input[CONF_URL]

    if not ws_address.startswith(("ws://", "wss://")):
        raise InvalidInput("invalid_ws_url")

    try:
        return await async_get_version_info(opp, ws_address)
    except CannotConnect as err:
        raise InvalidInput("cannot_connect") from err


async def async_get_version_info(opp: OpenPeerPower, ws_address: str) -> VersionInfo:
    """Return Z-Wave JS version info."""
    try:
        async with timeout(SERVER_VERSION_TIMEOUT):
            version_info: VersionInfo = await get_server_version(
                ws_address, async_get_clientsession(opp)
            )
    except (asyncio.TimeoutError, aiohttp.ClientError) as err:
        # We don't want to spam the log if the add-on isn't started
        # or takes a long time to start.
        _LOGGER.debug("Failed to connect to Z-Wave JS server: %s", err)
        raise CannotConnect from err

    return version_info


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Z-Wave JS."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self) -> None:
        """Set up flow instance."""
        self.network_key: Optional[str] = None
        self.usb_path: Optional[str] = None
        self.use_addon = False
        self.ws_address: Optional[str] = None
        # If we install the add-on we should uninstall it on entry remove.
        self.integration_created_addon = False
        self.install_task: Optional[asyncio.Task] = None
        self.start_task: Optional[asyncio.Task] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        assert self.opp  # typing
        if is_oppio(self.opp):  # type: ignore  # no-untyped-call
            return await self.async_step_on_supervisor()

        return await self.async_step_manual()

    async def async_step_manual(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle a manual configuration."""
        if user_input is None:
            return self.async_show_form(
                step_id="manual", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            version_info = await validate_input(self.opp, user_input)
        except InvalidInput as err:
            errors["base"] = err.error
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(
                version_info.home_id, raise_on_progress=False
            )
            self._abort_if_unique_id_configured(user_input)
            self.ws_address = user_input[CONF_URL]
            return self._async_create_entry_from_vars()

        return self.async_show_form(
            step_id="manual", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_oppio(  # type: ignore # override
        self, discovery_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Receive configuration from add-on discovery info.

        This flow is triggered by the Z-Wave JS add-on.
        """
        self.ws_address = f"ws://{discovery_info['host']}:{discovery_info['port']}"
        try:
            version_info = await async_get_version_info(self.opp, self.ws_address)
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(version_info.home_id)
        self._abort_if_unique_id_configured(updates={CONF_URL: self.ws_address})

        return await self.async_step_oppio_confirm()

    async def async_step_oppio_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Confirm the add-on discovery."""
        if user_input is not None:
            return await self.async_step_on_supervisor(
                user_input={CONF_USE_ADDON: True}
            )

        return self.async_show_form(step_id="oppio_confirm")

    @callback
    def _async_create_entry_from_vars(self) -> Dict[str, Any]:
        """Return a config entry for the flow."""
        return self.async_create_entry(
            title=TITLE,
            data={
                CONF_URL: self.ws_address,
                CONF_USB_PATH: self.usb_path,
                CONF_NETWORK_KEY: self.network_key,
                CONF_USE_ADDON: self.use_addon,
                CONF_INTEGRATION_CREATED_ADDON: self.integration_created_addon,
            },
        )

    async def async_step_on_supervisor(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle logic when on Supervisor host."""
        # Only one entry with Supervisor add-on support is allowed.
        for entry in self.opp.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_USE_ADDON):
                return await self.async_step_manual()

        if user_input is None:
            return self.async_show_form(
                step_id="on_supervisor", data_schema=ON_SUPERVISOR_SCHEMA
            )
        if not user_input[CONF_USE_ADDON]:
            return await self.async_step_manual()

        self.use_addon = True

        if await self._async_is_addon_running():
            addon_config = await self._async_get_addon_config()
            self.usb_path = addon_config[CONF_ADDON_DEVICE]
            self.network_key = addon_config.get(CONF_ADDON_NETWORK_KEY, "")
            return await self.async_step_finish_addon_setup()

        if await self._async_is_addon_installed():
            return await self.async_step_configure_addon()

        return await self.async_step_install_addon()

    async def async_step_install_addon(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Install Z-Wave JS add-on."""
        if not self.install_task:
            self.install_task = self.opp.async_create_task(self._async_install_addon())
            return self.async_show_progress(
                step_id="install_addon", progress_action="install_addon"
            )

        try:
            await self.install_task
        except AddonError as err:
            _LOGGER.error("Failed to install Z-Wave JS add-on: %s", err)
            return self.async_show_progress_done(next_step_id="install_failed")

        self.integration_created_addon = True

        return self.async_show_progress_done(next_step_id="configure_addon")

    async def async_step_install_failed(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add-on installation failed."""
        return self.async_abort(reason="addon_install_failed")

    async def async_step_configure_addon(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ask for config for Z-Wave JS add-on."""
        addon_config = await self._async_get_addon_config()

        errors: Dict[str, str] = {}

        if user_input is not None:
            self.network_key = user_input[CONF_NETWORK_KEY]
            self.usb_path = user_input[CONF_USB_PATH]

            new_addon_config = {
                CONF_ADDON_DEVICE: self.usb_path,
                CONF_ADDON_NETWORK_KEY: self.network_key,
            }

            if new_addon_config != addon_config:
                await self._async_set_addon_config(new_addon_config)

            return await self.async_step_start_addon()

        usb_path = addon_config.get(CONF_ADDON_DEVICE, self.usb_path or "")
        network_key = addon_config.get(CONF_ADDON_NETWORK_KEY, self.network_key or "")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USB_PATH, default=usb_path): str,
                vol.Optional(CONF_NETWORK_KEY, default=network_key): str,
            }
        )

        return self.async_show_form(
            step_id="configure_addon", data_schema=data_schema, errors=errors
        )

    async def async_step_start_addon(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start Z-Wave JS add-on."""
        assert self.opp
        if not self.start_task:
            self.start_task = self.opp.async_create_task(self._async_start_addon())
            return self.async_show_progress(
                step_id="start_addon", progress_action="start_addon"
            )

        try:
            await self.start_task
        except (CannotConnect, AddonError) as err:
            _LOGGER.error("Failed to start Z-Wave JS add-on: %s", err)
            return self.async_show_progress_done(next_step_id="start_failed")

        return self.async_show_progress_done(next_step_id="finish_addon_setup")

    async def async_step_start_failed(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add-on start failed."""
        return self.async_abort(reason="addon_start_failed")

    async def _async_start_addon(self) -> None:
        """Start the Z-Wave JS add-on."""
        assert self.opp
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            await addon_manager.async_start_addon()
            # Sleep some seconds to let the add-on start properly before connecting.
            for _ in range(ADDON_SETUP_TIMEOUT_ROUNDS):
                await asyncio.sleep(ADDON_SETUP_TIMEOUT)
                try:
                    if not self.ws_address:
                        discovery_info = await self._async_get_addon_discovery_info()
                        self.ws_address = (
                            f"ws://{discovery_info['host']}:{discovery_info['port']}"
                        )
                    await async_get_version_info(self.opp, self.ws_address)
                except (AbortFlow, CannotConnect) as err:
                    _LOGGER.debug(
                        "Add-on not ready yet, waiting %s seconds: %s",
                        ADDON_SETUP_TIMEOUT,
                        err,
                    )
                else:
                    break
            else:
                raise CannotConnect("Failed to start add-on: timeout")
        finally:
            # Continue the flow after show progress when the task is done.
            self.opp.async_create_task(
                self.opp.config_entries.flow.async_configure(flow_id=self.flow_id)
            )

    async def async_step_finish_addon_setup(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare info needed to complete the config entry.

        Get add-on discovery info and server version info.
        Set unique id and abort if already configured.
        """
        assert self.opp
        if not self.ws_address:
            discovery_info = await self._async_get_addon_discovery_info()
            self.ws_address = f"ws://{discovery_info['host']}:{discovery_info['port']}"

        if not self.unique_id:
            try:
                version_info = await async_get_version_info(self.opp, self.ws_address)
            except CannotConnect as err:
                raise AbortFlow("cannot_connect") from err
            await self.async_set_unique_id(
                version_info.home_id, raise_on_progress=False
            )

        self._abort_if_unique_id_configured()
        return self._async_create_entry_from_vars()

    async def _async_get_addon_info(self) -> dict:
        """Return and cache Z-Wave JS add-on info."""
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            addon_info: dict = await addon_manager.async_get_addon_info()
        except AddonError as err:
            _LOGGER.error("Failed to get Z-Wave JS add-on info: %s", err)
            raise AbortFlow("addon_info_failed") from err

        return addon_info

    async def _async_is_addon_running(self) -> bool:
        """Return True if Z-Wave JS add-on is running."""
        addon_info = await self._async_get_addon_info()
        return bool(addon_info["state"] == "started")

    async def _async_is_addon_installed(self) -> bool:
        """Return True if Z-Wave JS add-on is installed."""
        addon_info = await self._async_get_addon_info()
        return addon_info["version"] is not None

    async def _async_get_addon_config(self) -> dict:
        """Get Z-Wave JS add-on config."""
        addon_info = await self._async_get_addon_info()
        return cast(dict, addon_info["options"])

    async def _async_set_addon_config(self, config: dict) -> None:
        """Set Z-Wave JS add-on config."""
        options = {"options": config}
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            await addon_manager.async_set_addon_options(options)
        except AddonError as err:
            _LOGGER.error("Failed to set Z-Wave JS add-on config: %s", err)
            raise AbortFlow("addon_set_config_failed") from err

    async def _async_install_addon(self) -> None:
        """Install the Z-Wave JS add-on."""
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            await addon_manager.async_install_addon()
        finally:
            # Continue the flow after show progress when the task is done.
            self.opp.async_create_task(
                self.opp.config_entries.flow.async_configure(flow_id=self.flow_id)
            )

    async def _async_get_addon_discovery_info(self) -> dict:
        """Return add-on discovery info."""
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            discovery_info_config = await addon_manager.async_get_addon_discovery_info()
        except AddonError as err:
            _LOGGER.error("Failed to get Z-Wave JS add-on discovery info: %s", err)
            raise AbortFlow("addon_get_discovery_info_failed") from err

        return discovery_info_config


class CannotConnect(exceptions.OpenPeerPowerError):
    """Indicate connection error."""


class InvalidInput(exceptions.OpenPeerPowerError):
    """Error to indicate input data is invalid."""

    def __init__(self, error: str) -> None:
        """Initialize error."""
        super().__init__()
        self.error = error
