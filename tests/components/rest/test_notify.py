"""The tests for the rest.notify platform."""
from os import path
from unittest.mock import patch

import respx

from openpeerpower import config as opp_config
import openpeerpower.components.notify as notify
from openpeerpower.components.rest import DOMAIN
from openpeerpower.const import SERVICE_RELOAD
from openpeerpower.setup import async_setup_component


@respx.mock
async def test_reload_notify(opp):
    """Verify we can reload the notify service."""
    respx.get("http://localhost") % 200

    assert await async_setup_component(
        opp,
        notify.DOMAIN,
        {
            notify.DOMAIN: [
                {
                    "name": DOMAIN,
                    "platform": DOMAIN,
                    "resource": "http://127.0.0.1/off",
                },
            ]
        },
    )
    await opp.async_block_till_done()

    assert opp.services.has_service(notify.DOMAIN, DOMAIN)

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "rest/configuration.yaml",
    )
    with patch.object(opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert not opp.services.has_service(notify.DOMAIN, DOMAIN)
    assert opp.services.has_service(notify.DOMAIN, "rest_reloaded")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
