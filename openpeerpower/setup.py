"""All methods needed to bootstrap a Open Peer Power instance."""
import asyncio
import logging.handlers
from timeit import default_timer as timer
from types import ModuleType
from typing import Awaitable, Callable, Optional, Set

from openpeerpower import config as conf_util, core, loader, requirements
from openpeerpower.config import async_notify_setup_error
from openpeerpower.const import EVENT_COMPONENT_LOADED, PLATFORM_FORMAT
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

ATTR_COMPONENT = "component"

DATA_SETUP_DONE = "setup_done"
DATA_SETUP_STARTED = "setup_started"
DATA_SETUP = "setup_tasks"
DATA_DEPS_REQS = "deps_reqs_processed"

SLOW_SETUP_WARNING = 10
SLOW_SETUP_MAX_WAIT = 300


@core.callback
def async_set_domains_to_be_loaded(opp: core.OpenPeerPower, domains: Set[str]) -> None:
    """Set domains that are going to be loaded from the config.

    This will allow us to properly handle after_dependencies.
    """
    opp.data[DATA_SETUP_DONE] = {domain: asyncio.Event() for domain in domains}


def setup_component(opp: core.OpenPeerPower, domain: str, config: ConfigType) -> bool:
    """Set up a component and all its dependencies."""
    return asyncio.run_coroutine_threadsafe(
        async_setup_component(opp, domain, config), opp.loop
    ).result()


async def async_setup_component(
    opp: core.OpenPeerPower, domain: str, config: ConfigType
) -> bool:
    """Set up a component and all its dependencies.

    This method is a coroutine.
    """
    if domain in opp.config.components:
        return True

    setup_tasks = opp.data.setdefault(DATA_SETUP, {})

    if domain in setup_tasks:
        return await setup_tasks[domain]  # type: ignore

    task = setup_tasks[domain] = opp.async_create_task(
        _async_setup_component(opp, domain, config)
    )

    try:
        return await task  # type: ignore
    finally:
        if domain in opp.data.get(DATA_SETUP_DONE, {}):
            opp.data[DATA_SETUP_DONE].pop(domain).set()


async def _async_process_dependencies(
    opp: core.OpenPeerPower, config: ConfigType, integration: loader.Integration
) -> bool:
    """Ensure all dependencies are set up."""
    dependencies_tasks = {
        dep: opp.loop.create_task(async_setup_component(opp, dep, config))
        for dep in integration.dependencies
        if dep not in opp.config.components
    }

    after_dependencies_tasks = {}
    to_be_loaded = opp.data.get(DATA_SETUP_DONE, {})
    for dep in integration.after_dependencies:
        if (
            dep not in dependencies_tasks
            and dep in to_be_loaded
            and dep not in opp.config.components
        ):
            after_dependencies_tasks[dep] = opp.loop.create_task(
                to_be_loaded[dep].wait()
            )

    if not dependencies_tasks and not after_dependencies_tasks:
        return True

    if dependencies_tasks:
        _LOGGER.debug(
            "Dependency %s will wait for dependencies %s",
            integration.domain,
            list(dependencies_tasks),
        )
    if after_dependencies_tasks:
        _LOGGER.debug(
            "Dependency %s will wait for after dependencies %s",
            integration.domain,
            list(after_dependencies_tasks),
        )

    async with opp.timeout.async_freeze(integration.domain):
        results = await asyncio.gather(
            *dependencies_tasks.values(), *after_dependencies_tasks.values()
        )

    failed = [
        domain for idx, domain in enumerate(dependencies_tasks) if not results[idx]
    ]

    if failed:
        _LOGGER.error(
            "Unable to set up dependencies of %s. Setup failed for dependencies: %s",
            integration.domain,
            ", ".join(failed),
        )

        return False
    return True


