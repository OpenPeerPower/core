"""Support for Huawei LTE sensors."""

from bisect import bisect
import logging
import re
from typing import Callable, Dict, List, NamedTuple, Optional, Pattern, Tuple, Union

import attr

from openpeerpower.components.sensor import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    DOMAIN as SENSOR_DOMAIN,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_URL,
    DATA_BYTES,
    DATA_RATE_BYTES_PER_SECOND,
    PERCENTAGE,
    STATE_UNKNOWN,
    TIME_SECONDS,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.typing import OpenPeerPowerType, StateType

from . import HuaweiLteBaseEntity
from .const import (
    DOMAIN,
    KEY_DEVICE_INFORMATION,
    KEY_DEVICE_SIGNAL,
    KEY_MONITORING_CHECK_NOTIFICATIONS,
    KEY_MONITORING_MONTH_STATISTICS,
    KEY_MONITORING_STATUS,
    KEY_MONITORING_TRAFFIC_STATISTICS,
    KEY_NET_CURRENT_PLMN,
    KEY_NET_NET_MODE,
    KEY_SMS_SMS_COUNT,
    SENSOR_KEYS,
)

_LOGGER = logging.getLogger(__name__)


class SensorMeta(NamedTuple):
    """Metadata for defining sensors."""

    name: Optional[str] = None
    device_class: Optional[str] = None
    icon: Union[str, Callable[[StateType], str], None] = None
    unit: Optional[str] = None
    enabled_default: bool = False
    include: Optional[Pattern[str]] = None
    exclude: Optional[Pattern[str]] = None
    formatter: Optional[Callable[[str], Tuple[StateType, Optional[str]]]] = None


