"""Component for monitoring activity on a folder."""
import logging
import os

import voluptuous as vol
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from openpeerpower.const import EVENT_OPENPEERPOWER_START, EVENT_OPENPEERPOWER_STOP
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_FOLDER = "folder"
CONF_PATTERNS = "patterns"
DEFAULT_PATTERN = "*"
DOMAIN = "folder_watcher"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_FOLDER): cv.isdir,
                        vol.Optional(CONF_PATTERNS, default=[DEFAULT_PATTERN]): vol.All(
                            cv.ensure_list, [cv.string]
                        ),
                    }
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(opp, config):
    """Set up the folder watcher."""
    conf = config[DOMAIN]
    for watcher in conf:
        path = watcher[CONF_FOLDER]
        patterns = watcher[CONF_PATTERNS]
        if not opp.config.is_allowed_path(path):
            _LOGGER.error("folder %s is not valid or allowed", path)
            return False
        Watcher(path, patterns, opp)

    return True


def create_event_handler(patterns, opp):
    """Return the Watchdog EventHandler object."""

    class EventHandler(PatternMatchingEventHandler):
        """Class for handling Watcher events."""

        def __init__(self, patterns, opp):
            """Initialise the EventHandler."""
            super().__init__(patterns)
            self.opp = opp

        def process(self, event):
            """On Watcher event, fire OP event."""
            _LOGGER.debug("process(%s)", event)
            if not event.is_directory:
                folder, file_name = os.path.split(event.src_path)
                self.opp.bus.fire(
                    DOMAIN,
                    {
                        "event_type": event.event_type,
                        "path": event.src_path,
                        "file": file_name,
                        "folder": folder,
                    },
                )

        def on_modified(self, event):
            """File modified."""
            self.process(event)

        def on_moved(self, event):
            """File moved."""
            self.process(event)

        def on_created(self, event):
            """File created."""
            self.process(event)

        def on_deleted(self, event):
            """File deleted."""
            self.process(event)

    return EventHandler(patterns, opp)


class Watcher:
    """Class for starting Watchdog."""

    def __init__(self, path, patterns, opp):
        """Initialise the watchdog observer."""
        self._observer = Observer()
        self._observer.schedule(
            create_event_handler(patterns, opp), path, recursive=True
        )
        opp.bus.listen_once(EVENT_OPENPEERPOWER_START, self.startup)
        opp.bus.listen_once(EVENT_OPENPEERPOWER_STOP, self.shutdown)

    def startup(self, event):
        """Start the watcher."""
        self._observer.start()

    def shutdown(self, event):
        """Shutdown the watcher."""
        self._observer.stop()
        self._observer.join()
