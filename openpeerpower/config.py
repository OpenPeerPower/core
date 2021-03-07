"""Module to help with parsing and generating configuration files."""
from collections import OrderedDict
import logging
import os
from pathlib import Path
import re
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, Optional, Sequence, Set, Tuple, Union

from awesomeversion import AwesomeVersion
import voluptuous as vol
from voluptuous.humanize import humanize_error

from openpeerpower import auth
from openpeerpower.auth import (
    mfa_modules as auth_mfa_modules,
    providers as auth_providers,
)
from openpeerpower.const import (
    ATTR_ASSUMED_STATE,
    ATTR_FRIENDLY_NAME,
    ATTR_HIDDEN,
    CONF_ALLOWLIST_EXTERNAL_DIRS,
    CONF_ALLOWLIST_EXTERNAL_URLS,
    CONF_AUTH_MFA_MODULES,
    CONF_AUTH_PROVIDERS,
    CONF_CUSTOMIZE,
    CONF_CUSTOMIZE_DOMAIN,
    CONF_CUSTOMIZE_GLOB,
    CONF_ELEVATION,
    CONF_EXTERNAL_URL,
    CONF_ID,
    CONF_INTERNAL_URL,
    CONF_LATITUDE,
    CONF_LEGACY_TEMPLATES,
    CONF_LONGITUDE,
    CONF_MEDIA_DIRS,
    CONF_NAME,
    CONF_PACKAGES,
    CONF_TEMPERATURE_UNIT,
    CONF_TIME_ZONE,
    CONF_TYPE,
    CONF_UNIT_SYSTEM,
    CONF_UNIT_SYSTEM_IMPERIAL,
    LEGACY_CONF_WHITELIST_EXTERNAL_DIRS,
    TEMP_CELSIUS,
    __version__,
)
from openpeerpower.core import DOMAIN as CONF_CORE, SOURCE_YAML, OpenPeerPower, callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import config_per_platform, extract_domain_configs
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity_values import EntityValues
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.loader import Integration, IntegrationNotFound
from openpeerpower.requirements import (
    RequirementsNotFound,
    async_get_integration_with_requirements,
)
from openpeerpower.util.package import is_docker_env
from openpeerpower.util.unit_system import IMPERIAL_SYSTEM, METRIC_SYSTEM
from openpeerpower.util.yaml import SECRET_YAML, Secrets, load_yaml

_LOGGER = logging.getLogger(__name__)

DATA_PERSISTENT_ERRORS = "bootstrap_persistent_errors"
RE_YAML_ERROR = re.compile(r"openpeerpower\.util\.yaml")
RE_ASCII = re.compile(r"\033\[[^m]*m")
YAML_CONFIG_FILE = "configuration.yaml"
VERSION_FILE = ".HA_VERSION"
CONFIG_DIR_NAME = ".openpeerpower"
DATA_CUSTOMIZE = "opp_customize"

GROUP_CONFIG_PATH = "groups.yaml"
AUTOMATION_CONFIG_PATH = "automations.yaml"
SCRIPT_CONFIG_PATH = "scripts.yaml"
SCENE_CONFIG_PATH = "scenes.yaml"

LOAD_EXCEPTIONS = (ImportError, FileNotFoundError)
INTEGRATION_LOAD_EXCEPTIONS = (
    IntegrationNotFound,
    RequirementsNotFound,
    *LOAD_EXCEPTIONS,
)

DEFAULT_CONFIG = f"""
# Configure a default setup of Open Peer Power (frontend, api, etc)
default_config:

# Text to speech
tts:
  - platform: google_translate

group: !include {GROUP_CONFIG_PATH}
automation: !include {AUTOMATION_CONFIG_PATH}
script: !include {SCRIPT_CONFIG_PATH}
scene: !include {SCENE_CONFIG_PATH}
"""
DEFAULT_SECRETS = """
# Use this file to store secrets like usernames and passwords.
# Learn more at https://www.openpeerpower.io/docs/configuration/secrets/
some_password: welcome
"""
TTS_PRE_92 = """
tts:
  - platform: google
"""
TTS_92 = """
tts:
  - platform: google_translate
    service_name: google_say
"""


