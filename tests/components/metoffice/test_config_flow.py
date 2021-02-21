"""Test the National Weather Service (NWS) config flow."""
import json
from unittest.mock import patch

from openpeerpower import config_entries, setup
from openpeerpower.components.metoffice.const import DOMAIN

from .const import (
    METOFFICE_CONFIG_WAVERTREE,
    TEST_API_KEY,
    TEST_LATITUDE_WAVERTREE,
    TEST_LONGITUDE_WAVERTREE,
    TEST_SITE_NAME_WAVERTREE,
)

from tests.common import MockConfigEntry, load_fixture


async def test_form.opp, requests_mock):
    """Test we get the form."""
   .opp.config.latitude = TEST_LATITUDE_WAVERTREE
   .opp.config.longitude = TEST_LONGITUDE_WAVERTREE

    # all metoffice test data encapsulated in here
    mock_json = json.loads(load_fixture("metoffice.json"))
    all_sites = json.dumps(mock_json["all_sites"])
    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text=all_sites)

    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.metoffice.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.metoffice.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"], {"api_key": TEST_API_KEY}
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == TEST_SITE_NAME_WAVERTREE
    assert result2["data"] == {
        "api_key": TEST_API_KEY,
        "latitude": TEST_LATITUDE_WAVERTREE,
        "longitude": TEST_LONGITUDE_WAVERTREE,
        "name": TEST_SITE_NAME_WAVERTREE,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_already_configured.opp, requests_mock):
    """Test we handle duplicate entries."""
   .opp.config.latitude = TEST_LATITUDE_WAVERTREE
   .opp.config.longitude = TEST_LONGITUDE_WAVERTREE

    # all metoffice test data encapsulated in here
    mock_json = json.loads(load_fixture("metoffice.json"))

    all_sites = json.dumps(mock_json["all_sites"])

    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text=all_sites)
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=3hourly",
        text="",
    )

    MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{TEST_LATITUDE_WAVERTREE}_{TEST_LONGITUDE_WAVERTREE}",
        data=METOFFICE_CONFIG_WAVERTREE,
    ).add_to_opp.opp)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=METOFFICE_CONFIG_WAVERTREE,
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_form_cannot_connect.opp, requests_mock):
    """Test we handle cannot connect error."""
   .opp.config.latitude = TEST_LATITUDE_WAVERTREE
   .opp.config.longitude = TEST_LONGITUDE_WAVERTREE

    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text="")

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": TEST_API_KEY},
    )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error.opp, mock_simple_manager_fail):
    """Test we handle unknown error."""
    mock_instance = mock_simple_manager_fail.return_value
    mock_instance.get_nearest_forecast_site.side_effect = ValueError

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": TEST_API_KEY},
    )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}
