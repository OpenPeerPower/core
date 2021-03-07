"""Provide methods to bootstrap a Open Peer Power instance."""
import asyncio
import contextlib
from datetime import datetime
import logging
import logging.handlers
import os
import sys
import threading
from time import monotonic
from typing import TYPE_CHECKING, Any, Dict, Optional, Set

import voluptuous as vol
import yarl

from openpeerpower import config as conf_util, config_entries, core, loader
from openpeerpower.components import http
from openpeerpower.const import REQUIRED_NEXT_PYTHON_DATE, REQUIRED_NEXT_PYTHON_VER
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import area_registry, device_registry, entity_registry
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.setup import (
    DATA_SETUP,
    DATA_SETUP_STARTED,
    async_set_domains_to_be_loaded,
    async_setup_component,
)
from openpeerpower.util.async_ import gather_with_concurrency
from openpeerpower.util.logging import async_activate_log_queue_handler
from openpeerpower.util.package import async_get_user_site, is_virtual_env

if TYPE_CHECKING:
    from .runner import RuntimeConfig

_LOGGER = logging.getLogger(__name__)

ERROR_LOG_FILENAME = "open-peer-power.log"

# opp.data key for logging information.
DATA_LOGGING = "logging"

LOG_SLOW_STARTUP_INTERVAL = 60

STAGE_1_TIMEOUT = 120
STAGE_2_TIMEOUT = 300
WRAP_UP_TIMEOUT = 300
COOLDOWN_TIME = 60

MAX_LOAD_CONCURRENTLY = 6

DEBUGGER_INTEGRATIONS = {"debugpy"}
CORE_INTEGRATIONS = ("openpeerpower", "persistent_notification")
LOGGING_INTEGRATIONS = {
    # Set log levels
    "logger",
    # Error logging
    "system_log",
    "sentry",
    # To record data
    "recorder",
}
STAGE_1_INTEGRATIONS = {
    # To make sure we forward data to other instances
    "mqtt_eventstream",
    # To provide account link implementations
    "cloud",
    # Ensure supervisor is available
    "oppio",
    # Get the frontend up and running as soon
    # as possible so problem integrations can
    # be removed
    "frontend",
}


async def async_setup_opp(
    runtime_config: "RuntimeConfig",
) -> Optional[core.OpenPeerPower]:
    """Set up Open Peer Power."""
    opp = core.OpenPeerPower()
    opp.config.config_dir = runtime_config.config_dir

    async_enable_logging(
        opp,
        runtime_config.verbose,
        runtime_config.log_rotate_days,
        runtime_config.log_file,
        runtime_config.log_no_color,
    )

    opp.config.skip_pip = runtime_config.skip_pip
    if runtime_config.skip_pip:
        _LOGGER.warning(
            "Skipping pip installation of required modules. This may cause issues"
        )

    if not await conf_util.async_ensure_config_exists(opp):
        _LOGGER.error("Error getting configuration path")
        return None

    _LOGGER.info("Config directory: %s", runtime_config.config_dir)

    config_dict = None
    basic_setup_success = False
    safe_mode = runtime_config.safe_mode

    if not safe_mode:
        await opp.async_add_executor_job(conf_util.process_op_config_upgrade, opp)

        try:
            config_dict = await conf_util.async_opp_config_yaml(opp)
        except OpenPeerPowerError as err:
            _LOGGER.error(
                "Failed to parse configuration.yaml: %s. Activating safe mode",
                err,
            )
        else:
            if not is_virtual_env():
                await async_mount_local_lib_path(runtime_config.config_dir)

            basic_setup_success = (
                await async_from_config_dict(config_dict, opp) is not None
            )

    if config_dict is None:
        safe_mode = True

    elif not basic_setup_success:
        _LOGGER.warning("Unable to set up core integrations. Activating safe mode")
        safe_mode = True

    elif (
        "frontend" in opp.data.get(DATA_SETUP, {})
        and "frontend" not in opp.config.components
    ):
        _LOGGER.warning("Detected that frontend did not load. Activating safe mode")
        # Ask integrations to shut down. It's messy but we can't
        # do a clean stop without knowing what is broken
        with contextlib.suppress(asyncio.TimeoutError):
            async with opp.timeout.async_timeout(10):
                await opp.async_stop()

        safe_mode = True
        old_config = opp.config

        opp = core.OpenPeerPower()
        opp.config.skip_pip = old_config.skip_pip
        opp.config.internal_url = old_config.internal_url
        opp.config.external_url = old_config.external_url
        opp.config.config_dir = old_config.config_dir

    if safe_mode:
        _LOGGER.info("Starting in safe mode")
        opp.config.safe_mode = True

        http_conf = (await http.async_get_last_config(opp)) or {}

        await async_from_config_dict(
            {"safe_mode": {}, "http": http_conf},
            opp,
        )

    if runtime_config.open_ui:
        opp.add_job(open_opp_ui, opp)

    return opp


