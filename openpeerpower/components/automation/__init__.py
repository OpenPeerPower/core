"""Allow to set up simple automation rules via the config file."""
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Union, cast

import voluptuous as vol
from voluptuous.humanize import humanize_error

from openpeerpower.components import blueprint
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    CONF_ALIAS,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_ENTITY_ID,
    CONF_ID,
    CONF_MODE,
    CONF_PLATFORM,
    CONF_VARIABLES,
    CONF_ZONE,
    EVENT_OPENPEERPOWER_STARTED,
    SERVICE_RELOAD,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from openpeerpower.core import (
    Context,
    CoreState,
    OpenPeerPower,
    callback,
    split_entity_id,
)
from openpeerpower.exceptions import (
    ConditionError,
    ConditionErrorContainer,
    ConditionErrorIndex,
    OpenPeerPowerError,
)
from openpeerpower.helpers import condition, extract_domain_configs, template
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import ToggleEntity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.restore_state import RestoreEntity
from openpeerpower.helpers.script import (
    ATTR_CUR,
    ATTR_MAX,
    ATTR_MODE,
    CONF_MAX,
    CONF_MAX_EXCEEDED,
    Script,
)
from openpeerpower.helpers.script_variables import ScriptVariables
from openpeerpower.helpers.service import async_register_admin_service
from openpeerpower.helpers.trigger import async_initialize_triggers
from openpeerpower.helpers.typing import TemplateVarsType
from openpeerpower.loader import bind_opp
from openpeerpower.util.dt import parse_datetime

# Not used except by packages to check config structure
from .config import PLATFORM_SCHEMA  # noqa: F401
from .config import async_validate_config_item
from .const import (
    CONF_ACTION,
    CONF_INITIAL_STATE,
    CONF_TRIGGER,
    CONF_TRIGGER_VARIABLES,
    DEFAULT_INITIAL_STATE,
    DOMAIN,
    LOGGER,
)
from .helpers import async_get_blueprints

# mypy: allow-untyped-calls, allow-untyped-defs
# mypy: no-check-untyped-defs, no-warn-return-any

ENTITY_ID_FORMAT = DOMAIN + ".{}"


CONF_SKIP_CONDITION = "skip_condition"
CONF_STOP_ACTIONS = "stop_actions"
DEFAULT_STOP_ACTIONS = True

EVENT_AUTOMATION_RELOADED = "automation_reloaded"
EVENT_AUTOMATION_TRIGGERED = "automation_triggered"

ATTR_LAST_TRIGGERED = "last_triggered"
ATTR_SOURCE = "source"
ATTR_VARIABLES = "variables"
SERVICE_TRIGGER = "trigger"

AutomationActionType = Callable[[OpenPeerPower, TemplateVarsType], Awaitable[None]]


@bind_opp
def is_on(opp, entity_id):
    """
    Return true if specified automation entity_id is on.

    Async friendly.
    """
    return opp.states.is_state(entity_id, STATE_ON)


@callback
def automations_with_entity(opp: OpenPeerPower, entity_id: str) -> List[str]:
    """Return all automations that reference the entity."""
    if DOMAIN not in opp.data:
        return []

    component = opp.data[DOMAIN]

    return [
        automation_entity.entity_id
        for automation_entity in component.entities
        if entity_id in automation_entity.referenced_entities
    ]


@callback
def entities_in_automation(opp: OpenPeerPower, entity_id: str) -> List[str]:
    """Return all entities in a scene."""
    if DOMAIN not in opp.data:
        return []

    component = opp.data[DOMAIN]

    automation_entity = component.get_entity(entity_id)

    if automation_entity is None:
        return []

    return list(automation_entity.referenced_entities)


@callback
def automations_with_device(opp: OpenPeerPower, device_id: str) -> List[str]:
    """Return all automations that reference the device."""
    if DOMAIN not in opp.data:
        return []

    component = opp.data[DOMAIN]

    return [
        automation_entity.entity_id
        for automation_entity in component.entities
        if device_id in automation_entity.referenced_devices
    ]


@callback
def devices_in_automation(opp: OpenPeerPower, entity_id: str) -> List[str]:
    """Return all devices in a scene."""
    if DOMAIN not in opp.data:
        return []

    component = opp.data[DOMAIN]

    automation_entity = component.get_entity(entity_id)

    if automation_entity is None:
        return []

    return list(automation_entity.referenced_devices)