async def _async_setup_component(
    opp: core.OpenPeerPower, domain: str, config: ConfigType
) -> bool:
    """Set up a component for Open Peer Power.

    This method is a coroutine.
    """

    def log_error(msg: str, link: Optional[str] = None) -> None:
        """Log helper."""
        _LOGGER.error("Setup failed for %s: %s", domain, msg)
        async_notify_setup_error(opp, domain, link)

    try:
        integration = await loader.async_get_integration(opp, domain)
    except loader.IntegrationNotFound:
        log_error("Integration not found.")
        return False

    if integration.disabled:
        log_error(f"dependency is disabled - {integration.disabled}")
        return False

    # Validate all dependencies exist and there are no circular dependencies
    if not await integration.resolve_dependencies():
        return False

    # Process requirements as soon as possible, so we can import the component
    # without requiring imports to be in functions.
    try:
        await async_process_deps_reqs(opp, config, integration)
    except OpenPeerPowerError as err:
        log_error(str(err), integration.documentation)
        return False

    # Some integrations fail on import because they call functions incorrectly.
    # So we do it before validating config to catch these errors.
    try:
        component = integration.get_component()
    except ImportError as err:
        log_error(f"Unable to import component: {err}", integration.documentation)
        return False
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Setup failed for %s: unknown error", domain)
        return False

    processed_config = await conf_util.async_process_component_config(
        opp, config, integration
    )

    if processed_config is None:
        log_error("Invalid config.", integration.documentation)
        return False

    start = timer()
    _LOGGER.info("Setting up %s", domain)
    opp.data.setdefault(DATA_SETUP_STARTED, {})[domain] = dt_util.utcnow()

    if hasattr(component, "PLATFORM_SCHEMA"):
        # Entity components have their own warning
        warn_task = None
    else:
        warn_task = opp.loop.call_later(
            SLOW_SETUP_WARNING,
            _LOGGER.warning,
            "Setup of %s is taking over %s seconds.",
            domain,
            SLOW_SETUP_WARNING,
        )

    try:
        if hasattr(component, "async_setup"):
            task = component.async_setup(opp, processed_config)  # type: ignore
        elif hasattr(component, "setup"):
            # This should not be replaced with opp.async_add_executor_job because
            # we don't want to track this task in case it blocks startup.
            task = opp.loop.run_in_executor(
                None, component.setup, opp, processed_config  # type: ignore
            )
        else:
            log_error("No setup function defined.")
            opp.data[DATA_SETUP_STARTED].pop(domain)
            return False

        async with opp.timeout.async_timeout(SLOW_SETUP_MAX_WAIT, domain):
            result = await task
    except asyncio.TimeoutError:
        _LOGGER.error(
            "Setup of %s is taking longer than %s seconds."
            " Startup will proceed without waiting any longer",
            domain,
            SLOW_SETUP_MAX_WAIT,
        )
        opp.data[DATA_SETUP_STARTED].pop(domain)
        return False
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Error during setup of component %s", domain)
        async_notify_setup_error(opp, domain, integration.documentation)
        opp.data[DATA_SETUP_STARTED].pop(domain)
        return False
    finally:
        end = timer()
        if warn_task:
            warn_task.cancel()
    _LOGGER.info("Setup of domain %s took %.1f seconds", domain, end - start)

    if result is False:
        log_error("Integration failed to initialize.")
        opp.data[DATA_SETUP_STARTED].pop(domain)
        return False
    if result is not True:
        log_error(
            f"Integration {domain!r} did not return boolean if setup was "
            "successful. Disabling component."
        )
        opp.data[DATA_SETUP_STARTED].pop(domain)
        return False

    # Flush out async_setup calling create_task. Fragile but covered by test.
    await asyncio.sleep(0)
    await opp.config_entries.flow.async_wait_init_flow_finish(domain)

    await asyncio.gather(
        *[
            entry.async_setup(opp, integration=integration)
            for entry in opp.config_entries.async_entries(domain)
        ]
    )

    opp.config.components.add(domain)
    opp.data[DATA_SETUP_STARTED].pop(domain)

    # Cleanup
    if domain in opp.data[DATA_SETUP]:
        opp.data[DATA_SETUP].pop(domain)

    opp.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: domain})

    return True


async def async_prepare_setup_platform(
    opp: core.OpenPeerPower, opp_config: ConfigType, domain: str, platform_name: str
) -> Optional[ModuleType]:
    """Load a platform and makes sure dependencies are setup.

    This method is a coroutine.
    """
    platform_path = PLATFORM_FORMAT.format(domain=domain, platform=platform_name)

    def log_error(msg: str) -> None:
        """Log helper."""
        _LOGGER.error("Unable to prepare setup for platform %s: %s", platform_path, msg)
        async_notify_setup_error(opp, platform_path)

    try:
        integration = await loader.async_get_integration(opp, platform_name)
    except loader.IntegrationNotFound:
        log_error("Integration not found")
        return None

    # Process deps and reqs as soon as possible, so that requirements are
    # available when we import the platform.
    try:
        await async_process_deps_reqs(opp, opp_config, integration)
    except OpenPeerPowerError as err:
        log_error(str(err))
        return None

    try:
        platform = integration.get_platform(domain)
    except ImportError as exc:
        log_error(f"Platform not found ({exc}).")
        return None

    # Already loaded
    if platform_path in opp.config.components:
        return platform

    # Platforms cannot exist on their own, they are part of their integration.
    # If the integration is not set up yet, and can be set up, set it up.
    if integration.domain not in opp.config.components:
        try:
            component = integration.get_component()
        except ImportError as exc:
            log_error(f"Unable to import the component ({exc}).")
            return None

        if hasattr(component, "setup") or hasattr(component, "async_setup"):
            if not await async_setup_component(opp, integration.domain, opp_config):
                log_error("Unable to set up component.")
                return None

    return platform


async def async_process_deps_reqs(
    opp: core.OpenPeerPower, config: ConfigType, integration: loader.Integration
) -> None:
    """Process all dependencies and requirements for a module.

    Module is a Python module of either a component or platform.
    """
    processed = opp.data.get(DATA_DEPS_REQS)

    if processed is None:
        processed = opp.data[DATA_DEPS_REQS] = set()
    elif integration.domain in processed:
        return

    if not await _async_process_dependencies(opp, config, integration):
        raise OpenPeerPowerError("Could not set up all dependencies.")

    if not opp.config.skip_pip and integration.requirements:
        async with opp.timeout.async_freeze(integration.domain):
            await requirements.async_get_integration_with_requirements(
                opp, integration.domain
            )

    processed.add(integration.domain)


@core.callback
def async_when_setup(
    opp: core.OpenPeerPower,
    component: str,
    when_setup_cb: Callable[[core.OpenPeerPower, str], Awaitable[None]],
) -> None:
    """Call a method when a component is setup."""

    async def when_setup() -> None:
        """Call the callback."""
        try:
            await when_setup_cb(opp, component)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error handling when_setup callback for %s", component)

    # Running it in a new task so that it always runs after
    if component in opp.config.components:
        opp.async_create_task(when_setup())
        return

    unsub = None

    async def loaded_event(event: core.Event) -> None:
        """Call the callback."""
        if event.data[ATTR_COMPONENT] != component:
            return

        unsub()  # type: ignore
        await when_setup()

    unsub = opp.bus.async_listen(EVENT_COMPONENT_LOADED, loaded_event)
