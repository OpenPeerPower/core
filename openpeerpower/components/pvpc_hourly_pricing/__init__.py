"""The pvpc_hourly_pricing integration to collect Spain official electric prices."""
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv

from .const import ATTR_TARIFF, DEFAULT_NAME, DEFAULT_TARIFF, DOMAIN, PLATFORM, TARIFFS

UI_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(ATTR_TARIFF, default=DEFAULT_TARIFF): vol.In(TARIFFS),
    }
)
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: cv.ensure_list(UI_CONFIG_SCHEMA)}, extra=vol.ALLOW_EXTRA
)


async def async_setup(opp: OpenPeerPower, config: dict):
    """
    Set up the electricity price sensor from configuration.yaml.

    ```yaml
    pvpc_hourly_pricing:
      - name: PVPC manual ve
        tariff: electric_car
      - name: PVPC manual nocturna
        tariff: discrimination
        timeout: 3
    ```
    """
    for conf in config.get(DOMAIN, []):
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, data=conf, context={"source": config_entries.SOURCE_IMPORT}
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: config_entries.ConfigEntry):
    """Set up pvpc hourly pricing from a config entry."""
    opp.async_create_task(opp.config_entries.async_forward_entry_setup(entry, PLATFORM))

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: config_entries.ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_forward_entry_unload(entry, PLATFORM)
