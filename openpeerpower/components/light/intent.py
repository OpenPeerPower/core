"""Intents for the light integration."""
import voluptuous as vol

from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import intent
import openpeerpower.helpers.config_validation as cv
import openpeerpower.util.color as color_util

from . import (
    ATTR_BRIGHTNESS_PCT,
    ATTR_RGB_COLOR,
    DOMAIN,
    SERVICE_TURN_ON,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
)

INTENT_SET = "OppLightSet"


async def async_setup_intents(opp: OpenPeerPower) -> None:
    """Set up the light intents."""
    opp.helpers.intent.async_register(SetIntentHandler())


class SetIntentHandler(intent.IntentHandler):
    """Handle set color intents."""

    intent_type = INTENT_SET
    slot_schema = {
        vol.Required("name"): cv.string,
        vol.Optional("color"): color_util.color_name_to_rgb,
        vol.Optional("brightness"): vol.All(vol.Coerce(int), vol.Range(0, 100)),
    }

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the opp intent."""
        opp = intent_obj.opp
        slots = self.async_validate_slots(intent_obj.slots)
        state = opp.helpers.intent.async_match_state(
            slots["name"]["value"], opp.states.async_all(DOMAIN)
        )

        service_data = {ATTR_ENTITY_ID: state.entity_id}
        speech_parts = []

        if "color" in slots:
            intent.async_test_feature(state, SUPPORT_COLOR, "changing colors")
            service_data[ATTR_RGB_COLOR] = slots["color"]["value"]
            # Use original passed in value of the color because we don't have
            # human readable names for that internally.
            speech_parts.append(f"the color {intent_obj.slots['color']['value']}")

        if "brightness" in slots:
            intent.async_test_feature(state, SUPPORT_BRIGHTNESS, "changing brightness")
            service_data[ATTR_BRIGHTNESS_PCT] = slots["brightness"]["value"]
            speech_parts.append(f"{slots['brightness']['value']}% brightness")

        await opp.services.async_call(
            DOMAIN, SERVICE_TURN_ON, service_data, context=intent_obj.context
        )

        response = intent_obj.create_response()

        if not speech_parts:  # No attributes changed
            speech = f"Turned on {state.name}"
        else:
            parts = [f"Changed {state.name} to"]
            for index, part in enumerate(speech_parts):
                if index == 0:
                    parts.append(f" {part}")
                elif index != len(speech_parts) - 1:
                    parts.append(f", {part}")
                else:
                    parts.append(f" and {part}")
            speech = "".join(parts)

        response.async_set_speech(speech)
        return response
