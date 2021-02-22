"""Tests for eafm config flow."""
from unittest.mock import patch

import pytest
from voluptuous.error import MultipleInvalid

from openpeerpower.components.eafm import const


async def test_flow_no_discovered_stations.opp, mock_get_stations):
    """Test config flow discovers no station."""
    mock_get_stations.return_value = []
    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "no_stations"


async def test_flow_invalid_station.opp, mock_get_stations):
    """Test config flow errors on invalid station."""
    mock_get_stations.return_value = [
        {"label": "My station", "stationReference": "L12345"}
    ]

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"

    with pytest.raises(MultipleInvalid):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={"station": "My other station"}
        )


async def test_flow_works.opp, mock_get_stations, mock_get_station):
    """Test config flow discovers no station."""
    mock_get_stations.return_value = [
        {"label": "My station", "stationReference": "L12345"}
    ]
    mock_get_station.return_value = [
        {"label": "My station", "stationReference": "L12345"}
    ]

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"

    with patch("openpeerpower.components.eafm.async_setup_entry", return_value=True):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={"station": "My station"}
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "My station"
    assert result["data"] == {
        "station": "L12345",
    }
