"""Test the Plugwise config flow."""
from unittest.mock import MagicMock, patch

from plugwise.exceptions import (
    ConnectionFailedError,
    InvalidAuthentication,
    PlugwiseException,
)
import pytest

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.plugwise.const import (
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)

from tests.common import MockConfigEntry

TEST_HOST = "1.1.1.1"
TEST_HOSTNAME = "smileabcdef"
TEST_PASSWORD = "test_password"
TEST_PORT = 81
TEST_USERNAME = "smile"
TEST_USERNAME2 = "stretch"

TEST_DISCOVERY = {
    "host": TEST_HOST,
    "port": DEFAULT_PORT,
    "hostname": f"{TEST_HOSTNAME}.local.",
    "server": f"{TEST_HOSTNAME}.local.",
    "properties": {
        "product": "smile",
        "version": "1.2.3",
        "hostname": f"{TEST_HOSTNAME}.local.",
    },
}


@pytest.fixture(name="mock_smile")
def mock_smile():
    """Create a Mock Smile for testing exceptions."""
    with patch(
        "openpeerpower.components.plugwise.config_flow.Smile",
    ) as smile_mock:
        smile_mock.PlugwiseError = PlugwiseException
        smile_mock.InvalidAuthentication = InvalidAuthentication
        smile_mock.ConnectionFailedError = ConnectionFailedError
        smile_mock.return_value.connect.return_value = True
        yield smile_mock.return_value


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.plugwise.config_flow.Smile.connect",
        return_value=True,
    ), patch(
        "openpeerpower.components.plugwise.async_setup",
        return_value=True,
    ) as mock_setup, patch(
        "openpeerpower.components.plugwise.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
        )

    await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_PORT: DEFAULT_PORT,
        CONF_USERNAME: TEST_USERNAME,
    }

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_zeroconf_form.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=TEST_DISCOVERY,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.plugwise.config_flow.Smile.connect",
        return_value=True,
    ), patch(
        "openpeerpower.components.plugwise.async_setup",
        return_value=True,
    ) as mock_setup, patch(
        "openpeerpower.components.plugwise.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: TEST_PASSWORD},
        )

    await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_PORT: DEFAULT_PORT,
        CONF_USERNAME: TEST_USERNAME,
    }

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_username.opp):
    """Test we get the username data back."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.plugwise.config_flow.Smile.connect",
        return_value=True,
    ), patch(
        "openpeerpower.components.plugwise.async_setup",
        return_value=True,
    ) as mock_setup, patch(
        "openpeerpower.components.plugwise.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_PASSWORD: TEST_PASSWORD,
                CONF_USERNAME: TEST_USERNAME2,
            },
        )

    await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_PORT: DEFAULT_PORT,
        CONF_USERNAME: TEST_USERNAME2,
    }

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1

    result3 = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=TEST_DISCOVERY,
    )
    assert result3["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result3["errors"] == {}

    with patch(
        "openpeerpower.components.plugwise.config_flow.Smile.connect",
        return_value=True,
    ), patch(
        "openpeerpower.components.plugwise.async_setup",
        return_value=True,
    ) as mock_setup, patch(
        "openpeerpower.components.plugwise.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result4 = await opp.config_entries.flow.async_configure(
            result3["flow_id"],
            {CONF_PASSWORD: TEST_PASSWORD},
        )

    await opp.async_block_till_done()

    assert result4["type"] == "abort"
    assert result4["reason"] == "already_configured"


async def test_form_invalid_auth.opp, mock_smile):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_smile.connect.side_effect = InvalidAuthentication
    mock_smile.gateway_id = "0a636a4fc1704ab4a24e4f7e37fb187a"

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect.opp, mock_smile):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_smile.connect.side_effect = ConnectionFailedError
    mock_smile.gateway_id = "0a636a4fc1704ab4a24e4f7e37fb187a"

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_cannot_connect_port.opp, mock_smile):
    """Test we handle cannot connect to port error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_smile.connect.side_effect = ConnectionFailedError
    mock_smile.gateway_id = "0a636a4fc1704ab4a24e4f7e37fb187a"

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD, CONF_PORT: TEST_PORT},
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_other_problem.opp, mock_smile):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_smile.connect.side_effect = TimeoutError
    mock_smile.gateway_id = "0a636a4fc1704ab4a24e4f7e37fb187a"

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_options_flow_power.opp, mock_smile) -> None:
    """Test config flow options DSMR environments."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=CONF_NAME,
        data={CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
        options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
    )

    opp.data[DOMAIN] = {entry.entry_id: {"api": MagicMock(smile_type="power")}}
    entry.add_to.opp.opp)

    with patch(
        "openpeerpower.components.plugwise.async_setup_entry", return_value=True
    ):
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

        result = await opp.config_entries.options.async_init(entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_SCAN_INTERVAL: 10}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["data"] == {
            CONF_SCAN_INTERVAL: 10,
        }


async def test_options_flow_thermo.opp, mock_smile) -> None:
    """Test config flow options for thermostatic environments."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=CONF_NAME,
        data={CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
        options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
    )

    opp.data[DOMAIN] = {entry.entry_id: {"api": MagicMock(smile_type="thermostat")}}
    entry.add_to.opp.opp)

    with patch(
        "openpeerpower.components.plugwise.async_setup_entry", return_value=True
    ):
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

        result = await opp.config_entries.options.async_init(entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_SCAN_INTERVAL: 60}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["data"] == {
            CONF_SCAN_INTERVAL: 60,
        }
