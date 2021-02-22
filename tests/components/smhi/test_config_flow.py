"""Tests for SMHI config flow."""
from unittest.mock import Mock, patch

from smhi.smhi_lib import Smhi as SmhiApi, SmhiForecastException

from openpeerpower.components.smhi import config_flow
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE


# pylint: disable=protected-access
async def test_openpeerpower_location_exists() -> None:
    """Test if Open Peer Power location exists it should return True."""
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp
    with patch.object(flow, "_check_location", return_value=True):
        # Test exists
       .opp.config.location_name = "Home"
       .opp.config.latitude = 17.8419
       .opp.config.longitude = 59.3262

        assert await flow._openpeerpower_location_exists() is True

        # Test not exists
       .opp.config.location_name = None
       .opp.config.latitude = 0
       .opp.config.longitude = 0

        assert await flow._openpeerpower_location_exists() is False


async def test_name_in_configuration_exists() -> None:
    """Test if home location exists in configuration."""
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    # Test exists
   .opp.config.location_name = "Home"
   .opp.config.latitude = 17.8419
   .opp.config.longitude = 59.3262

    # Check not exists
    with patch.object(
        config_flow,
        "smhi_locations",
        return_value={"test": "something", "test2": "something else"},
    ):

        assert flow._name_in_configuration_exists("no_exist_name") is False

    # Check exists
    with patch.object(
        config_flow,
        "smhi_locations",
        return_value={"test": "something", "name_exist": "config"},
    ):

        assert flow._name_in_configuration_exists("name_exist") is True


def test_smhi_locations.opp) -> None:
    """Test return empty set."""
    locations = config_flow.smhi_locations.opp)
    assert not locations


async def test_show_config_form() -> None:
    """Test show configuration form."""
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    result = await flow._show_config_form()

    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_show_config_form_default_values() -> None:
    """Test show configuration form."""
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    result = await flow._show_config_form(name="test", latitude="65", longitude="17")

    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_flow_with_home_location.opp) -> None:
    """Test config flow .

    Tests the flow when a default location is configured
    then it should return a form with default values
    """
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    with patch.object(flow, "_check_location", return_value=True):
       .opp.config.location_name = "Home"
       .opp.config.latitude = 17.8419
       .opp.config.longitude = 59.3262

        result = await flow.async_step_user()
        assert result["type"] == "form"
        assert result["step_id"] == "user"


async def test_flow_show_form() -> None:
    """Test show form scenarios first time.

    Test when the form should show when no configurations exists
    """
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    # Test show form when Open Peer Power config exists and
    # home is already configured, then new config is allowed
    with patch.object(
        flow, "_show_config_form", return_value=None
    ) as config_form, patch.object(
        flow, "_openpeerpower_location_exists", return_value=True
    ), patch.object(
        config_flow,
        "smhi_locations",
        return_value={"test": "something", "name_exist": "config"},
    ):
        await flow.async_step_user()
        assert len(config_form.mock_calls) == 1

    # Test show form when Open Peer Power config not and
    # home is not configured
    with patch.object(
        flow, "_show_config_form", return_value=None
    ) as config_form, patch.object(
        flow, "_openpeerpower_location_exists", return_value=False
    ), patch.object(
        config_flow,
        "smhi_locations",
        return_value={"test": "something", "name_exist": "config"},
    ):

        await flow.async_step_user()
        assert len(config_form.mock_calls) == 1


async def test_flow_show_form_name_exists() -> None:
    """Test show form if name already exists.

    Test when the form should show when no configurations exists
    """
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp
    test_data = {"name": "home", CONF_LONGITUDE: "0", CONF_LATITUDE: "0"}
    # Test show form when Open Peer Power config exists and
    # home is already configured, then new config is allowed
    with patch.object(
        flow, "_show_config_form", return_value=None
    ) as config_form, patch.object(
        flow, "_name_in_configuration_exists", return_value=True
    ), patch.object(
        config_flow,
        "smhi_locations",
        return_value={"test": "something", "name_exist": "config"},
    ), patch.object(
        flow, "_check_location", return_value=True
    ):

        await flow.async_step_user(user_input=test_data)

        assert len(config_form.mock_calls) == 1
        assert len(flow._errors) == 1


async def test_flow_entry_created_from_user_input() -> None:
    """Test that create data from user input.

    Test when the form should show when no configurations exists
    """
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    test_data = {"name": "home", CONF_LONGITUDE: "0", CONF_LATITUDE: "0"}

    # Test that entry created when user_input name not exists
    with patch.object(
        flow, "_show_config_form", return_value=None
    ) as config_form, patch.object(
        flow, "_name_in_configuration_exists", return_value=False
    ), patch.object(
        flow, "_openpeerpower_location_exists", return_value=False
    ), patch.object(
        config_flow,
        "smhi_locations",
        return_value={"test": "something", "name_exist": "config"},
    ), patch.object(
        flow, "_check_location", return_value=True
    ):

        result = await flow.async_step_user(user_input=test_data)

        assert result["type"] == "create_entry"
        assert result["data"] == test_data
        assert not config_form.mock_calls


async def test_flow_entry_created_user_input_faulty() -> None:
    """Test that create data from user input and are faulty.

    Test when the form should show when user puts faulty location
    in the config gui. Then the form should show with error
    """
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    test_data = {"name": "home", CONF_LONGITUDE: "0", CONF_LATITUDE: "0"}

    # Test that entry created when user_input name not exists
    with patch.object(flow, "_check_location", return_value=True), patch.object(
        flow, "_show_config_form", return_value=None
    ) as config_form, patch.object(
        flow, "_name_in_configuration_exists", return_value=False
    ), patch.object(
        flow, "_openpeerpower_location_exists", return_value=False
    ), patch.object(
        config_flow,
        "smhi_locations",
        return_value={"test": "something", "name_exist": "config"},
    ), patch.object(
        flow, "_check_location", return_value=False
    ):

        await flow.async_step_user(user_input=test_data)

        assert len(config_form.mock_calls) == 1
        assert len(flow._errors) == 1


async def test_check_location_correct() -> None:
    """Test check location when correct input."""
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    with patch.object(
        config_flow.aiohttp_client, "async_get_clientsession"
    ), patch.object(SmhiApi, "async_get_forecast", return_value=None):

        assert await flow._check_location("58", "17") is True


async def test_check_location_faulty() -> None:
    """Test check location when faulty input."""
    opp =Mock()
    flow = config_flow.SmhiFlowHandler()
    flow.opp = opp

    with patch.object(
        config_flow.aiohttp_client, "async_get_clientsession"
    ), patch.object(SmhiApi, "async_get_forecast", side_effect=SmhiForecastException()):

        assert await flow._check_location("58", "17") is False
