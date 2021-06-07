"""Tests for the TotalConnect alarm control panel device."""
from unittest.mock import patch

import pytest

from openpeerpower.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_DISARM,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_DISARMING,
    STATE_ALARM_TRIGGERED,
)
from openpeerpower.exceptions import OpenPeerPowerError

from .common import (
    LOCATION_ID,
    RESPONSE_ARM_FAILURE,
    RESPONSE_ARM_SUCCESS,
    RESPONSE_ARMED_AWAY,
    RESPONSE_ARMED_CUSTOM,
    RESPONSE_ARMED_NIGHT,
    RESPONSE_ARMED_STAY,
    RESPONSE_ARMING,
    RESPONSE_DISARM_FAILURE,
    RESPONSE_DISARM_SUCCESS,
    RESPONSE_DISARMED,
    RESPONSE_DISARMING,
    RESPONSE_SUCCESS,
    RESPONSE_TRIGGERED_CARBON_MONOXIDE,
    RESPONSE_TRIGGERED_FIRE,
    RESPONSE_TRIGGERED_POLICE,
    RESPONSE_UNKNOWN,
    RESPONSE_USER_CODE_INVALID,
    setup_platform,
)

ENTITY_ID = "alarm_control_panel.test"
CODE = "-1"
DATA = {ATTR_ENTITY_ID: ENTITY_ID}


async def test_attributes(opp):
    """Test the alarm control panel attributes are correct."""
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        return_value=RESPONSE_DISARMED,
    ) as mock_request:
        await setup_platform(opp, ALARM_DOMAIN)
        state = opp.states.get(ENTITY_ID)
        assert state.state == STATE_ALARM_DISARMED
        mock_request.assert_called_once()
        assert state.attributes.get(ATTR_FRIENDLY_NAME) == "test"

        entity_registry = await opp.helpers.entity_registry.async_get_registry()
        entry = entity_registry.async_get(ENTITY_ID)
        # TotalConnect alarm device unique_id is the location_id
        assert entry.unique_id == LOCATION_ID


async def test_arm_home_success(opp):
    """Test arm home method success."""
    responses = [RESPONSE_DISARMED, RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_STAY]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED

        await opp.services.async_call(
            ALARM_DOMAIN, SERVICE_ALARM_ARM_HOME, DATA, blocking=True
        )

        await opp.async_block_till_done()
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_HOME


async def test_arm_home_failure(opp):
    """Test arm home method failure."""
    responses = [RESPONSE_DISARMED, RESPONSE_ARM_FAILURE, RESPONSE_DISARMED]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED

        with pytest.raises(OpenPeerPowerError) as err:
            await opp.services.async_call(
                ALARM_DOMAIN, SERVICE_ALARM_ARM_HOME, DATA, blocking=True
            )
            await opp.async_block_till_done()
        assert f"{err.value}" == "TotalConnect failed to arm home test."
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED


async def test_arm_home_invalid_usercode(opp):
    """Test arm home method with invalid usercode."""
    responses = [RESPONSE_DISARMED, RESPONSE_USER_CODE_INVALID, RESPONSE_DISARMED]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED

        with pytest.raises(OpenPeerPowerError) as err:
            await opp.services.async_call(
                ALARM_DOMAIN, SERVICE_ALARM_ARM_HOME, DATA, blocking=True
            )
            await opp.async_block_till_done()
        assert f"{err.value}" == "TotalConnect failed to arm home test."
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED


async def test_arm_away_success(opp):
    """Test arm away method success."""
    responses = [RESPONSE_DISARMED, RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_AWAY]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED

        await opp.services.async_call(
            ALARM_DOMAIN, SERVICE_ALARM_ARM_AWAY, DATA, blocking=True
        )
        await opp.async_block_till_done()
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_AWAY


async def test_arm_away_failure(opp):
    """Test arm away method failure."""
    responses = [RESPONSE_DISARMED, RESPONSE_ARM_FAILURE, RESPONSE_DISARMED]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED

        with pytest.raises(OpenPeerPowerError) as err:
            await opp.services.async_call(
                ALARM_DOMAIN, SERVICE_ALARM_ARM_AWAY, DATA, blocking=True
            )
            await opp.async_block_till_done()
        assert f"{err.value}" == "TotalConnect failed to arm away test."
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED


