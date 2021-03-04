"""Run Open Peer Power."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import dataclasses
import logging
from typing import Any, Dict, Optional

from openpeerpower import bootstrap
from openpeerpower.core import callback
from openpeerpower.helpers.frame import warn_use

# mypy: disallow-any-generics

#
# Python 3.8 has significantly less workers by default
# than Python 3.7.  In order to be consistent between
# supported versions, we need to set max_workers.
#
# In most cases the workers are not I/O bound, as they
# are sleeping/blocking waiting for data from integrations
# updating so this number should be higher than the default
# use case.
#
MAX_EXECUTOR_WORKERS = 64


@dataclasses.dataclass
class RuntimeConfig:
    """Class to hold the information for running Open Peer Power."""

    config_dir: str
    skip_pip: bool = False
    safe_mode: bool = False

    verbose: bool = False

    log_rotate_days: Optional[int] = None
    log_file: Optional[str] = None
    log_no_color: bool = False

    debug: bool = False
    open_ui: bool = False


class OppEventLoopPolicy(asyncio.DefaultEventLoopPolicy):  # type: ignore[valid-type,misc]
    """Event loop policy for Open Peer Power."""

    def __init__(self, debug: bool) -> None:
        """Init the event loop policy."""
        super().__init__()
        self.debug = debug

    @property
    def loop_name(self) -> str:
        """Return name of the loop."""
        return self._loop_factory.__name__  # type: ignore

    def new_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get the event loop."""
        loop: asyncio.AbstractEventLoop = super().new_event_loop()
        loop.set_exception_handler(_async_loop_exception_handler)
        if self.debug:
            loop.set_debug(True)

        executor = ThreadPoolExecutor(
            thread_name_prefix="SyncWorker", max_workers=MAX_EXECUTOR_WORKERS
        )
        loop.set_default_executor(executor)
        loop.set_default_executor = warn_use(  # type: ignore
            loop.set_default_executor, "sets default executor on the event loop"
        )

        # Shut down executor when we shut down loop
        orig_close = loop.close

        def close() -> None:
            executor.shutdown(wait=True)
            orig_close()

        loop.close = close  # type: ignore

        return loop


@callback
def _async_loop_exception_handler(_: Any, context: Dict[str, Any]) -> None:
    """Handle all exception inside the core loop."""
    kwargs = {}
    exception = context.get("exception")
    if exception:
        kwargs["exc_info"] = (type(exception), exception, exception.__traceback__)

    logging.getLogger(__package__).error(
        "Error doing job: %s", context["message"], **kwargs  # type: ignore
    )


async def setup_and_run_opp(runtime_config: RuntimeConfig) -> int:
    """Set up Open Peer Power and run."""
    opp = await bootstrap.async_setup_opp(runtime_config)

    if opp is None:
        return 1

    return await opp.async_run()


def run(runtime_config: RuntimeConfig) -> int:
    """Run Open Peer Power."""
    asyncio.set_event_loop_policy(OppEventLoopPolicy(runtime_config.debug))
    return asyncio.run(setup_and_run_opp(runtime_config))
