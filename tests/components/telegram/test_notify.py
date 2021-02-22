"""The tests for the telegram.notify platform."""
from os import path
from unittest.mock import patch

from openpeerpower import config as.opp_config
import openpeerpower.components.notify as notify
from openpeerpower.components.telegram import DOMAIN
from openpeerpower.const import SERVICE_RELOAD
from openpeerpower.setup import async_setup_component


async def test_reload_notify.opp):
    """Verify we can reload the notify service."""

    with patch("openpeerpower.components.telegram_bot.async_setup", return_value=True):
        assert await async_setup_component(
           .opp,
            notify.DOMAIN,
            {
                notify.DOMAIN: [
                    {
                        "name": DOMAIN,
                        "platform": DOMAIN,
                        "chat_id": 1,
                    },
                ]
            },
        )
        await opp.async_block_till_done()

    assert.opp.services.has_service(notify.DOMAIN, DOMAIN)

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "telegram/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert not.opp.services.has_service(notify.DOMAIN, DOMAIN)
    assert.opp.services.has_service(notify.DOMAIN, "telegram_reloaded")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
