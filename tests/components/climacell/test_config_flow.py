"""Test the ClimaCell config flow."""
import logging
from unittest.mock import patch

from pyclimacell.exceptions import (
    CantConnectException,
    InvalidAPIKeyException,
    RateLimitedException,
    UnknownException,
)

from openpeerpower import data_entry_flow
from openpeerpower.components.climacell.config_flow import (
    _get_config_schema,
    _get_unique_id,
)
from openpeerpower.components.climacell.const import (
    CONF_TIMESTEP,
    DEFAULT_NAME,
    DEFAULT_TIMESTEP,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import (
    CONF_API_KEY,
    CONF_API_VERSION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
)
from openpeerpower.core import OpenPeerPower

from .const import API_KEY, MIN_CONFIG

from tests.common import MockConfigEntry

_LOGGER = logging.getLogger(__name__)


async def test_user_flow_minimum_fields(opp: OpenPeerPower) -> None:
    """Test user config flow with minimum fields."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_get_config_schema(opp, MIN_CONFIG)(MIN_CONFIG),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"][CONF_NAME] == DEFAULT_NAME
    assert result["data"][CONF_API_KEY] == API_KEY
    assert result["data"][CONF_API_VERSION] == 4
    assert result["data"][CONF_LATITUDE] == opp.config.latitude
    assert result["data"][CONF_LONGITUDE] == opp.config.longitude


async def test_user_flow_v3(opp: OpenPeerPower) -> None:
    """Test user config flow with v3 API."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    data = _get_config_schema(opp, MIN_CONFIG)(MIN_CONFIG)
    data[CONF_API_VERSION] = 3

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=data,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"][CONF_NAME] == DEFAULT_NAME
    assert result["data"][CONF_API_KEY] == API_KEY
    assert result["data"][CONF_API_VERSION] == 3
    assert result["data"][CONF_LATITUDE] == opp.config.latitude
    assert result["data"][CONF_LONGITUDE] == opp.config.longitude


async def test_user_flow_same_unique_ids(opp: OpenPeerPower) -> None:
    """Test user config flow with the same unique ID as an existing entry."""
    user_input = _get_config_schema(opp, MIN_CONFIG)(MIN_CONFIG)
    MockConfigEntry(
        domain=DOMAIN,
        data=user_input,
        source=SOURCE_USER,
        unique_id=_get_unique_id(opp, user_input),
        version=2,
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=user_input,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_cannot_connect(opp: OpenPeerPower) -> None:
    """Test user config flow when ClimaCell can't connect."""
    with patch(
        "openpeerpower.components.climacell.config_flow.ClimaCellV4.realtime",
        side_effect=CantConnectException,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=_get_config_schema(opp, MIN_CONFIG)(MIN_CONFIG),
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_invalid_api(opp: OpenPeerPower) -> None:
    """Test user config flow when API key is invalid."""
    with patch(
        "openpeerpower.components.climacell.config_flow.ClimaCellV4.realtime",
        side_effect=InvalidAPIKeyException,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=_get_config_schema(opp, MIN_CONFIG)(MIN_CONFIG),
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_api_key"}


async def test_user_flow_rate_limited(opp: OpenPeerPower) -> None:
    """Test user config flow when API key is rate limited."""
    with patch(
        "openpeerpower.components.climacell.config_flow.ClimaCellV4.realtime",
        side_effect=RateLimitedException,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=_get_config_schema(opp, MIN_CONFIG)(MIN_CONFIG),
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {CONF_API_KEY: "rate_limited"}


async def test_user_flow_unknown_exception(opp: OpenPeerPower) -> None:
    """Test user config flow when unknown error occurs."""
    with patch(
        "openpeerpower.components.climacell.config_flow.ClimaCellV4.realtime",
        side_effect=UnknownException,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=_get_config_schema(opp, MIN_CONFIG)(MIN_CONFIG),
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "unknown"}


async def test_options_flow(opp: OpenPeerPower) -> None:
    """Test options config flow for climacell."""
    user_config = _get_config_schema(opp)(MIN_CONFIG)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=user_config,
        source=SOURCE_USER,
        unique_id=_get_unique_id(opp, user_config),
        version=1,
    )
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)

    assert entry.options[CONF_TIMESTEP] == DEFAULT_TIMESTEP
    assert CONF_TIMESTEP not in entry.data

    result = await opp.config_entries.options.async_init(entry.entry_id, data=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_TIMESTEP: 1}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"][CONF_TIMESTEP] == 1
    assert entry.options[CONF_TIMESTEP] == 1
