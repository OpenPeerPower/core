"""Config flow for Z-Wave JS integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from async_timeout import timeout
import voluptuous as vol
from zwave_js_server.version import VersionInfo, get_server_version

from openpeerpower import config_entries, exceptions
from openpeerpower.components.oppio import is_oppio
from openpeerpower.const import CONF_URL
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.data_entry_flow import AbortFlow, FlowResult
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .addon import AddonError, AddonInfo, AddonManager, AddonState, get_addon_manager
from .const import (
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

    def __init__(self) -> None:
        """Set up flow instance."""
        self.network_key: str | None = None
        self.usb_path: str | None = None
        self.use_addon = False
        self.ws_address: str | None = None
        # If we install the add-on we should uninstall it on entry remove.
        self.integration_created_addon = False
        self.install_task: asyncio.Task | None = None
        self.start_task: asyncio.Task | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if is_oppio(self.opp):
            return await self.async_step_on_supervisor()

        return await self.async_step_manual()

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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
            # Make sure we disable any add-on handling
            # if the controller is reconfigured in a manual step.
            self._abort_if_unique_id_configured(
                updates={
                    **user_input,
                    CONF_USE_ADDON: False,
                    CONF_INTEGRATION_CREATED_ADDON: False,
                }
            )
            self.ws_address = user_input[CONF_URL]
            return self._async_create_entry_from_vars()

        return self.async_show_form(
            step_id="manual", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_oppio(self, discovery_info: dict[str, Any]) -> FlowResult:
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
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the add-on discovery."""
        if user_input is not None:
            return await self.async_step_on_supervisor(
                user_input={CONF_USE_ADDON: True}
            )

        return self.async_show_form(step_id="oppio_confirm")

    @callback
    def _async_create_entry_from_vars(self) -> FlowResult:
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
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle logic when on Supervisor host."""
        if user_input is None:
            return self.async_show_form(
                step_id="on_supervisor", data_schema=ON_SUPERVISOR_SCHEMA
            )
        if not user_input[CONF_USE_ADDON]:
            return await self.async_step_manual()

        self.use_addon = True

        addon_info = await self._async_get_addon_info()

        if addon_info.state == AddonState.RUNNING:
            addon_config = addon_info.options
            self.usb_path = addon_config[CONF_ADDON_DEVICE]
            self.network_key = addon_config.get(CONF_ADDON_NETWORK_KEY, "")
            return await self.async_step_finish_addon_setup()

        if addon_info.state == AddonState.NOT_RUNNING:
            return await self.async_step_configure_addon()

        return await self.async_step_install_addon()

    async def async_step_install_addon(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Install Z-Wave JS add-on."""
        if not self.install_task:
            self.install_task = self.opp.async_create_task(self._async_install_addon())
            return self.async_show_progress(
                step_id="install_addon", progress_action="install_addon"
            )

        try:
            await self.install_task
        except AddonError as err:
            _LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="install_failed")

        self.integration_created_addon = True

        return self.async_show_progress_done(next_step_id="configure_addon")

    async def async_step_install_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add-on installation failed."""
        return self.async_abort(reason="addon_install_failed")

    async def async_step_configure_addon(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask for config for Z-Wave JS add-on."""
        addon_info = await self._async_get_addon_info()
        addon_config = addon_info.options

        errors: dict[str, str] = {}

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
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Start Z-Wave JS add-on."""
        if not self.start_task:
            self.start_task = self.opp.async_create_task(self._async_start_addon())
            return self.async_show_progress(
                step_id="start_addon", progress_action="start_addon"
            )

        try:
            await self.start_task
        except (CannotConnect, AddonError) as err:
            _LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="start_failed")

        return self.async_show_progress_done(next_step_id="finish_addon_setup")

    async def async_step_start_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add-on start failed."""
        return self.async_abort(reason="addon_start_failed")

    async def _async_start_addon(self) -> None:
        """Start the Z-Wave JS add-on."""
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            await addon_manager.async_schedule_start_addon()
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
                raise CannotConnect("Failed to start Z-Wave JS add-on: timeout")
        finally:
            # Continue the flow after show progress when the task is done.
            self.opp.async_create_task(
                self.opp.config_entries.flow.async_configure(flow_id=self.flow_id)
            )

    async def async_step_finish_addon_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Prepare info needed to complete the config entry.

        Get add-on discovery info and server version info.
        Set unique id and abort if already configured.
        """
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

        self._abort_if_unique_id_configured(
            updates={
                CONF_URL: self.ws_address,
                CONF_USB_PATH: self.usb_path,
                CONF_NETWORK_KEY: self.network_key,
            }
        )
        return self._async_create_entry_from_vars()

    async def _async_get_addon_info(self) -> AddonInfo:
        """Return and cache Z-Wave JS add-on info."""
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            addon_info: AddonInfo = await addon_manager.async_get_addon_info()
        except AddonError as err:
            _LOGGER.error(err)
            raise AbortFlow("addon_info_failed") from err

        return addon_info

    async def _async_set_addon_config(self, config: dict) -> None:
        """Set Z-Wave JS add-on config."""
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            await addon_manager.async_set_addon_options(config)
        except AddonError as err:
            _LOGGER.error(err)
            raise AbortFlow("addon_set_config_failed") from err

    async def _async_install_addon(self) -> None:
        """Install the Z-Wave JS add-on."""
        addon_manager: AddonManager = get_addon_manager(self.opp)
        try:
            await addon_manager.async_schedule_install_addon()
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
            _LOGGER.error(err)
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
