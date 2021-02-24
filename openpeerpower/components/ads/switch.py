"""Support for ADS switch platform."""
import voluptuous as vol

from openpeerpower.components.switch import PLATFORM_SCHEMA, SwitchEntity
from openpeerpower.const import CONF_NAME
import openpeerpower.helpers.config_validation as cv

from . import CONF_ADS_VAR, DATA_ADS, STATE_KEY_STATE, AdsEntity

DEFAULT_NAME = "ADS Switch"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up switch platform for ADS."""
    ads_hub = opp.data.get(DATA_ADS)

    name = config[CONF_NAME]
    ads_var = config[CONF_ADS_VAR]

    add_entities([AdsSwitch(ads_hub, name, ads_var)])


class AdsSwitch(AdsEntity, SwitchEntity):
    """Representation of an ADS switch device."""

    async def async_added_to_opp(self):
        """Register device notification."""
        await self.async_initialize_device(self._ads_var, self._ads_hub.PLCTYPE_BOOL)

    @property
    def is_on(self):
        """Return True if the entity is on."""
        return self._state_dict[STATE_KEY_STATE]

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._ads_hub.write_by_name(self._ads_var, True, self._ads_hub.PLCTYPE_BOOL)

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self._ads_hub.write_by_name(self._ads_var, False, self._ads_hub.PLCTYPE_BOOL)
