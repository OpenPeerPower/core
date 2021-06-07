"""Define tests for the AirVisual config flow."""
from unittest.mock import patch

from pyairvisual.errors import (
    AirVisualError,
    InvalidKeyError,
    NodeProError,
    NotFoundError,
)

from openpeerpower import data_entry_flow
from openpeerpower.components.airvisual.const import (
    CONF_CITY,
    CONF_COUNTRY,
    CONF_GEOGRAPHIES,
    CONF_INTEGRATION_TYPE,
    DOMAIN,
    INTEGRATION_TYPE_GEOGRAPHY_COORDS,
    INTEGRATION_TYPE_GEOGRAPHY_NAME,
    INTEGRATION_TYPE_NODE_PRO,
)
from openpeerpower.config_entries import SOURCE_REAUTH, SOURCE_USER
from openpeerpower.const import (
    CONF_API_KEY,
    CONF_IP_ADDRESS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_SHOW_ON_MAP,
    CONF_STATE,
)
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_duplicate_error(opp):
    """Test that errors are shown when duplicate entries are added."""
    geography_conf = {
        CONF_API_KEY: "abcde12345",
        CONF_LATITUDE: 51.528308,
        CONF_LONGITUDE: -0.3817765,
    }

    MockConfigEntry(
        domain=DOMAIN, unique_id="51.528308, -0.3817765", data=geography_conf
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"type": INTEGRATION_TYPE_GEOGRAPHY_COORDS},
    )
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=geography_conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    node_pro_conf = {CONF_IP_ADDRESS: "192.168.1.100", CONF_PASSWORD: "12345"}

    MockConfigEntry(
        domain=DOMAIN, unique_id="192.168.1.100", data=node_pro_conf
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"type": "AirVisual Node/Pro"}
    )
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=node_pro_conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_invalid_identifier_geography_api_key(opp):
    """Test that an invalid API key throws an error."""
    with patch(
        "pyairvisual.air_quality.AirQuality.nearest_city",
        side_effect=InvalidKeyError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"type": INTEGRATION_TYPE_GEOGRAPHY_COORDS},
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "abcde12345",
                CONF_LATITUDE: 51.528308,
                CONF_LONGITUDE: -0.3817765,
            },
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_api_key"}


async def test_invalid_identifier_geography_name(opp):
    """Test that an invalid location name throws an error."""
    with patch(
        "pyairvisual.air_quality.AirQuality.city",
        side_effect=NotFoundError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"type": INTEGRATION_TYPE_GEOGRAPHY_NAME},
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "abcde12345",
                CONF_CITY: "Beijing",
                CONF_STATE: "Beijing",
                CONF_COUNTRY: "China",
            },
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {CONF_CITY: "location_not_found"}


async def test_invalid_identifier_geography_unknown(opp):
    """Test that an unknown identifier issue throws an error."""
    with patch(
        "pyairvisual.air_quality.AirQuality.city",
        side_effect=AirVisualError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"type": INTEGRATION_TYPE_GEOGRAPHY_NAME},
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "abcde12345",
                CONF_CITY: "Beijing",
                CONF_STATE: "Beijing",
                CONF_COUNTRY: "China",
            },
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "unknown"}


async def test_invalid_identifier_node_pro(opp):
    """Test that an invalid Node/Pro identifier shows an error."""
    node_pro_conf = {CONF_IP_ADDRESS: "192.168.1.100", CONF_PASSWORD: "my_password"}

    with patch(
        "pyairvisual.node.NodeSamba.async_connect",
        side_effect=NodeProError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={"type": "AirVisual Node/Pro"}
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input=node_pro_conf
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {CONF_IP_ADDRESS: "cannot_connect"}


async def test_migration(opp):
    """Test migrating from version 1 to the current version."""
    conf = {
        CONF_API_KEY: "abcde12345",
        CONF_GEOGRAPHIES: [
            {CONF_LATITUDE: 51.528308, CONF_LONGITUDE: -0.3817765},
            {CONF_CITY: "Beijing", CONF_STATE: "Beijing", CONF_COUNTRY: "China"},
        ],
    }

    config_entry = MockConfigEntry(
        domain=DOMAIN, version=1, unique_id="abcde12345", data=conf
    )
    config_entry.add_to_opp(opp)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1

    with patch("pyairvisual.air_quality.AirQuality.city"), patch(
        "pyairvisual.air_quality.AirQuality.nearest_city"
    ), patch.object(opp.config_entries, "async_forward_entry_setup"):
        assert await async_setup_component(opp, DOMAIN, {DOMAIN: conf})
        await opp.async_block_till_done()

    config_entries = opp.config_entries.async_entries(DOMAIN)

    assert len(config_entries) == 2

    assert config_entries[0].unique_id == "51.528308, -0.3817765"
    assert config_entries[0].title == "Cloud API (51.528308, -0.3817765)"
    assert config_entries[0].data == {
        CONF_API_KEY: "abcde12345",
        CONF_LATITUDE: 51.528308,
        CONF_LONGITUDE: -0.3817765,
        CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_COORDS,
    }

    assert config_entries[1].unique_id == "Beijing, Beijing, China"
    assert config_entries[1].title == "Cloud API (Beijing, Beijing, China)"
    assert config_entries[1].data == {
        CONF_API_KEY: "abcde12345",
        CONF_CITY: "Beijing",
        CONF_STATE: "Beijing",
        CONF_COUNTRY: "China",
        CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_NAME,
    }


async def test_options_flow(opp):
    """Test config flow options."""
    geography_conf = {
        CONF_API_KEY: "abcde12345",
        CONF_LATITUDE: 51.528308,
        CONF_LONGITUDE: -0.3817765,
    }

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="51.528308, -0.3817765",
        data=geography_conf,
        options={CONF_SHOW_ON_MAP: True},
    )
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.airvisual.async_setup_entry", return_value=True
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        result = await opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_SHOW_ON_MAP: False}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options == {CONF_SHOW_ON_MAP: False}


