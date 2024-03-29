"""Support for interfacing with NAD receivers through RS-232."""
from nad_receiver import NADReceiver, NADReceiverTCP, NADReceiverTelnet
import voluptuous as vol

from openpeerpower.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from openpeerpower.components.media_player.const import (
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TYPE,
    STATE_OFF,
    STATE_ON,
)
import openpeerpower.helpers.config_validation as cv

DEFAULT_TYPE = "RS232"
DEFAULT_SERIAL_PORT = "/dev/ttyUSB0"
DEFAULT_PORT = 53
DEFAULT_NAME = "NAD Receiver"
DEFAULT_MIN_VOLUME = -92
DEFAULT_MAX_VOLUME = -20
DEFAULT_VOLUME_STEP = 4

SUPPORT_NAD = (
    SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_VOLUME_STEP
    | SUPPORT_SELECT_SOURCE
)

CONF_SERIAL_PORT = "serial_port"  # for NADReceiver
CONF_MIN_VOLUME = "min_volume"
CONF_MAX_VOLUME = "max_volume"
CONF_VOLUME_STEP = "volume_step"  # for NADReceiverTCP
CONF_SOURCE_DICT = "sources"  # for NADReceiver

SOURCE_DICT_SCHEMA = vol.Schema({vol.Range(min=1, max=10): cv.string})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_TYPE, default=DEFAULT_TYPE): vol.In(
            ["RS232", "Telnet", "TCP"]
        ),
        vol.Optional(CONF_SERIAL_PORT, default=DEFAULT_SERIAL_PORT): cv.string,
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MIN_VOLUME, default=DEFAULT_MIN_VOLUME): int,
        vol.Optional(CONF_MAX_VOLUME, default=DEFAULT_MAX_VOLUME): int,
        vol.Optional(CONF_SOURCE_DICT, default={}): SOURCE_DICT_SCHEMA,
        vol.Optional(CONF_VOLUME_STEP, default=DEFAULT_VOLUME_STEP): int,
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the NAD platform."""
    if config.get(CONF_TYPE) in ("RS232", "Telnet"):
        add_entities(
            [NAD(config)],
            True,
        )
    else:
        add_entities(
            [NADtcp(config)],
            True,
        )


class NAD(MediaPlayerEntity):
    """Representation of a NAD Receiver."""

    def __init__(self, config):
        """Initialize the NAD Receiver device."""
        self.config = config
        self._instantiate_nad_receiver()
        self._min_volume = config[CONF_MIN_VOLUME]
        self._max_volume = config[CONF_MAX_VOLUME]
        self._source_dict = config[CONF_SOURCE_DICT]
        self._reverse_mapping = {value: key for key, value in self._source_dict.items()}

        self._volume = self._state = self._mute = self._source = None

    def _instantiate_nad_receiver(self) -> NADReceiver:
        if self.config[CONF_TYPE] == "RS232":
            self._nad_receiver = NADReceiver(self.config[CONF_SERIAL_PORT])
        else:
            host = self.config.get(CONF_HOST)
            port = self.config[CONF_PORT]
            self._nad_receiver = NADReceiverTelnet(host, port)

    @property
    def name(self):
        """Return the name of the device."""
        return self.config[CONF_NAME]

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def icon(self):
        """Return the icon for the device."""
        return "mdi:speaker-multiple"

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._mute

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_NAD

    def turn_off(self):
        """Turn the media player off."""
        self._nad_receiver.main_power("=", "Off")

    def turn_on(self):
        """Turn the media player on."""
        self._nad_receiver.main_power("=", "On")

    def volume_up(self):
        """Volume up the media player."""
        self._nad_receiver.main_volume("+")

    def volume_down(self):
        """Volume down the media player."""
        self._nad_receiver.main_volume("-")

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._nad_receiver.main_volume("=", self.calc_db(volume))

    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        if mute:
            self._nad_receiver.main_mute("=", "On")
        else:
            self._nad_receiver.main_mute("=", "Off")

    def select_source(self, source):
        """Select input source."""
        self._nad_receiver.main_source("=", self._reverse_mapping.get(source))

    @property
    def source(self):
        """Name of the current input source."""
        return self._source

    @property
    def source_list(self):
        """List of available input sources."""
        return sorted(self._reverse_mapping)

    @property
    def available(self):
        """Return if device is available."""
        return self._state is not None

    def update(self) -> None:
        """Retrieve latest state."""
        power_state = self._nad_receiver.main_power("?")
        if not power_state:
            self._state = None
            return
        self._state = (
            STATE_ON if self._nad_receiver.main_power("?") == "On" else STATE_OFF
        )

        if self._state == STATE_ON:
            self._mute = self._nad_receiver.main_mute("?") == "On"
            volume = self._nad_receiver.main_volume("?")
            # Some receivers cannot report the volume, e.g. C 356BEE,
            # instead they only support stepping the volume up or down
            self._volume = self.calc_volume(volume) if volume is not None else None
            self._source = self._source_dict.get(self._nad_receiver.main_source("?"))

    def calc_volume(self, decibel):
        """
        Calculate the volume given the decibel.

        Return the volume (0..1).
        """
        return abs(self._min_volume - decibel) / abs(
            self._min_volume - self._max_volume
        )

    def calc_db(self, volume):
        """
        Calculate the decibel given the volume.

        Return the dB.
        """
        return self._min_volume + round(
            abs(self._min_volume - self._max_volume) * volume
        )


class NADtcp(MediaPlayerEntity):
    """Representation of a NAD Digital amplifier."""

    def __init__(self, config):
        """Initialize the amplifier."""
        self._name = config[CONF_NAME]
        self._nad_receiver = NADReceiverTCP(config.get(CONF_HOST))
        self._min_vol = (config[CONF_MIN_VOLUME] + 90) * 2  # from dB to nad vol (0-200)
        self._max_vol = (config[CONF_MAX_VOLUME] + 90) * 2  # from dB to nad vol (0-200)
        self._volume_step = config[CONF_VOLUME_STEP]
        self._state = None
        self._mute = None
        self._nad_volume = None
        self._volume = None
        self._source = None
        self._source_list = self._nad_receiver.available_sources()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._mute

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_NAD

    def turn_off(self):
        """Turn the media player off."""
        self._nad_receiver.power_off()

    def turn_on(self):
        """Turn the media player on."""
        self._nad_receiver.power_on()

    def volume_up(self):
        """Step volume up in the configured increments."""
        self._nad_receiver.set_volume(self._nad_volume + 2 * self._volume_step)

    def volume_down(self):
        """Step volume down in the configured increments."""
        self._nad_receiver.set_volume(self._nad_volume - 2 * self._volume_step)

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        nad_volume_to_set = int(
            round(volume * (self._max_vol - self._min_vol) + self._min_vol)
        )
        self._nad_receiver.set_volume(nad_volume_to_set)

    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        if mute:
            self._nad_receiver.mute()
        else:
            self._nad_receiver.unmute()

    def select_source(self, source):
        """Select input source."""
        self._nad_receiver.select_source(source)

    @property
    def source(self):
        """Name of the current input source."""
        return self._source

    @property
    def source_list(self):
        """List of available input sources."""
        return self._nad_receiver.available_sources()

    def update(self):
        """Get the latest details from the device."""
        try:
            nad_status = self._nad_receiver.status()
        except OSError:
            return
        if nad_status is None:
            return

        # Update on/off state
        if nad_status["power"]:
            self._state = STATE_ON
        else:
            self._state = STATE_OFF

        # Update current volume
        self._volume = self.nad_vol_to_internal_vol(nad_status["volume"])
        self._nad_volume = nad_status["volume"]

        # Update muted state
        self._mute = nad_status["muted"]

        # Update current source
        self._source = nad_status["source"]

    def nad_vol_to_internal_vol(self, nad_volume):
        """Convert nad volume range (0-200) to internal volume range.

        Takes into account configured min and max volume.
        """
        if nad_volume < self._min_vol:
            volume_internal = 0.0
        elif nad_volume > self._max_vol:
            volume_internal = 1.0
        else:
            volume_internal = (nad_volume - self._min_vol) / (
                self._max_vol - self._min_vol
            )
        return volume_internal
