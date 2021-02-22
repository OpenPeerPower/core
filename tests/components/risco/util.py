"""Utilities for Risco tests."""
from unittest.mock import MagicMock, PropertyMock, patch

from pytest import fixture

from openpeerpower.components.risco.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_PIN, CONF_USERNAME

from tests.common import MockConfigEntry

TEST_CONFIG = {
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
    CONF_PIN: "1234",
}
TEST_SITE_UUID = "test-site-uuid"
TEST_SITE_NAME = "test-site-name"


async def setup_risco.opp, events=[], options={}):
    """Set up a Risco integration for testing."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=TEST_CONFIG, options=options)
    config_entry.add_to.opp.opp)

    with patch(
        "openpeerpower.components.risco.RiscoAPI.login",
        return_value=True,
    ), patch(
        "openpeerpower.components.risco.RiscoAPI.site_uuid",
        new_callable=PropertyMock(return_value=TEST_SITE_UUID),
    ), patch(
        "openpeerpower.components.risco.RiscoAPI.site_name",
        new_callable=PropertyMock(return_value=TEST_SITE_NAME),
    ), patch(
        "openpeerpower.components.risco.RiscoAPI.close"
    ), patch(
        "openpeerpower.components.risco.RiscoAPI.get_events",
        return_value=events,
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    return config_entry


def _zone_mock():
    return MagicMock(
        triggered=False,
        bypassed=False,
    )


@fixture
def two_zone_alarm():
    """Fixture to mock alarm with two zones."""
    zone_mocks = {0: _zone_mock(), 1: _zone_mock()}
    alarm_mock = MagicMock()
    with patch.object(
        zone_mocks[0], "id", new_callable=PropertyMock(return_value=0)
    ), patch.object(
        zone_mocks[0], "name", new_callable=PropertyMock(return_value="Zone 0")
    ), patch.object(
        zone_mocks[1], "id", new_callable=PropertyMock(return_value=1)
    ), patch.object(
        zone_mocks[1], "name", new_callable=PropertyMock(return_value="Zone 1")
    ), patch.object(
        alarm_mock,
        "zones",
        new_callable=PropertyMock(return_value=zone_mocks),
    ), patch(
        "openpeerpower.components.risco.RiscoAPI.get_state",
        return_value=alarm_mock,
    ):
        yield alarm_mock
