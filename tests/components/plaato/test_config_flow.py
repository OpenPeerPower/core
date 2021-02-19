"""Test the Plaato config flow."""
from unittest.mock import patch

from pyplaato.models.device import PlaatoDeviceType
import pytest

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.plaato.const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    CONF_USE_WEBHOOK,
    DOMAIN,
)
from openpeerpower.const import CONF_SCAN_INTERVAL, CONF_TOKEN, CONF_WEBHOOK_ID
from openpeerpowerr.data_entry_flow import RESULT_TYPE_CREATE_ENTRY, RESULT_TYPE_FORM

from tests.common import MockConfigEntry

BASE_URL = "http://example.com"
WEBHOOK_ID = "webhook_id"
UNIQUE_ID = "plaato_unique_id"


@pytest.fixture(name="webhook_id")
def mock_webhook_id():
    """Mock webhook_id."""
    with patch(
        "openpeerpower.components.webhook.async_generate_id", return_value=WEBHOOK_ID
    ), patch(
        "openpeerpower.components.webhook.async_generate_url", return_value="hook_id"
    ):
        yield


async def test_show_config_form.opp):
    """Test show configuration form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_show_config_form_device_type_airlock.opp):
    """Test show configuration form."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"
    assert result["data_schema"].schema.get(CONF_TOKEN) == str
    assert result["data_schema"].schema.get(CONF_USE_WEBHOOK) == bool


async def test_show_config_form_device_type_keg.opp):
    """Test show configuration form."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_DEVICE_TYPE: PlaatoDeviceType.Keg, CONF_DEVICE_NAME: "device_name"},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"
    assert result["data_schema"].schema.get(CONF_TOKEN) == str
    assert result["data_schema"].schema.get(CONF_USE_WEBHOOK) is None


async def test_show_config_form_validate_webhook.opp, webhook_id):
    """Test show configuration form."""

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"

   .opp.config.components.add("cloud")
    with patch(
        "openpeerpower.components.cloud.async_active_subscription", return_value=True
    ), patch(
        "openpeerpower.components.cloud.async_create_cloudhook",
        return_value="https://hooks.nabu.casa/ABCD",
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_TOKEN: "",
                CONF_USE_WEBHOOK: True,
            },
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "webhook"


async def test_show_config_form_validate_token.opp):
    """Test show configuration form."""

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Keg,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"

    with patch("openpeerpower.components.plaato.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_TOKEN: "valid_token"}
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == PlaatoDeviceType.Keg.name
    assert result["data"] == {
        CONF_USE_WEBHOOK: False,
        CONF_TOKEN: "valid_token",
        CONF_DEVICE_TYPE: PlaatoDeviceType.Keg,
        CONF_DEVICE_NAME: "device_name",
    }


async def test_show_config_form_no_cloud_webhook.opp, webhook_id):
    """Test show configuration form."""

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USE_WEBHOOK: True,
            CONF_TOKEN: "",
        },
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "webhook"
    assert result["errors"] is None


async def test_show_config_form_api_method_no_auth_token.opp, webhook_id):
    """Test show configuration form."""

    # Using Keg
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Keg,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOKEN: ""}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"
    assert len(result["errors"]) == 1
    assert result["errors"]["base"] == "no_auth_token"

    # Using Airlock
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOKEN: ""}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "api_method"
    assert len(result["errors"]) == 1
    assert result["errors"]["base"] == "no_api_method"


async def test_options.opp):
    """Test updating options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="NAME",
        data={},
        options={CONF_SCAN_INTERVAL: 5},
    )
    config_entry.add_to_opp.opp)

    with patch(
        "openpeerpower.components.plaato.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.plaato.async_setup_entry", return_value=True
    ) as mock_setup_entry:

        await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

        result = await.opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result = await.opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_SCAN_INTERVAL: 10},
        )

        await.opp.async_block_till_done()

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["data"][CONF_SCAN_INTERVAL] == 10

        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_options_webhook.opp, webhook_id):
    """Test updating options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="NAME",
        data={CONF_USE_WEBHOOK: True, CONF_WEBHOOK_ID: None},
        options={CONF_SCAN_INTERVAL: 5},
    )
    config_entry.add_to_opp.opp)

    with patch(
        "openpeerpower.components.plaato.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.plaato.async_setup_entry", return_value=True
    ) as mock_setup_entry:

        await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

        result = await.opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "webhook"
        assert result["description_placeholders"] == {"webhook_url": ""}

        result = await.opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_WEBHOOK_ID: WEBHOOK_ID},
        )

        await.opp.async_block_till_done()

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["data"][CONF_WEBHOOK_ID] == CONF_WEBHOOK_ID

        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1
