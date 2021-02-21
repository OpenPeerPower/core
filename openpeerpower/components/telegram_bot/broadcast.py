"""Support for Telegram bot to send messages only."""
import logging

from . import initialize_bot

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform.opp, config):
    """Set up the Telegram broadcast platform."""
    bot = initialize_bot(config)

    bot_config = await.opp.async_add_executor_job(bot.getMe)
    _LOGGER.debug(
        "Telegram broadcast platform setup with bot %s", bot_config["username"]
    )
    return True
