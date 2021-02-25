"""Test cases for the switcher_kis component."""
from datetime import timedelta
from typing import Any, Generator
from unittest.mock import patch

from aioswitcher.consts import COMMAND_ON
from aioswitcher.devices import SwitcherV2Device
from pytest import raises

from openpeerpower.components.switcher_kis import (
    DATA_DEVICE,
    DOMAIN,
    SIGNAL_SWITCHER_DEVICE_UPDATE,
)
from openpeerpower.components.switcher_kis.switch import (
    CONF_AUTO_OFF,
    CONF_TIMER_MINUTES,
    SERVICE_SET_AUTO_OFF_NAME,
    SERVICE_TURN_ON_WITH_TIMER_NAME,
)
from openpeerpower.const import CONF_ENTITY_ID
from openpeerpower.core import Context, callback
from openpeerpower.exceptions import UnknownUser
from openpeerpower.helpers.config_validation import time_period_str
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt

from .consts import (
    DUMMY_AUTO_OFF_SET,
    DUMMY_DEVICE_ID,
    DUMMY_DEVICE_NAME,
    DUMMY_DEVICE_STATE,
    DUMMY_ELECTRIC_CURRENT,
    DUMMY_IP_ADDRESS,
    DUMMY_MAC_ADDRESS,
    DUMMY_PHONE_ID,
    DUMMY_POWER_CONSUMPTION,
    DUMMY_REMAINING_TIME,
    DUMMY_TIMER_MINUTES_SET,
    MANDATORY_CONFIGURATION,
    SWITCH_ENTITY_ID,
)

from tests.common import MockUser, async_fire_time_changed


async def test_failed_config(
    opp: OpenPeerPowerType, mock_failed_bridge: Generator[None, Any, None]
) -> None:
    """Test failed configuration."""
    assert await async_setup_component(opp, DOMAIN, MANDATORY_CONFIGURATION) is False


async def test_minimal_config(
    opp: OpenPeerPowerType, mock_bridge: Generator[None, Any, None]
) -> None:
    """Test setup with configuration minimal entries."""
    assert await async_setup_component(opp, DOMAIN, MANDATORY_CONFIGURATION)


async def test_discovery_data_bucket(
    opp: OpenPeerPowerType, mock_bridge: Generator[None, Any, None]
) -> None:
    """Test the event send with the updated device."""
    assert await async_setup_component(opp, DOMAIN, MANDATORY_CONFIGURATION)

    await opp.async_block_till_done()

    device = opp.data[DOMAIN].get(DATA_DEVICE)
    assert device.device_id == DUMMY_DEVICE_ID
    assert device.ip_addr == DUMMY_IP_ADDRESS
    assert device.mac_addr == DUMMY_MAC_ADDRESS
    assert device.name == DUMMY_DEVICE_NAME
    assert device.state == DUMMY_DEVICE_STATE
    assert device.remaining_time == DUMMY_REMAINING_TIME
    assert device.auto_off_set == DUMMY_AUTO_OFF_SET
    assert device.power_consumption == DUMMY_POWER_CONSUMPTION
    assert device.electric_current == DUMMY_ELECTRIC_CURRENT
    assert device.phone_id == DUMMY_PHONE_ID


async def test_set_auto_off_service(
    opp: OpenPeerPowerType,
    mock_bridge: Generator[None, Any, None],
    mock_api: Generator[None, Any, None],
    opp.owner_user: MockUser,
) -> None:
    """Test the set_auto_off service."""
    assert await async_setup_component(opp, DOMAIN, MANDATORY_CONFIGURATION)

    await opp.async_block_till_done()

    assert opp.services.has_service(DOMAIN, SERVICE_SET_AUTO_OFF_NAME)

    await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_AUTO_OFF_NAME,
        {CONF_ENTITY_ID: SWITCH_ENTITY_ID, CONF_AUTO_OFF: DUMMY_AUTO_OFF_SET},
        blocking=True,
        context=Context(user_id(opp_owner_user.id),
    )

    with raises(UnknownUser) as unknown_user_exc:
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_AUTO_OFF_NAME,
            {CONF_ENTITY_ID: SWITCH_ENTITY_ID, CONF_AUTO_OFF: DUMMY_AUTO_OFF_SET},
            blocking=True,
            context=Context(user_id="not_real_user"),
        )

    assert unknown_user_exc.type is UnknownUser

    with patch(
        "openpeerpower.components.switcher_kis.switch.SwitcherV2Api.set_auto_shutdown"
    ) as mock_set_auto_shutdown:
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_AUTO_OFF_NAME,
            {CONF_ENTITY_ID: SWITCH_ENTITY_ID, CONF_AUTO_OFF: DUMMY_AUTO_OFF_SET},
        )

        await opp.async_block_till_done()

        mock_set_auto_shutdown.assert_called_once_with(
            time_period_str(DUMMY_AUTO_OFF_SET)
        )


async def test_turn_on_with_timer_service(
    opp: OpenPeerPowerType,
    mock_bridge: Generator[None, Any, None],
    mock_api: Generator[None, Any, None],
    opp.owner_user: MockUser,
) -> None:
    """Test the set_auto_off service."""
    assert await async_setup_component(opp, DOMAIN, MANDATORY_CONFIGURATION)

    await opp.async_block_till_done()

    assert opp.services.has_service(DOMAIN, SERVICE_TURN_ON_WITH_TIMER_NAME)

    await opp.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON_WITH_TIMER_NAME,
        {CONF_ENTITY_ID: SWITCH_ENTITY_ID, CONF_TIMER_MINUTES: DUMMY_TIMER_MINUTES_SET},
        blocking=True,
        context=Context(user_id(opp_owner_user.id),
    )

    with raises(UnknownUser) as unknown_user_exc:
        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_ON_WITH_TIMER_NAME,
            {
                CONF_ENTITY_ID: SWITCH_ENTITY_ID,
                CONF_TIMER_MINUTES: DUMMY_TIMER_MINUTES_SET,
            },
            blocking=True,
            context=Context(user_id="not_real_user"),
        )

    assert unknown_user_exc.type is UnknownUser

    with patch(
        "openpeerpower.components.switcher_kis.switch.SwitcherV2Api.control_device"
    ) as mock_control_device:
        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_ON_WITH_TIMER_NAME,
            {
                CONF_ENTITY_ID: SWITCH_ENTITY_ID,
                CONF_TIMER_MINUTES: DUMMY_TIMER_MINUTES_SET,
            },
        )

        await opp.async_block_till_done()

        mock_control_device.assert_called_once_with(
            COMMAND_ON, int(DUMMY_TIMER_MINUTES_SET)
        )


async def test_signal_dispatcher(
    opp: OpenPeerPowerType, mock_bridge: Generator[None, Any, None]
) -> None:
    """Test signal dispatcher dispatching device updates every 4 seconds."""
    assert await async_setup_component(opp, DOMAIN, MANDATORY_CONFIGURATION)

    await opp.async_block_till_done()

    @callback
    def verify_update_data(device: SwitcherV2Device) -> None:
        """Use as callback for signal dispatcher."""
        pass

    async_dispatcher_connect(opp, SIGNAL_SWITCHER_DEVICE_UPDATE, verify_update_data)

    async_fire_time_changed(opp, dt.utcnow() + timedelta(seconds=5))
