"""Test check_config helper."""
import logging
from unittest.mock import Mock, patch

from openpeerpower.config import YAML_CONFIG_FILE
from openpeerpower.helpers.check_config import (
    CheckConfigError,
    async_check_op_config_file,
)

from tests.common import mock_platform, patch_yaml_files

_LOGGER = logging.getLogger(__name__)

BASE_CONFIG = (
    "openpeerpower:\n"
    "  name: Home\n"
    "  latitude: -26.107361\n"
    "  longitude: 28.054500\n"
    "  elevation: 1600\n"
    "  unit_system: metric\n"
    "  time_zone: GMT\n"
    "\n\n"
)

BAD_CORE_CONFIG = "openpeerpower:\n  unit_system: bad\n\n\n"


def log_op_config(conf):
    """Log the returned config."""
    cnt = 0
    _LOGGER.debug("CONFIG - %s lines - %s errors", len(conf), len(conf.errors))
    for key, val in conf.items():
        _LOGGER.debug("#%s - %s: %s", cnt, key, val)
        cnt += 1
    for cnt, err in enumerate(conf.errors):
        _LOGGER.debug("error[%s] = %s", cnt, err)


async def test_bad_core_config(opp):
    """Test a bad core config setup."""
    files = {YAML_CONFIG_FILE: BAD_CORE_CONFIG}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_op_config_file.opp)
        log_op_config(res)

        assert isinstance(res.errors[0].message, str)
        assert res.errors[0].domain == "openpeerpower"
        assert res.errors[0].config == {"unit_system": "bad"}

        # Only 1 error expected
        res.errors.pop(0)
        assert not res.errors


async def test_config_platform_valid.opp):
    """Test a valid platform setup."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:\n  platform: demo"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_op_config_file.opp)
        log_op_config(res)

        assert res.keys() == {"openpeerpower", "light"}
        assert res["light"] == [{"platform": "demo"}]
        assert not res.errors


async def test_component_platform_not_found.opp):
    """Test errors if component or platform not found."""
    # Make sure they don't exist
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "beer:"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_op_config_file.opp)
        log_op_config(res)

        assert res.keys() == {"openpeerpower"}
        assert res.errors[0] == CheckConfigError(
            "Component error: beer - Integration 'beer' not found.", None, None
        )

        # Only 1 error expected
        res.errors.pop(0)
        assert not res.errors


async def test_component_platform_not_found_2.opp):
    """Test errors if component or platform not found."""
    # Make sure they don't exist
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:\n  platform: beer"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_op_config_file.opp)
        log_op_config(res)

        assert res.keys() == {"openpeerpower", "light"}
        assert res["light"] == []

        assert res.errors[0] == CheckConfigError(
            "Platform error light.beer - Integration 'beer' not found.", None, None
        )

        # Only 1 error expected
        res.errors.pop(0)
        assert not res.errors


async def test_package_invalid.opp):
    """Test a valid platform setup."""
    files = {
        YAML_CONFIG_FILE: BASE_CONFIG + ("  packages:\n    p1:\n" '      group: ["a"]')
    }
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_op_config_file.opp)
        log_op_config(res)

        assert res.errors[0].domain == "openpeerpower.packages.p1.group"
        assert res.errors[0].config == {"group": ["a"]}
        # Only 1 error expected
        res.errors.pop(0)
        assert not res.errors

        assert res.keys() == {"openpeerpower"}


async def test_bootstrap_error(opp):
    """Test a valid platform setup."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "automation: !include no.yaml"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_op_config_file.opp)
        log_op_config(res)

        assert res.errors[0].domain is None

        # Only 1 error expected
        res.errors.pop(0)
        assert not res.errors


async def test_automation_config_platform.opp):
    """Test automation async config."""
    files = {
        YAML_CONFIG_FILE: BASE_CONFIG
        + """
automation:
  use_blueprint:
    path: test_event_service.yaml
    input:
      trigger_event: blueprint_event
      service_to_call: test.automation
input_datetime:
""",
       .opp.config.path(
            "blueprints/automation/test_event_service.yaml"
        ): """
blueprint:
  name: "Call service based on event"
  domain: automation
  input:
    trigger_event:
    service_to_call:
trigger:
  platform: event
  event_type: !input trigger_event
action:
  service: !input service_to_call
""",
    }
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_op_config_file.opp)
        assert len(res.get("automation", [])) == 1
        assert len(res.errors) == 0
        assert "input_datetime" in res


async def test_config_platform_raise.opp):
    """Test bad config validation platform."""
    mock_platform(
       .opp,
        "bla.config",
        Mock(async_validate_config=Mock(side_effect=Exception("Broken"))),
    )
    files = {
        YAML_CONFIG_FILE: BASE_CONFIG
        + """
bla:
  value: 1
""",
    }
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_op_config_file.opp)
        assert len(res.errors) == 1
        err = res.errors[0]
        assert err.domain == "bla"
        assert err.message == "Unexpected error calling config validator: Broken"
        assert err.config == {"value": 1}
