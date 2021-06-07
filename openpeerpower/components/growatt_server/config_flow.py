"""Config flow for growatt server integration."""
import growattServer
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import callback

from .const import CONF_PLANT_ID, DOMAIN


class GrowattServerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow class."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialise growatt server flow."""
        self.api = growattServer.GrowattApi()
        self.user_id = None
        self.data = {}

    @callback
    def _async_show_user_form(self, errors=None):
        """Show the form to the user."""
        data_schema = vol.Schema(
            {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the start of the config flow."""
        if not user_input:
            return self._async_show_user_form()

        login_response = await self.opp.async_add_executor_job(
            self.api.login, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
        )

        if not login_response["success"] and login_response["errCode"] == "102":
            return self._async_show_user_form({"base": "invalid_auth"})
        self.user_id = login_response["userId"]

        self.data = user_input
        return await self.async_step_plant()

    async def async_step_plant(self, user_input=None):
        """Handle adding a "plant" to Open Peer Power."""
        plant_info = await self.opp.async_add_executor_job(
            self.api.plant_list, self.user_id
        )

        if not plant_info["data"]:
            return self.async_abort(reason="no_plants")

        plants = {plant["plantId"]: plant["plantName"] for plant in plant_info["data"]}

        if user_input is None and len(plant_info["data"]) > 1:
            data_schema = vol.Schema({vol.Required(CONF_PLANT_ID): vol.In(plants)})

            return self.async_show_form(step_id="plant", data_schema=data_schema)

        if user_input is None and len(plant_info["data"]) == 1:
            user_input = {CONF_PLANT_ID: plant_info["data"][0]["plantId"]}

        user_input[CONF_NAME] = plants[user_input[CONF_PLANT_ID]]
        await self.async_set_unique_id(user_input[CONF_PLANT_ID])
        self._abort_if_unique_id_configured()
        self.data.update(user_input)
        return self.async_create_entry(title=self.data[CONF_NAME], data=self.data)

    async def async_step_import(self, import_data):
        """Migrate old yaml config to config flow."""
        return await self.async_step_user(import_data)