SENSOR_META: Dict[Union[str, Tuple[str, str]], SensorMeta] = {
    KEY_DEVICE_INFORMATION: SensorMeta(
        include=re.compile(r"^WanIP.*Address$", re.IGNORECASE)
    ),
    (KEY_DEVICE_INFORMATION, "WanIPAddress"): SensorMeta(
        name="WAN IP address", icon="mdi:ip", enabled_default=True
    ),
    (KEY_DEVICE_INFORMATION, "WanIPv6Address"): SensorMeta(
        name="WAN IPv6 address", icon="mdi:ip"
    ),
    (KEY_DEVICE_SIGNAL, "band"): SensorMeta(name="Band"),
    (KEY_DEVICE_SIGNAL, "cell_id"): SensorMeta(name="Cell ID"),
    (KEY_DEVICE_SIGNAL, "dl_mcs"): SensorMeta(name="Downlink MCS"),
    (KEY_DEVICE_SIGNAL, "dlbandwidth"): SensorMeta(
        name="Downlink bandwidth",
        icon=lambda x: (
            "mdi:speedometer-slow",
            "mdi:speedometer-medium",
            "mdi:speedometer",
        )[bisect((8, 15), x if x is not None else -1000)],
    ),
    (KEY_DEVICE_SIGNAL, "earfcn"): SensorMeta(name="EARFCN"),
    (KEY_DEVICE_SIGNAL, "lac"): SensorMeta(name="LAC", icon="mdi:map-marker"),
    (KEY_DEVICE_SIGNAL, "plmn"): SensorMeta(name="PLMN"),
    (KEY_DEVICE_SIGNAL, "rac"): SensorMeta(name="RAC", icon="mdi:map-marker"),
    (KEY_DEVICE_SIGNAL, "rrc_status"): SensorMeta(name="RRC status"),
    (KEY_DEVICE_SIGNAL, "tac"): SensorMeta(name="TAC", icon="mdi:map-marker"),
    (KEY_DEVICE_SIGNAL, "tdd"): SensorMeta(name="TDD"),
    (KEY_DEVICE_SIGNAL, "txpower"): SensorMeta(
        name="Transmit power",
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
    ),
    (KEY_DEVICE_SIGNAL, "ul_mcs"): SensorMeta(name="Uplink MCS"),
    (KEY_DEVICE_SIGNAL, "ulbandwidth"): SensorMeta(
        name="Uplink bandwidth",
        icon=lambda x: (
            "mdi:speedometer-slow",
            "mdi:speedometer-medium",
            "mdi:speedometer",
        )[bisect((8, 15), x if x is not None else -1000)],
    ),
    (KEY_DEVICE_SIGNAL, "mode"): SensorMeta(
        name="Mode",
        formatter=lambda x: ({"0": "2G", "2": "3G", "7": "4G"}.get(x, "Unknown"), None),
    ),
    (KEY_DEVICE_SIGNAL, "pci"): SensorMeta(name="PCI"),
    (KEY_DEVICE_SIGNAL, "rsrq"): SensorMeta(
        name="RSRQ",
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        # http://www.lte-anbieter.info/technik/rsrq.php
        icon=lambda x: (
            "mdi:signal-cellular-outline",
            "mdi:signal-cellular-1",
            "mdi:signal-cellular-2",
            "mdi:signal-cellular-3",
        )[bisect((-11, -8, -5), x if x is not None else -1000)],
        enabled_default=True,
    ),
    (KEY_DEVICE_SIGNAL, "rsrp"): SensorMeta(
        name="RSRP",
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        # http://www.lte-anbieter.info/technik/rsrp.php
        icon=lambda x: (
            "mdi:signal-cellular-outline",
            "mdi:signal-cellular-1",
            "mdi:signal-cellular-2",
            "mdi:signal-cellular-3",
        )[bisect((-110, -95, -80), x if x is not None else -1000)],
        enabled_default=True,
    ),
    (KEY_DEVICE_SIGNAL, "rssi"): SensorMeta(
        name="RSSI",
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        # https://eyesaas.com/wi-fi-signal-strength/
        icon=lambda x: (
            "mdi:signal-cellular-outline",
            "mdi:signal-cellular-1",
            "mdi:signal-cellular-2",
            "mdi:signal-cellular-3",
        )[bisect((-80, -70, -60), x if x is not None else -1000)],
        enabled_default=True,
    ),
    (KEY_DEVICE_SIGNAL, "sinr"): SensorMeta(
        name="SINR",
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        # http://www.lte-anbieter.info/technik/sinr.php
        icon=lambda x: (
            "mdi:signal-cellular-outline",
            "mdi:signal-cellular-1",
            "mdi:signal-cellular-2",
            "mdi:signal-cellular-3",
        )[bisect((0, 5, 10), x if x is not None else -1000)],
        enabled_default=True,
    ),
    (KEY_DEVICE_SIGNAL, "rscp"): SensorMeta(
        name="RSCP",
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        # https://wiki.teltonika.lt/view/RSCP
        icon=lambda x: (
            "mdi:signal-cellular-outline",
            "mdi:signal-cellular-1",
            "mdi:signal-cellular-2",
            "mdi:signal-cellular-3",
        )[bisect((-95, -85, -75), x if x is not None else -1000)],
    ),
    (KEY_DEVICE_SIGNAL, "ecio"): SensorMeta(
        name="EC/IO",
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        # https://wiki.teltonika.lt/view/EC/IO
        icon=lambda x: (
            "mdi:signal-cellular-outline",
            "mdi:signal-cellular-1",
            "mdi:signal-cellular-2",
            "mdi:signal-cellular-3",
        )[bisect((-20, -10, -6), x if x is not None else -1000)],
    ),
    KEY_MONITORING_CHECK_NOTIFICATIONS: SensorMeta(
        exclude=re.compile(
            r"^(onlineupdatestatus|smsstoragefull)$",
            re.IGNORECASE,
        )
    ),
    (KEY_MONITORING_CHECK_NOTIFICATIONS, "UnreadMessage"): SensorMeta(
        name="SMS unread", icon="mdi:email-receive"
    ),
    KEY_MONITORING_MONTH_STATISTICS: SensorMeta(
        exclude=re.compile(r"^month(duration|lastcleartime)$", re.IGNORECASE)
    ),
    (KEY_MONITORING_MONTH_STATISTICS, "CurrentMonthDownload"): SensorMeta(
        name="Current month download", unit=DATA_BYTES, icon="mdi:download"
    ),
    (KEY_MONITORING_MONTH_STATISTICS, "CurrentMonthUpload"): SensorMeta(
        name="Current month upload", unit=DATA_BYTES, icon="mdi:upload"
    ),
    KEY_MONITORING_STATUS: SensorMeta(
        include=re.compile(
            r"^(batterypercent|currentwifiuser|(primary|secondary).*dns)$",
            re.IGNORECASE,
        )
    ),
    (KEY_MONITORING_STATUS, "BatteryPercent"): SensorMeta(
        name="Battery",
        device_class=DEVICE_CLASS_BATTERY,
        unit=PERCENTAGE,
    ),
    (KEY_MONITORING_STATUS, "CurrentWifiUser"): SensorMeta(
        name="WiFi clients connected", icon="mdi:wifi"
    ),
    (KEY_MONITORING_STATUS, "PrimaryDns"): SensorMeta(
        name="Primary DNS server", icon="mdi:ip"
    ),
    (KEY_MONITORING_STATUS, "SecondaryDns"): SensorMeta(
        name="Secondary DNS server", icon="mdi:ip"
    ),
    (KEY_MONITORING_STATUS, "PrimaryIPv6Dns"): SensorMeta(
        name="Primary IPv6 DNS server", icon="mdi:ip"
    ),
    (KEY_MONITORING_STATUS, "SecondaryIPv6Dns"): SensorMeta(
        name="Secondary IPv6 DNS server", icon="mdi:ip"
    ),
    KEY_MONITORING_TRAFFIC_STATISTICS: SensorMeta(
        exclude=re.compile(r"^showtraffic$", re.IGNORECASE)
    ),
    (KEY_MONITORING_TRAFFIC_STATISTICS, "CurrentConnectTime"): SensorMeta(
        name="Current connection duration", unit=TIME_SECONDS, icon="mdi:timer-outline"
    ),
    (KEY_MONITORING_TRAFFIC_STATISTICS, "CurrentDownload"): SensorMeta(
        name="Current connection download", unit=DATA_BYTES, icon="mdi:download"
    ),
    (KEY_MONITORING_TRAFFIC_STATISTICS, "CurrentDownloadRate"): SensorMeta(
        name="Current download rate",
        unit=DATA_RATE_BYTES_PER_SECOND,
        icon="mdi:download",
    ),
    (KEY_MONITORING_TRAFFIC_STATISTICS, "CurrentUpload"): SensorMeta(
        name="Current connection upload", unit=DATA_BYTES, icon="mdi:upload"
    ),
    (KEY_MONITORING_TRAFFIC_STATISTICS, "CurrentUploadRate"): SensorMeta(
        name="Current upload rate",
        unit=DATA_RATE_BYTES_PER_SECOND,
        icon="mdi:upload",
    ),
    (KEY_MONITORING_TRAFFIC_STATISTICS, "TotalConnectTime"): SensorMeta(
        name="Total connected duration", unit=TIME_SECONDS, icon="mdi:timer-outline"
    ),
    (KEY_MONITORING_TRAFFIC_STATISTICS, "TotalDownload"): SensorMeta(
        name="Total download", unit=DATA_BYTES, icon="mdi:download"
    ),
    (KEY_MONITORING_TRAFFIC_STATISTICS, "TotalUpload"): SensorMeta(
        name="Total upload", unit=DATA_BYTES, icon="mdi:upload"
    ),
    KEY_NET_CURRENT_PLMN: SensorMeta(
        exclude=re.compile(r"^(Rat|ShortName|Spn)$", re.IGNORECASE)
    ),
    (KEY_NET_CURRENT_PLMN, "State"): SensorMeta(
        name="Operator search mode",
        formatter=lambda x: ({"0": "Auto", "1": "Manual"}.get(x, "Unknown"), None),
    ),
    (KEY_NET_CURRENT_PLMN, "FullName"): SensorMeta(
        name="Operator name",
    ),
    (KEY_NET_CURRENT_PLMN, "Numeric"): SensorMeta(
        name="Operator code",
    ),
    KEY_NET_NET_MODE: SensorMeta(include=re.compile(r"^NetworkMode$", re.IGNORECASE)),
    (KEY_NET_NET_MODE, "NetworkMode"): SensorMeta(
        name="Preferred mode",
        formatter=lambda x: (
            {
                "00": "4G/3G/2G",
                "01": "2G",
                "02": "3G",
                "03": "4G",
                "0301": "4G/2G",
                "0302": "4G/3G",
                "0201": "3G/2G",
            }.get(x, "Unknown"),
            None,
        ),
    ),
    (KEY_SMS_SMS_COUNT, "LocalDeleted"): SensorMeta(
        name="SMS deleted (device)",
        icon="mdi:email-minus",
    ),
    (KEY_SMS_SMS_COUNT, "LocalDraft"): SensorMeta(
        name="SMS drafts (device)",
        icon="mdi:email-send-outline",
    ),
    (KEY_SMS_SMS_COUNT, "LocalInbox"): SensorMeta(
        name="SMS inbox (device)",
        icon="mdi:email",
    ),
    (KEY_SMS_SMS_COUNT, "LocalMax"): SensorMeta(
        name="SMS capacity (device)",
        icon="mdi:email",
    ),
    (KEY_SMS_SMS_COUNT, "LocalOutbox"): SensorMeta(
        name="SMS outbox (device)",
        icon="mdi:email-send",
    ),
    (KEY_SMS_SMS_COUNT, "LocalUnread"): SensorMeta(
        name="SMS unread (device)",
        icon="mdi:email-receive",
    ),
    (KEY_SMS_SMS_COUNT, "SimDraft"): SensorMeta(
        name="SMS drafts (SIM)",
        icon="mdi:email-send-outline",
    ),
    (KEY_SMS_SMS_COUNT, "SimInbox"): SensorMeta(
        name="SMS inbox (SIM)",
        icon="mdi:email",
    ),
    (KEY_SMS_SMS_COUNT, "SimMax"): SensorMeta(
        name="SMS capacity (SIM)",
        icon="mdi:email",
    ),
    (KEY_SMS_SMS_COUNT, "SimOutbox"): SensorMeta(
        name="SMS outbox (SIM)",
        icon="mdi:email-send",
    ),
    (KEY_SMS_SMS_COUNT, "SimUnread"): SensorMeta(
        name="SMS unread (SIM)",
        icon="mdi:email-receive",
    ),
    (KEY_SMS_SMS_COUNT, "SimUsed"): SensorMeta(
        name="SMS messages (SIM)",
        icon="mdi:email-receive",
    ),
}


