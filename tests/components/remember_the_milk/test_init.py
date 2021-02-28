"""Tests for the Remember The Milk component."""
from unittest.mock import Mock, mock_open, patch

import openpeerpower.components.remember_the_milk as rtm

from .const import JSON_STRING, PROFILE, TOKEN


def test_create_new(opp):
    """Test creating a new config file."""
    with patch("builtins.open", mock_open()), patch(
        "os.path.isfile", Mock(return_value=False)
    ), patch.object(rtm.RememberTheMilkConfiguration, "save_config"):
        config = rtm.RememberTheMilkConfiguration.opp)
        config.set_token(PROFILE, TOKEN)
    assert config.get_token(PROFILE) == TOKEN


def test_load_config(opp):
    """Test loading an existing token from the file."""
    with patch("builtins.open", mock_open(read_data=JSON_STRING)), patch(
        "os.path.isfile", Mock(return_value=True)
    ):
        config = rtm.RememberTheMilkConfiguration.opp)
    assert config.get_token(PROFILE) == TOKEN


def test_invalid_data(opp):
    """Test starts with invalid data and should not raise an exception."""
    with patch("builtins.open", mock_open(read_data="random characters")), patch(
        "os.path.isfile", Mock(return_value=True)
    ):
        config = rtm.RememberTheMilkConfiguration.opp)
    assert config is not None


def test_id_map(opp):
    """Test the.opp to rtm task is mapping."""
    opp.id = opp-id-1234"
    list_id = "mylist"
    timeseries_id = "my_timeseries"
    rtm_id = "rtm-id-4567"
    with patch("builtins.open", mock_open()), patch(
        "os.path.isfile", Mock(return_value=False)
    ), patch.object(rtm.RememberTheMilkConfiguration, "save_config"):
        config = rtm.RememberTheMilkConfiguration.opp)

        assert config.get_rtm_id(PROFILE, opp_id) is None
        config.set_rtm_id(PROFILE, opp_id, list_id, timeseries_id, rtm_id)
        assert (list_id, timeseries_id, rtm_id) == config.get_rtm_id(PROFILE, opp_id)
        config.delete_rtm_id(PROFILE, opp_id)
        assert config.get_rtm_id(PROFILE, opp_id) is None


def test_load_key_map(opp):
    """Test loading an existing key map from the file."""
    with patch("builtins.open", mock_open(read_data=JSON_STRING)), patch(
        "os.path.isfile", Mock(return_value=True)
    ):
        config = rtm.RememberTheMilkConfiguration.opp)
    assert ("0", "1", "2") == config.get_rtm_id(PROFILE, "1234")
