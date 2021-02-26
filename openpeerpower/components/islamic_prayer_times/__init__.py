"""The islamic_prayer_times component."""
from datetime import timedelta
import logging

from prayer_times_calculator import PrayerTimesCalculator, exceptions
from requests.exceptions import ConnectionError as ConnError
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.event import async_call_later, async_track_point_in_time
import openpeerpower.util.dt as dt_util

from .const import (
    CALC_METHODS,
    CONF_CALC_METHOD,
    DATA_UPDATED,
    DEFAULT_CALC_METHOD,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            vol.Optional(CONF_CALC_METHOD, default=DEFAULT_CALC_METHOD): vol.In(
                CALC_METHODS
            ),
        }
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Import the Islamic Prayer component from config."""
    if DOMAIN in config:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )

    return True


async def async_setup_entry(opp, config_entry):
    """Set up the Islamic Prayer Component."""
    client = IslamicPrayerClient(opp, config_entry)

    if not await client.async_setup():
        return False

    opp.data.setdefault(DOMAIN, client)
    return True


async def async_unload_entry(opp, config_entry):
    """Unload Islamic Prayer entry from config_entry."""
    if opp.data[DOMAIN].event_unsub:
        opp.data[DOMAIN].event_unsub()
    opp.data.pop(DOMAIN)
    await opp.config_entries.async_forward_entry_unload(config_entry, "sensor")

    return True


class IslamicPrayerClient:
    """Islamic Prayer Client Object."""

    def __init__(self, opp, config_entry):
        """Initialize the Islamic Prayer client."""
        self.opp = opp
        self.config_entry = config_entry
        self.prayer_times_info = {}
        self.available = True
        self.event_unsub = None

    @property
    def calc_method(self):
        """Return the calculation method."""
        return self.config_entry.options[CONF_CALC_METHOD]

    def get_new_prayer_times(self):
        """Fetch prayer times for today."""
        calc = PrayerTimesCalculator(
            latitude=self.opp.config.latitude,
            longitude=self.opp.config.longitude,
            calculation_method=self.calc_method,
            date=str(dt_util.now().date()),
        )
        return calc.fetch_prayer_times()

    async def async_schedule_future_update(self):
        """Schedule future update for sensors.

        Midnight is a calculated time.  The specifics of the calculation
        depends on the method of the prayer time calculation.  This calculated
        midnight is the time at which the time to pray the Isha prayers have
        expired.

        Calculated Midnight: The Islamic midnight.
        Traditional Midnight: 12:00AM

        Update logic for prayer times:

        If the Calculated Midnight is before the traditional midnight then wait
        until the traditional midnight to run the update.  This way the day
        will have changed over and we don't need to do any fancy calculations.

        If the Calculated Midnight is after the traditional midnight, then wait
        until after the calculated Midnight.  We don't want to update the prayer
        times too early or else the timings might be incorrect.

        Example:
        calculated midnight = 11:23PM (before traditional midnight)
        Update time: 12:00AM

        calculated midnight = 1:35AM (after traditional midnight)
        update time: 1:36AM.

        """
        _LOGGER.debug("Scheduling next update for Islamic prayer times")

        now = dt_util.utcnow()

        midnight_dt = self.prayer_times_info["Midnight"]

        if now > dt_util.as_utc(midnight_dt):
            next_update_at = midnight_dt + timedelta(days=1, minutes=1)
            _LOGGER.debug(
                "Midnight is after day the changes so schedule update for after Midnight the next day"
            )
        else:
            _LOGGER.debug(
                "Midnight is before the day changes so schedule update for the next start of day"
            )
            next_update_at = dt_util.start_of_local_day(now + timedelta(days=1))

        _LOGGER.info("Next update scheduled for: %s", next_update_at)

        self.event_unsub = async_track_point_in_time(
            self.opp, self.async_update, next_update_at
        )

    async def async_update(self, *_):
        """Update sensors with new prayer times."""
        try:
            prayer_times = await self.opp.async_add_executor_job(
                self.get_new_prayer_times
            )
            self.available = True
        except (exceptions.InvalidResponseError, ConnError):
            self.available = False
            _LOGGER.debug("Error retrieving prayer times")
            async_call_later(self.opp, 60, self.async_update)
            return

        for prayer, time in prayer_times.items():
            self.prayer_times_info[prayer] = dt_util.parse_datetime(
                f"{dt_util.now().date()} {time}"
            )
        await self.async_schedule_future_update()

        _LOGGER.debug("New prayer times retrieved. Updating sensors")
        async_dispatcher_send(self.opp, DATA_UPDATED)

    async def async_setup(self):
        """Set up the Islamic prayer client."""
        await self.async_add_options()

        try:
            await self.opp.async_add_executor_job(self.get_new_prayer_times)
        except (exceptions.InvalidResponseError, ConnError) as err:
            raise ConfigEntryNotReady from err

        await self.async_update()
        self.config_entry.add_update_listener(self.async_options_updated)

        self.opp.async_create_task(
            self.opp.config_entries.async_forward_entry_setup(
                self.config_entry, "sensor"
            )
        )

        return True

    async def async_add_options(self):
        """Add options for entry."""
        if not self.config_entry.options:
            data = dict(self.config_entry.data)
            calc_method = data.pop(CONF_CALC_METHOD, DEFAULT_CALC_METHOD)

            self.opp.config_entries.async_update_entry(
                self.config_entry, data=data, options={CONF_CALC_METHOD: calc_method}
            )

    @staticmethod
    async def async_options_updated(opp, entry):
        """Triggered by config entry options updates."""
        if opp.data[DOMAIN].event_unsub:
            opp.data[DOMAIN].event_unsub()
        await opp.data[DOMAIN].async_update()
