"""Offer MQTT listening automation rules."""
import json
import logging

import voluptuous as vol

from openpeerpower.const import CONF_PAYLOAD, CONF_PLATFORM, CONF_VALUE_TEMPLATE
from openpeerpower.core import OppJob, callback
from openpeerpower.helpers import config_validation as cv, template

from .. import mqtt

# mypy: allow-untyped-defs

CONF_ENCODING = "encoding"
CONF_QOS = "qos"
CONF_TOPIC = "topic"
DEFAULT_ENCODING = "utf-8"
DEFAULT_QOS = 0

TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): mqtt.DOMAIN,
        vol.Required(CONF_TOPIC): mqtt.util.valid_subscribe_topic_template,
        vol.Optional(CONF_PAYLOAD): cv.template,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_ENCODING, default=DEFAULT_ENCODING): cv.string,
        vol.Optional(CONF_QOS, default=DEFAULT_QOS): vol.All(
            vol.Coerce(int), vol.In([0, 1, 2])
        ),
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_attach_trigger(opp, config, action, automation_info):
    """Listen for state changes based on configuration."""
    topic = config[CONF_TOPIC]
    wanted_payload = config.get(CONF_PAYLOAD)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    encoding = config[CONF_ENCODING] or None
    qos = config[CONF_QOS]
    job = OppJob(action)
    variables = None
    if automation_info:
        variables = automation_info.get("variables")

    template.attach(opp, wanted_payload)
    if wanted_payload:
        wanted_payload = wanted_payload.async_render(
            variables, limited=True, parse_result=False
        )

    template.attach(opp, topic)
    if isinstance(topic, template.Template):
        topic = topic.async_render(variables, limited=True, parse_result=False)
        topic = mqtt.util.valid_subscribe_topic(topic)

    template.attach(opp, value_template)

    @callback
    def mqtt_automation_listener(mqttmsg):
        """Listen for MQTT messages."""
        payload = mqttmsg.payload

        if value_template is not None:
            payload = value_template.async_render_with_possible_json_value(
                payload,
                error_value=None,
            )

        if wanted_payload is None or wanted_payload == payload:
            data = {
                "platform": "mqtt",
                "topic": mqttmsg.topic,
                "payload": mqttmsg.payload,
                "qos": mqttmsg.qos,
                "description": f"mqtt topic {mqttmsg.topic}",
            }

            try:
                data["payload_json"] = json.loads(mqttmsg.payload)
            except ValueError:
                pass

            opp.async_run_opp_job(job, {"trigger": data})

    _LOGGER.debug(
        "Attaching MQTT trigger for topic: '%s', payload: '%s'", topic, wanted_payload
    )

    remove = await mqtt.async_subscribe(
        opp, topic, mqtt_automation_listener, encoding=encoding, qos=qos
    )
    return remove