def _no_duplicate_auth_provider(
    configs: Sequence[Dict[str, Any]]
) -> Sequence[Dict[str, Any]]:
    """No duplicate auth provider config allowed in a list.

    Each type of auth provider can only have one config without optional id.
    Unique id is required if same type of auth provider used multiple times.
    """
    config_keys: Set[Tuple[str, Optional[str]]] = set()
    for config in configs:
        key = (config[CONF_TYPE], config.get(CONF_ID))
        if key in config_keys:
            raise vol.Invalid(
                f"Duplicate auth provider {config[CONF_TYPE]} found. "
                "Please add unique IDs "
                "if you want to have the same auth provider twice"
            )
        config_keys.add(key)
    return configs


def _no_duplicate_auth_mfa_module(
    configs: Sequence[Dict[str, Any]]
) -> Sequence[Dict[str, Any]]:
    """No duplicate auth mfa module item allowed in a list.

    Each type of mfa module can only have one config without optional id.
    A global unique id is required if same type of mfa module used multiple
    times.
    Note: this is different than auth provider
    """
    config_keys: Set[str] = set()
    for config in configs:
        key = config.get(CONF_ID, config[CONF_TYPE])
        if key in config_keys:
            raise vol.Invalid(
                f"Duplicate mfa module {config[CONF_TYPE]} found. "
                "Please add unique IDs "
                "if you want to have the same mfa module twice"
            )
        config_keys.add(key)
    return configs


PACKAGES_CONFIG_SCHEMA = cv.schema_with_slug_keys(  # Package names are slugs
    vol.Schema({cv.string: vol.Any(dict, list, None)})  # Component config
)

CUSTOMIZE_DICT_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
        vol.Optional(ATTR_HIDDEN): cv.boolean,
        vol.Optional(ATTR_ASSUMED_STATE): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)

CUSTOMIZE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CUSTOMIZE, default={}): vol.Schema(
            {cv.entity_id: CUSTOMIZE_DICT_SCHEMA}
        ),
        vol.Optional(CONF_CUSTOMIZE_DOMAIN, default={}): vol.Schema(
            {cv.string: CUSTOMIZE_DICT_SCHEMA}
        ),
        vol.Optional(CONF_CUSTOMIZE_GLOB, default={}): vol.Schema(
            {cv.string: CUSTOMIZE_DICT_SCHEMA}
        ),
    }
)

CORE_CONFIG_SCHEMA = CUSTOMIZE_CONFIG_SCHEMA.extend(
    {
        CONF_NAME: vol.Coerce(str),
        CONF_LATITUDE: cv.latitude,
        CONF_LONGITUDE: cv.longitude,
        CONF_ELEVATION: vol.Coerce(int),
        vol.Optional(CONF_TEMPERATURE_UNIT): cv.temperature_unit,
        CONF_UNIT_SYSTEM: cv.unit_system,
        CONF_TIME_ZONE: cv.time_zone,
        vol.Optional(CONF_INTERNAL_URL): cv.url,
        vol.Optional(CONF_EXTERNAL_URL): cv.url,
        vol.Optional(CONF_ALLOWLIST_EXTERNAL_DIRS): vol.All(
            cv.ensure_list, [vol.IsDir()]  # pylint: disable=no-value-for-parameter
        ),
        vol.Optional(LEGACY_CONF_WHITELIST_EXTERNAL_DIRS): vol.All(
            cv.ensure_list, [vol.IsDir()]  # pylint: disable=no-value-for-parameter
        ),
        vol.Optional(CONF_ALLOWLIST_EXTERNAL_URLS): vol.All(cv.ensure_list, [cv.url]),
        vol.Optional(CONF_PACKAGES, default={}): PACKAGES_CONFIG_SCHEMA,
        vol.Optional(CONF_AUTH_PROVIDERS): vol.All(
            cv.ensure_list,
            [
                auth_providers.AUTH_PROVIDER_SCHEMA.extend(
                    {
                        CONF_TYPE: vol.NotIn(
                            ["insecure_example"],
                            "The insecure_example auth provider"
                            " is for testing only.",
                        )
                    }
                )
            ],
            _no_duplicate_auth_provider,
        ),
        vol.Optional(CONF_AUTH_MFA_MODULES): vol.All(
            cv.ensure_list,
            [
                auth_mfa_modules.MULTI_FACTOR_AUTH_MODULE_SCHEMA.extend(
                    {
                        CONF_TYPE: vol.NotIn(
                            ["insecure_example"],
                            "The insecure_example mfa module is for testing only.",
                        )
                    }
                )
            ],
            _no_duplicate_auth_mfa_module,
        ),
        # pylint: disable=no-value-for-parameter
        vol.Optional(CONF_MEDIA_DIRS): cv.schema_with_slug_keys(vol.IsDir()),
        vol.Optional(CONF_LEGACY_TEMPLATES): cv.boolean,
    }
)


