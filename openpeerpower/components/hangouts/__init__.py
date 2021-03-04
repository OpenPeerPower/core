"""Support for Hangouts."""
import logging

from hangups.auth import GoogleAuthError
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.conversation.util import create_matcher
from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.helpers import dispatcher, intent
import openpeerpower.helpers.config_validation as cv

# We need an import from .config_flow, without it .config_flow is never loaded.
from .config_flow import HangoutsFlowHandler  # noqa: F401
from .const import (
    CONF_BOT,
    CONF_DEFAULT_CONVERSATIONS,
    CONF_ERROR_SUPPRESSED_CONVERSATIONS,
    CONF_INTENTS,
    CONF_MATCHERS,
    CONF_REFRESH_TOKEN,
    CONF_SENTENCES,
    DOMAIN,
    EVENT_HANGOUTS_CONNECTED,
    EVENT_HANGOUTS_CONVERSATIONS_CHANGED,
    EVENT_HANGOUTS_CONVERSATIONS_RESOLVED,
    INTENT_HELP,
    INTENT_SCHEMA,
    MESSAGE_SCHEMA,
    SERVICE_RECONNECT,
    SERVICE_SEND_MESSAGE,
    SERVICE_UPDATE,
    TARGETS_SCHEMA,
)
from .hangouts_bot import HangoutsBot
from .intents import HelpIntent

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_INTENTS, default={}): vol.Schema(
                    {cv.string: INTENT_SCHEMA}
                ),
                vol.Optional(CONF_DEFAULT_CONVERSATIONS, default=[]): [TARGETS_SCHEMA],
                vol.Optional(CONF_ERROR_SUPPRESSED_CONVERSATIONS, default=[]): [
                    TARGETS_SCHEMA
                ],
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Hangouts bot component."""
    config = config.get(DOMAIN)
    if config is None:
        opp.data[DOMAIN] = {
            CONF_INTENTS: {},
            CONF_DEFAULT_CONVERSATIONS: [],
            CONF_ERROR_SUPPRESSED_CONVERSATIONS: [],
        }
        return True

    opp.data[DOMAIN] = {
        CONF_INTENTS: config[CONF_INTENTS],
        CONF_DEFAULT_CONVERSATIONS: config[CONF_DEFAULT_CONVERSATIONS],
        CONF_ERROR_SUPPRESSED_CONVERSATIONS: config[
            CONF_ERROR_SUPPRESSED_CONVERSATIONS
        ],
    }

    if (
        opp.data[DOMAIN][CONF_INTENTS]
        and INTENT_HELP not in opp.data[DOMAIN][CONF_INTENTS]
    ):
        opp.data[DOMAIN][CONF_INTENTS][INTENT_HELP] = {CONF_SENTENCES: ["HELP"]}

    for data in opp.data[DOMAIN][CONF_INTENTS].values():
        matchers = []
        for sentence in data[CONF_SENTENCES]:
            matchers.append(create_matcher(sentence))

        data[CONF_MATCHERS] = matchers

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
        )
    )

    return True


async def async_setup_entry(opp, config):
    """Set up a config entry."""
    try:
        bot = HangoutsBot(
            opp,
            config.data.get(CONF_REFRESH_TOKEN),
            opp.data[DOMAIN][CONF_INTENTS],
            opp.data[DOMAIN][CONF_DEFAULT_CONVERSATIONS],
            opp.data[DOMAIN][CONF_ERROR_SUPPRESSED_CONVERSATIONS],
        )
        opp.data[DOMAIN][CONF_BOT] = bot
    except GoogleAuthError as exception:
        _LOGGER.error("Hangouts failed to log in: %s", str(exception))
        return False

    dispatcher.async_dispatcher_connect(
        opp, EVENT_HANGOUTS_CONNECTED, bot.async_handle_update_users_and_conversations
    )

    dispatcher.async_dispatcher_connect(
        opp, EVENT_HANGOUTS_CONVERSATIONS_CHANGED, bot.async_resolve_conversations
    )

    dispatcher.async_dispatcher_connect(
        opp,
        EVENT_HANGOUTS_CONVERSATIONS_RESOLVED,
        bot.async_update_conversation_commands,
    )

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, bot.async_handle_opp_stop)

    await bot.async_connect()

    opp.services.async_register(
        DOMAIN,
        SERVICE_SEND_MESSAGE,
        bot.async_handle_send_message,
        schema=MESSAGE_SCHEMA,
    )
    opp.services.async_register(
        DOMAIN,
        SERVICE_UPDATE,
        bot.async_handle_update_users_and_conversations,
        schema=vol.Schema({}),
    )

    opp.services.async_register(
        DOMAIN, SERVICE_RECONNECT, bot.async_handle_reconnect, schema=vol.Schema({})
    )

    intent.async_register(opp, HelpIntent(opp))

    return True


async def async_unload_entry(opp, _):
    """Unload a config entry."""
    bot = opp.data[DOMAIN].pop(CONF_BOT)
    await bot.async_disconnect()
    return True