async def test_disarm_success(opp):
    """Test disarm method success."""
    responses = [RESPONSE_ARMED_AWAY, RESPONSE_DISARM_SUCCESS, RESPONSE_DISARMED]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_AWAY

        await opp.services.async_call(
            ALARM_DOMAIN, SERVICE_ALARM_DISARM, DATA, blocking=True
        )
        await opp.async_block_till_done()
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED


async def test_disarm_failure(opp):
    """Test disarm method failure."""
    responses = [RESPONSE_ARMED_AWAY, RESPONSE_DISARM_FAILURE, RESPONSE_ARMED_AWAY]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_AWAY

        with pytest.raises(OpenPeerPowerError) as err:
            await opp.services.async_call(
                ALARM_DOMAIN, SERVICE_ALARM_DISARM, DATA, blocking=True
            )
            await opp.async_block_till_done()
        assert f"{err.value}" == "TotalConnect failed to disarm test."
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_AWAY


async def test_disarm_invalid_usercode(opp):
    """Test disarm method failure."""
    responses = [RESPONSE_ARMED_AWAY, RESPONSE_USER_CODE_INVALID, RESPONSE_ARMED_AWAY]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_AWAY

        with pytest.raises(OpenPeerPowerError) as err:
            await opp.services.async_call(
                ALARM_DOMAIN, SERVICE_ALARM_DISARM, DATA, blocking=True
            )
            await opp.async_block_till_done()
        assert f"{err.value}" == "TotalConnect failed to disarm test."
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_AWAY


async def test_arm_night_success(opp):
    """Test arm night method success."""
    responses = [RESPONSE_DISARMED, RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_NIGHT]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED

        await opp.services.async_call(
            ALARM_DOMAIN, SERVICE_ALARM_ARM_NIGHT, DATA, blocking=True
        )

        await opp.async_block_till_done()
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_NIGHT


async def test_arm_night_failure(opp):
    """Test arm night method failure."""
    responses = [RESPONSE_DISARMED, RESPONSE_ARM_FAILURE, RESPONSE_DISARMED]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED

        with pytest.raises(OpenPeerPowerError) as err:
            await opp.services.async_call(
                ALARM_DOMAIN, SERVICE_ALARM_ARM_NIGHT, DATA, blocking=True
            )
            await opp.async_block_till_done()
        assert f"{err.value}" == "TotalConnect failed to arm night test."
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED


async def test_arming(opp):
    """Test arming."""
    responses = [RESPONSE_DISARMED, RESPONSE_SUCCESS, RESPONSE_ARMING]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMED

        await opp.services.async_call(
            ALARM_DOMAIN, SERVICE_ALARM_ARM_NIGHT, DATA, blocking=True
        )
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMING


async def test_disarming(opp):
    """Test disarming."""
    responses = [RESPONSE_ARMED_AWAY, RESPONSE_SUCCESS, RESPONSE_DISARMING]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_ARMED_AWAY

        await opp.services.async_call(
            ALARM_DOMAIN, SERVICE_ALARM_DISARM, DATA, blocking=True
        )
        assert opp.states.get(ENTITY_ID).state == STATE_ALARM_DISARMING


async def test_triggered_fire(opp):
    """Test triggered by fire."""
    responses = [RESPONSE_TRIGGERED_FIRE]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        state = opp.states.get(ENTITY_ID)
        assert state.state == STATE_ALARM_TRIGGERED
        assert state.attributes.get("triggered_source") == "Fire/Smoke"


async def test_triggered_police(opp):
    """Test triggered by police."""
    responses = [RESPONSE_TRIGGERED_POLICE]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        state = opp.states.get(ENTITY_ID)
        assert state.state == STATE_ALARM_TRIGGERED
        assert state.attributes.get("triggered_source") == "Police/Medical"


async def test_triggered_carbon_monoxide(opp):
    """Test triggered by carbon monoxide."""
    responses = [RESPONSE_TRIGGERED_CARBON_MONOXIDE]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        state = opp.states.get(ENTITY_ID)
        assert state.state == STATE_ALARM_TRIGGERED
        assert state.attributes.get("triggered_source") == "Carbon Monoxide"


async def test_armed_custom(opp):
    """Test armed custom."""
    responses = [RESPONSE_ARMED_CUSTOM]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        state = opp.states.get(ENTITY_ID)
        assert state.state == STATE_ALARM_ARMED_CUSTOM_BYPASS


async def test_unknown(opp):
    """Test unknown arm status."""
    responses = [RESPONSE_UNKNOWN]
    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ):
        await setup_platform(opp, ALARM_DOMAIN)
        state = opp.states.get(ENTITY_ID)
        assert state.state == "unknown"
