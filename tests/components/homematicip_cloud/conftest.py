"""Initializer helpers for HomematicIP fake server."""
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from homematicip.aio.auth import AsyncAuth
from homematicip.aio.connection import AsyncConnection
from homematicip.aio.home import AsyncHome
from homematicip.base.enums import WeatherCondition, WeatherDayTime
import pytest

from openpeerpower import config_entries
from openpeerpower.components.homematicip_cloud import (
    DOMAIN as HMIPC_DOMAIN,
    async_setup as hmip_async_setup,
)
from openpeerpower.components.homematicip_cloud.const import (
    HMIPC_AUTHTOKEN,
    HMIPC_HAPID,
    HMIPC_NAME,
    HMIPC_PIN,
)
from openpeerpower.components.homematicip_cloud.hap import HomematicipHAP
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpowerr.helpers.typing import ConfigType, OpenPeerPowerType

from .helper import AUTH_TOKEN, HAPID, HAPPIN, HomeFactory

from tests.common import MockConfigEntry
from tests.components.light.conftest import mock_light_profiles  # noqa


@pytest.fixture(name="mock_connection")
def mock_connection_fixture() -> AsyncConnection:
    """Return a mocked connection."""
    connection = MagicMock(spec=AsyncConnection)

    def _rest_call_side_effect(path, body=None):
        return path, body

    connection._restCall.side_effect = (  # pylint: disable=protected-access
        _rest_call_side_effect
    )
    connection.api_call = AsyncMock(return_value=True)
    connection.init = AsyncMock(side_effect=True)

    return connection


@pytest.fixture(name="hmip_config_entry")
def hmip_config_entry_fixture() -> config_entries.ConfigEntry:
    """Create a mock config entry for homematic ip cloud."""
    entry_data = {
        HMIPC_HAPID: HAPID,
        HMIPC_AUTHTOKEN: AUTH_TOKEN,
        HMIPC_NAME: "",
        HMIPC_PIN: HAPPIN,
    }
    config_entry = MockConfigEntry(
        version=1,
        domain=HMIPC_DOMAIN,
        title="Home Test SN",
        unique_id=HAPID,
        data=entry_data,
        source=SOURCE_IMPORT,
        connection_class=config_entries.CONN_CLASS_CLOUD_PUSH,
        system_options={"disable_new_entities": False},
    )

    return config_entry


@pytest.fixture(name="default_mock_op._factory")
async def default_mock_op._factory_fixture(
   .opp: OpenPeerPowerType, mock_connection, hmip_config_entry
) -> HomematicipHAP:
    """Create a mocked homematic access point."""
    return HomeFactory.opp, mock_connection, hmip_config_entry)


@pytest.fixture(name="hmip_config")
def hmip_config_fixture() -> ConfigType:
    """Create a config for homematic ip cloud."""

    entry_data = {
        HMIPC_HAPID: HAPID,
        HMIPC_AUTHTOKEN: AUTH_TOKEN,
        HMIPC_NAME: "",
        HMIPC_PIN: HAPPIN,
    }

    return {HMIPC_DOMAIN: [entry_data]}


@pytest.fixture(name="dummy_config")
def dummy_config_fixture() -> ConfigType:
    """Create a dummy config."""
    return {"blabla": None}


@pytest.fixture(name="mock_op._with_service")
async def mock_op._with_service_fixture(
   .opp: OpenPeerPowerType, default_mock_op._factory, dummy_config
) -> HomematicipHAP:
    """Create a fake homematic access point with opp services."""
    mock_op. = await default_mock_op._factory.async_get_mock_op.()
    await hmip_async_setup.opp, dummy_config)
    await opp..async_block_till_done()
   .opp.data[HMIPC_DOMAIN] = {HAPID: mock_op.}
    return mock_op.


@pytest.fixture(name="simple_mock_home")
def simple_mock_home_fixture():
    """Return a simple mocked connection."""

    mock_home = Mock(
        spec=AsyncHome,
        name="Demo",
        devices=[],
        groups=[],
        location=Mock(),
        weather=Mock(
            temperature=0.0,
            weatherCondition=WeatherCondition.UNKNOWN,
            weatherDayTime=WeatherDayTime.DAY,
            minTemperature=0.0,
            maxTemperature=0.0,
            humidity=0,
            windSpeed=0.0,
            windDirection=0,
            vaporAmount=0.0,
        ),
        id=42,
        dutyCycle=88,
        connected=True,
        currentAPVersion="2.0.36",
    )

    with patch(
        "openpeerpower.components.homematicip_cloud.hap.AsyncHome",
        autospec=True,
        return_value=mock_home,
    ):
        yield


@pytest.fixture(name="mock_connection_init")
def mock_connection_init_fixture():
    """Return a simple mocked connection."""

    with patch(
        "openpeerpower.components.homematicip_cloud.hap.AsyncHome.init",
        return_value=None,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.AsyncAuth.init",
        return_value=None,
    ):
        yield


@pytest.fixture(name="simple_mock_auth")
def simple_mock_auth_fixture() -> AsyncAuth:
    """Return a simple AsyncAuth Mock."""
    return Mock(spec=AsyncAuth, pin=HAPPIN, create=True)
