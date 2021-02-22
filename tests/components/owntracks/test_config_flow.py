"""Tests for OwnTracks config flow."""
from unittest.mock import patch

import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components.owntracks import config_flow
from openpeerpower.components.owntracks.config_flow import CONF_CLOUDHOOK, CONF_SECRET
from openpeerpower.components.owntracks.const import DOMAIN
from openpeerpower.config import async_process_ha_core_config
from openpeerpower.const import CONF_WEBHOOK_ID
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry

CONF_WEBHOOK_URL = "webhook_url"

BASE_URL = "http://example.com"
CLOUDHOOK = False
SECRET = "test-secret"
WEBHOOK_ID = "webhook_id"
WEBHOOK_URL = f"{BASE_URL}/api/webhook/webhook_id"


@pytest.fixture(name="webhook_id")
def mock_webhook_id():
    """Mock webhook_id."""
    with patch(
        "openpeerpower.components.webhook.async_generate_id", return_value=WEBHOOK_ID
    ):
        yield


@pytest.fixture(name="secret")
def mock_secret():
    """Mock secret."""
    with patch("secrets.token_hex", return_value=SECRET):
        yield


@pytest.fixture(name="not_supports_encryption")
def mock_not_supports_encryption():
    """Mock non successful nacl import."""
    with patch(
        "openpeerpower.components.owntracks.config_flow.supports_encryption",
        return_value=False,
    ):
        yield


async def init_config_flow.opp):
    """Init a configuration flow."""
    await async_process_ha_core_config(
       .opp,
        {"external_url": BASE_URL},
    )
    flow = config_flow.OwnTracksFlow()
    flow.opp =.opp
    return flow


async def test_user.opp, webhook_id, secret):
    """Test user step."""
    flow = await init_config_flow.opp)

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await flow.async_step_user({})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "OwnTracks"
    assert result["data"][CONF_WEBHOOK_ID] == WEBHOOK_ID
    assert result["data"][CONF_SECRET] == SECRET
    assert result["data"][CONF_CLOUDHOOK] == CLOUDHOOK
    assert result["description_placeholders"][CONF_WEBHOOK_URL] == WEBHOOK_URL


async def test_import.opp, webhook_id, secret):
    """Test import step."""
    flow = await init_config_flow.opp)

    result = await flow.async_step_import({})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "OwnTracks"
    assert result["data"][CONF_WEBHOOK_ID] == WEBHOOK_ID
    assert result["data"][CONF_SECRET] == SECRET
    assert result["data"][CONF_CLOUDHOOK] == CLOUDHOOK
    assert result["description_placeholders"] is None


async def test_import_setup_opp):
    """Test that we automatically create a config flow."""
    await async_process_ha_core_config(
       .opp,
        {"external_url": "http://example.com"},
    )

    assert not.opp.config_entries.async_entries(DOMAIN)
    assert await async_setup_component.opp, DOMAIN, {"owntracks": {}})
    await.opp.async_block_till_done()
    assert.opp.config_entries.async_entries(DOMAIN)


async def test_abort_if_already_setup_opp):
    """Test that we can't add more than one instance."""
    flow = await init_config_flow.opp)

    MockConfigEntry(domain=DOMAIN, data={}).add_to.opp.opp)
    assert.opp.config_entries.async_entries(DOMAIN)

    # Should fail, already setup (import)
    result = await flow.async_step_import({})
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"

    # Should fail, already setup (flow)
    result = await flow.async_step_user({})
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_user_not_supports_encryption.opp, not_supports_encryption):
    """Test user step."""
    flow = await init_config_flow.opp)

    result = await flow.async_step_user({})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert (
        result["description_placeholders"]["secret"]
        == "Encryption is not supported because nacl is not installed."
    )


async def test_unload.opp):
    """Test unloading a config flow."""
    await async_process_ha_core_config(
       .opp,
        {"external_url": "http://example.com"},
    )

    with patch(
        "openpeerpower.config_entries.ConfigEntries.async_forward_entry_setup"
    ) as mock_forward:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "import"}, data={}
        )

    assert len(mock_forward.mock_calls) == 1
    entry = result["result"]

    assert mock_forward.mock_calls[0][1][0] is entry
    assert mock_forward.mock_calls[0][1][1] == "device_tracker"
    assert entry.data["webhook_id"] in.opp.data["webhook"]

    with patch(
        "openpeerpower.config_entries.ConfigEntries.async_forward_entry_unload",
        return_value=None,
    ) as mock_unload:
        assert await.opp.config_entries.async_unload(entry.entry_id)

    assert len(mock_unload.mock_calls) == 1
    assert mock_forward.mock_calls[0][1][0] is entry
    assert mock_forward.mock_calls[0][1][1] == "device_tracker"
    assert entry.data["webhook_id"] not in.opp.data["webhook"]


async def test_with_cloud_sub.opp):
    """Test creating a config flow while subscribed."""
   .opp.config.components.add("cloud")
    with patch(
        "openpeerpower.components.cloud.async_active_subscription", return_value=True
    ), patch(
        "openpeerpower.components.cloud.async_create_cloudhook",
        return_value="https://hooks.nabu.casa/ABCD",
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data={}
        )

    entry = result["result"]
    assert entry.data["cloudhook"]
    assert (
        result["description_placeholders"]["webhook_url"]
        == "https://hooks.nabu.casa/ABCD"
    )
