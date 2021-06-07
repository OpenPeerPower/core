"""Test the Ruckus Unleashed config flow."""
from datetime import timedelta
from unittest.mock import patch

from pyruckus.exceptions import AuthenticationError

from openpeerpower import config_entries
from openpeerpower.components.ruckus_unleashed.const import DOMAIN
from openpeerpower.util import utcnow

from tests.common import async_fire_time_changed
from tests.components.ruckus_unleashed import CONFIG, DEFAULT_SYSTEM_INFO, DEFAULT_TITLE


async def test_form(opp):
    """Test we get the form."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.connect",
        return_value=None,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.mesh_name",
        return_value=DEFAULT_TITLE,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.system_info",
        return_value=DEFAULT_SYSTEM_INFO,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == DEFAULT_TITLE
    assert result2["data"] == CONFIG
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.connect",
        side_effect=AuthenticationError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.connect",
        side_effect=ConnectionError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error(opp):
    """Test we handle unknown error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.connect",
        side_effect=Exception,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_form_cannot_connect_unknown_serial(opp):
    """Test we handle cannot connect error on invalid serial number."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.connect",
        return_value=None,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.mesh_name",
        return_value=DEFAULT_TITLE,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.system_info",
        return_value={},
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_duplicate_error(opp):
    """Test we handle duplicate error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.connect",
        return_value=None,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.mesh_name",
        return_value=DEFAULT_TITLE,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.system_info",
        return_value=DEFAULT_SYSTEM_INFO,
    ):
        await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

        future = utcnow() + timedelta(minutes=60)
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"
        assert result["errors"] == {}

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"
