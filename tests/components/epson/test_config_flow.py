"""Test the epson config flow."""
from unittest.mock import patch

from openpeerpower import config_entries, setup
from openpeerpower.components.epson.const import DOMAIN
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_PORT, STATE_UNAVAILABLE


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}
    assert result["step_id"] == config_entries.SOURCE_USER

    with patch(
        "openpeerpower.components.epson.Projector.get_property",
        return_value="04",
    ), patch(
        "openpeerpower.components.epson.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.epson.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_NAME: "test-epson", CONF_PORT: 80},
        )
    assert result2["type"] == "create_entry"
    assert result2["title"] == "test-epson"
    assert result2["data"] == {CONF_HOST: "1.1.1.1", CONF_PORT: 80}
    await opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.epson.Projector.get_property",
        return_value=STATE_UNAVAILABLE,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_NAME: "test-epson", CONF_PORT: 80},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_import.opp):
    """Test config.yaml import."""
    with patch(
        "openpeerpower.components.epson.Projector.get_property",
        return_value="04",
    ), patch("openpeerpower.components.epson.async_setup", return_value=True), patch(
        "openpeerpower.components.epson.async_setup_entry",
        return_value=True,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_HOST: "1.1.1.1", CONF_NAME: "test-epson", CONF_PORT: 80},
        )
        assert result["type"] == "create_entry"
        assert result["title"] == "test-epson"
        assert result["data"] == {CONF_HOST: "1.1.1.1", CONF_PORT: 80}


async def test_import_cannot_connect.opp):
    """Test we handle cannot connect error with import."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
    )

    with patch(
        "openpeerpower.components.epson.Projector.get_property",
        return_value=STATE_UNAVAILABLE,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_NAME: "test-epson", CONF_PORT: 80},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}
