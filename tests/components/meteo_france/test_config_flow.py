"""Tests for the Meteo-France config flow."""
from unittest.mock import patch

from meteofrance_api.model import Place
import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components.meteo_france.const import (
    CONF_CITY,
    DOMAIN,
    FORECAST_MODE_DAILY,
    FORECAST_MODE_HOURLY,
)
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_MODE
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry

CITY_1_POSTAL = "74220"
CITY_1_NAME = "La Clusaz"
CITY_1_LAT = 45.90417
CITY_1_LON = 6.42306
CITY_1_COUNTRY = "FR"
CITY_1_ADMIN = "Rhône-Alpes"
CITY_1_ADMIN2 = "74"
CITY_1 = Place(
    {
        "name": CITY_1_NAME,
        "lat": CITY_1_LAT,
        "lon": CITY_1_LON,
        "country": CITY_1_COUNTRY,
        "admin": CITY_1_ADMIN,
        "admin2": CITY_1_ADMIN2,
    }
)

CITY_2_NAME = "Auch"
CITY_2_LAT = 43.64528
CITY_2_LON = 0.58861
CITY_2_COUNTRY = "FR"
CITY_2_ADMIN = "Midi-Pyrénées"
CITY_2_ADMIN2 = "32"
CITY_2 = Place(
    {
        "name": CITY_2_NAME,
        "lat": CITY_2_LAT,
        "lon": CITY_2_LON,
        "country": CITY_2_COUNTRY,
        "admin": CITY_2_ADMIN,
        "admin2": CITY_2_ADMIN2,
    }
)

CITY_3_NAME = "Auchel"
CITY_3_LAT = 50.50833
CITY_3_LON = 2.47361
CITY_3_COUNTRY = "FR"
CITY_3_ADMIN = "Nord-Pas-de-Calais"
CITY_3_ADMIN2 = "62"
CITY_3 = Place(
    {
        "name": CITY_3_NAME,
        "lat": CITY_3_LAT,
        "lon": CITY_3_LON,
        "country": CITY_3_COUNTRY,
        "admin": CITY_3_ADMIN,
        "admin2": CITY_3_ADMIN2,
    }
)


@pytest.fixture(name="client_single")
def mock_controller_client_single():
    """Mock a successful client."""
    with patch(
        "openpeerpower.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.search_places.return_value = [CITY_1]
        yield service_mock


@pytest.fixture(autouse=True)
def mock_setup():
    """Prevent setup."""
    with patch(
        "openpeerpower.components.meteo_france.async_setup",
        return_value=True,
    ), patch(
        "openpeerpower.components.meteo_france.async_setup_entry",
        return_value=True,
    ):
        yield


@pytest.fixture(name="client_multiple")
def mock_controller_client_multiple():
    """Mock a successful client."""
    with patch(
        "openpeerpower.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.search_places.return_value = [CITY_2, CITY_3]
        yield service_mock


@pytest.fixture(name="client_empty")
def mock_controller_client_empty():
    """Mock a successful client."""
    with patch(
        "openpeerpower.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.search_places.return_value = []
        yield service_mock


async def test_user(opp, client_single):
    """Test user config."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # test with all provided with search returning only 1 place
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_1_POSTAL},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].unique_id == f"{CITY_1_LAT}, {CITY_1_LON}"
    assert result["title"] == f"{CITY_1}"
    assert result["data"][CONF_LATITUDE] == str(CITY_1_LAT)
    assert result["data"][CONF_LONGITUDE] == str(CITY_1_LON)


async def test_user_list(opp, client_multiple):
    """Test user config."""

    # test with all provided with search returning more than 1 place
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_2_NAME},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "cities"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CITY: f"{CITY_3};{CITY_3_LAT};{CITY_3_LON}"},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].unique_id == f"{CITY_3_LAT}, {CITY_3_LON}"
    assert result["title"] == f"{CITY_3}"
    assert result["data"][CONF_LATITUDE] == str(CITY_3_LAT)
    assert result["data"][CONF_LONGITUDE] == str(CITY_3_LON)


async def test_import(opp, client_multiple):
    """Test import step."""
    # import with all
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_CITY: CITY_2_NAME},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].unique_id == f"{CITY_2_LAT}, {CITY_2_LON}"
    assert result["title"] == f"{CITY_2}"
    assert result["data"][CONF_LATITUDE] == str(CITY_2_LAT)
    assert result["data"][CONF_LONGITUDE] == str(CITY_2_LON)


async def test_search_failed(opp, client_empty):
    """Test error displayed if no result in search."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_1_POSTAL},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_CITY: "empty"}


async def test_abort_if_already_setup(opp, client_single):
    """Test we abort if already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_LATITUDE: CITY_1_LAT, CONF_LONGITUDE: CITY_1_LON},
        unique_id=f"{CITY_1_LAT}, {CITY_1_LON}",
    ).add_to_opp(opp)

    # Should fail, same CITY same postal code (import)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_CITY: CITY_1_POSTAL},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    # Should fail, same CITY same postal code (flow)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_1_POSTAL},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(opp: OpenPeerPower):
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_LATITUDE: CITY_1_LAT, CONF_LONGITUDE: CITY_1_LON},
        unique_id=f"{CITY_1_LAT}, {CITY_1_LON}",
    )
    config_entry.add_to_opp(opp)

    assert config_entry.options == {}

    result = await opp.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    # Default
    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options[CONF_MODE] == FORECAST_MODE_DAILY

    # Manual
    result = await opp.config_entries.options.async_init(config_entry.entry_id)
    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MODE: FORECAST_MODE_HOURLY},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options[CONF_MODE] == FORECAST_MODE_HOURLY
