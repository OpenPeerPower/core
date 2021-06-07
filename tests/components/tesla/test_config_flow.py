"""Test the Tesla config flow."""
import datetime
from unittest.mock import patch

from teslajsonpy.exceptions import IncompleteCredentials, TeslaException

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.tesla.const import (
    CONF_EXPIRATION,
    CONF_WAKE_ON_START,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WAKE_ON_START,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from openpeerpower.const import (
    CONF_ACCESS_TOKEN,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USERNAME,
    HTTP_NOT_FOUND,
)

from tests.common import MockConfigEntry

TEST_USERNAME = "test-username"
TEST_TOKEN = "test-token"
TEST_PASSWORD = "test-password"
TEST_ACCESS_TOKEN = "test-access-token"
TEST_VALID_EXPIRATION = datetime.datetime.now().timestamp() * 2


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.tesla.config_flow.TeslaAPI.connect",
        return_value={
            "refresh_token": TEST_TOKEN,
            CONF_ACCESS_TOKEN: TEST_ACCESS_TOKEN,
            CONF_EXPIRATION: TEST_VALID_EXPIRATION,
        },
    ), patch(
        "openpeerpower.components.tesla.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.tesla.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "test", CONF_USERNAME: "test@email.com"}
        )
        await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "test@email.com"
    assert result2["data"] == {
        CONF_USERNAME: "test@email.com",
        CONF_PASSWORD: "test",
        CONF_TOKEN: TEST_TOKEN,
        CONF_ACCESS_TOKEN: TEST_ACCESS_TOKEN,
        CONF_EXPIRATION: TEST_VALID_EXPIRATION,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.tesla.config_flow.TeslaAPI.connect",
        side_effect=TeslaException(401),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: TEST_USERNAME, CONF_PASSWORD: TEST_PASSWORD},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_invalid_auth_incomplete_credentials(opp):
    """Test we handle invalid auth with incomplete credentials."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.tesla.config_flow.TeslaAPI.connect",
        side_effect=IncompleteCredentials(401),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: TEST_USERNAME, CONF_PASSWORD: TEST_PASSWORD},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.tesla.config_flow.TeslaAPI.connect",
        side_effect=TeslaException(code=HTTP_NOT_FOUND),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: TEST_PASSWORD, CONF_USERNAME: TEST_USERNAME},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_repeat_identifier(opp):
    """Test we handle repeat identifiers."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TEST_USERNAME,
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        options=None,
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "openpeerpower.components.tesla.config_flow.TeslaAPI.connect",
        return_value={
            "refresh_token": TEST_TOKEN,
            CONF_ACCESS_TOKEN: TEST_ACCESS_TOKEN,
            CONF_EXPIRATION: TEST_VALID_EXPIRATION,
        },
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: TEST_USERNAME, CONF_PASSWORD: TEST_PASSWORD},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"


async def test_form_reauth(opp):
    """Test we handle reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=TEST_USERNAME,
        data={"username": TEST_USERNAME, "password": "same"},
        options=None,
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH},
        data={"username": TEST_USERNAME},
    )
    with patch(
        "openpeerpower.components.tesla.config_flow.TeslaAPI.connect",
        return_value={
            "refresh_token": TEST_TOKEN,
            CONF_ACCESS_TOKEN: TEST_ACCESS_TOKEN,
            CONF_EXPIRATION: TEST_VALID_EXPIRATION,
        },
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: TEST_USERNAME, CONF_PASSWORD: "new-password"},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "reauth_successful"


async def test_import(opp):
    """Test import step."""

    with patch(
        "openpeerpower.components.tesla.config_flow.TeslaAPI.connect",
        return_value={
            "refresh_token": TEST_TOKEN,
            CONF_ACCESS_TOKEN: TEST_ACCESS_TOKEN,
            CONF_EXPIRATION: TEST_VALID_EXPIRATION,
        },
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_PASSWORD: TEST_PASSWORD, CONF_USERNAME: TEST_USERNAME},
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == TEST_USERNAME
    assert result["data"][CONF_ACCESS_TOKEN] == TEST_ACCESS_TOKEN
    assert result["data"][CONF_TOKEN] == TEST_TOKEN
    assert result["description_placeholders"] is None


async def test_option_flow(opp):
    """Test config flow options."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=None)
    entry.add_to_opp(opp)

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 350, CONF_WAKE_ON_START: True},
    )
    assert result["type"] == "create_entry"
    assert result["data"] == {CONF_SCAN_INTERVAL: 350, CONF_WAKE_ON_START: True}


async def test_option_flow_defaults(opp):
    """Test config flow options."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=None)
    entry.add_to_opp(opp)

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_WAKE_ON_START: DEFAULT_WAKE_ON_START,
    }


async def test_option_flow_input_floor(opp):
    """Test config flow options."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=None)
    entry.add_to_opp(opp)

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_SCAN_INTERVAL: 1}
    )
    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_SCAN_INTERVAL: MIN_SCAN_INTERVAL,
        CONF_WAKE_ON_START: DEFAULT_WAKE_ON_START,
    }
