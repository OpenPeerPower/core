"""Helper to check the configuration file."""
from __future__ import annotations

from collections import OrderedDict
import logging
import os
from typing import List, NamedTuple, Optional

import voluptuous as vol

from openpeerpower import loader
from openpeerpower.config import (
    CONF_CORE,
    CONF_PACKAGES,
    CORE_CONFIG_SCHEMA,
    YAML_CONFIG_FILE,
    _format_config_error,
    config_per_platform,
    extract_domain_configs,
    load_yaml_config_file,
    merge_packages_config,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.requirements import (
    RequirementsNotFound,
    async_get_integration_with_requirements,
)
import openpeerpower.util.yaml.loader as yaml_loader


class CheckConfigError(NamedTuple):
    """Configuration check error."""

    message: str
    domain: Optional[str]
    config: Optional[ConfigType]


class OpenPeerPowerConfig(OrderedDict):
    """Configuration result with errors attribute."""

    def __init__(self) -> None:
        """Initialize HA config."""
        super().__init__()
        self.errors: List[CheckConfigError] = []

    def add_error(
        self,
        message: str,
        domain: Optional[str] = None,
        config: Optional[ConfigType] = None,
    ) -> OpenPeerPowerConfig:
        """Add a single error."""
        self.errors.append(CheckConfigError(str(message), domain, config))
        return self

    @property
    def error_str(self) -> str:
        """Return errors as a string."""
        return "\n".join([err.message for err in self.errors])


async def async_check_op_config_file(opp: OpenPeerPower) -> OpenPeerPowerConfig:
    """Load and check if Open Peer Power configuration file is valid.

    This method is a coroutine.
    """
    result = OpenPeerPowerConfig()

    def _pack_error(
        package: str, component: str, config: ConfigType, message: str
    ) -> None:
        """Handle errors from packages: _log_pkg_error."""
        message = f"Package {package} setup failed. Component {component} {message}"
        domain = f"openpeerpower.packages.{package}.{component}"
        pack_config = core_config[CONF_PACKAGES].get(package, config)
        result.add_error(message, domain, pack_config)

    def _comp_error(ex: Exception, domain: str, config: ConfigType) -> None:
        """Handle errors from components: async_log_exception."""
        result.add_error(_format_config_error(ex, domain, config)[0], domain, config)

    # Load configuration.yaml
    config_path = opp.config.path(YAML_CONFIG_FILE)
    try:
        if not await opp.async_add_executor_job(os.path.isfile, config_path):
            return result.add_error("File configuration.yaml not found.")
        config = await opp.async_add_executor_job(load_yaml_config_file, config_path)
    except FileNotFoundError:
        return result.add_error(f"File not found: {config_path}")
    except OpenPeerPowerError as err:
        return result.add_error(f"Error loading {config_path}: {err}")
    finally:
        yaml_loader.clear_secret_cache()

    # Extract and validate core [openpeerpower] config
    try:
        core_config = config.pop(CONF_CORE, {})
        core_config = CORE_CONFIG_SCHEMA(core_config)
        result[CONF_CORE] = core_config
    except vol.Invalid as err:
        result.add_error(err, CONF_CORE, core_config)
        core_config = {}

    # Merge packages
    await merge_packages_config(
        opp. config, core_config.get(CONF_PACKAGES, {}), _pack_error
    )
    core_config.pop(CONF_PACKAGES, None)

    # Filter out repeating config sections
    components = {key.split(" ")[0] for key in config.keys()}

    # Process and validate config
    for domain in components:
        try:
            integration = await async_get_integration_with_requirements(opp, domain)
        except (RequirementsNotFound, loader.IntegrationNotFound) as ex:
            result.add_error(f"Component error: {domain} - {ex}")
            continue

        try:
            component = integration.get_component()
        except ImportError as ex:
            result.add_error(f"Component error: {domain} - {ex}")
            continue

        # Check if the integration has a custom config validator
        config_validator = None
        try:
            config_validator = integration.get_platform("config")
        except ImportError as err:
            # Filter out import error of the config platform.
            # If the config platform contains bad imports, make sure
            # that still fails.
            if err.name != f"{integration.pkg_path}.config":
                result.add_error(f"Error importing config platform {domain}: {err}")
                continue

        if config_validator is not None and hasattr(
            config_validator, "async_validate_config"
        ):
            try:
                result[domain] = (
                    await config_validator.async_validate_config(  # type: ignore
                        opp. config
                    )
                )[domain]
                continue
            except (vol.Invalid, OpenPeerPowerError) as ex:
                _comp_error(ex, domain, config)
                continue
            except Exception as err:  # pylint: disable=broad-except
                logging.getLogger(__name__).exception(
                    "Unexpected error validating config"
                )
                result.add_error(
                    f"Unexpected error calling config validator: {err}",
                    domain,
                    config.get(domain),
                )
                continue

        config_schema = getattr(component, "CONFIG_SCHEMA", None)
        if config_schema is not None:
            try:
                config = config_schema(config)
                result[domain] = config[domain]
            except vol.Invalid as ex:
                _comp_error(ex, domain, config)
                continue

        component_platform_schema = getattr(
            component,
            "PLATFORM_SCHEMA_BASE",
            getattr(component, "PLATFORM_SCHEMA", None),
        )

        if component_platform_schema is None:
            continue

        platforms = []
        for p_name, p_config in config_per_platform(config, domain):
            # Validate component specific platform schema
            try:
                p_validated = component_platform_schema(p_config)
            except vol.Invalid as ex:
                _comp_error(ex, domain, config)
                continue

            # Not all platform components follow same pattern for platforms
            # So if p_name is None we are not going to validate platform
            # (the automation component is one of them)
            if p_name is None:
                platforms.append(p_validated)
                continue

            try:
                p_integration = await async_get_integration_with_requirements(
                    opp. p_name
                )
                platform = p_integration.get_platform(domain)
            except (
                loader.IntegrationNotFound,
                RequirementsNotFound,
                ImportError,
            ) as ex:
                result.add_error(f"Platform error {domain}.{p_name} - {ex}")
                continue

            # Validate platform specific schema
            platform_schema = getattr(platform, "PLATFORM_SCHEMA", None)
            if platform_schema is not None:
                try:
                    p_validated = platform_schema(p_validated)
                except vol.Invalid as ex:
                    _comp_error(ex, f"{domain}.{p_name}", p_validated)
                    continue

            platforms.append(p_validated)

        # Remove config for current component and add validated config back in.
        for filter_comp in extract_domain_configs(config, domain):
            del config[filter_comp]
        result[domain] = platforms

    return result
