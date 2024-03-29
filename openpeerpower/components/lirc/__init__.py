"""Support for LIRC devices."""
# pylint: disable=import-error
import logging
import threading
import time

import lirc

from openpeerpower.const import EVENT_OPENPEERPOWER_START, EVENT_OPENPEERPOWER_STOP

_LOGGER = logging.getLogger(__name__)

BUTTON_NAME = "button_name"

DOMAIN = "lirc"

EVENT_IR_COMMAND_RECEIVED = "ir_command_received"

ICON = "mdi:remote"


def setup(opp, config):
    """Set up the LIRC capability."""
    # blocking=True gives unexpected behavior (multiple responses for 1 press)
    # also by not blocking, we allow opp to shut down the thread gracefully
    # on exit.
    lirc.init("openpeerpower", blocking=False)
    lirc_interface = LircInterface(opp)

    def _start_lirc(_event):
        lirc_interface.start()

    def _stop_lirc(_event):
        lirc_interface.stopped.set()

    opp.bus.listen_once(EVENT_OPENPEERPOWER_START, _start_lirc)
    opp.bus.listen_once(EVENT_OPENPEERPOWER_STOP, _stop_lirc)

    return True


class LircInterface(threading.Thread):
    """
    This interfaces with the lirc daemon to read IR commands.

    When using lirc in blocking mode, sometimes repeated commands get produced
    in the next read of a command so we use a thread here to just wait
    around until a non-empty response is obtained from lirc.
    """

    def __init__(self, opp):
        """Construct a LIRC interface object."""
        threading.Thread.__init__(self)
        self.daemon = True
        self.stopped = threading.Event()
        self.opp = opp

    def run(self):
        """Run the loop of the LIRC interface thread."""
        _LOGGER.debug("LIRC interface thread started")
        while not self.stopped.isSet():
            try:
                code = lirc.nextcode()  # list; empty if no buttons pressed
            except lirc.NextCodeError:
                _LOGGER.warning("Error reading next code from LIRC")
                code = None
            # interpret result from python-lirc
            if code:
                code = code[0]
                _LOGGER.info("Got new LIRC code %s", code)
                self.opp.bus.fire(EVENT_IR_COMMAND_RECEIVED, {BUTTON_NAME: code})
            else:
                time.sleep(0.2)
        lirc.deinit()
        _LOGGER.debug("LIRC interface thread stopped")
