"""Support for Alexa skill service end point."""
import copy
import hmac
import logging
import uuid

from openpeerpower.components import http
from openpeerpower.const import CONF_PASSWORD, HTTP_NOT_FOUND, HTTP_UNAUTHORIZED
from openpeerpower.core import callback
from openpeerpower.helpers import template
import openpeerpower.util.dt as dt_util

from .const import (
    API_PASSWORD,
    ATTR_MAIN_TEXT,
    ATTR_REDIRECTION_URL,
    ATTR_STREAM_URL,
    ATTR_TITLE_TEXT,
    ATTR_UID,
    ATTR_UPDATE_DATE,
    CONF_AUDIO,
    CONF_DISPLAY_URL,
    CONF_TEXT,
    CONF_TITLE,
    CONF_UID,
    DATE_FORMAT,
)

_LOGGER = logging.getLogger(__name__)

FLASH_BRIEFINGS_API_ENDPOINT = "/api/alexa/flash_briefings/{briefing_id}"


@callback
def async_setup(opp, flash_briefing_config):
    """Activate Alexa component."""
    opp.http.register_view(AlexaFlashBriefingView(opp, flash_briefing_config))


class AlexaFlashBriefingView(http.OpenPeerPowerView):
    """Handle Alexa Flash Briefing skill requests."""

    url = FLASH_BRIEFINGS_API_ENDPOINT
    requires_auth = False
    name = "api:alexa:flash_briefings"

    def __init__(self, opp, flash_briefings):
        """Initialize Alexa view."""
        super().__init__()
        self.flash_briefings = copy.deepcopy(flash_briefings)
        template.attach(opp, self.flash_briefings)

    @callback
    def get(self, request, briefing_id):
        """Handle Alexa Flash Briefing request."""
        _LOGGER.debug("Received Alexa flash briefing request for: %s", briefing_id)

        if request.query.get(API_PASSWORD) is None:
            err = "No password provided for Alexa flash briefing: %s"
            _LOGGER.error(err, briefing_id)
            return b"", HTTP_UNAUTHORIZED

        if not hmac.compare_digest(
            request.query[API_PASSWORD].encode("utf-8"),
            self.flash_briefings[CONF_PASSWORD].encode("utf-8"),
        ):
            err = "Wrong password for Alexa flash briefing: %s"
            _LOGGER.error(err, briefing_id)
            return b"", HTTP_UNAUTHORIZED

        if not isinstance(self.flash_briefings.get(briefing_id), list):
            err = "No configured Alexa flash briefing was found for: %s"
            _LOGGER.error(err, briefing_id)
            return b"", HTTP_NOT_FOUND

        briefing = []

        for item in self.flash_briefings.get(briefing_id, []):
            output = {}
            if item.get(CONF_TITLE) is not None:
                if isinstance(item.get(CONF_TITLE), template.Template):
                    output[ATTR_TITLE_TEXT] = item[CONF_TITLE].async_render(
                        parse_result=False
                    )
                else:
                    output[ATTR_TITLE_TEXT] = item.get(CONF_TITLE)

            if item.get(CONF_TEXT) is not None:
                if isinstance(item.get(CONF_TEXT), template.Template):
                    output[ATTR_MAIN_TEXT] = item[CONF_TEXT].async_render(
                        parse_result=False
                    )
                else:
                    output[ATTR_MAIN_TEXT] = item.get(CONF_TEXT)

            uid = item.get(CONF_UID)
            if uid is None:
                uid = str(uuid.uuid4())
            output[ATTR_UID] = uid

            if item.get(CONF_AUDIO) is not None:
                if isinstance(item.get(CONF_AUDIO), template.Template):
                    output[ATTR_STREAM_URL] = item[CONF_AUDIO].async_render(
                        parse_result=False
                    )
                else:
                    output[ATTR_STREAM_URL] = item.get(CONF_AUDIO)

            if item.get(CONF_DISPLAY_URL) is not None:
                if isinstance(item.get(CONF_DISPLAY_URL), template.Template):
                    output[ATTR_REDIRECTION_URL] = item[CONF_DISPLAY_URL].async_render(
                        parse_result=False
                    )
                else:
                    output[ATTR_REDIRECTION_URL] = item.get(CONF_DISPLAY_URL)

            output[ATTR_UPDATE_DATE] = dt_util.utcnow().strftime(DATE_FORMAT)

            briefing.append(output)

        return self.json(briefing)
