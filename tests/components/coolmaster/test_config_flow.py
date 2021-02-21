"""Test the Coolmaster config flow."""
from unittest.mock import patch

from openpeerpower import config_entries
from openpeerpower.components.coolmaster.const import AVAILABLE_MODES, DOMAIN


def _flow_data():
    options = {"host": "1.1.1.1"}
    for mode in AVAILABLE_MODES:
        options[mode] = True
    return options


async def test_form.opp):
    """Test we get the form."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    with patch(
        "openpeerpower.components.coolmaster.config_flow.CoolMasterNet.status",
        return_value={"test_id": "test_unit"},
    ), patch(
        "openpeerpower.components.coolmaster.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.coolmaster.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"], _flow_data()
        )
        await.opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "1.1.1.1"
    assert result2["data"] == {
        "host": "1.1.1.1",
        "port": 10102,
        "supported_modes": AVAILABLE_MODES,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_timeout.opp):
    """Test we handle a connection timeout."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.coolmaster.config_flow.CoolMasterNet.status",
        side_effect=TimeoutError(),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"], _flow_data()
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_connection_refused.opp):
    """Test we handle a connection error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.coolmaster.config_flow.CoolMasterNet.status",
        side_effect=ConnectionRefusedError(),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"], _flow_data()
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_no_units.opp):
    """Test we handle no units found."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.coolmaster.config_flow.CoolMasterNet.status",
        return_value={},
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"], _flow_data()
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "no_units"}