def get_default_config_dir() -> str:
    """Put together the default configuration directory based on the OS."""
    data_dir = os.getenv("APPDATA") if os.name == "nt" else os.path.expanduser("~")
    return os.path.join(data_dir, CONFIG_DIR_NAME)  # type: ignore


async def async_ensure_config_exists(opp: OpenPeerPower) -> bool:
    """Ensure a configuration file exists in given configuration directory.

    Creating a default one if needed.
    Return boolean if configuration dir is ready to go.
    """
    config_path = opp.config.path(YAML_CONFIG_FILE)

    if os.path.isfile(config_path):
        return True

    print(
        "Unable to find configuration. Creating default one in", opp.config.config_dir
    )
    return await async_create_default_config(opp)


async def async_create_default_config(opp: OpenPeerPower) -> bool:
    """Create a default configuration file in given configuration directory.

    Return if creation was successful.
    """
    return await opp.async_add_executor_job(
        _write_default_config, opp.config.config_dir
    )


def _write_default_config(config_dir: str) -> bool:
    """Write the default config."""
    config_path = os.path.join(config_dir, YAML_CONFIG_FILE)
    secret_path = os.path.join(config_dir, SECRET_YAML)
    version_path = os.path.join(config_dir, VERSION_FILE)
    group_yaml_path = os.path.join(config_dir, GROUP_CONFIG_PATH)
    automation_yaml_path = os.path.join(config_dir, AUTOMATION_CONFIG_PATH)
    script_yaml_path = os.path.join(config_dir, SCRIPT_CONFIG_PATH)
    scene_yaml_path = os.path.join(config_dir, SCENE_CONFIG_PATH)

    # Writing files with YAML does not create the most human readable results
    # So we're hard coding a YAML template.
    try:
        with open(config_path, "wt") as config_file:
            config_file.write(DEFAULT_CONFIG)

        with open(secret_path, "wt") as secret_file:
            secret_file.write(DEFAULT_SECRETS)

        with open(version_path, "wt") as version_file:
            version_file.write(__version__)

        with open(group_yaml_path, "wt"):
            pass

        with open(automation_yaml_path, "wt") as fil:
            fil.write("[]")

        with open(script_yaml_path, "wt"):
            pass

        with open(scene_yaml_path, "wt"):
            pass

        return True

    except OSError:
        print("Unable to create default configuration file", config_path)
        return False


async def async_opp_config_yaml(opp: OpenPeerPower) -> Dict:
    """Load YAML from a Open Peer Power configuration file.

    This function allow a component inside the asyncio loop to reload its
    configuration by itself. Include package merge.
    """
    if opp.config.config_dir is None:
        secrets = None
    else:
        secrets = Secrets(Path(opp.config.config_dir))

    # Not using async_add_executor_job because this is an internal method.
    config = await opp.loop.run_in_executor(
        None,
        load_yaml_config_file,
        opp.config.path(YAML_CONFIG_FILE),
        secrets,
    )
    core_config = config.get(CONF_CORE, {})
    await merge_packages_config(opp, config, core_config.get(CONF_PACKAGES, {}))
    return config


def load_yaml_config_file(
    config_path: str, secrets: Optional[Secrets] = None
) -> Dict[Any, Any]:
    """Parse a YAML configuration file.

    Raises FileNotFoundError or OpenPeerPowerError.

    This method needs to run in an executor.
    """
    conf_dict = load_yaml(config_path, secrets)

    if not isinstance(conf_dict, dict):
        msg = (
            f"The configuration file {os.path.basename(config_path)} "
            "does not contain a dictionary"
        )
        _LOGGER.error(msg)
        raise OpenPeerPowerError(msg)

    # Convert values to dictionaries if they are None
    for key, value in conf_dict.items():
        conf_dict[key] = value or {}
    return conf_dict


