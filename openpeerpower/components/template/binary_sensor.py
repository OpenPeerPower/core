"""Support for exposing a templated binary sensor."""
import voluptuous as vol

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    BinarySensorEntity,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    CONF_DEVICE_CLASS,
    CONF_ENTITY_PICTURE_TEMPLATE,
    CONF_ICON_TEMPLATE,
    CONF_SENSORS,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
)
from openpeerpower.core import callback
from openpeerpower.exceptions import TemplateError
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import async_generate_entity_id
from openpeerpower.helpers.event import async_call_later
from openpeerpower.helpers.reload import async_setup_reload_service
from openpeerpower.helpers.template import result_as_boolean

from .const import CONF_AVAILABILITY_TEMPLATE, DOMAIN, PLATFORMS
from .template_entity import TemplateEntity

CONF_DELAY_ON = "delay_on"
CONF_DELAY_OFF = "delay_off"
CONF_ATTRIBUTE_TEMPLATES = "attribute_templates"

SENSOR_SCHEMA = vol.All(
    cv.deprecated(ATTR_ENTITY_ID),
    vol.Schema(
        {
            vol.Required(CONF_VALUE_TEMPLATE): cv.template,
            vol.Optional(CONF_ICON_TEMPLATE): cv.template,
            vol.Optional(CONF_ENTITY_PICTURE_TEMPLATE): cv.template,
            vol.Optional(CONF_AVAILABILITY_TEMPLATE): cv.template,
            vol.Optional(CONF_ATTRIBUTE_TEMPLATES): vol.Schema(
                {cv.string: cv.template}
            ),
            vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
            vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
            vol.Optional(CONF_DELAY_ON): vol.Any(cv.positive_time_period, cv.template),
            vol.Optional(CONF_DELAY_OFF): vol.Any(cv.positive_time_period, cv.template),
            vol.Optional(CONF_UNIQUE_ID): cv.string,
        }
    ),
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_SENSORS): cv.schema_with_slug_keys(SENSOR_SCHEMA)}
)


async def _async_create_entities(opp, config):
    """Create the template binary sensors."""
    sensors = []

    for device, device_config in config[CONF_SENSORS].items():
        value_template = device_config[CONF_VALUE_TEMPLATE]
        icon_template = device_config.get(CONF_ICON_TEMPLATE)
        entity_picture_template = device_config.get(CONF_ENTITY_PICTURE_TEMPLATE)
        availability_template = device_config.get(CONF_AVAILABILITY_TEMPLATE)
        attribute_templates = device_config.get(CONF_ATTRIBUTE_TEMPLATES, {})

        friendly_name = device_config.get(ATTR_FRIENDLY_NAME, device)
        device_class = device_config.get(CONF_DEVICE_CLASS)
        delay_on_raw = device_config.get(CONF_DELAY_ON)
        delay_off_raw = device_config.get(CONF_DELAY_OFF)
        unique_id = device_config.get(CONF_UNIQUE_ID)

        sensors.append(
            BinarySensorTemplate(
                opp,
                device,
                friendly_name,
                device_class,
                value_template,
                icon_template,
                entity_picture_template,
                availability_template,
                delay_on_raw,
                delay_off_raw,
                attribute_templates,
                unique_id,
            )
        )

    return sensors


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the template binary sensors."""
    await async_setup_reload_service(opp, DOMAIN, PLATFORMS)
    async_add_entities(await _async_create_entities(opp, config))


class BinarySensorTemplate(TemplateEntity, BinarySensorEntity):
    """A virtual binary sensor that triggers from another sensor."""

    def __init__(
        self,
        opp,
        device,
        friendly_name,
        device_class,
        value_template,
        icon_template,
        entity_picture_template,
        availability_template,
        delay_on_raw,
        delay_off_raw,
        attribute_templates,
        unique_id,
    ):
        """Initialize the Template binary sensor."""
        super().__init__(
            attribute_templates=attribute_templates,
            availability_template=availability_template,
            icon_template=icon_template,
            entity_picture_template=entity_picture_template,
        )
        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, device, opp=opp)
        self._name = friendly_name
        self._device_class = device_class
        self._template = value_template
        self._state = None
        self._delay_cancel = None
        self._delay_on = None
        self._delay_on_raw = delay_on_raw
        self._delay_off = None
        self._delay_off_raw = delay_off_raw
        self._unique_id = unique_id

    async def async_added_to_opp(self):
        """Register callbacks."""
        self.add_template_attribute("_state", self._template, None, self._update_state)

        if self._delay_on_raw is not None:
            try:
                self._delay_on = cv.positive_time_period(self._delay_on_raw)
            except vol.Invalid:
                self.add_template_attribute(
                    "_delay_on", self._delay_on_raw, cv.positive_time_period
                )

        if self._delay_off_raw is not None:
            try:
                self._delay_off = cv.positive_time_period(self._delay_off_raw)
            except vol.Invalid:
                self.add_template_attribute(
                    "_delay_off", self._delay_off_raw, cv.positive_time_period
                )

        await super().async_added_to_opp()

    @callback
    def _update_state(self, result):
        super()._update_state(result)

        if self._delay_cancel:
            self._delay_cancel()
            self._delay_cancel = None

        state = None if isinstance(result, TemplateError) else result_as_boolean(result)

        if state == self._state:
            return

        # state without delay
        if (
            state is None
            or (state and not self._delay_on)
            or (not state and not self._delay_off)
        ):
            self._state = state
            return

        @callback
        def _set_state(_):
            """Set state of template binary sensor."""
            self._state = state
            self.async_write_op_state()

        delay = (self._delay_on if state else self._delay_off).seconds
        # state with delay. Cancelled if template result changes.
        self._delay_cancel = async_call_later(self.opp, delay, _set_state)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id of this binary sensor."""
        return self._unique_id

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the sensor class of the binary sensor."""
        return self._device_class
