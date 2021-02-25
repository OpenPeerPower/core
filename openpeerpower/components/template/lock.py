"""Support for locks which integrates with other components."""
import voluptuous as vol

from openpeerpower.components.lock import PLATFORM_SCHEMA, LockEntity
from openpeerpower.const import (
    CONF_NAME,
    CONF_OPTIMISTIC,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
    STATE_LOCKED,
    STATE_ON,
)
from openpeerpower.core import callback
from openpeerpower.exceptions import TemplateError
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.reload import async_setup_reload_service
from openpeerpower.helpers.script import Script

from .const import CONF_AVAILABILITY_TEMPLATE, DOMAIN, PLATFORMS
from .template_entity import TemplateEntity

CONF_LOCK = "lock"
CONF_UNLOCK = "unlock"

DEFAULT_NAME = "Template Lock"
DEFAULT_OPTIMISTIC = False

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_LOCK): cv.SCRIPT_SCHEMA,
        vol.Required(CONF_UNLOCK): cv.SCRIPT_SCHEMA,
        vol.Required(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_AVAILABILITY_TEMPLATE): cv.template,
        vol.Optional(CONF_OPTIMISTIC, default=DEFAULT_OPTIMISTIC): cv.boolean,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


async def _async_create_entities(opp, config):
    """Create the Template lock."""
    device = config.get(CONF_NAME)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    availability_template = config.get(CONF_AVAILABILITY_TEMPLATE)

    return [
        TemplateLock(
            opp,
            device,
            value_template,
            availability_template,
            config.get(CONF_LOCK),
            config.get(CONF_UNLOCK),
            config.get(CONF_OPTIMISTIC),
            config.get(CONF_UNIQUE_ID),
        )
    ]


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the template lock."""
    await async_setup_reload_service(opp, DOMAIN, PLATFORMS)
    async_add_entities(await _async_create_entities(opp, config))


class TemplateLock(TemplateEntity, LockEntity):
    """Representation of a template lock."""

    def __init__(
        self,
        opp,
        name,
        value_template,
        availability_template,
        command_lock,
        command_unlock,
        optimistic,
        unique_id,
    ):
        """Initialize the lock."""
        super().__init__(availability_template=availability_template)
        self._state = None
        self._name = name
        self._state_template = value_template
        domain = __name__.split(".")[-2]
        self._command_lock = Script(opp, command_lock, name, domain)
        self._command_unlock = Script(opp, command_unlock, name, domain)
        self._optimistic = optimistic
        self._unique_id = unique_id

    @property
    def assumed_state(self):
        """Return true if we do optimistic updates."""
        return self._optimistic

    @property
    def name(self):
        """Return the name of the lock."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id of this lock."""
        return self._unique_id

    @property
    def is_locked(self):
        """Return true if lock is locked."""
        return self._state

    @callback
    def _update_state(self, result):
        super()._update_state(result)
        if isinstance(result, TemplateError):
            self._state = None
            return

        if isinstance(result, bool):
            self._state = result
            return

        if isinstance(result, str):
            self._state = result.lower() in ("true", STATE_ON, STATE_LOCKED)
            return

        self._state = False

    async def async_added_to_opp(self):
        """Register callbacks."""
        self.add_template_attribute(
            "_state", self._state_template, None, self._update_state
        )
        await super().async_added_to_opp()

    async def async_lock(self, **kwargs):
        """Lock the device."""
        if self._optimistic:
            self._state = True
            self.async_write_op_state()
        await self._command_lock.async_run(context=self._context)

    async def async_unlock(self, **kwargs):
        """Unlock the device."""
        if self._optimistic:
            self._state = False
            self.async_write_op_state()
        await self._command_unlock.async_run(context=self._context)
