"""Test the habitica init module."""
from openpeerpower.components.habitica.const import (
    DEFAULT_URL,
    DOMAIN,
    SERVICE_API_CALL,
)

from tests.common import MockConfigEntry


async def test_entry_setup_unload(opp, aioclient_mock):
    """Test integration setup and unload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test-api-user",
        data={
            "api_user": "test-api-user",
            "api_key": "test-api-key",
            "url": DEFAULT_URL,
        },
    )
    entry.add_to(opp.opp)

    aioclient_mock.get(
        "https://habitica.com/api/v3/user",
        json={"data": {"api_user": "test-api-user", "profile": {"name": "test_user"}}},
    )

    assert await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert opp.services.has_service(DOMAIN, SERVICE_API_CALL)

    assert await opp.config_entries.async_unload(entry.entry_id)

    assert not.opp.services.has_service(DOMAIN, SERVICE_API_CALL)
