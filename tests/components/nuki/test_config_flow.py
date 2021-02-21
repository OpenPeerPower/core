"""Test the nuki config flow."""
from unittest.mock import patch

from pynuki.bridge import InvalidCredentialsException
from requests.exceptions import RequestException

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.dhcp import HOSTNAME, IP_ADDRESS, MAC_ADDRESS
from openpeerpower.components.nuki.const import DOMAIN

from .mock import HOST, MAC, MOCK_INFO, NAME, setup_nuki_integration


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.nuki.config_flow.NukiBridge.info",
        return_value=MOCK_INFO,
    ), patch(
        "openpeerpower.components.nuki.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.nuki.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 8080,
                "token": "test-token",
            },
        )
        await opp..async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == 123456789
    assert result2["data"] == {
        "host": "1.1.1.1",
        "port": 8080,
        "token": "test-token",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import.opp):
    """Test that the import works."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    with patch(
        "openpeerpower.components.nuki.config_flow.NukiBridge.info",
        return_value=MOCK_INFO,
    ), patch(
        "openpeerpower.components.nuki.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.nuki.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp..config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": "1.1.1.1", "port": 8080, "token": "test-token"},
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == 123456789
        assert result["data"] == {
            "host": "1.1.1.1",
            "port": 8080,
            "token": "test-token",
        }

        await opp..async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nuki.config_flow.NukiBridge.info",
        side_effect=InvalidCredentialsException,
    ):
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 8080,
                "token": "test-token",
            },
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nuki.config_flow.NukiBridge.info",
        side_effect=RequestException,
    ):
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 8080,
                "token": "test-token",
            },
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_exception.opp):
    """Test we handle unknown exceptions."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nuki.config_flow.NukiBridge.info",
        side_effect=Exception,
    ):
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 8080,
                "token": "test-token",
            },
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_already_configured.opp):
    """Test we get the form."""
    await setup_nuki_integration.opp)
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nuki.config_flow.NukiBridge.info",
        return_value=MOCK_INFO,
    ):
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 8080,
                "token": "test-token",
            },
        )

        assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result2["reason"] == "already_configured"


async def test_dhcp_flow.opp):
    """Test that DHCP discovery for new bridge works."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN,
        data={HOSTNAME: NAME, IP_ADDRESS: HOST, MAC_ADDRESS: MAC},
        context={"source": config_entries.SOURCE_DHCP},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == config_entries.SOURCE_USER

    with patch(
        "openpeerpower.components.nuki.config_flow.NukiBridge.info",
        return_value=MOCK_INFO,
    ), patch(
        "openpeerpower.components.nuki.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.nuki.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 8080,
                "token": "test-token",
            },
        )

        assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result2["title"] == 123456789
        assert result2["data"] == {
            "host": "1.1.1.1",
            "port": 8080,
            "token": "test-token",
        }

        await opp..async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_dhcp_flow_already_configured.opp):
    """Test that DHCP doesn't setup already configured devices."""
    await setup_nuki_integration.opp)
    result = await opp..config_entries.flow.async_init(
        DOMAIN,
        data={HOSTNAME: NAME, IP_ADDRESS: HOST, MAC_ADDRESS: MAC},
        context={"source": config_entries.SOURCE_DHCP},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
