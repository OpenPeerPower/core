"""Fixtures for history tests."""
import pytest

from openpeerpower.components import history
from openpeerpower.setup import setup_component


@pytest.fixture
def opp_history(opp_recorder):
    """Open Peer Power fixture with history."""
    opp = opp_recorder()

    config = history.CONFIG_SCHEMA(
        {
            history.DOMAIN: {
                history.CONF_INCLUDE: {
                    history.CONF_DOMAINS: ["media_player"],
                    history.CONF_ENTITIES: ["thermostat.test"],
                },
                history.CONF_EXCLUDE: {
                    history.CONF_DOMAINS: ["thermostat"],
                    history.CONF_ENTITIES: ["media_player.test"],
                },
            }
        }
    )
    assert setup_component(opp, history.DOMAIN, config)

    yield opp
