"""Tests for the Verisure platform."""

from contextlib import contextmanager
from unittest.mock import call, patch

from openpeerpower.components.lock import (
    DOMAIN as LOCK_DOMAIN,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
)
from openpeerpower.components.verisure import DOMAIN as VERISURE_DOMAIN
from openpeerpower.const import STATE_UNLOCKED
from openpeerpower.setup import async_setup_component

NO_DEFAULT_LOCK_CODE_CONFIG = {
    "verisure": {
        "username": "test",
        "password": "test",
        "locks": True,
        "alarm": False,
        "door_window": False,
        "hygrometers": False,
        "mouse": False,
        "smartplugs": False,
        "thermometers": False,
        "smartcam": False,
    }
}

DEFAULT_LOCK_CODE_CONFIG = {
    "verisure": {
        "username": "test",
        "password": "test",
        "locks": True,
        "default_lock_code": "9999",
        "alarm": False,
        "door_window": False,
        "hygrometers": False,
        "mouse": False,
        "smartplugs": False,
        "thermometers": False,
        "smartcam": False,
    }
}

LOCKS = ["door_lock"]


@contextmanager
def mock_hub(config, get_response=LOCKS[0]):
    """Extensively mock out a verisure hub."""
    hub_prefix = "openpeerpower.components.verisure.lock.hub"
    # Since there is no conf to disable ethernet status, mock hub for
    # binary sensor too
    hub_binary_sensor = "openpeerpower.components.verisure.binary_sensor.hub"
    verisure_prefix = "verisure.Session"
    with patch(verisure_prefix) as session, patch(hub_prefix) as hub:
        session.login.return_value = True

        hub.config = config["verisure"]
        hub.get.return_value = LOCKS
        hub.get_first.return_value = get_response.upper()
        hub.session.set_lock_state.return_value = {
            "doorLockStateChangeTransactionId": "test"
        }
        hub.session.get_lock_state_transaction.return_value = {"result": "OK"}

        with patch(hub_binary_sensor, hub):
            yield hub


async def setup_verisure_locks(opp, config):
    """Set up mock verisure locks."""
    with mock_hub(config):
        await async_setup_component(opp, VERISURE_DOMAIN, config)
        await opp.async_block_till_done()
        # lock.door_lock, ethernet_status
        assert len(opp.states.async_all()) == 2


async def test_verisure_no_default_code.opp):
    """Test configs without a default lock code."""
    await setup_verisure_locks(opp, NO_DEFAULT_LOCK_CODE_CONFIG)
    with mock_hub(NO_DEFAULT_LOCK_CODE_CONFIG, STATE_UNLOCKED) as hub:

        mock = hub.session.set_lock_state
        await opp.services.async_call(
            LOCK_DOMAIN, SERVICE_LOCK, {"entity_id": "lock.door_lock"}
        )
        await opp.async_block_till_done()
        assert mock.call_count == 0

        await opp.services.async_call(
            LOCK_DOMAIN, SERVICE_LOCK, {"entity_id": "lock.door_lock", "code": "12345"}
        )
        await opp.async_block_till_done()
        assert mock.call_args == call("12345", LOCKS[0], "lock")

        mock.reset_mock()
        await opp.services.async_call(
            LOCK_DOMAIN, SERVICE_UNLOCK, {"entity_id": "lock.door_lock"}
        )
        await opp.async_block_till_done()
        assert mock.call_count == 0

        await opp.services.async_call(
            LOCK_DOMAIN,
            SERVICE_UNLOCK,
            {"entity_id": "lock.door_lock", "code": "12345"},
        )
        await opp.async_block_till_done()
        assert mock.call_args == call("12345", LOCKS[0], "unlock")


async def test_verisure_default_code.opp):
    """Test configs with a default lock code."""
    await setup_verisure_locks(opp, DEFAULT_LOCK_CODE_CONFIG)
    with mock_hub(DEFAULT_LOCK_CODE_CONFIG, STATE_UNLOCKED) as hub:
        mock = hub.session.set_lock_state
        await opp.services.async_call(
            LOCK_DOMAIN, SERVICE_LOCK, {"entity_id": "lock.door_lock"}
        )
        await opp.async_block_till_done()
        assert mock.call_args == call("9999", LOCKS[0], "lock")

        await opp.services.async_call(
            LOCK_DOMAIN, SERVICE_UNLOCK, {"entity_id": "lock.door_lock"}
        )
        await opp.async_block_till_done()
        assert mock.call_args == call("9999", LOCKS[0], "unlock")

        await opp.services.async_call(
            LOCK_DOMAIN, SERVICE_LOCK, {"entity_id": "lock.door_lock", "code": "12345"}
        )
        await opp.async_block_till_done()
        assert mock.call_args == call("12345", LOCKS[0], "lock")

        await opp.services.async_call(
            LOCK_DOMAIN,
            SERVICE_UNLOCK,
            {"entity_id": "lock.door_lock", "code": "12345"},
        )
        await opp.async_block_till_done()
        assert mock.call_args == call("12345", LOCKS[0], "unlock")