async def test_step_geography_by_coords(opp):
    """Test setting up a geopgraphy entry by latitude/longitude."""
    conf = {
        CONF_API_KEY: "abcde12345",
        CONF_LATITUDE: 51.528308,
        CONF_LONGITUDE: -0.3817765,
    }

    with patch(
        "openpeerpower.components.airvisual.async_setup_entry", return_value=True
    ), patch("pyairvisual.air_quality.AirQuality.nearest_city"):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"type": INTEGRATION_TYPE_GEOGRAPHY_COORDS},
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input=conf
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "Cloud API (51.528308, -0.3817765)"
        assert result["data"] == {
            CONF_API_KEY: "abcde12345",
            CONF_LATITUDE: 51.528308,
            CONF_LONGITUDE: -0.3817765,
            CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_COORDS,
        }


async def test_step_geography_by_name(opp):
    """Test setting up a geopgraphy entry by city/state/country."""
    conf = {
        CONF_API_KEY: "abcde12345",
        CONF_CITY: "Beijing",
        CONF_STATE: "Beijing",
        CONF_COUNTRY: "China",
    }

    with patch(
        "openpeerpower.components.airvisual.async_setup_entry", return_value=True
    ), patch("pyairvisual.air_quality.AirQuality.city"):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"type": INTEGRATION_TYPE_GEOGRAPHY_NAME},
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input=conf
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "Cloud API (Beijing, Beijing, China)"
        assert result["data"] == {
            CONF_API_KEY: "abcde12345",
            CONF_CITY: "Beijing",
            CONF_STATE: "Beijing",
            CONF_COUNTRY: "China",
            CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_NAME,
        }


async def test_step_node_pro(opp):
    """Test the Node/Pro step."""
    conf = {CONF_IP_ADDRESS: "192.168.1.100", CONF_PASSWORD: "my_password"}

    with patch(
        "openpeerpower.components.airvisual.async_setup_entry", return_value=True
    ), patch("pyairvisual.node.NodeSamba.async_connect"), patch(
        "pyairvisual.node.NodeSamba.async_get_latest_measurements"
    ), patch(
        "pyairvisual.node.NodeSamba.async_disconnect"
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={"type": "AirVisual Node/Pro"}
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input=conf
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "Node/Pro (192.168.1.100)"
        assert result["data"] == {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_PASSWORD: "my_password",
            CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_NODE_PRO,
        }


async def test_step_reauth(opp):
    """Test that the reauth step works."""
    entry_data = {
        CONF_API_KEY: "abcde12345",
        CONF_LATITUDE: 51.528308,
        CONF_LONGITUDE: -0.3817765,
        CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_COORDS,
    }

    MockConfigEntry(
        domain=DOMAIN, unique_id="51.528308, -0.3817765", data=entry_data
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_REAUTH}, data=entry_data
    )
    assert result["step_id"] == "reauth_confirm"

    result = await opp.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "openpeerpower.components.airvisual.async_setup_entry", return_value=True
    ), patch("pyairvisual.air_quality.AirQuality.nearest_city", return_value=True):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_API_KEY: "defgh67890"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "reauth_successful"

    assert len(opp.config_entries.async_entries()) == 1


async def test_step_user(opp):
    """Test the user ("pick the integration type") step."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"type": INTEGRATION_TYPE_GEOGRAPHY_COORDS},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "geography_by_coords"

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"type": INTEGRATION_TYPE_GEOGRAPHY_NAME},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "geography_by_name"

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"type": INTEGRATION_TYPE_NODE_PRO},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "node_pro"