def open_opp_ui(opp: core.OpenPeerPower) -> None:
    """Open the UI."""
    import webbrowser  # pylint: disable=import-outside-toplevel

    if opp.config.api is None or "frontend" not in opp.config.components:
        _LOGGER.warning("Cannot launch the UI because frontend not loaded")
        return

    scheme = "https" if opp.config.api.use_ssl else "http"
    url = str(yarl.URL.build(scheme=scheme, host="127.0.0.1", port=opp.config.api.port))

    if not webbrowser.open(url):
        _LOGGER.warning(
            "Unable to open the Open Peer Power UI in a browser. Open it yourself at %s",
            url,
        )


async def async_from_config_dict(
    config: ConfigType, opp: core.OpenPeerPower
) -> Optional[core.OpenPeerPower]:
    """Try to configure Open Peer Power from a configuration dictionary.

    Dynamically loads required components and its dependencies.
    This method is a coroutine.
    """
    start = monotonic()

    opp.config_entries = config_entries.ConfigEntries(opp, config)
    await opp.config_entries.async_initialize()

    # Set up core.
    _LOGGER.debug("Setting up %s", CORE_INTEGRATIONS)

    if not all(
        await asyncio.gather(
            *(
                async_setup_component(opp, domain, config)
                for domain in CORE_INTEGRATIONS
            )
        )
    ):
        _LOGGER.error("Open Peer Power core failed to initialize. ")
        return None

    _LOGGER.debug("Open Peer Power core initialized")

    core_config = config.get(core.DOMAIN, {})

    try:
        await conf_util.async_process_op_core_config(opp, core_config)
    except vol.Invalid as config_err:
        conf_util.async_log_exception(config_err, "openpeerpower", core_config, opp)
        return None
    except OpenPeerPowerError:
        _LOGGER.error(
            "Open Peer Power core failed to initialize. "
            "Further initialization aborted"
        )
        return None

    await _async_set_up_integrations(opp, config)

    stop = monotonic()
    _LOGGER.info("Open Peer Power initialized in %.2fs", stop - start)

    if REQUIRED_NEXT_PYTHON_DATE and sys.version_info[:3] < REQUIRED_NEXT_PYTHON_VER:
        msg = (
            "Support for the running Python version "
            f"{'.'.join(str(x) for x in sys.version_info[:3])} is deprecated and will "
            f"be removed in the first release after {REQUIRED_NEXT_PYTHON_DATE}. "
            "Please upgrade Python to "
            f"{'.'.join(str(x) for x in REQUIRED_NEXT_PYTHON_VER)} or "
            "higher."
        )
        _LOGGER.warning(msg)
        opp.components.persistent_notification.async_create(
            msg, "Python version", "python_version"
        )

    return opp


