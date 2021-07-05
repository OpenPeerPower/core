"""Intents for the humidifier integration."""
import voluptuous as vol

from openpeerpower.const import ATTR_ENTITY_ID, ATTR_MODE, STATE_OFF
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import intent
import openpeerpower.helpers.config_validation as cv

from . import (
    ATTR_AVAILABLE_MODES,
    ATTR_HUMIDITY,
    DOMAIN,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_MODE,
    SERVICE_TURN_ON,
    SUPPORT_MODES,
)

INTENT_HUMIDITY = "OppHumidifierSetpoint"
INTENT_MODE = "OppHumidifierMode"


async def async_setup_intents(opp: OpenPeerPower) -> None:
    """Set up the humidifier intents."""
    opp.helpers.intent.async_register(HumidityHandler())
    opp.helpers.intent.async_register(SetModeHandler())


class HumidityHandler(intent.IntentHandler):
    """Handle set humidity intents."""

    intent_type = INTENT_HUMIDITY
    slot_schema = {
        vol.Required("name"): cv.string,
        vol.Required("humidity"): vol.All(vol.Coerce(int), vol.Range(0, 100)),
    }

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the opp intent."""
        opp = intent_obj.opp
        slots = self.async_validate_slots(intent_obj.slots)
        state = opp.helpers.intent.async_match_state(
            slots["name"]["value"], opp.states.async_all(DOMAIN)
        )

        service_data = {ATTR_ENTITY_ID: state.entity_id}

        humidity = slots["humidity"]["value"]

        if state.state == STATE_OFF:
            await opp.services.async_call(
                DOMAIN, SERVICE_TURN_ON, service_data, context=intent_obj.context
            )
            speech = f"Turned {state.name} on and set humidity to {humidity}%"
        else:
            speech = f"The {state.name} is set to {humidity}%"

        service_data[ATTR_HUMIDITY] = humidity
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_HUMIDITY,
            service_data,
            context=intent_obj.context,
            blocking=True,
        )

        response = intent_obj.create_response()

        response.async_set_speech(speech)
        return response


class SetModeHandler(intent.IntentHandler):
    """Handle set humidity intents."""

    intent_type = INTENT_MODE
    slot_schema = {
        vol.Required("name"): cv.string,
        vol.Required("mode"): cv.string,
    }

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the opp intent."""
        opp = intent_obj.opp
        slots = self.async_validate_slots(intent_obj.slots)
        state = opp.helpers.intent.async_match_state(
            slots["name"]["value"],
            opp.states.async_all(DOMAIN),
        )

        service_data = {ATTR_ENTITY_ID: state.entity_id}

        intent.async_test_feature(state, SUPPORT_MODES, "modes")
        mode = slots["mode"]["value"]

        if mode not in state.attributes.get(ATTR_AVAILABLE_MODES, []):
            raise intent.IntentHandleError(
                f"Entity {state.name} does not support {mode} mode"
            )

        if state.state == STATE_OFF:
            await opp.services.async_call(
                DOMAIN,
                SERVICE_TURN_ON,
                service_data,
                context=intent_obj.context,
                blocking=True,
            )
            speech = f"Turned {state.name} on and set {mode} mode"
        else:
            speech = f"The mode for {state.name} is set to {mode}"

        service_data[ATTR_MODE] = mode
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_MODE,
            service_data,
            context=intent_obj.context,
            blocking=True,
        )

        response = intent_obj.create_response()

        response.async_set_speech(speech)
        return response
