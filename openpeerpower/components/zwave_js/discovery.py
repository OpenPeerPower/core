"""Map Z-Wave nodes and values to Open Peer Power entities."""

from dataclasses import dataclass
from typing import Generator, List, Optional, Set, Union

from zwave_js_server.const import CommandClass
from zwave_js_server.model.device_class import DeviceClassItem
from zwave_js_server.model.node import Node as ZwaveNode
from zwave_js_server.model.value import Value as ZwaveValue

from openpeerpower.core import callback


@dataclass
class ZwaveDiscoveryInfo:
    """Info discovered from (primary) ZWave Value to create entity."""

    # node to which the value(s) belongs
    node: ZwaveNode
    # the value object itself for primary value
    primary_value: ZwaveValue
    # the open peer power platform for which an entity should be created
    platform: str
    # hint for the platform about this discovered entity
    platform_hint: Optional[str] = ""


@dataclass
class ZWaveValueDiscoverySchema:
    """Z-Wave Value discovery schema.

    The Z-Wave Value must match these conditions.
    Use the Z-Wave specifications to find out the values for these parameters:
    https://github.com/zwave-js/node-zwave-js/tree/master/specs
    """

    # [optional] the value's command class must match ANY of these values
    command_class: Optional[Set[int]] = None
    # [optional] the value's endpoint must match ANY of these values
    endpoint: Optional[Set[int]] = None
    # [optional] the value's property must match ANY of these values
    property: Optional[Set[Union[str, int]]] = None
    # [optional] the value's metadata_type must match ANY of these values
    type: Optional[Set[str]] = None


@dataclass
class ZWaveDiscoverySchema:
    """Z-Wave discovery schema.

    The Z-Wave node and it's (primary) value for an entity must match these conditions.
    Use the Z-Wave specifications to find out the values for these parameters:
    https://github.com/zwave-js/node-zwave-js/tree/master/specs
    """

    # specify the opp platform for which this scheme applies (e.g. light, sensor)
    platform: str
    # primary value belonging to this discovery scheme
    primary_value: ZWaveValueDiscoverySchema
    # [optional] hint for platform
    hint: Optional[str] = None
    # [optional] the node's manufacturer_id must match ANY of these values
    manufacturer_id: Optional[Set[int]] = None
    # [optional] the node's product_id must match ANY of these values
    product_id: Optional[Set[int]] = None
    # [optional] the node's product_type must match ANY of these values
    product_type: Optional[Set[int]] = None
    # [optional] the node's firmware_version must match ANY of these values
    firmware_version: Optional[Set[str]] = None
    # [optional] the node's basic device class must match ANY of these values
    device_class_basic: Optional[Set[Union[str, int]]] = None
    # [optional] the node's generic device class must match ANY of these values
    device_class_generic: Optional[Set[Union[str, int]]] = None
    # [optional] the node's specific device class must match ANY of these values
    device_class_specific: Optional[Set[Union[str, int]]] = None
    # [optional] additional values that ALL need to be present on the node for this scheme to pass
    required_values: Optional[List[ZWaveValueDiscoverySchema]] = None
    # [optional] additional values that MAY NOT be present on the node for this scheme to pass
    absent_values: Optional[List[ZWaveValueDiscoverySchema]] = None
    # [optional] bool to specify if this primary value may be discovered by multiple platforms
    allow_multi: bool = False


SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA = ZWaveValueDiscoverySchema(
    command_class={CommandClass.SWITCH_MULTILEVEL},
    property={"currentValue"},
    type={"number"},
)

