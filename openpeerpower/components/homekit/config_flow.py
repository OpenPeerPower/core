"""Config flow for HomeKit integration."""
import random
import re
import string

import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.camera import DOMAIN as CAMERA_DOMAIN
from openpeerpower.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import (
    ATTR_FRIENDLY_NAME,
    CONF_DOMAINS,
    CONF_ENTITIES,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_PORT,
)
from openpeerpower.core import callback, split_entity_id
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entityfilter import (
    CONF_EXCLUDE_DOMAINS,
    CONF_EXCLUDE_ENTITIES,
    CONF_INCLUDE_DOMAINS,
    CONF_INCLUDE_ENTITIES,
)

from .const import (
    CONF_AUTO_START,
    CONF_ENTITY_CONFIG,
    CONF_EXCLUDE_ACCESSORY_MODE,
    CONF_FILTER,
    CONF_HOMEKIT_MODE,
    CONF_VIDEO_CODEC,
    DEFAULT_AUTO_START,
    DEFAULT_CONFIG_FLOW_PORT,
    DEFAULT_HOMEKIT_MODE,
    DOMAIN,
    HOMEKIT_MODE_ACCESSORY,
    HOMEKIT_MODE_BRIDGE,
    HOMEKIT_MODES,
    SHORT_BRIDGE_NAME,
    VIDEO_CODEC_COPY,
)
from .util import async_find_next_available_port, state_needs_accessory_mode

CONF_CAMERA_COPY = "camera_copy"
CONF_INCLUDE_EXCLUDE_MODE = "include_exclude_mode"

MODE_INCLUDE = "include"
MODE_EXCLUDE = "exclude"

INCLUDE_EXCLUDE_MODES = [MODE_EXCLUDE, MODE_INCLUDE]

DOMAINS_NEED_ACCESSORY_MODE = [CAMERA_DOMAIN, MEDIA_PLAYER_DOMAIN]
NEVER_BRIDGED_DOMAINS = [CAMERA_DOMAIN]

CAMERA_ENTITY_PREFIX = f"{CAMERA_DOMAIN}."

SUPPORTED_DOMAINS = [
    "alarm_control_panel",
    "automation",
    "binary_sensor",
    CAMERA_DOMAIN,
    "climate",
    "cover",
    "demo",
    "device_tracker",
    "fan",
    "humidifier",
    "input_boolean",
    "light",
    "lock",
    MEDIA_PLAYER_DOMAIN,
    "person",
    "remote",
    "scene",
    "script",
    "sensor",
    "switch",
    "vacuum",
    "water_heater",
]

DEFAULT_DOMAINS = [
    "alarm_control_panel",
    "climate",
    CAMERA_DOMAIN,
    "cover",
    "humidifier",
    "fan",
    "light",
    "lock",
    MEDIA_PLAYER_DOMAIN,
    "switch",
    "vacuum",
    "water_heater",
]

