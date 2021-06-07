"""Test the buienradar2 config flow."""
from unittest.mock import patch

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.buienradar.const import DOMAIN
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE

from tests.common import MockConfigEntry

TEST_LATITUDE = 51.5288504
TEST_LONGITUDE = 5.4002156


async def test_config_flow_setup_(opp):
    """Test setup of camera."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.buienradar.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == f"{TEST_LATITUDE},{TEST_LONGITUDE}"
    assert result["data"] == {
        CONF_LATITUDE: TEST_LATITUDE,
        CONF_LONGITUDE: TEST_LONGITUDE,
    }


async def test_config_flow_already_configured_weather(opp):
    """Test already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LATITUDE: TEST_LATITUDE,
            CONF_LONGITUDE: TEST_LONGITUDE,
        },
        unique_id=f"{TEST_LATITUDE}-{TEST_LONGITUDE}",
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_import_camera(opp):
    """Test import of camera."""
    with patch(
        "openpeerpower.components.buienradar.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == f"{TEST_LATITUDE},{TEST_LONGITUDE}"
    assert result["data"] == {
        CONF_LATITUDE: TEST_LATITUDE,
        CONF_LONGITUDE: TEST_LONGITUDE,
    }

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_options_flow(opp):
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LATITUDE: TEST_LATITUDE,
            CONF_LONGITUDE: TEST_LONGITUDE,
        },
        unique_id=DOMAIN,
    )
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"country_code": "BE", "delta": 450, "timeframe": 30},
    )

    with patch(
        "openpeerpower.components.buienradar.async_setup_entry", return_value=True
    ), patch(
        "openpeerpower.components.buienradar.async_unload_entry", return_value=True
    ):
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

        await opp.async_block_till_done()

    assert entry.options == {"country_code": "BE", "delta": 450, "timeframe": 30}