# For device class mapping see:
# https://github.com/zwave-js/node-zwave-js/blob/master/packages/config/config/deviceClasses.json
DISCOVERY_SCHEMAS = [
    # ====== START OF DEVICE SPECIFIC MAPPING SCHEMAS =======
    # Honeywell 39358 In-Wall Fan Control using switch multilevel CC
    ZWaveDiscoverySchema(
        platform="fan",
        manufacturer_id={0x0039},
        product_id={0x3131},
        product_type={0x4944},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # GE/Jasco fan controllers using switch multilevel CC
    ZWaveDiscoverySchema(
        platform="fan",
        manufacturer_id={0x0063},
        product_id={0x3034, 0x3131, 0x3138},
        product_type={0x4944},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # Leviton ZW4SF fan controllers using switch multilevel CC
    ZWaveDiscoverySchema(
        platform="fan",
        manufacturer_id={0x001D},
        product_id={0x0002},
        product_type={0x0038},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # Inovelli LZW36 light / fan controller combo using switch multilevel CC
    # The fan is endpoint 2, the light is endpoint 1.
    ZWaveDiscoverySchema(
        platform="fan",
        manufacturer_id={0x031E},
        product_id={0x0001},
        product_type={0x000E},
        primary_value=ZWaveValueDiscoverySchema(
            command_class={CommandClass.SWITCH_MULTILEVEL},
            endpoint={2},
            property={"currentValue"},
            type={"number"},
        ),
    ),
    # Fibaro Shutter Fibaro FGS222
    ZWaveDiscoverySchema(
        platform="cover",
        manufacturer_id={0x010F},
        product_id={0x1000},
        product_type={0x0302},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # Qubino flush shutter
    ZWaveDiscoverySchema(
        platform="cover",
        manufacturer_id={0x0159},
        product_id={0x0052},
        product_type={0x0003},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # Graber/Bali/Spring Fashion Covers
    ZWaveDiscoverySchema(
        platform="cover",
        manufacturer_id={0x026E},
        product_id={0x5A31},
        product_type={0x4353},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # iBlinds v2 window blind motor
    ZWaveDiscoverySchema(
        platform="cover",
        manufacturer_id={0x0287},
        product_id={0x000D},
        product_type={0x0003},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # ====== START OF GENERIC MAPPING SCHEMAS =======
    # locks
    ZWaveDiscoverySchema(
        platform="lock",
        device_class_generic={"Entry Control"},
        device_class_specific={
            "Door Lock",
            "Advanced Door Lock",
            "Secure Keypad Door Lock",
            "Secure Lockbox",
        },
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.LOCK,
                CommandClass.DOOR_LOCK,
            },
            property={"currentMode", "locked"},
            type={"number", "boolean"},
        ),
    ),
    # door lock door status
    ZWaveDiscoverySchema(
        platform="binary_sensor",
        hint="property",
        device_class_generic={"Entry Control"},
        device_class_specific={
            "Door Lock",
            "Advanced Door Lock",
            "Secure Keypad Door Lock",
            "Secure Lockbox",
        },
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.LOCK,
                CommandClass.DOOR_LOCK,
            },
            property={"doorStatus"},
            type={"any"},
        ),
    ),
    # climate
    # thermostats supporting mode (and optional setpoint)
    ZWaveDiscoverySchema(
        platform="climate",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={CommandClass.THERMOSTAT_MODE},
            property={"mode"},
            type={"number"},
        ),
    ),
    # thermostats supporting setpoint only (and thus not mode)
    ZWaveDiscoverySchema(
        platform="climate",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={CommandClass.THERMOSTAT_SETPOINT},
            property={"setpoint"},
            type={"number"},
        ),
        absent_values=[  # mode must not be present to prevent dupes
            ZWaveValueDiscoverySchema(
                command_class={CommandClass.THERMOSTAT_MODE},
                property={"mode"},
                type={"number"},
            ),
        ],
    ),
    # binary sensors
    ZWaveDiscoverySchema(
        platform="binary_sensor",
        hint="boolean",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.SENSOR_BINARY,
                CommandClass.BATTERY,
                CommandClass.SENSOR_ALARM,
            },
            type={"boolean"},
        ),
    ),
    ZWaveDiscoverySchema(
        platform="binary_sensor",
        hint="notification",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.NOTIFICATION,
            },
            type={"number"},
        ),
        allow_multi=True,
    ),
    # generic text sensors
    ZWaveDiscoverySchema(
        platform="sensor",
        hint="string_sensor",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.SENSOR_ALARM,
                CommandClass.INDICATOR,
            },
            type={"string"},
        ),
    ),
    # generic numeric sensors
    ZWaveDiscoverySchema(
        platform="sensor",
        hint="numeric_sensor",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.SENSOR_MULTILEVEL,
                CommandClass.SENSOR_ALARM,
                CommandClass.INDICATOR,
                CommandClass.BATTERY,
            },
            type={"number"},
        ),
    ),
    # numeric sensors for Meter CC
    ZWaveDiscoverySchema(
        platform="sensor",
        hint="numeric_sensor",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.METER,
            },
            type={"number"},
            property={"value"},
        ),
    ),
    # special list sensors (Notification CC)
    ZWaveDiscoverySchema(
        platform="sensor",
        hint="list_sensor",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.NOTIFICATION,
            },
            type={"number"},
        ),
        allow_multi=True,
    ),
    # sensor for basic CC
    ZWaveDiscoverySchema(
        platform="sensor",
        hint="numeric_sensor",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={
                CommandClass.BASIC,
            },
            type={"number"},
            property={"currentValue"},
        ),
    ),
    # binary switches
    ZWaveDiscoverySchema(
        platform="switch",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={CommandClass.SWITCH_BINARY}, property={"currentValue"}
        ),
    ),
    # binary switch
    # barrier operator signaling states
    ZWaveDiscoverySchema(
        platform="switch",
        hint="barrier_event_signaling_state",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={CommandClass.BARRIER_OPERATOR},
            property={"signalingState"},
            type={"number"},
        ),
    ),
    # cover
    # window coverings
    ZWaveDiscoverySchema(
        platform="cover",
        hint="window_cover",
        device_class_generic={"Multilevel Switch"},
        device_class_specific={
            "Motor Control Class A",
            "Motor Control Class B",
            "Motor Control Class C",
            "Multiposition Motor",
        },
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # cover
    # motorized barriers
    ZWaveDiscoverySchema(
        platform="cover",
        hint="motorized_barrier",
        primary_value=ZWaveValueDiscoverySchema(
            command_class={CommandClass.BARRIER_OPERATOR},
            property={"currentState"},
            type={"number"},
        ),
        required_values=[
            ZWaveValueDiscoverySchema(
                command_class={CommandClass.BARRIER_OPERATOR},
                property={"targetState"},
                type={"number"},
            ),
        ],
    ),
    # fan
    ZWaveDiscoverySchema(
        platform="fan",
        hint="fan",
        device_class_generic={"Multilevel Switch"},
        device_class_specific={"Fan Switch"},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # number platform
    # valve control for thermostats
    ZWaveDiscoverySchema(
        platform="number",
        hint="Valve control",
        device_class_generic={"Thermostat"},
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
    # lights
    # primary value is the currentValue (brightness)
    # catch any device with multilevel CC as light
    # NOTE: keep this at the bottom of the discovery scheme,
    # to handle all others that need the multilevel CC first
    ZWaveDiscoverySchema(
        platform="light",
        primary_value=SWITCH_MULTILEVEL_CURRENT_VALUE_SCHEMA,
    ),
]


@callback
def async_discover_values(node: ZwaveNode) -> Generator[ZwaveDiscoveryInfo, None, None]:
    """Run discovery on ZWave node and return matching (primary) values."""
    for value in node.values.values():
        for schema in DISCOVERY_SCHEMAS:
            # check manufacturer_id
            if (
                schema.manufacturer_id is not None
                and value.node.manufacturer_id not in schema.manufacturer_id
            ):
                continue
            # check product_id
            if (
                schema.product_id is not None
                and value.node.product_id not in schema.product_id
            ):
                continue
            # check product_type
            if (
                schema.product_type is not None
                and value.node.product_type not in schema.product_type
            ):
                continue
            # check firmware_version
            if (
                schema.firmware_version is not None
                and value.node.firmware_version not in schema.firmware_version
            ):
                continue
            # check device_class_basic
            if not check_device_class(
                value.node.device_class.basic, schema.device_class_basic
            ):
                continue
            # check device_class_generic
            if not check_device_class(
                value.node.device_class.generic, schema.device_class_generic
            ):
                continue
            # check device_class_specific
            if not check_device_class(
                value.node.device_class.specific, schema.device_class_specific
            ):
                continue
            # check primary value
            if not check_value(value, schema.primary_value):
                continue
            # check additional required values
            if schema.required_values is not None:
                if not all(
                    any(check_value(val, val_scheme) for val in node.values.values())
                    for val_scheme in schema.required_values
                ):
                    continue
            # check for values that may not be present
            if schema.absent_values is not None:
                if any(
                    any(check_value(val, val_scheme) for val in node.values.values())
                    for val_scheme in schema.absent_values
                ):
                    continue
            # all checks passed, this value belongs to an entity
            yield ZwaveDiscoveryInfo(
                node=value.node,
                primary_value=value,
                platform=schema.platform,
                platform_hint=schema.hint,
            )
            if not schema.allow_multi:
                # break out of loop, this value may not be discovered by other schemas/platforms
                break


@callback
def check_value(value: ZwaveValue, schema: ZWaveValueDiscoverySchema) -> bool:
    """Check if value matches scheme."""
    # check command_class
    if (
        schema.command_class is not None
        and value.command_class not in schema.command_class
    ):
        return False
    # check endpoint
    if schema.endpoint is not None and value.endpoint not in schema.endpoint:
        return False
    # check property
    if schema.property is not None and value.property_ not in schema.property:
        return False
    # check metadata_type
    if schema.type is not None and value.metadata.type not in schema.type:
        return False
    return True


@callback
def check_device_class(
    device_class: DeviceClassItem, required_value: Optional[Set[Union[str, int]]]
) -> bool:
    """Check if device class id or label matches."""
    if required_value is None:
        return True
    for val in required_value:
        if isinstance(val, str) and device_class.label == val:
            return True
        if isinstance(val, int) and device_class.key == val:
            return True
    return False
