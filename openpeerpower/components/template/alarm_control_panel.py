"""Support for Template alarm control panels."""
import logging

import voluptuous as vol

from openpeerpower.components.alarm_control_panel import (
    ENTITY_ID_FORMAT,
    FORMAT_NUMBER,
    PLATFORM_SCHEMA,
    AlarmControlPanelEntity,
)
from openpeerpower.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_NIGHT,
)
from openpeerpower.const import (
    ATTR_CODE,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    STATE_UNAVAILABLE,
)
from openpeerpower.core import callback
from openpeerpower.exceptions import TemplateError
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import async_generate_entity_id
from openpeerpower.helpers.reload import async_setup_reload_service
from openpeerpower.helpers.script import Script

from .const import DOMAIN, PLATFORMS
from .template_entity import TemplateEntity

_LOGGER = logging.getLogger(__name__)
_VALID_STATES = [
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    STATE_UNAVAILABLE,
]

CONF_ARM_AWAY_ACTION = "arm_away"
CONF_ARM_HOME_ACTION = "arm_home"
CONF_ARM_NIGHT_ACTION = "arm_night"
CONF_DISARM_ACTION = "disarm"
CONF_ALARM_CONTROL_PANELS = "panels"
CONF_CODE_ARM_REQUIRED = "code_arm_required"

ALARM_CONTROL_PANEL_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_DISARM_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_ARM_AWAY_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_ARM_HOME_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_ARM_NIGHT_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_CODE_ARM_REQUIRED, default=True): cv.boolean,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ALARM_CONTROL_PANELS): cv.schema_with_slug_keys(
            ALARM_CONTROL_PANEL_SCHEMA
        ),
    }
)


async def _async_create_entities(opp, config):
    """Create Template Alarm Control Panels."""
    alarm_control_panels = []

    for device, device_config in config[CONF_ALARM_CONTROL_PANELS].items():
        name = device_config.get(CONF_NAME, device)
        state_template = device_config.get(CONF_VALUE_TEMPLATE)
        disarm_action = device_config.get(CONF_DISARM_ACTION)
        arm_away_action = device_config.get(CONF_ARM_AWAY_ACTION)
        arm_home_action = device_config.get(CONF_ARM_HOME_ACTION)
        arm_night_action = device_config.get(CONF_ARM_NIGHT_ACTION)
        code_arm_required = device_config[CONF_CODE_ARM_REQUIRED]
        unique_id = device_config.get(CONF_UNIQUE_ID)

        alarm_control_panels.append(
            AlarmControlPanelTemplate(
                opp,
                device,
                name,
                state_template,
                disarm_action,
                arm_away_action,
                arm_home_action,
                arm_night_action,
                code_arm_required,
                unique_id,
            )
        )

    return alarm_control_panels


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Template Alarm Control Panels."""
    await async_setup_reload_service(opp, DOMAIN, PLATFORMS)
    async_add_entities(await _async_create_entities(opp, config))


class AlarmControlPanelTemplate(TemplateEntity, AlarmControlPanelEntity):
    """Representation of a templated Alarm Control Panel."""

    def __init__(
        self,
        opp,
        device_id,
        name,
        state_template,
        disarm_action,
        arm_away_action,
        arm_home_action,
        arm_night_action,
        code_arm_required,
        unique_id,
    ):
        """Initialize the panel."""
        super().__init__()
        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, device_id, opp=opp)
        self._name = name
        self._template = state_template
        self._disarm_script = None
        self._code_arm_required = code_arm_required
        domain = __name__.split(".")[-2]
        if disarm_action is not None:
            self._disarm_script = Script(opp, disarm_action, name, domain)
        self._arm_away_script = None
        if arm_away_action is not None:
            self._arm_away_script = Script(opp, arm_away_action, name, domain)
        self._arm_home_script = None
        if arm_home_action is not None:
            self._arm_home_script = Script(opp, arm_home_action, name, domain)
        self._arm_night_script = None
        if arm_night_action is not None:
            self._arm_night_script = Script(opp, arm_night_action, name, domain)

        self._state = None
        self._unique_id = unique_id

    @property
    def name(self):
        """Return the display name of this alarm control panel."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id of this alarm control panel."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = 0
        if self._arm_night_script is not None:
            supported_features = supported_features | SUPPORT_ALARM_ARM_NIGHT

        if self._arm_home_script is not None:
            supported_features = supported_features | SUPPORT_ALARM_ARM_HOME

        if self._arm_away_script is not None:
            supported_features = supported_features | SUPPORT_ALARM_ARM_AWAY

        return supported_features

    @property
    def code_format(self):
        """Return one or more digits/characters."""
        return FORMAT_NUMBER

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        return self._code_arm_required

    @callback
    def _update_state(self, result):
        if isinstance(result, TemplateError):
            self._state = None
            return

        # Validate state
        if result in _VALID_STATES:
            self._state = result
            _LOGGER.debug("Valid state - %s", result)
            return

        _LOGGER.error(
            "Received invalid alarm panel state: %s. Expected: %s",
            result,
            ", ".join(_VALID_STATES),
        )
        self._state = None

    async def async_added_to_opp(self):
        """Register callbacks."""
        if self._template:
            self.add_template_attribute(
                "_state", self._template, None, self._update_state
            )
        await super().async_added_to_opp()

    async def _async_alarm_arm(self, state, script=None, code=None):
        """Arm the panel to specified state with supplied script."""
        optimistic_set = False

        if self._template is None:
            self._state = state
            optimistic_set = True

        if script is not None:
            await script.async_run({ATTR_CODE: code}, context=self._context)
        else:
            _LOGGER.error("No script action defined for %s", state)

        if optimistic_set:
            self.async_write_op_state()

    async def async_alarm_arm_away(self, code=None):
        """Arm the panel to Away."""
        await self._async_alarm_arm(
            STATE_ALARM_ARMED_AWAY, script=self._arm_away_script, code=code
        )

    async def async_alarm_arm_home(self, code=None):
        """Arm the panel to Home."""
        await self._async_alarm_arm(
            STATE_ALARM_ARMED_HOME, script=self._arm_home_script, code=code
        )

    async def async_alarm_arm_night(self, code=None):
        """Arm the panel to Night."""
        await self._async_alarm_arm(
            STATE_ALARM_ARMED_NIGHT, script=self._arm_night_script, code=code
        )

    async def async_alarm_disarm(self, code=None):
        """Disarm the panel."""
        await self._async_alarm_arm(
            STATE_ALARM_DISARMED, script=self._disarm_script, code=code
        )
