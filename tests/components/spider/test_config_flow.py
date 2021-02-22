"""Tests for the Spider config flow."""
from unittest.mock import Mock, patch

import pytest

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.spider.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

USERNAME = "spider-username"
PASSWORD = "spider-password"

SPIDER_USER_DATA = {
    CONF_USERNAME: USERNAME,
    CONF_PASSWORD: PASSWORD,
}


@pytest.fixture(name="spider")
def spider_fixture() -> Mock:
    """Patch libraries."""
    with patch("openpeerpower.components.spider.config_flow.SpiderApi") as spider:
        yield spider


async def test_user.opp, spider):
    """Test user config."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.spider.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.spider.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input=SPIDER_USER_DATA
        )
        await.opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DOMAIN
    assert result["data"][CONF_USERNAME] == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert not result["result"].unique_id

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import.opp, spider):
    """Test import step."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    with patch(
        "openpeerpower.components.spider.async_setup",
        return_value=True,
    ) as mock_setup, patch(
        "openpeerpower.components.spider.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=SPIDER_USER_DATA,
        )
        await.opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DOMAIN
    assert result["data"][CONF_USERNAME] == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert not result["result"].unique_id

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_abort_if_already_setup_opp, spider):
    """Test we abort if Spider is already setup."""
    MockConfigEntry(domain=DOMAIN, data=SPIDER_USER_DATA).add_to.opp.opp)

    # Should fail, config exist (import)
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=SPIDER_USER_DATA
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"

    # Should fail, config exist (flow)
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=SPIDER_USER_DATA
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"