async def async_setup(opp, config):
    """Set up the automation."""
    opp.data[DOMAIN] = component = EntityComponent(LOGGER, DOMAIN, opp)

    # To register the automation blueprints
    async_get_blueprints(opp)

    if not await _async_process_config(opp, config, component):
        await async_get_blueprints(opp).async_populate()

    async def trigger_service_handler(entity, service_call):
        """Handle automation triggers."""
        await entity.async_trigger(
            service_call.data[ATTR_VARIABLES],
            skip_condition=service_call.data[CONF_SKIP_CONDITION],
            context=service_call.context,
        )

    component.async_register_entity_service(
        SERVICE_TRIGGER,
        {
            vol.Optional(ATTR_VARIABLES, default={}): dict,
            vol.Optional(CONF_SKIP_CONDITION, default=True): bool,
        },
        trigger_service_handler,
    )
    component.async_register_entity_service(SERVICE_TOGGLE, {}, "async_toggle")
    component.async_register_entity_service(SERVICE_TURN_ON, {}, "async_turn_on")
    component.async_register_entity_service(
        SERVICE_TURN_OFF,
        {vol.Optional(CONF_STOP_ACTIONS, default=DEFAULT_STOP_ACTIONS): cv.boolean},
        "async_turn_off",
    )

    async def reload_service_handler(service_call):
        """Remove all automations and load new ones from config."""
        conf = await component.async_prepare_reload()
        if conf is None:
            return
        async_get_blueprints(opp).async_reset_cache()
        await _async_process_config(opp, conf, component)
        opp.bus.async_fire(EVENT_AUTOMATION_RELOADED, context=service_call.context)

    async_register_admin_service(
        opp, DOMAIN, SERVICE_RELOAD, reload_service_handler, schema=vol.Schema({})
    )

    return True