async def async_setup_entry(
    opp: OpenPeerPowerType,
    config_entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up from config entry."""
    router = opp.data[DOMAIN].routers[config_entry.data[CONF_URL]]
    sensors: List[Entity] = []
    for key in SENSOR_KEYS:
        items = router.data.get(key)
        if not items:
            continue
        key_meta = SENSOR_META.get(key)
        if key_meta:
            if key_meta.include:
                items = filter(key_meta.include.search, items)
            if key_meta.exclude:
                items = [x for x in items if not key_meta.exclude.search(x)]
        for item in items:
            sensors.append(
                HuaweiLteSensor(
                    router, key, item, SENSOR_META.get((key, item), SensorMeta())
                )
            )

    async_add_entities(sensors, True)


def format_default(value: StateType) -> Tuple[StateType, Optional[str]]:
    """Format value."""
    unit = None
    if value is not None:
        # Clean up value and infer unit, e.g. -71dBm, 15 dB
        match = re.match(
            r"([>=<]*)(?P<value>.+?)\s*(?P<unit>[a-zA-Z]+)\s*$", str(value)
        )
        if match:
            try:
                value = float(match.group("value"))
                unit = match.group("unit")
            except ValueError:
                pass
    return value, unit


@attr.s
class HuaweiLteSensor(HuaweiLteBaseEntity):
    """Huawei LTE sensor entity."""

    key: str = attr.ib()
    item: str = attr.ib()
    meta: SensorMeta = attr.ib()

    _state: StateType = attr.ib(init=False, default=STATE_UNKNOWN)
    _unit: Optional[str] = attr.ib(init=False)

    async def async_added_to_opp(self) -> None:
        """Subscribe to needed data on add."""
        await super().async_added_to_opp()
        self.router.subscriptions[self.key].add(f"{SENSOR_DOMAIN}/{self.item}")

    async def async_will_remove_from_opp(self) -> None:
        """Unsubscribe from needed data on remove."""
        await super().async_will_remove_from_opp()
        self.router.subscriptions[self.key].remove(f"{SENSOR_DOMAIN}/{self.item}")

    @property
    def _entity_name(self) -> str:
        return self.meta.name or self.item

    @property
    def _device_unique_id(self) -> str:
        return f"{self.key}.{self.item}"

    @property
    def state(self) -> StateType:
        """Return sensor state."""
        return self._state

    @property
    def device_class(self) -> Optional[str]:
        """Return sensor device class."""
        return self.meta.device_class

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return sensor's unit of measurement."""
        return self.meta.unit or self._unit

    @property
    def icon(self) -> Optional[str]:
        """Return icon for sensor."""
        icon = self.meta.icon
        if callable(icon):
            return icon(self.state)
        return icon

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.meta.enabled_default

    async def async_update(self) -> None:
        """Update state."""
        try:
            value = self.router.data[self.key][self.item]
        except KeyError:
            _LOGGER.debug("%s[%s] not in data", self.key, self.item)
            value = None

        formatter = self.meta.formatter
        if not callable(formatter):
            formatter = format_default

        self._state, self._unit = formatter(value)
        self._available = value is not None
