"""Define tests for the GeoNet NZ Quakes config flow."""
from datetime import timedelta
from unittest.mock import patch

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.geonetnz_quakes import (
    CONF_MINIMUM_MAGNITUDE,
    CONF_MMI,
    DOMAIN,
)
from openpeerpower.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_SYSTEM,
)


async def test_duplicate_error(opp, config_entry):
    """Test that errors are shown when duplicates are added."""
    conf = {CONF_LATITUDE: -41.2, CONF_LONGITUDE: 174.7, CONF_RADIUS: 25}
    config_entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=conf
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_show_form(opp):
    """Test that the form is served with no input."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_step_import(opp):
    """Test that the import step works."""
    conf = {
        CONF_LATITUDE: -41.2,
        CONF_LONGITUDE: 174.7,
        CONF_RADIUS: 25,
        CONF_UNIT_SYSTEM: "metric",
        CONF_MMI: 2,
        CONF_SCAN_INTERVAL: timedelta(minutes=4),
        CONF_MINIMUM_MAGNITUDE: 2.5,
    }

    with patch(
        "openpeerpower.components.geonetnz_quakes.async_setup_entry", return_value=True
    ), patch("openpeerpower.components.geonetnz_quakes.async_setup", return_value=True):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=conf
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "-41.2, 174.7"
    assert result["data"] == {
        CONF_LATITUDE: -41.2,
        CONF_LONGITUDE: 174.7,
        CONF_RADIUS: 25,
        CONF_MMI: 2,
        CONF_UNIT_SYSTEM: "metric",
        CONF_SCAN_INTERVAL: 240.0,
        CONF_MINIMUM_MAGNITUDE: 2.5,
    }


async def test_step_user(opp):
    """Test that the user step works."""
    opp.config.latitude = -41.2
    opp.config.longitude = 174.7
    conf = {CONF_RADIUS: 25, CONF_MMI: 4}

    with patch(
        "openpeerpower.components.geonetnz_quakes.async_setup_entry", return_value=True
    ), patch("openpeerpower.components.geonetnz_quakes.async_setup", return_value=True):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=conf
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "-41.2, 174.7"
    assert result["data"] == {
        CONF_LATITUDE: -41.2,
        CONF_LONGITUDE: 174.7,
        CONF_RADIUS: 25,
        CONF_MMI: 4,
        CONF_SCAN_INTERVAL: 300.0,
        CONF_MINIMUM_MAGNITUDE: 0.0,
    }
