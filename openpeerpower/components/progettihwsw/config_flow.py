"""Config flow for ProgettiHWSW Automation integration."""

from ProgettiHWSW.ProgettiHWSWAPI import ProgettiHWSWAPI
import voluptuous as vol

from openpeerpower import config_entries, core, exceptions

from .const import DOMAIN

DATA_SCHEMA = vol.Schema(
    {vol.Required("host"): str, vol.Required("port", default=80): int}
)


async def validate_input(opp: core.OpenPeerPower, data):
    """Validate the user host input."""

    confs = opp.config_entries.async_entries(DOMAIN)
    same_entries = [
        True
        for entry in confs
        if entry.data.get("host") == data["host"]
        and entry.data.get("port") == data["port"]
    ]

    if same_entries:
        raise ExistingEntry

    api_instance = ProgettiHWSWAPI(f'{data["host"]}:{data["port"]}')
    is_valid = await api_instance.check_board()

    if not is_valid:
        raise CannotConnect

    return {
        "title": is_valid["title"],
        "relay_count": is_valid["relay_count"],
        "input_count": is_valid["input_count"],
        "is_old": is_valid["is_old"],
    }


class ProgettiHWSWConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ProgettiHWSW Automation."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize class variables."""
        self.s1_in = None

    async def async_step_relay_modes(self, user_input=None):
        """Manage relay modes step."""
        errors = {}
        if user_input is not None:

            whole_data = user_input
            whole_data.update(self.s1_in)

            return self.async_create_entry(title=whole_data["title"], data=whole_data)

        relay_modes_schema = {}
        for i in range(1, int(self.s1_in["relay_count"]) + 1):
            relay_modes_schema[
                vol.Required(f"relay_{str(i)}", default="bistable")
            ] = vol.In(
                {
                    "bistable": "Bistable (ON/OFF Mode)",
                    "monostable": "Monostable (Timer Mode)",
                }
            )

        return self.async_show_form(
            step_id="relay_modes",
            data_schema=vol.Schema(relay_modes_schema),
            errors=errors,
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:

            try:
                info = await validate_input(self.opp, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ExistingEntry:
                return self.async_abort(reason="already_configured")
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
            else:
                user_input.update(info)
                self.s1_in = user_input
                return await self.async_step_relay_modes()

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot identify host."""


class WrongInfo(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot validate relay modes input."""


class ExistingEntry(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot validate relay modes input."""
