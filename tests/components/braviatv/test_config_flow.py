"""Define tests for the Bravia TV config flow."""
from unittest.mock import patch

from bravia_tv.braviarc import NoIPControl

from openpeerpower import data_entry_flow
from openpeerpower.components.braviatv.const import CONF_IGNORED_SOURCES, DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import CONF_HOST, CONF_MAC, CONF_PIN

from tests.common import MockConfigEntry

BRAVIA_SYSTEM_INFO = {
    "product": "TV",
    "region": "XEU",
    "language": "pol",
    "model": "TV-Model",
    "serial": "serial_number",
    "macAddr": "AA:BB:CC:DD:EE:FF",
    "name": "BRAVIA",
    "generation": "5.2.0",
    "area": "POL",
    "cid": "very_unique_string",
}

BRAVIA_SOURCE_LIST = {
    "HDMI 1": "extInput:hdmi?port=1",
    "HDMI 2": "extInput:hdmi?port=2",
    "HDMI 3/ARC": "extInput:hdmi?port=3",
    "HDMI 4": "extInput:hdmi?port=4",
    "AV/Component": "extInput:component?port=1",
}

IMPORT_CONFIG_HOSTNAME = {CONF_HOST: "bravia-host", CONF_PIN: "1234"}
IMPORT_CONFIG_IP = {CONF_HOST: "10.10.10.12", CONF_PIN: "1234"}


async def test_show_form(opp):
    """Test that the form is served with no input."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER


async def test_import(opp):
    """Test that the import works."""
    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=True
    ), patch(
        "bravia_tv.BraviaRC.get_system_info", return_value=BRAVIA_SYSTEM_INFO
    ), patch(
        "openpeerpower.components.braviatv.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=IMPORT_CONFIG_HOSTNAME
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["result"].unique_id == "very_unique_string"
        assert result["title"] == "TV-Model"
        assert result["data"] == {
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        }


async def test_import_cannot_connect(opp):
    """Test that errors are shown when cannot connect to the host during import."""
    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=False
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=IMPORT_CONFIG_HOSTNAME
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "cannot_connect"


async def test_import_model_unsupported(opp):
    """Test that errors are shown when the TV is not supported during import."""
    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=True
    ), patch("bravia_tv.BraviaRC.get_system_info", return_value={}):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=IMPORT_CONFIG_IP
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "unsupported_model"


async def test_import_no_ip_control(opp):
    """Test that errors are shown when IP Control is disabled on the TV during import."""
    with patch("bravia_tv.BraviaRC.connect", side_effect=NoIPControl("No IP Control")):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=IMPORT_CONFIG_IP
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "no_ip_control"


async def test_import_duplicate_error(opp):
    """Test that errors are shown when duplicates are added during import."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="very_unique_string",
        data={
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        title="TV-Model",
    )
    config_entry.add_to_opp(opp)

    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=True
    ), patch("bravia_tv.BraviaRC.get_system_info", return_value=BRAVIA_SYSTEM_INFO):

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=IMPORT_CONFIG_HOSTNAME
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "already_configured"


async def test_user_invalid_host(opp):
    """Test that errors are shown when the host is invalid."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "invalid/host"}
    )

    assert result["errors"] == {CONF_HOST: "invalid_host"}


async def test_authorize_cannot_connect(opp):
    """Test that errors are shown when cannot connect to host at the authorize step."""
    with patch("bravia_tv.BraviaRC.connect", return_value=True):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        assert result["errors"] == {"base": "cannot_connect"}


async def test_authorize_model_unsupported(opp):
    """Test that errors are shown when the TV is not supported at the authorize step."""
    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=True
    ), patch("bravia_tv.BraviaRC.get_system_info", return_value={}):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "10.10.10.12"}
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        assert result["errors"] == {"base": "unsupported_model"}


async def test_authorize_no_ip_control(opp):
    """Test that errors are shown when IP Control is disabled on the TV."""
    with patch("bravia_tv.BraviaRC.connect", side_effect=NoIPControl("No IP Control")):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "no_ip_control"


async def test_duplicate_error(opp):
    """Test that errors are shown when duplicates are added."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="very_unique_string",
        data={
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        title="TV-Model",
    )
    config_entry.add_to_opp(opp)

    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=True
    ), patch("bravia_tv.BraviaRC.get_system_info", return_value=BRAVIA_SYSTEM_INFO):

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "already_configured"


async def test_create_entry(opp):
    """Test that the user step works."""
    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=True
    ), patch(
        "bravia_tv.BraviaRC.get_system_info", return_value=BRAVIA_SYSTEM_INFO
    ), patch(
        "openpeerpower.components.braviatv.async_setup_entry", return_value=True
    ):

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "authorize"

        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["result"].unique_id == "very_unique_string"
        assert result["title"] == "TV-Model"
        assert result["data"] == {
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        }


async def test_create_entry_with_ipv6_address(opp):
    """Test that the user step works with device IPv6 address."""
    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=True
    ), patch(
        "bravia_tv.BraviaRC.get_system_info", return_value=BRAVIA_SYSTEM_INFO
    ), patch(
        "openpeerpower.components.braviatv.async_setup_entry", return_value=True
    ):

        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_HOST: "2001:db8::1428:57ab"},
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "authorize"

        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["result"].unique_id == "very_unique_string"
        assert result["title"] == "TV-Model"
        assert result["data"] == {
            CONF_HOST: "2001:db8::1428:57ab",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        }


async def test_options_flow(opp):
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="very_unique_string",
        data={
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        title="TV-Model",
    )
    config_entry.add_to_opp(opp)

    with patch("bravia_tv.BraviaRC.connect", return_value=True), patch(
        "bravia_tv.BraviaRC.is_connected", return_value=True
    ), patch("bravia_tv.BraviaRC.get_system_info", return_value=BRAVIA_SYSTEM_INFO):
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    with patch("bravia_tv.BraviaRC.load_source_list", return_value=BRAVIA_SOURCE_LIST):
        result = await opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_IGNORED_SOURCES: ["HDMI 1", "HDMI 2"]}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options == {CONF_IGNORED_SOURCES: ["HDMI 1", "HDMI 2"]}
