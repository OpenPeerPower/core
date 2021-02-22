"""Test the Powerwall config flow."""

from unittest.mock import patch

from tesla_powerwall import (
    AccessDeniedError,
    MissingAttributeError,
    PowerwallUnreachableError,
)

from openpeerpower import config_entries, setup
from openpeerpower.components.dhcp import HOSTNAME, IP_ADDRESS, MAC_ADDRESS
from openpeerpower.components.powerwall.const import DOMAIN
from openpeerpower.const import CONF_IP_ADDRESS, CONF_PASSWORD

from .mocks import _mock_powerwall_side_effect, _mock_powerwall_site_name

from tests.common import MockConfigEntry

VALID_CONFIG = {CONF_IP_ADDRESS: "1.2.3.4", CONF_PASSWORD: "00GGX"}


async def test_form_source_user.opp):
    """Test we get config flow setup form as a user."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_powerwall = await _mock_powerwall_site_name.opp, "My site")

    with patch(
        "openpeerpower.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ), patch(
        "openpeerpower.components.powerwall.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.powerwall.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "My site"
    assert result2["data"] == VALID_CONFIG
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_powerwall = _mock_powerwall_side_effect(site_info=PowerwallUnreachableError)

    with patch(
        "openpeerpower.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {CONF_IP_ADDRESS: "cannot_connect"}


async def test_invalid_auth.opp):
    """Test we handle invalid auth error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_powerwall = _mock_powerwall_side_effect(site_info=AccessDeniedError("any"))

    with patch(
        "openpeerpower.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {CONF_PASSWORD: "invalid_auth"}


async def test_form_unknown_exeption.opp):
    """Test we handle an unknown exception."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_powerwall = _mock_powerwall_side_effect(site_info=ValueError)

    with patch(
        "openpeerpower.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], VALID_CONFIG
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_form_wrong_version.opp):
    """Test we can handle wrong version error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_powerwall = _mock_powerwall_side_effect(
        site_info=MissingAttributeError({}, "")
    )

    with patch(
        "openpeerpower.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result3 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    assert result3["type"] == "form"
    assert result3["errors"] == {"base": "wrong_version"}


async def test_already_configured.opp):
    """Test we abort when already configured."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    config_entry = MockConfigEntry(domain=DOMAIN, data={CONF_IP_ADDRESS: "1.1.1.1"})
    config_entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data={
            IP_ADDRESS: "1.1.1.1",
            MAC_ADDRESS: "AA:BB:CC:DD:EE:FF",
            HOSTNAME: "any",
        },
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_already_configured_with_ignored.opp):
    """Test ignored entries do not break checking for existing entries."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    config_entry = MockConfigEntry(domain=DOMAIN, data={}, source="ignore")
    config_entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data={
            IP_ADDRESS: "1.1.1.1",
            MAC_ADDRESS: "AA:BB:CC:DD:EE:FF",
            HOSTNAME: "any",
        },
    )
    assert result["type"] == "form"


async def test_dhcp_discovery.opp):
    """Test we can process the discovery from dhcp."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data={
            IP_ADDRESS: "1.1.1.1",
            MAC_ADDRESS: "AA:BB:CC:DD:EE:FF",
            HOSTNAME: "any",
        },
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_powerwall = await _mock_powerwall_site_name.opp, "Some site")
    with patch(
        "openpeerpower.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ), patch(
        "openpeerpower.components.powerwall.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.powerwall.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Some site"
    assert result2["data"] == VALID_CONFIG
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_reauth.opp):
    """Test reauthenticate."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id="1.2.3.4",
    )
    entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "reauth"}, data=entry.data
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_powerwall = await _mock_powerwall_site_name.opp, "My site")

    with patch(
        "openpeerpower.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ), patch(
        "openpeerpower.components.powerwall.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.powerwall.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "1.2.3.4",
                CONF_PASSWORD: "new-test-password",
            },
        )
        await opp.async_block_till_done()

    assert result2["type"] == "abort"
    assert result2["reason"] == "reauth_successful"
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