_EMPTY_ENTITY_FILTER = {
    CONF_INCLUDE_DOMAINS: [],
    CONF_EXCLUDE_DOMAINS: [],
    CONF_INCLUDE_ENTITIES: [],
    CONF_EXCLUDE_ENTITIES: [],
}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HomeKit."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize config flow."""
        self.hk_data = {}

    async def async_step_user(self, user_input=None):
        """Choose specific domains in bridge mode."""
        if user_input is not None:
            entity_filter = _EMPTY_ENTITY_FILTER.copy()
            entity_filter[CONF_INCLUDE_DOMAINS] = user_input[CONF_INCLUDE_DOMAINS]
            self.hk_data[CONF_FILTER] = entity_filter
            return await self.async_step_pairing()

        self.hk_data[CONF_HOMEKIT_MODE] = HOMEKIT_MODE_BRIDGE
        default_domains = [] if self._async_current_names() else DEFAULT_DOMAINS
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INCLUDE_DOMAINS, default=default_domains
                    ): cv.multi_select(SUPPORTED_DOMAINS),
                }
            ),
        )

    async def async_step_pairing(self, user_input=None):
        """Pairing instructions."""
        if user_input is not None:
            port = await async_find_next_available_port(
                self.opp, DEFAULT_CONFIG_FLOW_PORT
            )
            await self._async_add_entries_for_accessory_mode_entities(port)
            self.hk_data[CONF_PORT] = port
            include_domains_filter = self.hk_data[CONF_FILTER][CONF_INCLUDE_DOMAINS]
            for domain in NEVER_BRIDGED_DOMAINS:
                if domain in include_domains_filter:
                    include_domains_filter.remove(domain)
            return self.async_create_entry(
                title=f"{self.hk_data[CONF_NAME]}:{self.hk_data[CONF_PORT]}",
                data=self.hk_data,
            )

        self.hk_data[CONF_NAME] = self._async_available_name(SHORT_BRIDGE_NAME)
        self.hk_data[CONF_EXCLUDE_ACCESSORY_MODE] = True
        return self.async_show_form(
            step_id="pairing",
            description_placeholders={CONF_NAME: self.hk_data[CONF_NAME]},
        )

    async def _async_add_entries_for_accessory_mode_entities(self, last_assigned_port):
        """Generate new flows for entities that need their own instances."""
        accessory_mode_entity_ids = _async_get_entity_ids_for_accessory_mode(
            self.opp, self.hk_data[CONF_FILTER][CONF_INCLUDE_DOMAINS]
        )
        exiting_entity_ids_accessory_mode = _async_entity_ids_with_accessory_mode(
            self.opp
        )
        next_port_to_check = last_assigned_port + 1
        for entity_id in accessory_mode_entity_ids:
            if entity_id in exiting_entity_ids_accessory_mode:
                continue
            port = await async_find_next_available_port(self.opp, next_port_to_check)
            next_port_to_check = port + 1
            self.opp.async_create_task(
                self.opp.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "accessory"},
                    data={CONF_ENTITY_ID: entity_id, CONF_PORT: port},
                )
            )

    async def async_step_accessory(self, accessory_input):
        """Handle creation a single accessory in accessory mode."""
        entity_id = accessory_input[CONF_ENTITY_ID]
        port = accessory_input[CONF_PORT]

        state = self.opp.states.get(entity_id)
        name = state.attributes.get(ATTR_FRIENDLY_NAME) or state.entity_id
        entity_filter = _EMPTY_ENTITY_FILTER.copy()
        entity_filter[CONF_INCLUDE_ENTITIES] = [entity_id]

        entry_data = {
            CONF_PORT: port,
            CONF_NAME: self._async_available_name(name),
            CONF_HOMEKIT_MODE: HOMEKIT_MODE_ACCESSORY,
            CONF_FILTER: entity_filter,
        }
        if entity_id.startswith(CAMERA_ENTITY_PREFIX):
            entry_data[CONF_ENTITY_CONFIG] = {
                entity_id: {CONF_VIDEO_CODEC: VIDEO_CODEC_COPY}
            }

        return self.async_create_entry(
            title=f"{name}:{entry_data[CONF_PORT]}", data=entry_data
        )

    async def async_step_import(self, user_input=None):
        """Handle import from yaml."""
        if not self._async_is_unique_name_port(user_input):
            return self.async_abort(reason="port_name_in_use")
        return self.async_create_entry(
            title=f"{user_input[CONF_NAME]}:{user_input[CONF_PORT]}", data=user_input
        )

    @callback
    def _async_current_names(self):
        """Return a set of bridge names."""
        return {
            entry.data[CONF_NAME]
            for entry in self._async_current_entries()
            if CONF_NAME in entry.data
        }

    @callback
    def _async_available_name(self, requested_name):
        """Return an available for the bridge."""
        current_names = self._async_current_names()
        valid_mdns_name = re.sub("[^A-Za-z0-9 ]+", " ", requested_name)

        if valid_mdns_name not in current_names:
            return valid_mdns_name

        acceptable_mdns_chars = string.ascii_uppercase + string.digits
        suggested_name = None
        while not suggested_name or suggested_name in current_names:
            trailer = "".join(random.choices(acceptable_mdns_chars, k=2))
            suggested_name = f"{valid_mdns_name} {trailer}"

        return suggested_name

    @callback
    def _async_is_unique_name_port(self, user_input):
        """Determine is a name or port is already used."""
        name = user_input[CONF_NAME]
        port = user_input[CONF_PORT]
        for entry in self._async_current_entries():
            if entry.data[CONF_NAME] == name or entry.data[CONF_PORT] == port:
                return False
        return True

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for homekit."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.hk_options = {}
        self.included_cameras = set()

    async def async_step_yaml(self, user_input=None):
        """No options for yaml managed entries."""
        if user_input is not None:
            # Apparently not possible to abort an options flow
            # at the moment
            return self.async_create_entry(title="", data=self.config_entry.options)

        return self.async_show_form(step_id="yaml")

    async def async_step_advanced(self, user_input=None):
        """Choose advanced options."""
        if not self.show_advanced_options or user_input is not None:
            if user_input:
                self.hk_options.update(user_input)

            self.hk_options[CONF_AUTO_START] = self.hk_options.get(
                CONF_AUTO_START, DEFAULT_AUTO_START
            )

            for key in (CONF_DOMAINS, CONF_ENTITIES):
                if key in self.hk_options:
                    del self.hk_options[key]

            return self.async_create_entry(title="", data=self.hk_options)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AUTO_START,
                        default=self.hk_options.get(
                            CONF_AUTO_START, DEFAULT_AUTO_START
                        ),
                    ): bool
                }
            ),
        )

    async def async_step_cameras(self, user_input=None):
        """Choose camera config."""
        if user_input is not None:
            entity_config = self.hk_options[CONF_ENTITY_CONFIG]
            for entity_id in self.included_cameras:
                if entity_id in user_input[CONF_CAMERA_COPY]:
                    entity_config.setdefault(entity_id, {})[
                        CONF_VIDEO_CODEC
                    ] = VIDEO_CODEC_COPY
                elif (
                    entity_id in entity_config
                    and CONF_VIDEO_CODEC in entity_config[entity_id]
                ):
                    del entity_config[entity_id][CONF_VIDEO_CODEC]
            return await self.async_step_advanced()

        cameras_with_copy = []
        entity_config = self.hk_options.setdefault(CONF_ENTITY_CONFIG, {})
        for entity in self.included_cameras:
            hk_entity_config = entity_config.get(entity, {})
            if hk_entity_config.get(CONF_VIDEO_CODEC) == VIDEO_CODEC_COPY:
                cameras_with_copy.append(entity)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CAMERA_COPY,
                    default=cameras_with_copy,
                ): cv.multi_select(self.included_cameras),
            }
        )
        return self.async_show_form(step_id="cameras", data_schema=data_schema)

    async def async_step_include_exclude(self, user_input=None):
        """Choose entities to include or exclude from the domain."""
        if user_input is not None:
            entity_filter = _EMPTY_ENTITY_FILTER.copy()
            if isinstance(user_input[CONF_ENTITIES], list):
                entities = user_input[CONF_ENTITIES]
            else:
                entities = [user_input[CONF_ENTITIES]]

            if (
                self.hk_options[CONF_HOMEKIT_MODE] == HOMEKIT_MODE_ACCESSORY
                or user_input[CONF_INCLUDE_EXCLUDE_MODE] == MODE_INCLUDE
            ):
                entity_filter[CONF_INCLUDE_ENTITIES] = entities
                # Include all of the domain if there are no entities
                # explicitly included as the user selected the domain
                domains_with_entities_selected = _domains_set_from_entities(entities)
                entity_filter[CONF_INCLUDE_DOMAINS] = [
                    domain
                    for domain in self.hk_options[CONF_DOMAINS]
                    if domain not in domains_with_entities_selected
                ]

                self.included_cameras = {
                    entity_id
                    for entity_id in entities
                    if entity_id.startswith(CAMERA_ENTITY_PREFIX)
                }
            else:
                entity_filter[CONF_INCLUDE_DOMAINS] = self.hk_options[CONF_DOMAINS]
                entity_filter[CONF_EXCLUDE_ENTITIES] = entities
                if CAMERA_DOMAIN in entity_filter[CONF_INCLUDE_DOMAINS]:
                    camera_entities = _async_get_matching_entities(
                        self.opp,
                        domains=[CAMERA_DOMAIN],
                    )
                    self.included_cameras = {
                        entity_id
                        for entity_id in camera_entities
                        if entity_id not in entities
                    }
                else:
                    self.included_cameras = set()

            self.hk_options[CONF_FILTER] = entity_filter

            if self.included_cameras:
                return await self.async_step_cameras()

            return await self.async_step_advanced()

        entity_filter = self.hk_options.get(CONF_FILTER, {})
        all_supported_entities = _async_get_matching_entities(
            self.opp,
            domains=self.hk_options[CONF_DOMAINS],
        )

        data_schema = {}
        entities = entity_filter.get(CONF_INCLUDE_ENTITIES, [])
        if self.hk_options[CONF_HOMEKIT_MODE] == HOMEKIT_MODE_ACCESSORY:
            entity_schema = vol.In
        else:
            if entities:
                include_exclude_mode = MODE_INCLUDE
            else:
                include_exclude_mode = MODE_EXCLUDE
                entities = entity_filter.get(CONF_EXCLUDE_ENTITIES, [])
            data_schema[
                vol.Required(CONF_INCLUDE_EXCLUDE_MODE, default=include_exclude_mode)
            ] = vol.In(INCLUDE_EXCLUDE_MODES)
            entity_schema = cv.multi_select

        data_schema[vol.Optional(CONF_ENTITIES, default=entities)] = entity_schema(
            all_supported_entities
        )

        return self.async_show_form(
            step_id="include_exclude", data_schema=vol.Schema(data_schema)
        )

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if self.config_entry.source == SOURCE_IMPORT:
            return await self.async_step_yaml(user_input)

        if user_input is not None:
            self.hk_options.update(user_input)
            return await self.async_step_include_exclude()

        self.hk_options = dict(self.config_entry.options)
        entity_filter = self.hk_options.get(CONF_FILTER, {})
        homekit_mode = self.hk_options.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
        domains = entity_filter.get(CONF_INCLUDE_DOMAINS, [])
        include_entities = entity_filter.get(CONF_INCLUDE_ENTITIES)
        if include_entities:
            domains.extend(_domains_set_from_entities(include_entities))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOMEKIT_MODE, default=homekit_mode): vol.In(
                        HOMEKIT_MODES
                    ),
                    vol.Required(
                        CONF_DOMAINS,
                        default=domains,
                    ): cv.multi_select(SUPPORTED_DOMAINS),
                }
            ),
        )