def process_op_config_upgrade(opp: OpenPeerPower) -> None:
    """Upgrade configuration if necessary.

    This method needs to run in an executor.
    """
    version_path = opp.config.path(VERSION_FILE)

    try:
        with open(version_path) as inp:
            conf_version = inp.readline().strip()
    except FileNotFoundError:
        # Last version to not have this file
        conf_version = "0.7.7"

    if conf_version == __version__:
        return

    _LOGGER.info(
        "Upgrading configuration directory from %s to %s", conf_version, __version__
    )

    version_obj = AwesomeVersion(conf_version)

    if version_obj < AwesomeVersion("0.50"):
        # 0.50 introduced persistent deps dir.
        lib_path = opp.config.path("deps")
        if os.path.isdir(lib_path):
            shutil.rmtree(lib_path)

    if version_obj < AwesomeVersion("0.92"):
        # 0.92 moved google/tts.py to google_translate/tts.py
        config_path = opp.config.path(YAML_CONFIG_FILE)

        with open(config_path, encoding="utf-8") as config_file:
            config_raw = config_file.read()

        if TTS_PRE_92 in config_raw:
            _LOGGER.info("Migrating google tts to google_translate tts")
            config_raw = config_raw.replace(TTS_PRE_92, TTS_92)
            try:
                with open(config_path, "wt", encoding="utf-8") as config_file:
                    config_file.write(config_raw)
            except OSError:
                _LOGGER.exception("Migrating to google_translate tts failed")

    if version_obj < AwesomeVersion("0.94") and is_docker_env():
        # In 0.94 we no longer install packages inside the deps folder when
        # running inside a Docker container.
        lib_path = opp.config.path("deps")
        if os.path.isdir(lib_path):
            shutil.rmtree(lib_path)

    with open(version_path, "wt") as outp:
        outp.write(__version__)


@callback
def async_log_exception(
    ex: Exception,
    domain: str,
    config: Dict,
    opp: OpenPeerPower,
    link: Optional[str] = None,
) -> None:
    """Log an error for configuration validation.

    This method must be run in the event loop.
    """
    if opp is not None:
        async_notify_setup_error(opp, domain, link)
    message, is_friendly = _format_config_error(ex, domain, config, link)
    _LOGGER.error(message, exc_info=not is_friendly and ex)


@callback
def _format_config_error(
    ex: Exception, domain: str, config: Dict, link: Optional[str] = None
) -> Tuple[str, bool]:
    """Generate log exception for configuration validation.

    This method must be run in the event loop.
    """
    is_friendly = False
    message = f"Invalid config for [{domain}]: "
    if isinstance(ex, vol.Invalid):
        if "extra keys not allowed" in ex.error_message:
            path = "->".join(str(m) for m in ex.path)
            message += (
                f"[{ex.path[-1]}] is an invalid option for [{domain}]. "
                f"Check: {domain}->{path}."
            )
        else:
            message += f"{humanize_error(config, ex)}."
        is_friendly = True
    else:
        message += str(ex) or repr(ex)

    try:
        domain_config = config.get(domain, config)
    except AttributeError:
        domain_config = config

    message += (
        f" (See {getattr(domain_config, '__config_file__', '?')}, "
        f"line {getattr(domain_config, '__line__', '?')}). "
    )

    if domain != CONF_CORE and link:
        message += f"Please check the docs at {link}"

    return message, is_friendly


