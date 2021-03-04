"""StarLine Account."""
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

from starline import StarlineApi, StarlineDevice

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.event import async_track_time_interval

from .const import (
    _LOGGER,
    DATA_EXPIRES,
    DATA_SLID_TOKEN,
    DATA_SLNET_TOKEN,
    DATA_USER_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_OBD_INTERVAL,
    DOMAIN,
)


class StarlineAccount:
    """StarLine Account class."""

    def __init__(self, opp: OpenPeerPower, config_entry: ConfigEntry):
        """Initialize StarLine account."""
        self._opp: OpenPeerPower = opp
        self._config_entry: ConfigEntry = config_entry
        self._update_interval: int = DEFAULT_SCAN_INTERVAL
        self._update_obd_interval: int = DEFAULT_SCAN_OBD_INTERVAL
        self._unsubscribe_auto_updater: Optional[Callable] = None
        self._unsubscribe_auto_obd_updater: Optional[Callable] = None
        self._api: StarlineApi = StarlineApi(
            config_entry.data[DATA_USER_ID], config_entry.data[DATA_SLNET_TOKEN]
        )

    def _check_slnet_token(self, interval: int) -> None:
        """Check SLNet token expiration and update if needed."""
        now = datetime.now().timestamp()
        slnet_token_expires = self._config_entry.data[DATA_EXPIRES]

        if now + interval > slnet_token_expires:
            self._update_slnet_token()

    def _update_slnet_token(self) -> None:
        """Update SLNet token."""
        slid_token = self._config_entry.data[DATA_SLID_TOKEN]

        try:
            slnet_token, slnet_token_expires, user_id = self._api.get_user_id(
                slid_token
            )
            self._api.set_slnet_token(slnet_token)
            self._api.set_user_id(user_id)
            self._opp.config_entries.async_update_entry(
                self._config_entry,
                data={
                    **self._config_entry.data,
                    DATA_SLNET_TOKEN: slnet_token,
                    DATA_EXPIRES: slnet_token_expires,
                    DATA_USER_ID: user_id,
                },
            )
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error updating SLNet token: %s", err)

    def _update_data(self):
        """Update StarLine data."""
        self._check_slnet_token(self._update_interval)
        self._api.update()

    def _update_obd_data(self):
        """Update StarLine OBD data."""
        self._check_slnet_token(self._update_obd_interval)
        self._api.update_obd()

    @property
    def api(self) -> StarlineApi:
        """Return the instance of the API."""
        return self._api

    async def update(self, unused=None):
        """Update StarLine data."""
        await self._opp.async_add_executor_job(self._update_data)

    async def update_obd(self, unused=None):
        """Update StarLine OBD data."""
        await self._opp.async_add_executor_job(self._update_obd_data)

    def set_update_interval(self, interval: int) -> None:
        """Set StarLine API update interval."""
        _LOGGER.debug("Setting update interval: %ds", interval)
        self._update_interval = interval
        if self._unsubscribe_auto_updater is not None:
            self._unsubscribe_auto_updater()

        delta = timedelta(seconds=interval)
        self._unsubscribe_auto_updater = async_track_time_interval(
            self._opp, self.update, delta
        )

    def set_update_obd_interval(self, interval: int) -> None:
        """Set StarLine API OBD update interval."""
        _LOGGER.debug("Setting OBD update interval: %ds", interval)
        self._update_obd_interval = interval
        if self._unsubscribe_auto_obd_updater is not None:
            self._unsubscribe_auto_obd_updater()

        delta = timedelta(seconds=interval)
        self._unsubscribe_auto_obd_updater = async_track_time_interval(
            self._opp, self.update_obd, delta
        )

    def unload(self):
        """Unload StarLine API."""
        _LOGGER.debug("Unloading StarLine API.")
        if self._unsubscribe_auto_updater is not None:
            self._unsubscribe_auto_updater()
            self._unsubscribe_auto_updater = None
        if self._unsubscribe_auto_obd_updater is not None:
            self._unsubscribe_auto_obd_updater()
            self._unsubscribe_auto_obd_updater = None

    @staticmethod
    def device_info(device: StarlineDevice) -> Dict[str, Any]:
        """Device information for entities."""
        return {
            "identifiers": {(DOMAIN, device.device_id)},
            "manufacturer": "StarLine",
            "name": device.name,
            "sw_version": device.fw_version,
            "model": device.typename,
        }

    @staticmethod
    def gps_attrs(device: StarlineDevice) -> Dict[str, Any]:
        """Attributes for device tracker."""
        return {
            "updated": datetime.utcfromtimestamp(device.position["ts"]).isoformat(),
            "online": device.online,
        }

    @staticmethod
    def balance_attrs(device: StarlineDevice) -> Dict[str, Any]:
        """Attributes for balance sensor."""
        return {
            "operator": device.balance.get("operator"),
            "state": device.balance.get("state"),
            "updated": device.balance.get("ts"),
        }

    @staticmethod
    def gsm_attrs(device: StarlineDevice) -> Dict[str, Any]:
        """Attributes for GSM sensor."""
        return {
            "raw": device.gsm_level,
            "imei": device.imei,
            "phone": device.phone,
            "online": device.online,
        }

    @staticmethod
    def engine_attrs(device: StarlineDevice) -> Dict[str, Any]:
        """Attributes for engine switch."""
        return {
            "autostart": device.car_state.get("r_start"),
            "ignition": device.car_state.get("run"),
        }

    @staticmethod
    def errors_attrs(device: StarlineDevice) -> Dict[str, Any]:
        """Attributes for errors sensor."""
        return {"errors": device.errors.get("errors")}
