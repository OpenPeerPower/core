"""Support for Telegram bot using polling."""
import logging

from telegram import Update
from telegram.error import NetworkError, RetryAfter, TelegramError, TimedOut
from telegram.ext import CallbackContext, Dispatcher, Handler, Updater
from telegram.utils.types import HandlerArg

from openpeerpower.const import EVENT_OPENPEERPOWER_START, EVENT_OPENPEERPOWER_STOP

from . import CONF_ALLOWED_CHAT_IDS, BaseTelegramBotEntity, initialize_bot

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform.opp, config):
    """Set up the Telegram polling platform."""
    bot = initialize_bot(config)
    pol = TelegramPoll(bot,.opp, config[CONF_ALLOWED_CHAT_IDS])

    def _start_bot(_event):
        """Start the bot."""
        pol.start_polling()

    def _stop_bot(_event):
        """Stop the bot."""
        pol.stop_polling()

   .opp.bus.async_listen_once(EVENT_OPENPEERPOWER_START, _start_bot)
   .opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, _stop_bot)

    return True


def process_error(update: Update, context: CallbackContext):
    """Telegram bot error handler."""
    try:
        raise context.error
    except (TimedOut, NetworkError, RetryAfter):
        # Long polling timeout or connection problem. Nothing serious.
        pass
    except TelegramError:
        _LOGGER.error('Update "%s" caused error: "%s"', update, context.error)


def message_handler(handler):
    """Create messages handler."""

    class MessageHandler(Handler):
        """Telegram bot message handler."""

        def __init__(self):
            """Initialize the messages handler instance."""
            super().__init__(handler)

        def check_update(self, update):
            """Check is update valid."""
            return isinstance(update, Update)

        def handle_update(
            self,
            update: HandlerArg,
            dispatcher: Dispatcher,
            check_result: object,
            context: CallbackContext = None,
        ):
            """Handle update."""
            optional_args = self.collect_optional_args(dispatcher, update)
            context.args = optional_args
            return self.callback(update, context)

    return MessageHandler()


class TelegramPoll(BaseTelegramBotEntity):
    """Asyncio telegram incoming message handler."""

    def __init__(self, bot,.opp, allowed_chat_ids):
        """Initialize the polling instance."""

        BaseTelegramBotEntity.__init__(self,.opp, allowed_chat_ids)

        self.updater = Updater(bot=bot, workers=4)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(message_handler(self.process_update))
        self.dispatcher.add_error_handler(process_error)

    def start_polling(self):
        """Start the polling task."""
        self.updater.start_polling()

    def stop_polling(self):
        """Stop the polling task."""
        self.updater.stop()

    def process_update(self, update: HandlerArg, context: CallbackContext):
        """Process incoming message."""
        self.process_message(update.to_dict())