async def async_process_op_core_config(opp: OpenPeerPower, config: Dict) -> None:
    """Process the [openpeerpower] section from the configuration.

    This method is a coroutine.
    """
    config = CORE_CONFIG_SCHEMA(config)

    # Only load auth during startup.
    if not hasattr(opp, "auth"):
        auth_conf = config.get(CONF_AUTH_PROVIDERS)

        if auth_conf is None:
            auth_conf = [{"type": "openpeerpower"}]

        mfa_conf = config.get(
            CONF_AUTH_MFA_MODULES,
            [{"type": "totp", "id": "totp", "name": "Authenticator app"}],
        )

        setattr(
            opp, "auth", await auth.auth_manager_from_config(opp, auth_conf, mfa_conf)
        )

    await opp.config.async_load()

    hac = opp.config

    if any(
        k in config
        for k in [
            CONF_LATITUDE,
            CONF_LONGITUDE,
            CONF_NAME,
            CONF_ELEVATION,
            CONF_TIME_ZONE,
            CONF_UNIT_SYSTEM,
            CONF_EXTERNAL_URL,
            CONF_INTERNAL_URL,
        ]
    ):
        hac.config_source = SOURCE_YAML

    for key, attr in (
        (CONF_LATITUDE, "latitude"),
        (CONF_LONGITUDE, "longitude"),
        (CONF_NAME, "location_name"),
        (CONF_ELEVATION, "elevation"),
        (CONF_INTERNAL_URL, "internal_url"),
        (CONF_EXTERNAL_URL, "external_url"),
        (CONF_MEDIA_DIRS, "media_dirs"),
        (CONF_LEGACY_TEMPLATES, "legacy_templates"),
    ):
        if key in config:
            setattr(hac, attr, config[key])

    if CONF_TIME_ZONE in config:
        hac.set_time_zone(config[CONF_TIME_ZONE])

    if CONF_MEDIA_DIRS not in config:
        if is_docker_env():
            hac.media_dirs = {"local": "/media"}
        else:
            hac.media_dirs = {"local": opp.config.path("media")}

    # Init whitelist external dir
    hac.allowlist_external_dirs = {opp.config.path("www"), *hac.media_dirs.values()}
    if CONF_ALLOWLIST_EXTERNAL_DIRS in config:
        hac.allowlist_external_dirs.update(set(config[CONF_ALLOWLIST_EXTERNAL_DIRS]))

    elif LEGACY_CONF_WHITELIST_EXTERNAL_DIRS in config:
        _LOGGER.warning(
            "Key %s has been replaced with %s. Please update your config",
            LEGACY_CONF_WHITELIST_EXTERNAL_DIRS,
            CONF_ALLOWLIST_EXTERNAL_DIRS,
        )
        hac.allowlist_external_dirs.update(
            set(config[LEGACY_CONF_WHITELIST_EXTERNAL_DIRS])
        )

    # Init whitelist external URL list – make sure to add / to every URL that doesn't
    # already have it so that we can properly test "path ownership"
    if CONF_ALLOWLIST_EXTERNAL_URLS in config:
        hac.allowlist_external_urls.update(
            url if url.endswith("/") else f"{url}/"
            for url in config[CONF_ALLOWLIST_EXTERNAL_URLS]
        )

    # Customize
    cust_exact = dict(config[CONF_CUSTOMIZE])
    cust_domain = dict(config[CONF_CUSTOMIZE_DOMAIN])
    cust_glob = OrderedDict(config[CONF_CUSTOMIZE_GLOB])

    for name, pkg in config[CONF_PACKAGES].items():
        pkg_cust = pkg.get(CONF_CORE)

        if pkg_cust is None:
            continue

        try:
            pkg_cust = CUSTOMIZE_CONFIG_SCHEMA(pkg_cust)
        except vol.Invalid:
            _LOGGER.warning("Package %s contains invalid customize", name)
            continue

        cust_exact.update(pkg_cust[CONF_CUSTOMIZE])
        cust_domain.update(pkg_cust[CONF_CUSTOMIZE_DOMAIN])
        cust_glob.update(pkg_cust[CONF_CUSTOMIZE_GLOB])

    opp.data[DATA_CUSTOMIZE] = EntityValues(cust_exact, cust_domain, cust_glob)

    if CONF_UNIT_SYSTEM in config:
        if config[CONF_UNIT_SYSTEM] == CONF_UNIT_SYSTEM_IMPERIAL:
            hac.units = IMPERIAL_SYSTEM
        else:
            hac.units = METRIC_SYSTEM
    elif CONF_TEMPERATURE_UNIT in config:
        unit = config[CONF_TEMPERATURE_UNIT]
        hac.units = METRIC_SYSTEM if unit == TEMP_CELSIUS else IMPERIAL_SYSTEM
        _LOGGER.warning(
            "Found deprecated temperature unit in core "
            "configuration expected unit system. Replace '%s: %s' "
            "with '%s: %s'",
            CONF_TEMPERATURE_UNIT,
            unit,
            CONF_UNIT_SYSTEM,
            hac.units.name,
        )


def _log_pkg_error(package: str, component: str, config: Dict, message: str) -> None:
    """Log an error while merging packages."""
    message = f"Package {package} setup failed. Integration {component} {message}"

    pack_config = config[CONF_CORE][CONF_PACKAGES].get(package, config)
    message += (
        f" (See {getattr(pack_config, '__config_file__', '?')}:"
        f"{getattr(pack_config, '__line__', '?')}). "
    )

    _LOGGER.error(message)


