"""Test the Bond config flow."""
from typing import Any, Dict
from unittest.mock import Mock, patch

from aiohttp import ClientConnectionError, ClientResponseError

from openpeerpower import config_entries, core, setup
from openpeerpower.components.bond.const import DOMAIN
from openpeerpower.const import CONF_ACCESS_TOKEN, CONF_HOST

from .common import patch_bond_device_ids, patch_bond_version

from tests.common import MockConfigEntry


async def test_user_form.opp: core.OpenPeerPower):
    """Test we get the user initiated form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch_bond_version(
        return_value={"bondid": "test-bond-id"}
    ), patch_bond_device_ids(), _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "test-bond-id"
    assert result2["data"] == {
        CONF_HOST: "some host",
        CONF_ACCESS_TOKEN: "test-token",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_invalid_auth.opp: core.OpenPeerPower):
    """Test we handle invalid auth."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch_bond_version(
        return_value={"bond_id": "test-bond-id"}
    ), patch_bond_device_ids(
        side_effect=ClientResponseError(Mock(), Mock(), status=401),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_user_form_cannot_connect.opp: core.OpenPeerPower):
    """Test we handle cannot connect error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch_bond_version(
        side_effect=ClientConnectionError()
    ), patch_bond_device_ids():
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_user_form_old_firmware.opp: core.OpenPeerPower):
    """Test we handle unsupported old firmware."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch_bond_version(
        return_value={"no_bond_id": "present"}
    ), patch_bond_device_ids():
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "old_firmware"}


async def test_user_form_unexpected_client_error.opp: core.OpenPeerPower):
    """Test we handle unexpected client error gracefully."""
    await _help_test_form_unexpected_error(
       .opp,
        source=config_entries.SOURCE_USER,
        user_input={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        error=ClientResponseError(Mock(), Mock(), status=500),
    )


async def test_user_form_unexpected_error.opp: core.OpenPeerPower):
    """Test we handle unexpected error gracefully."""
    await _help_test_form_unexpected_error(
       .opp,
        source=config_entries.SOURCE_USER,
        user_input={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        error=Exception(),
    )


async def test_user_form_one_entry_per_device_allowed.opp: core.OpenPeerPower):
    """Test that only one entry allowed per unique ID reported by Bond hub device."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="already-registered-bond-id",
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    ).add_to_opp.opp)

    await setup.async_setup_component.opp, "persistent_notification", {})

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch_bond_version(
        return_value={"bondid": "already-registered-bond-id"}
    ), patch_bond_device_ids(), _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"

    await opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0


async def test_zeroconf_form.opp: core.OpenPeerPower):
    """Test we get the discovery form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data={"name": "test-bond-id.some-other-tail-info", "host": "test-host"},
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch_bond_version(
        return_value={"bondid": "test-bond-id"}
    ), patch_bond_device_ids(), _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCESS_TOKEN: "test-token"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "test-bond-id"
    assert result2["data"] == {
        CONF_HOST: "test-host",
        CONF_ACCESS_TOKEN: "test-token",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_zeroconf_already_configured.opp: core.OpenPeerPower):
    """Test starting a flow from discovery when already configured."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="already-registered-bond-id",
        data={CONF_HOST: "stored-host", CONF_ACCESS_TOKEN: "test-token"},
    )
    entry.add_to_opp.opp)

    with _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data={
                "name": "already-registered-bond-id.some-other-tail-info",
                "host": "updated-host",
            },
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "updated-host"

    await opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0


async def test_zeroconf_form_unexpected_error.opp: core.OpenPeerPower):
    """Test we handle unexpected error gracefully."""
    await _help_test_form_unexpected_error(
       .opp,
        source=config_entries.SOURCE_ZEROCONF,
        initial_input={
            "name": "test-bond-id.some-other-tail-info",
            "host": "test-host",
        },
        user_input={CONF_ACCESS_TOKEN: "test-token"},
        error=Exception(),
    )


async def _help_test_form_unexpected_error(
   .opp: core.OpenPeerPower,
    *,
    source: str,
    initial_input: Dict[str, Any] = None,
    user_input: Dict[str, Any],
    error: Exception,
):
    """Test we handle unexpected error gracefully."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": source}, data=initial_input
    )

    with patch_bond_version(
        return_value={"bond_id": "test-bond-id"}
    ), patch_bond_device_ids(side_effect=error):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


def _patch_async_setup():
    return patch("openpeerpower.components.bond.async_setup", return_value=True)


def _patch_async_setup_entry():
    return patch(
        "openpeerpower.components.bond.async_setup_entry",
        return_value=True,
    )