@core.callback
def async_enable_logging(
    opp: core.OpenPeerPower,
    verbose: bool = False,
    log_rotate_days: Optional[int] = None,
    log_file: Optional[str] = None,
    log_no_color: bool = False,
) -> None:
    """Set up the logging.

    This method must be run in the event loop.
    """
    fmt = "%(asctime)s %(levelname)s (%(threadName)s) [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    if not log_no_color:
        try:
            # pylint: disable=import-outside-toplevel
            from colorlog import ColoredFormatter

            # basicConfig must be called after importing colorlog in order to
            # ensure that the handlers it sets up wraps the correct streams.
            logging.basicConfig(level=logging.INFO)

            colorfmt = f"%(log_color)s{fmt}%(reset)s"
            logging.getLogger().handlers[0].setFormatter(
                ColoredFormatter(
                    colorfmt,
                    datefmt=datefmt,
                    reset=True,
                    log_colors={
                        "DEBUG": "cyan",
                        "INFO": "green",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "red",
                    },
                )
            )
        except ImportError:
            pass

    # If the above initialization failed for any reason, setup the default
    # formatting.  If the above succeeds, this will result in a no-op.
    logging.basicConfig(format=fmt, datefmt=datefmt, level=logging.INFO)

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

    sys.excepthook = lambda *args: logging.getLogger(None).exception(
        "Uncaught exception", exc_info=args  # type: ignore
    )
    threading.excepthook = lambda args: logging.getLogger(None).exception(
        "Uncaught thread exception",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),  # type: ignore[arg-type]
    )

    # Log errors to a file if we have write access to file or config dir
    if log_file is None:
        err_log_path = opp.config.path(ERROR_LOG_FILENAME)
    else:
        err_log_path = os.path.abspath(log_file)

    err_path_exists = os.path.isfile(err_log_path)
    err_dir = os.path.dirname(err_log_path)

    # Check if we can write to the error log if it exists or that
    # we can create files in the containing directory if not.
    if (err_path_exists and os.access(err_log_path, os.W_OK)) or (
        not err_path_exists and os.access(err_dir, os.W_OK)
    ):

        if log_rotate_days:
            err_handler: logging.FileHandler = (
                logging.handlers.TimedRotatingFileHandler(
                    err_log_path, when="midnight", backupCount=log_rotate_days
                )
            )
        else:
            err_handler = logging.FileHandler(err_log_path, mode="w", delay=True)

        err_handler.setLevel(logging.INFO if verbose else logging.WARNING)
        err_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

        logger = logging.getLogger("")
        logger.addHandler(err_handler)
        logger.setLevel(logging.INFO if verbose else logging.WARNING)

        # Save the log file location for access by other components.
        opp.data[DATA_LOGGING] = err_log_path
    else:
        _LOGGER.error("Unable to set up error log %s (access denied)", err_log_path)

    async_activate_log_queue_handler(opp)


async def async_mount_local_lib_path(config_dir: str) -> str:
    """Add local library to Python Path.

    This function is a coroutine.
    """
    deps_dir = os.path.join(config_dir, "deps")
    lib_dir = await async_get_user_site(deps_dir)
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)
    return deps_dir


@core.callback
def _get_domains(opp: core.OpenPeerPower, config: Dict[str, Any]) -> Set[str]:
    """Get domains of components to set up."""
    # Filter out the repeating and common config section [openpeerpower]
    domains = {key.split(" ")[0] for key in config if key != core.DOMAIN}

    # Add config entry domains
    if not opp.config.safe_mode:
        domains.update(opp.config_entries.async_domains())

    # Make sure the Opp.io component is loaded
    if "OPPIO" in os.environ:
        domains.add("oppio")

    return domains


async def _async_log_pending_setups(
    opp: core.OpenPeerPower, domains: Set[str], setup_started: Dict[str, datetime]
) -> None:
    """Periodic log of setups that are pending for longer than LOG_SLOW_STARTUP_INTERVAL."""
    while True:
        await asyncio.sleep(LOG_SLOW_STARTUP_INTERVAL)
        remaining = [domain for domain in domains if domain in setup_started]

        if remaining:
            _LOGGER.warning(
                "Waiting on integrations to complete setup: %s",
                ", ".join(remaining),
            )
        _LOGGER.debug("Running timeout Zones: %s", opp.timeout.zones)


async def async_setup_multi_components(
    opp: core.OpenPeerPower,
    domains: Set[str],
    config: Dict[str, Any],
    setup_started: Dict[str, datetime],
) -> None:
    """Set up multiple domains. Log on failure."""
    futures = {
        domain: opp.async_create_task(async_setup_component(opp, domain, config))
        for domain in domains
    }
    log_task = asyncio.create_task(
        _async_log_pending_setups(opp, domains, setup_started)
    )
    await asyncio.wait(futures.values())
    log_task.cancel()
    errors = [domain for domain in domains if futures[domain].exception()]
    for domain in errors:
        exception = futures[domain].exception()
        assert exception is not None
        _LOGGER.error(
            "Error setting up integration %s - received exception",
            domain,
            exc_info=(type(exception), exception, exception.__traceback__),
        )