def _identify_config_schema(module: ModuleType) -> Optional[str]:
    """Extract the schema and identify list or dict based."""
    if not isinstance(module.CONFIG_SCHEMA, vol.Schema):  # type: ignore
        return None

    schema = module.CONFIG_SCHEMA.schema  # type: ignore

    if isinstance(schema, vol.All):
        for subschema in schema.validators:
            if isinstance(subschema, dict):
                schema = subschema
                break
        else:
            return None

    try:
        key = next(k for k in schema if k == module.DOMAIN)  # type: ignore
    except (TypeError, AttributeError, StopIteration):
        return None
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected error identifying config schema")
        return None

    if hasattr(key, "default") and not isinstance(
        key.default, vol.schema_builder.Undefined
    ):
        default_value = module.CONFIG_SCHEMA({module.DOMAIN: key.default()})[  # type: ignore
            module.DOMAIN  # type: ignore
        ]

        if isinstance(default_value, dict):
            return "dict"

        if isinstance(default_value, list):
            return "list"

        return None

    domain_schema = schema[key]

    t_schema = str(domain_schema)
    if t_schema.startswith("{") or "schema_with_slug_keys" in t_schema:
        return "dict"
    if t_schema.startswith(("[", "All(<function ensure_list")):
        return "list"
    return None


def _recursive_merge(conf: Dict[str, Any], package: Dict[str, Any]) -> Union[bool, str]:
    """Merge package into conf, recursively."""
    error: Union[bool, str] = False
    for key, pack_conf in package.items():
        if isinstance(pack_conf, dict):
            if not pack_conf:
                continue
            conf[key] = conf.get(key, OrderedDict())
            error = _recursive_merge(conf=conf[key], package=pack_conf)

        elif isinstance(pack_conf, list):
            conf[key] = cv.remove_falsy(
                cv.ensure_list(conf.get(key)) + cv.ensure_list(pack_conf)
            )

        else:
            if conf.get(key) is not None:
                return key
            conf[key] = pack_conf
    return error


async def merge_packages_config(
    opp: OpenPeerPower,
    config: Dict,
    packages: Dict[str, Any],
    _log_pkg_error: Callable = _log_pkg_error,
) -> Dict:
    """Merge packages into the top-level configuration. Mutate config."""
    PACKAGES_CONFIG_SCHEMA(packages)
    for pack_name, pack_conf in packages.items():
        for comp_name, comp_conf in pack_conf.items():
            if comp_name == CONF_CORE:
                continue
            # If component name is given with a trailing description, remove it
            # when looking for component
            domain = comp_name.split(" ")[0]

            try:
                integration = await async_get_integration_with_requirements(opp, domain)
                component = integration.get_component()
            except INTEGRATION_LOAD_EXCEPTIONS as ex:
                _log_pkg_error(pack_name, comp_name, config, str(ex))
                continue

            merge_list = hasattr(component, "PLATFORM_SCHEMA")

            if not merge_list and hasattr(component, "CONFIG_SCHEMA"):
                merge_list = _identify_config_schema(component) == "list"

            if merge_list:
                config[comp_name] = cv.remove_falsy(
                    cv.ensure_list(config.get(comp_name)) + cv.ensure_list(comp_conf)
                )
                continue

            if comp_conf is None:
                comp_conf = OrderedDict()

            if not isinstance(comp_conf, dict):
                _log_pkg_error(
                    pack_name, comp_name, config, "cannot be merged. Expected a dict."
                )
                continue

            if comp_name not in config or config[comp_name] is None:
                config[comp_name] = OrderedDict()

            if not isinstance(config[comp_name], dict):
                _log_pkg_error(
                    pack_name,
                    comp_name,
                    config,
                    "cannot be merged. Dict expected in main config.",
                )
                continue

            error = _recursive_merge(conf=config[comp_name], package=comp_conf)
            if error:
                _log_pkg_error(
                    pack_name, comp_name, config, f"has duplicate key '{error}'"
                )

    return config


