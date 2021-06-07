"""Test the DenonAVR config flow."""
from unittest.mock import patch

import pytest

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components import ssdp
from openpeerpower.components.denonavr.config_flow import (
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_SERIAL_NUMBER,
    CONF_SHOW_ALL_SOURCES,
    CONF_TYPE,
    CONF_UPDATE_AUDYSSEY,
    CONF_ZONE2,
    CONF_ZONE3,
    DOMAIN,
    AvrTimoutError,
)
from openpeerpower.const import CONF_HOST

from tests.common import MockConfigEntry

TEST_HOST = "1.2.3.4"
TEST_HOST2 = "5.6.7.8"
TEST_NAME = "Test_Receiver"
TEST_MODEL = "model5"
TEST_IGNORED_MODEL = "HEOS 7"
TEST_RECEIVER_TYPE = "avr-x"
TEST_SERIALNUMBER = "123456789"
TEST_MANUFACTURER = "Denon"
TEST_UPDATE_AUDYSSEY = False
TEST_SSDP_LOCATION = f"http://{TEST_HOST}/"
TEST_UNIQUE_ID = f"{TEST_MODEL}-{TEST_SERIALNUMBER}"
TEST_DISCOVER_1_RECEIVER = [{CONF_HOST: TEST_HOST}]
TEST_DISCOVER_2_RECEIVER = [{CONF_HOST: TEST_HOST}, {CONF_HOST: TEST_HOST2}]


@pytest.fixture(name="denonavr_connect", autouse=True)
def denonavr_connect_fixture():
    """Mock denonavr connection and entry setup."""
    with patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.async_setup",
        return_value=None,
    ), patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.async_update",
        return_value=None,
    ), patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.support_sound_mode",
        return_value=True,
    ), patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.name",
        TEST_NAME,
    ), patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.model_name",
        TEST_MODEL,
    ), patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.serial_number",
        TEST_SERIALNUMBER,
    ), patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.manufacturer",
        TEST_MANUFACTURER,
    ), patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.receiver_type",
        TEST_RECEIVER_TYPE,
    ), patch(
        "openpeerpower.components.denonavr.async_setup_entry", return_value=True
    ):
        yield


async def test_config_flow_manual_host_success(opp):
    """
    Successful flow manually initialized by the user.

    Host specified.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: TEST_SERIALNUMBER,
    }


async def test_config_flow_manual_discover_1_success(opp):
    """
    Successful flow manually initialized by the user.

    Without the host specified and 1 receiver discovered.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.denonavr.config_flow.denonavr.async_discover",
        return_value=TEST_DISCOVER_1_RECEIVER,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: TEST_SERIALNUMBER,
    }


async def test_config_flow_manual_discover_2_success(opp):
    """
    Successful flow manually initialized by the user.

    Without the host specified and 2 receiver discovered.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.denonavr.config_flow.denonavr.async_discover",
        return_value=TEST_DISCOVER_2_RECEIVER,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "select"
    assert result["errors"] == {}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"select_host": TEST_HOST2},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST2,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: TEST_SERIALNUMBER,
    }


async def test_config_flow_manual_discover_error(opp):
    """
    Failed flow manually initialized by the user.

    Without the host specified and no receiver discovered.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.denonavr.config_flow.denonavr.async_discover",
        return_value=[],
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "discovery_error"}


async def test_config_flow_manual_host_no_serial(opp):
    """
    Successful flow manually initialized by the user.

    Host specified and an error getting the serial number.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.serial_number",
        None,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: None,
    }


async def test_config_flow_manual_host_connection_error(opp):
    """
    Failed flow manually initialized by the user.

    Host specified and a connection error.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.async_setup",
        side_effect=AvrTimoutError("Timeout", "async_setup"),
    ), patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.receiver_type",
        None,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_config_flow_manual_host_no_device_info(opp):
    """
    Failed flow manually initialized by the user.

    Host specified and no device info (due to receiver power off).
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.receiver_type",
        None,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_config_flow_ssdp(opp):
    """Successful flow initialized by ssdp discovery."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data={
            ssdp.ATTR_UPNP_MANUFACTURER: TEST_MANUFACTURER,
            ssdp.ATTR_UPNP_MODEL_NAME: TEST_MODEL,
            ssdp.ATTR_UPNP_SERIAL: TEST_SERIALNUMBER,
            ssdp.ATTR_SSDP_LOCATION: TEST_SSDP_LOCATION,
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: TEST_SERIALNUMBER,
    }


async def test_config_flow_ssdp_not_denon(opp):
    """
    Failed flow initialized by ssdp discovery.

    Not supported manufacturer.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data={
            ssdp.ATTR_UPNP_MANUFACTURER: "NotSupported",
            ssdp.ATTR_UPNP_MODEL_NAME: TEST_MODEL,
            ssdp.ATTR_UPNP_SERIAL: TEST_SERIALNUMBER,
            ssdp.ATTR_SSDP_LOCATION: TEST_SSDP_LOCATION,
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_denonavr_manufacturer"


async def test_config_flow_ssdp_missing_info(opp):
    """
    Failed flow initialized by ssdp discovery.

    Missing information.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data={
            ssdp.ATTR_UPNP_MANUFACTURER: TEST_MANUFACTURER,
            ssdp.ATTR_SSDP_LOCATION: TEST_SSDP_LOCATION,
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_denonavr_missing"


async def test_config_flow_ssdp_ignored_model(opp):
    """
    Failed flow initialized by ssdp discovery.

    Model in the ignored models list.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data={
            ssdp.ATTR_UPNP_MANUFACTURER: TEST_MANUFACTURER,
            ssdp.ATTR_UPNP_MODEL_NAME: TEST_IGNORED_MODEL,
            ssdp.ATTR_UPNP_SERIAL: TEST_SERIALNUMBER,
            ssdp.ATTR_SSDP_LOCATION: TEST_SSDP_LOCATION,
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_denonavr_manufacturer"


async def test_options_flow(opp):
    """Test specifying non default settings using options flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_UNIQUE_ID,
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL,
            CONF_TYPE: TEST_RECEIVER_TYPE,
            CONF_MANUFACTURER: TEST_MANUFACTURER,
            CONF_SERIAL_NUMBER: TEST_SERIALNUMBER,
            CONF_UPDATE_AUDYSSEY: TEST_UPDATE_AUDYSSEY,
        },
        title=TEST_NAME,
    )
    config_entry.add_to_opp(opp)

    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SHOW_ALL_SOURCES: True, CONF_ZONE2: True, CONF_ZONE3: True},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        CONF_SHOW_ALL_SOURCES: True,
        CONF_ZONE2: True,
        CONF_ZONE3: True,
        CONF_UPDATE_AUDYSSEY: False,
    }


async def test_config_flow_manual_host_no_serial_double_config(opp):
    """
    Failed flow manually initialized by the user twice.

    Host specified and an error getting the serial number.
    """
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.serial_number",
        None,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: None,
    }

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.denonavr.receiver.DenonAVR.serial_number",
        None,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
