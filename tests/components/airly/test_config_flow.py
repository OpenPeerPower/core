"""Define tests for the Airly config flow."""
from airly.exceptions import AirlyError

from openpeerpower import data_entry_flow
from openpeerpower.components.airly.const import CONF_USE_NEAREST, DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    HTTP_NOT_FOUND,
    HTTP_UNAUTHORIZED,
)

from . import API_NEAREST_URL, API_POINT_URL

from tests.common import MockConfigEntry, load_fixture, patch

CONFIG = {
    CONF_NAME: "Home",
    CONF_API_KEY: "foo",
    CONF_LATITUDE: 123,
    CONF_LONGITUDE: 456,
}


async def test_show_form.opp):
    """Test that the form is served with no input."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER


async def test_invalid_api_key.opp, aioclient_mock):
    """Test that errors are shown when API key is invalid."""
    aioclient_mock.get(
        API_POINT_URL,
        exc=AirlyError(
            HTTP_UNAUTHORIZED, {"message": "Invalid authentication credentials"}
        ),
    )

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    assert result["errors"] == {"base": "invalid_api_key"}


async def test_invalid_location.opp, aioclient_mock):
    """Test that errors are shown when location is invalid."""
    aioclient_mock.get(API_POINT_URL, text=load_fixture("airly_no_station.json"))

    aioclient_mock.get(
        API_NEAREST_URL,
        exc=AirlyError(HTTP_NOT_FOUND, {"message": "Installation was not found"}),
    )

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    assert result["errors"] == {"base": "wrong_location"}


async def test_duplicate_error(opp, aioclient_mock):
    """Test that errors are shown when duplicates are added."""
    aioclient_mock.get(API_POINT_URL, text=load_fixture("airly_valid_station.json"))
    MockConfigEntry(domain=DOMAIN, unique_id="123-456", data=CONFIG).add_to.opp.opp)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_create_entry.opp, aioclient_mock):
    """Test that the user step works."""
    aioclient_mock.get(API_POINT_URL, text=load_fixture("airly_valid_station.json"))

    with patch("openpeerpower.components.airly.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == CONFIG[CONF_NAME]
    assert result["data"][CONF_LATITUDE] == CONFIG[CONF_LATITUDE]
    assert result["data"][CONF_LONGITUDE] == CONFIG[CONF_LONGITUDE]
    assert result["data"][CONF_API_KEY] == CONFIG[CONF_API_KEY]
    assert result["data"][CONF_USE_NEAREST] is False


async def test_create_entry_with_nearest_method.opp, aioclient_mock):
    """Test that the user step works with nearest method."""

    aioclient_mock.get(API_POINT_URL, text=load_fixture("airly_no_station.json"))

    aioclient_mock.get(API_NEAREST_URL, text=load_fixture("airly_valid_station.json"))

    with patch("openpeerpower.components.airly.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == CONFIG[CONF_NAME]
    assert result["data"][CONF_LATITUDE] == CONFIG[CONF_LATITUDE]
    assert result["data"][CONF_LONGITUDE] == CONFIG[CONF_LONGITUDE]
    assert result["data"][CONF_API_KEY] == CONFIG[CONF_API_KEY]
    assert result["data"][CONF_USE_NEAREST] is True