async def async_process_component_config(
    opp: OpenPeerPower, config: ConfigType, integration: Integration
) -> Optional[ConfigType]:
    """Check component configuration and return processed configuration.

    Returns None on error.

    This method must be run in the event loop.
    """
    domain = integration.domain
    try:
        component = integration.get_component()
    except LOAD_EXCEPTIONS as ex:
        _LOGGER.error("Unable to import %s: %s", domain, ex)
        return None

    # Check if the integration has a custom config validator
    config_validator = None
    try:
        config_validator = integration.get_platform("config")
    except ImportError as err:
        # Filter out import error of the config platform.
        # If the config platform contains bad imports, make sure
        # that still fails.
        if err.name != f"{integration.pkg_path}.config":
            _LOGGER.error("Error importing config platform %s: %s", domain, err)
            return None

    if config_validator is not None and hasattr(
        config_validator, "async_validate_config"
    ):
        try:
            return await config_validator.async_validate_config(  # type: ignore
                opp, config
            )
        except (vol.Invalid, OpenPeerPowerError) as ex:
            async_log_exception(ex, domain, config, opp, integration.documentation)
            return None
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unknown error calling %s config validator", domain)
            return None

    # No custom config validator, proceed with schema validation
    if hasattr(component, "CONFIG_SCHEMA"):
        try:
            return component.CONFIG_SCHEMA(config)  # type: ignore
        except vol.Invalid as ex:
            async_log_exception(ex, domain, config, opp, integration.documentation)
            return None
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unknown error calling %s CONFIG_SCHEMA", domain)
            return None

    component_platform_schema = getattr(
        component, "PLATFORM_SCHEMA_BASE", getattr(component, "PLATFORM_SCHEMA", None)
    )

    if component_platform_schema is None:
        return config

    platforms = []
    for p_name, p_config in config_per_platform(config, domain):
        # Validate component specific platform schema
        try:
            p_validated = component_platform_schema(p_config)
        except vol.Invalid as ex:
            async_log_exception(ex, domain, p_config, opp, integration.documentation)
            continue
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Unknown error validating %s platform config with %s component platform schema",
                p_name,
                domain,
            )
            continue

        # Not all platform components follow same pattern for platforms
        # So if p_name is None we are not going to validate platform
        # (the automation component is one of them)
        if p_name is None:
            platforms.append(p_validated)
            continue

        try:
            p_integration = await async_get_integration_with_requirements(opp, p_name)
        except (RequirementsNotFound, IntegrationNotFound) as ex:
            _LOGGER.error("Platform error: %s - %s", domain, ex)
            continue

        try:
            platform = p_integration.get_platform(domain)
        except LOAD_EXCEPTIONS:
            _LOGGER.exception("Platform error: %s", domain)
            continue

        # Validate platform specific schema
        if hasattr(platform, "PLATFORM_SCHEMA"):
            try:
                p_validated = platform.PLATFORM_SCHEMA(p_config)  # type: ignore
            except vol.Invalid as ex:
                async_log_exception(
                    ex,
                    f"{domain}.{p_name}",
                    p_config,
                    opp,
                    p_integration.documentation,
                )
                continue
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception(
                    "Unknown error validating config for %s platform for %s component with PLATFORM_SCHEMA",
                    p_name,
                    domain,
                )
                continue

        platforms.append(p_validated)

    # Create a copy of the configuration with all config for current
    # component removed and add validated config back in.
    config = config_without_domain(config, domain)
    config[domain] = platforms

    return config


@callback
def config_without_domain(config: Dict, domain: str) -> Dict:
    """Return a config with all configuration for a domain removed."""
    filter_keys = extract_domain_configs(config, domain)
    return {key: value for key, value in config.items() if key not in filter_keys}


async def async_check_op_config_file(opp: OpenPeerPower) -> Optional[str]:
    """Check if Open Peer Power configuration file is valid.

    This method is a coroutine.
    """
    # pylint: disable=import-outside-toplevel
    import openpeerpower.helpers.check_config as check_config

    res = await check_config.async_check_op_config_file(opp)

    if not res.errors:
        return None
    return res.error_str


@callback
def async_notify_setup_error(
    opp: OpenPeerPower, component: str, display_link: Optional[str] = None
) -> None:
    """Print a persistent notification.

    This method must be run in the event loop.
    """
    # pylint: disable=import-outside-toplevel
    from openpeerpower.components import persistent_notification

    errors = opp.data.get(DATA_PERSISTENT_ERRORS)

    if errors is None:
        errors = opp.data[DATA_PERSISTENT_ERRORS] = {}

    errors[component] = errors.get(component) or display_link

    message = "The following integrations and platforms could not be set up:\n\n"

    for name, link in errors.items():
        part = f"[{name}]({link})" if link else name
        message += f" - {part}\n"

    message += "\nPlease check your config and [logs](/config/logs)."

    persistent_notification.async_create(
        opp, message, "Invalid config", "invalid_config"
    )
