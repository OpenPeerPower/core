"""Tests for the reload helper."""
import logging
from os import path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from openpeerpower import config
from openpeerpower.const import SERVICE_RELOAD
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.entity_platform import async_get_platforms
from openpeerpower.helpers.reload import (
    async_get_platform_without_config_entry,
    async_integration_yaml_config,
    async_reload_integration_platforms,
    async_setup_reload_service,
)
from openpeerpower.loader import async_get_integration

from tests.common import (
    MockModule,
    MockPlatform,
    mock_entity_platform,
    mock_integration,
)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "test_domain"
PLATFORM = "test_platform"


async def test_reload_platform(opp):
    """Test the polling of only updated entities."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(opp, MockModule(DOMAIN, setup=component_setup))
    mock_integration(opp, MockModule(PLATFORM, dependencies=[DOMAIN]))

    mock_platform = MockPlatform(async_setup_platform=setup_platform)
    mock_entity_platform(opp, f"{DOMAIN}.{PLATFORM}", mock_platform)

    component = EntityComponent(_LOGGER, DOMAIN, opp)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await opp.async_block_till_done()
    assert component_setup.called

    assert f"{DOMAIN}.{PLATFORM}" in.opp.config.components
    assert len(setup_called) == 1

    platform = async_get_platform_without_config_entry(opp, PLATFORM, DOMAIN)
    assert platform.platform_name == PLATFORM
    assert platform.domain == DOMAIN

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "helpers/reload_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await async_reload_integration_platforms(opp, PLATFORM, [DOMAIN])

    assert len(setup_called) == 2

    existing_platforms = async_get_platforms(opp, PLATFORM)
    for existing_platform in existing_platforms:
        existing_platform.config_entry = "abc"
    assert not async_get_platform_without_config_entry(opp, PLATFORM, DOMAIN)


async def test_setup_reload_service(opp):
    """Test setting up a reload service."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(opp, MockModule(DOMAIN, setup=component_setup))
    mock_integration(opp, MockModule(PLATFORM, dependencies=[DOMAIN]))

    mock_platform = MockPlatform(async_setup_platform=setup_platform)
    mock_entity_platform(opp, f"{DOMAIN}.{PLATFORM}", mock_platform)

    component = EntityComponent(_LOGGER, DOMAIN, opp)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await opp.async_block_till_done()
    assert component_setup.called

    assert f"{DOMAIN}.{PLATFORM}" in.opp.config.components
    assert len(setup_called) == 1

    await async_setup_reload_service(opp, PLATFORM, [DOMAIN])

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "helpers/reload_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            PLATFORM,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(setup_called) == 2


async def test_setup_reload_service_when_async_process_component_config_fails(opp):
    """Test setting up a reload service with the config processing failing."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(opp, MockModule(DOMAIN, setup=component_setup))
    mock_integration(opp, MockModule(PLATFORM, dependencies=[DOMAIN]))

    mock_platform = MockPlatform(async_setup_platform=setup_platform)
    mock_entity_platform(opp, f"{DOMAIN}.{PLATFORM}", mock_platform)

    component = EntityComponent(_LOGGER, DOMAIN, opp)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await opp.async_block_till_done()
    assert component_setup.called

    assert f"{DOMAIN}.{PLATFORM}" in.opp.config.components
    assert len(setup_called) == 1

    await async_setup_reload_service(opp, PLATFORM, [DOMAIN])

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "helpers/reload_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path), patch.object(
        config, "async_process_component_config", return_value=None
    ):
        await opp.services.async_call(
            PLATFORM,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(setup_called) == 1


async def test_setup_reload_service_with_platform_that_provides_async_reset_platform(
    opp,
):
    """Test setting up a reload service using a platform that has its own async_reset_platform."""
    component_setup = AsyncMock(return_value=True)

    setup_called = []
    async_reset_platform_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    async def async_reset_platform(*args):
        async_reset_platform_called.append(args)

    mock_integration(opp, MockModule(DOMAIN, async_setup=component_setup))
    integration = await async_get_integration(opp, DOMAIN)
    integration.get_component().async_reset_platform = async_reset_platform

    mock_integration(opp, MockModule(PLATFORM, dependencies=[DOMAIN]))

    mock_platform = MockPlatform(async_setup_platform=setup_platform)
    mock_entity_platform(opp, f"{DOMAIN}.{PLATFORM}", mock_platform)

    component = EntityComponent(_LOGGER, DOMAIN, opp)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "name": "xyz"}})
    await opp.async_block_till_done()
    assert component_setup.called

    assert f"{DOMAIN}.{PLATFORM}" in.opp.config.components
    assert len(setup_called) == 1

    await async_setup_reload_service(opp, PLATFORM, [DOMAIN])

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "helpers/reload_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            PLATFORM,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(setup_called) == 1
    assert len(async_reset_platform_called) == 1


async def test_async_integration_yaml_config(opp):
    """Test loading yaml config for an integration."""
    mock_integration(opp, MockModule(DOMAIN))

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        f"helpers/{DOMAIN}_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        processed_config = await async_integration_yaml_config(opp, DOMAIN)

    assert processed_config == {DOMAIN: [{"name": "one"}, {"name": "two"}]}


async def test_async_integration_missing_yaml_config(opp):
    """Test loading missing yaml config for an integration."""
    mock_integration(opp, MockModule(DOMAIN))

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "helpers/does_not_exist_configuration.yaml",
    )
    with pytest.raises(FileNotFoundError), patch.object(
        config, "YAML_CONFIG_FILE", yaml_path
    ):
        await async_integration_yaml_config(opp, DOMAIN)


def _get_fixtures_base_path():
    return path.dirname(path.dirname(__file__))