async def _async_set_up_integrations(
    opp: core.OpenPeerPower, config: Dict[str, Any]
) -> None:
    """Set up all the integrations."""
    setup_started = opp.data[DATA_SETUP_STARTED] = {}
    domains_to_setup = _get_domains(opp, config)

    # Resolve all dependencies so we know all integrations
    # that will have to be loaded and start rightaway
    integration_cache: Dict[str, loader.Integration] = {}
    to_resolve = domains_to_setup
    while to_resolve:
        old_to_resolve = to_resolve
        to_resolve = set()

        integrations_to_process = [
            int_or_exc
            for int_or_exc in await gather_with_concurrency(
                loader.MAX_LOAD_CONCURRENTLY,
                *(
                    loader.async_get_integration(opp, domain)
                    for domain in old_to_resolve
                ),
                return_exceptions=True,
            )
            if isinstance(int_or_exc, loader.Integration)
        ]
        resolve_dependencies_tasks = [
            itg.resolve_dependencies()
            for itg in integrations_to_process
            if not itg.all_dependencies_resolved
        ]

        if resolve_dependencies_tasks:
            await asyncio.gather(*resolve_dependencies_tasks)

        for itg in integrations_to_process:
            integration_cache[itg.domain] = itg

            for dep in itg.all_dependencies:
                if dep in domains_to_setup:
                    continue

                domains_to_setup.add(dep)
                to_resolve.add(dep)

    _LOGGER.info("Domains to be set up: %s", domains_to_setup)

    logging_domains = domains_to_setup & LOGGING_INTEGRATIONS

    # Load logging as soon as possible
    if logging_domains:
        _LOGGER.info("Setting up logging: %s", logging_domains)
        await async_setup_multi_components(opp, logging_domains, config, setup_started)

    # Start up debuggers. Start these first in case they want to wait.
    debuggers = domains_to_setup & DEBUGGER_INTEGRATIONS

    if debuggers:
        _LOGGER.debug("Setting up debuggers: %s", debuggers)
        await async_setup_multi_components(opp, debuggers, config, setup_started)

    # calculate what components to setup in what stage
    stage_1_domains = set()

    # Find all dependencies of any dependency of any stage 1 integration that
    # we plan on loading and promote them to stage 1
    deps_promotion = STAGE_1_INTEGRATIONS
    while deps_promotion:
        old_deps_promotion = deps_promotion
        deps_promotion = set()

        for domain in old_deps_promotion:
            if domain not in domains_to_setup or domain in stage_1_domains:
                continue

            stage_1_domains.add(domain)

            dep_itg = integration_cache.get(domain)

            if dep_itg is None:
                continue

            deps_promotion.update(dep_itg.all_dependencies)

    stage_2_domains = domains_to_setup - logging_domains - debuggers - stage_1_domains

    # Load the registries
    await asyncio.gather(
        device_registry.async_load(opp),
        entity_registry.async_load(opp),
        area_registry.async_load(opp),
    )

    # Start setup
    if stage_1_domains:
        _LOGGER.info("Setting up stage 1: %s", stage_1_domains)
        try:
            async with opp.timeout.async_timeout(
                STAGE_1_TIMEOUT, cool_down=COOLDOWN_TIME
            ):
                await async_setup_multi_components(
                    opp, stage_1_domains, config, setup_started
                )
        except asyncio.TimeoutError:
            _LOGGER.warning("Setup timed out for stage 1 - moving forward")

    # Enables after dependencies
    async_set_domains_to_be_loaded(opp, stage_2_domains)

    if stage_2_domains:
        _LOGGER.info("Setting up stage 2: %s", stage_2_domains)
        try:
            async with opp.timeout.async_timeout(
                STAGE_2_TIMEOUT, cool_down=COOLDOWN_TIME
            ):
                await async_setup_multi_components(
                    opp, stage_2_domains, config, setup_started
                )
        except asyncio.TimeoutError:
            _LOGGER.warning("Setup timed out for stage 2 - moving forward")

    # Wrap up startup
    _LOGGER.debug("Waiting for startup to wrap up")
    try:
        async with opp.timeout.async_timeout(WRAP_UP_TIMEOUT, cool_down=COOLDOWN_TIME):
            await opp.async_block_till_done()
    except asyncio.TimeoutError:
        _LOGGER.warning("Setup timed out for bootstrap - moving forward")