def _async_get_matching_entities(opp, domains=None):
    """Fetch all entities or entities in the given domains."""
    return {
        state.entity_id: f"{state.attributes.get(ATTR_FRIENDLY_NAME, state.entity_id)} ({state.entity_id})"
        for state in sorted(
            opp.states.async_all(domains and set(domains)),
            key=lambda item: item.entity_id,
        )
    }


def _domains_set_from_entities(entity_ids):
    """Build a set of domains for the given entity ids."""
    return {split_entity_id(entity_id)[0] for entity_id in entity_ids}


@callback
def _async_get_entity_ids_for_accessory_mode(opp, include_domains):
    """Build a list of entities that should be paired in accessory mode."""
    accessory_mode_domains = {
        domain for domain in include_domains if domain in DOMAINS_NEED_ACCESSORY_MODE
    }

    if not accessory_mode_domains:
        return []

    return [
        state.entity_id
        for state in opp.states.async_all(accessory_mode_domains)
        if state_needs_accessory_mode(state)
    ]


@callback
def _async_entity_ids_with_accessory_mode(opp):
    """Return a set of entity ids that have config entries in accessory mode."""

    entity_ids = set()

    current_entries = opp.config_entries.async_entries(DOMAIN)
    for entry in current_entries:
        # We have to handle the case where the data has not yet
        # been migrated to options because the data was just
        # imported and the entry was never started
        target = entry.options if CONF_HOMEKIT_MODE in entry.options else entry.data
        if target.get(CONF_HOMEKIT_MODE) != HOMEKIT_MODE_ACCESSORY:
            continue

        entity_ids.add(target[CONF_FILTER][CONF_INCLUDE_ENTITIES][0])

    return entity_ids