class AutomationEntity(ToggleEntity, RestoreEntity):
    """Entity to show status of entity."""

    def __init__(
        self,
        automation_id,
        name,
        trigger_config,
        cond_func,
        action_script,
        initial_state,
        variables,
        trigger_variables,
    ):
        """Initialize an automation entity."""
        self._id = automation_id
        self._name = name
        self._trigger_config = trigger_config
        self._async_detach_triggers = None
        self._cond_func = cond_func
        self.action_script = action_script
        self.action_script.change_listener = self.async_write_op_state
        self._initial_state = initial_state
        self._is_enabled = False
        self._referenced_entities: Optional[Set[str]] = None
        self._referenced_devices: Optional[Set[str]] = None
        self._logger = LOGGER
        self._variables: ScriptVariables = variables
        self._trigger_variables: ScriptVariables = trigger_variables

    @property
    def name(self):
        """Name of the automation."""
        return self._name

    @property
    def unique_id(self):
        """Return unique ID."""
        return self._id

    @property
    def should_poll(self):
        """No polling needed for automation entities."""
        return False

    @property
    def state_attributes(self):
        """Return the entity state attributes."""
        attrs = {
            ATTR_LAST_TRIGGERED: self.action_script.last_triggered,
            ATTR_MODE: self.action_script.script_mode,
            ATTR_CUR: self.action_script.runs,
        }
        if self.action_script.supports_max:
            attrs[ATTR_MAX] = self.action_script.max_runs
        return attrs

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._async_detach_triggers is not None or self._is_enabled

    @property
    def referenced_devices(self):
        """Return a set of referenced devices."""
        if self._referenced_devices is not None:
            return self._referenced_devices

        referenced = self.action_script.referenced_devices

        if self._cond_func is not None:
            for conf in self._cond_func.config:
                referenced |= condition.async_extract_devices(conf)

        for conf in self._trigger_config:
            device = _trigger_extract_device(conf)
            if device is not None:
                referenced.add(device)

        self._referenced_devices = referenced
        return referenced

    @property
    def referenced_entities(self):
        """Return a set of referenced entities."""
        if self._referenced_entities is not None:
            return self._referenced_entities

        referenced = self.action_script.referenced_entities

        if self._cond_func is not None:
            for conf in self._cond_func.config:
                referenced |= condition.async_extract_entities(conf)

        for conf in self._trigger_config:
            for entity_id in _trigger_extract_entities(conf):
                referenced.add(entity_id)

        self._referenced_entities = referenced
        return referenced

    async def async_added_to_opp(self) -> None:
        """Startup with initial state or previous state."""
        await super().async_added_to_opp()

        self._logger = logging.getLogger(
            f"{__name__}.{split_entity_id(self.entity_id)[1]}"
        )
        self.action_script.update_logger(self._logger)

        state = await self.async_get_last_state()
        if state:
            enable_automation = state.state == STATE_ON
            last_triggered = state.attributes.get("last_triggered")
            if last_triggered is not None:
                self.action_script.last_triggered = parse_datetime(last_triggered)
            self._logger.debug(
                "Loaded automation %s with state %s from state "
                " storage last state %s",
                self.entity_id,
                enable_automation,
                state,
            )
        else:
            enable_automation = DEFAULT_INITIAL_STATE
            self._logger.debug(
                "Automation %s not in state storage, state %s from default is used",
                self.entity_id,
                enable_automation,
            )

        if self._initial_state is not None:
            enable_automation = self._initial_state
            self._logger.debug(
                "Automation %s initial state %s overridden from "
                "config initial_state",
                self.entity_id,
                enable_automation,
            )

        if enable_automation:
            await self.async_enable()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on and update the state."""
        await self.async_enable()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        if CONF_STOP_ACTIONS in kwargs:
            await self.async_disable(kwargs[CONF_STOP_ACTIONS])
        else:
            await self.async_disable()

    async def async_trigger(self, run_variables, context=None, skip_condition=False):
        """Trigger automation.

        This method is a coroutine.
        """
        if self._variables:
            try:
                variables = self._variables.async_render(self.opp, run_variables)
            except template.TemplateError as err:
                self._logger.error("Error rendering variables: %s", err)
                return
        else:
            variables = run_variables

        if (
            not skip_condition
            and self._cond_func is not None
            and not self._cond_func(variables)
        ):
            return

        # Create a new context referring to the old context.
        parent_id = None if context is None else context.id
        trigger_context = Context(parent_id=parent_id)

        self.async_set_context(trigger_context)
        event_data = {
            ATTR_NAME: self._name,
            ATTR_ENTITY_ID: self.entity_id,
        }
        if "trigger" in variables and "description" in variables["trigger"]:
            event_data[ATTR_SOURCE] = variables["trigger"]["description"]

        @callback
        def started_action():
            self.opp.bus.async_fire(
                EVENT_AUTOMATION_TRIGGERED, event_data, context=trigger_context
            )

        try:
            await self.action_script.async_run(
                variables, trigger_context, started_action
            )
        except (vol.Invalid, OpenPeerPowerError) as err:
            self._logger.error(
                "Error while executing automation %s: %s",
                self.entity_id,
                err,
            )
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("While executing automation %s", self.entity_id)

    async def async_will_remove_from_opp(self):
        """Remove listeners when removing automation from Open Peer Power."""
        await super().async_will_remove_from_opp()
        await self.async_disable()

    async def async_enable(self):
        """Enable this automation entity.

        This method is a coroutine.
        """
        if self._is_enabled:
            return

        self._is_enabled = True

        # OpenPeerPower is starting up
        if self.opp.state != CoreState.not_running:
            self._async_detach_triggers = await self._async_attach_triggers(False)
            self.async_write_op_state()
            return

        async def async_enable_automation(event):
            """Start automation on startup."""
            # Don't do anything if no longer enabled or already attached
            if not self._is_enabled or self._async_detach_triggers is not None:
                return

            self._async_detach_triggers = await self._async_attach_triggers(True)

        self.opp.bus.async_listen_once(
            EVENT_OPENPEERPOWER_STARTED, async_enable_automation
        )
        self.async_write_op_state()

    async def async_disable(self, stop_actions=DEFAULT_STOP_ACTIONS):
        """Disable the automation entity."""
        if not self._is_enabled and not self.action_script.runs:
            return

        self._is_enabled = False

        if self._async_detach_triggers is not None:
            self._async_detach_triggers()
            self._async_detach_triggers = None

        if stop_actions:
            await self.action_script.async_stop()

        self.async_write_op_state()

    async def _async_attach_triggers(
        self, open_peer_power_start: bool
    ) -> Optional[Callable[[], None]]:
        """Set up the triggers."""

        def log_cb(level, msg, **kwargs):
            self._logger.log(level, "%s %s", msg, self._name, **kwargs)

        variables = None
        if self._trigger_variables:
            try:
                variables = self._trigger_variables.async_render(
                    cast(OpenPeerPower, self.opp), None, limited=True
                )
            except template.TemplateError as err:
                self._logger.error("Error rendering trigger variables: %s", err)
                return None

        return await async_initialize_triggers(
            cast(OpenPeerPower, self.opp),
            self._trigger_config,
            self.async_trigger,
            DOMAIN,
            self._name,
            log_cb,
            open_peer_power_start,
            variables,
        )

    @property
    def device_state_attributes(self):
        """Return automation attributes."""
        if self._id is None:
            return None

        return {CONF_ID: self._id}


async def _async_process_config(
    opp: OpenPeerPower,
    config: Dict[str, Any],
    component: EntityComponent,
) -> bool:
    """Process config and add automations.

    Returns if blueprints were used.
    """
    entities = []
    blueprints_used = False

    for config_key in extract_domain_configs(config, DOMAIN):
        conf: List[Union[Dict[str, Any], blueprint.BlueprintInputs]] = config[  # type: ignore
            config_key
        ]

        for list_no, config_block in enumerate(conf):
            if isinstance(config_block, blueprint.BlueprintInputs):  # type: ignore
                blueprints_used = True
                blueprint_inputs = config_block

                try:
                    config_block = cast(
                        Dict[str, Any],
                        await async_validate_config_item(
                            opp, blueprint_inputs.async_substitute()
                        ),
                    )
                except vol.Invalid as err:
                    LOGGER.error(
                        "Blueprint %s generated invalid automation with inputs %s: %s",
                        blueprint_inputs.blueprint.name,
                        blueprint_inputs.inputs,
                        humanize_error(config_block, err),
                    )
                    continue

            automation_id = config_block.get(CONF_ID)
            name = config_block.get(CONF_ALIAS) or f"{config_key} {list_no}"

            initial_state = config_block.get(CONF_INITIAL_STATE)

            action_script = Script(
                opp,
                config_block[CONF_ACTION],
                name,
                DOMAIN,
                running_description="automation actions",
                script_mode=config_block[CONF_MODE],
                max_runs=config_block[CONF_MAX],
                max_exceeded=config_block[CONF_MAX_EXCEEDED],
                logger=LOGGER,
                # We don't pass variables here
                # Automation will already render them to use them in the condition
                # and so will pass them on to the script.
            )

            if CONF_CONDITION in config_block:
                cond_func = await _async_process_if(opp, name, config, config_block)

                if cond_func is None:
                    continue
            else:
                cond_func = None

            # Add trigger variables to variables
            variables = None
            if CONF_TRIGGER_VARIABLES in config_block:
                variables = ScriptVariables(
                    dict(config_block[CONF_TRIGGER_VARIABLES].as_dict())
                )
            if CONF_VARIABLES in config_block:
                if variables:
                    variables.variables.update(config_block[CONF_VARIABLES].as_dict())
                else:
                    variables = config_block[CONF_VARIABLES]

            entity = AutomationEntity(
                automation_id,
                name,
                config_block[CONF_TRIGGER],
                cond_func,
                action_script,
                initial_state,
                variables,
                config_block.get(CONF_TRIGGER_VARIABLES),
            )

            entities.append(entity)

    if entities:
        await component.async_add_entities(entities)

    return blueprints_used


async def _async_process_if(opp, name, config, p_config):
    """Process if checks."""
    if_configs = p_config[CONF_CONDITION]

    checks = []
    for if_config in if_configs:
        try:
            checks.append(await condition.async_from_config(opp, if_config, False))
        except OpenPeerPowerError as ex:
            LOGGER.warning("Invalid condition: %s", ex)
            return None

    def if_action(variables=None):
        """AND all conditions."""
        errors = []
        for index, check in enumerate(checks):
            try:
                if not check(opp, variables):
                    return False
            except ConditionError as ex:
                errors.append(
                    ConditionErrorIndex(
                        "condition", index=index, total=len(checks), error=ex
                    )
                )

        if errors:
            LOGGER.warning(
                "Error evaluating condition in '%s':\n%s",
                name,
                ConditionErrorContainer("condition", errors=errors),
            )
            return False

        return True

    if_action.config = if_configs

    return if_action


@callback
def _trigger_extract_device(trigger_conf: dict) -> Optional[str]:
    """Extract devices from a trigger config."""
    if trigger_conf[CONF_PLATFORM] != "device":
        return None

    return trigger_conf[CONF_DEVICE_ID]


@callback
def _trigger_extract_entities(trigger_conf: dict) -> List[str]:
    """Extract entities from a trigger config."""
    if trigger_conf[CONF_PLATFORM] in ("state", "numeric_state"):
        return trigger_conf[CONF_ENTITY_ID]

    if trigger_conf[CONF_PLATFORM] == "zone":
        return trigger_conf[CONF_ENTITY_ID] + [trigger_conf[CONF_ZONE]]

    if trigger_conf[CONF_PLATFORM] == "geo_location":
        return [trigger_conf[CONF_ZONE]]

    if trigger_conf[CONF_PLATFORM] == "sun":
        return ["sun.sun"]

    return []
