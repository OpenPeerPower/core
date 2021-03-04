"""Component to allow running Python scripts."""
import datetime
import glob
import logging
import os
import time

from RestrictedPython import (
    compile_restricted_exec,
    limited_builtins,
    safe_builtins,
    utility_builtins,
)
from RestrictedPython.Eval import default_guarded_getitem
from RestrictedPython.Guards import (
    full_write_guard,
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
)
import voluptuous as vol

from openpeerpower.const import SERVICE_RELOAD
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers.service import async_set_service_schema
from openpeerpower.loader import bind_opp
from openpeerpower.util import raise_if_invalid_filename
import openpeerpower.util.dt as dt_util
from openpeerpower.util.yaml.loader import load_yaml

_LOGGER = logging.getLogger(__name__)

DOMAIN = "python_script"

FOLDER = "python_scripts"

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema(dict)}, extra=vol.ALLOW_EXTRA)

ALLOWED_OPP = {"bus", "services", "states"}
ALLOWED_EVENTBUS = {"fire"}
ALLOWED_STATEMACHINE = {
    "entity_ids",
    "all",
    "get",
    "is_state",
    "is_state_attr",
    "remove",
    "set",
}
ALLOWED_SERVICEREGISTRY = {"services", "has_service", "call"}
ALLOWED_TIME = {
    "sleep",
    "strftime",
    "strptime",
    "gmtime",
    "localtime",
    "ctime",
    "time",
    "mktime",
}
ALLOWED_DATETIME = {"date", "time", "datetime", "timedelta", "tzinfo"}
ALLOWED_DT_UTIL = {
    "utcnow",
    "now",
    "as_utc",
    "as_timestamp",
    "as_local",
    "utc_from_timestamp",
    "start_of_local_day",
    "parse_datetime",
    "parse_date",
    "get_age",
}


class ScriptError(OpenPeerPowerError):
    """When a script error occurs."""


def setup(opp, config):
    """Initialize the Python script component."""
    path = opp.config.path(FOLDER)

    if not os.path.isdir(path):
        _LOGGER.warning("Folder %s not found in configuration folder", FOLDER)
        return False

    discover_scripts(opp)

    def reload_scripts_handler(call):
        """Handle reload service calls."""
        discover_scripts(opp)

    opp.services.register(DOMAIN, SERVICE_RELOAD, reload_scripts_handler)

    return True


def discover_scripts(opp):
    """Discover python scripts in folder."""
    path = opp.config.path(FOLDER)

    if not os.path.isdir(path):
        _LOGGER.warning("Folder %s not found in configuration folder", FOLDER)
        return False

    def python_script_service_handler(call):
        """Handle python script service calls."""
        execute_script(opp, call.service, call.data)

    existing = opp.services.services.get(DOMAIN, {}).keys()
    for existing_service in existing:
        if existing_service == SERVICE_RELOAD:
            continue
        opp.services.remove(DOMAIN, existing_service)

    # Load user-provided service descriptions from python_scripts/services.yaml
    services_yaml = os.path.join(path, "services.yaml")
    if os.path.exists(services_yaml):
        services_dict = load_yaml(services_yaml)
    else:
        services_dict = {}

    for fil in glob.iglob(os.path.join(path, "*.py")):
        name = os.path.splitext(os.path.basename(fil))[0]
        opp.services.register(DOMAIN, name, python_script_service_handler)

        service_desc = {
            "description": services_dict.get(name, {}).get("description", ""),
            "fields": services_dict.get(name, {}).get("fields", {}),
        }
        async_set_service_schema(opp, DOMAIN, name, service_desc)


@bind_opp
def execute_script(opp, name, data=None):
    """Execute a script."""
    filename = f"{name}.py"
    raise_if_invalid_filename(filename)
    with open(opp.config.path(FOLDER, filename)) as fil:
        source = fil.read()
    execute(opp, filename, source, data)


@bind_opp
def execute(opp, filename, source, data=None):
    """Execute Python source."""

    compiled = compile_restricted_exec(source, filename=filename)

    if compiled.errors:
        _LOGGER.error(
            "Error loading script %s: %s", filename, ", ".join(compiled.errors)
        )
        return

    if compiled.warnings:
        _LOGGER.warning(
            "Warning loading script %s: %s", filename, ", ".join(compiled.warnings)
        )

    def protected_getattr(obj, name, default=None):
        """Restricted method to get attributes."""
        if name.startswith("async_"):
            raise ScriptError("Not allowed to access async methods")
        if (
            obj is opp
            and name not in ALLOWED_OPP
            or obj is opp.bus
            and name not in ALLOWED_EVENTBUS
            or obj is opp.states
            and name not in ALLOWED_STATEMACHINE
            or obj is opp.services
            and name not in ALLOWED_SERVICEREGISTRY
            or obj is dt_util
            and name not in ALLOWED_DT_UTIL
            or obj is datetime
            and name not in ALLOWED_DATETIME
            or isinstance(obj, TimeWrapper)
            and name not in ALLOWED_TIME
        ):
            raise ScriptError(f"Not allowed to access {obj.__class__.__name__}.{name}")

        return getattr(obj, name, default)

    extra_builtins = {
        "datetime": datetime,
        "sorted": sorted,
        "time": TimeWrapper(),
        "dt_util": dt_util,
        "min": min,
        "max": max,
        "sum": sum,
        "any": any,
        "all": all,
    }
    builtins = safe_builtins.copy()
    builtins.update(utility_builtins)
    builtins.update(limited_builtins)
    builtins.update(extra_builtins)
    logger = logging.getLogger(f"{__name__}.{filename}")
    restricted_globals = {
        "__builtins__": builtins,
        "_print_": StubPrinter,
        "_getattr_": protected_getattr,
        "_write_": full_write_guard,
        "_getiter_": iter,
        "_getitem_": default_guarded_getitem,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        "_unpack_sequence_": guarded_unpack_sequence,
        "opp": opp,
        "data": data or {},
        "logger": logger,
    }

    try:
        _LOGGER.info("Executing %s: %s", filename, data)
        # pylint: disable=exec-used
        exec(compiled.code, restricted_globals)
    except ScriptError as err:
        logger.error("Error executing script: %s", err)
    except Exception as err:  # pylint: disable=broad-except
        logger.exception("Error executing script: %s", err)


class StubPrinter:
    """Class to handle printing inside scripts."""

    def __init__(self, _getattr_):
        """Initialize our printer."""

    def _call_print(self, *objects, **kwargs):
        """Print text."""
        # pylint: disable=no-self-use
        _LOGGER.warning("Don't use print() inside scripts. Use logger.info() instead")


class TimeWrapper:
    """Wrap the time module."""

    # Class variable, only going to warn once per Open Peer Power run
    warned = False

    # pylint: disable=no-self-use
    def sleep(self, *args, **kwargs):
        """Sleep method that warns once."""
        if not TimeWrapper.warned:
            TimeWrapper.warned = True
            _LOGGER.warning(
                "Using time.sleep can reduce the performance of Open Peer Power"
            )

        time.sleep(*args, **kwargs)

    def __getattr__(self, attr):
        """Fetch an attribute from Time module."""
        attribute = getattr(time, attr)
        if callable(attribute):

            def wrapper(*args, **kw):
                """Wrap to return callable method if callable."""
                return attribute(*args, **kw)

            return wrapper
        return attribute
