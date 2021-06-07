"""The tests for the august platform."""
import asyncio
from unittest.mock import patch

from aiohttp import ClientResponseError
from yalexs.authenticator_common import AuthenticationState
from yalexs.exceptions import AugustApiAIOHTTPError

from openpeerpower import setup
from openpeerpower.components.august.const import DOMAIN
from openpeerpower.components.lock import DOMAIN as LOCK_DOMAIN
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
    STATE_LOCKED,
    STATE_ON,
)
from openpeerpower.exceptions import OpenPeerPowerError

from tests.common import MockConfigEntry
from tests.components.august.mocks import (
    _create_august_with_devices,
    _mock_august_authentication,
    _mock_doorsense_enabled_august_lock_detail,
    _mock_doorsense_missing_august_lock_detail,
    _mock_get_config,
    _mock_inoperative_august_lock_detail,
    _mock_operative_august_lock_detail,
)


async def test_august_is_offline(opp):
    """Config entry state is SETUP_RETRY when august is offline."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=_mock_get_config()[DOMAIN],
        title="August august",
    )
    config_entry.add_to_opp(opp)

    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(
        "yalexs.authenticator_async.AuthenticatorAsync.async_authenticate",
        side_effect=asyncio.TimeoutError,
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unlock_throws_august_api_http_error(opp):
    """Test unlock throws correct error on http error."""
    mocked_lock_detail = await _mock_operative_august_lock_detail(opp)

    def _unlock_return_activities_side_effect(access_token, device_id):
        raise AugustApiAIOHTTPError("This should bubble up as its user consumable")

    await _create_august_with_devices(
        opp,
        [mocked_lock_detail],
        api_call_side_effects={
            "unlock_return_activities": _unlock_return_activities_side_effect
        },
    )
    last_err = None
    data = {ATTR_ENTITY_ID: "lock.a6697750d607098bae8d6baa11ef8063_name"}
    try:
        await opp.services.async_call(LOCK_DOMAIN, SERVICE_UNLOCK, data, blocking=True)
    except OpenPeerPowerError as err:
        last_err = err
    assert (
        str(last_err)
        == "A6697750D607098BAE8D6BAA11EF8063 Name: This should bubble up as its user consumable"
    )


async def test_lock_throws_august_api_http_error(opp):
    """Test lock throws correct error on http error."""
    mocked_lock_detail = await _mock_operative_august_lock_detail(opp)

    def _lock_return_activities_side_effect(access_token, device_id):
        raise AugustApiAIOHTTPError("This should bubble up as its user consumable")

    await _create_august_with_devices(
        opp,
        [mocked_lock_detail],
        api_call_side_effects={
            "lock_return_activities": _lock_return_activities_side_effect
        },
    )
    last_err = None
    data = {ATTR_ENTITY_ID: "lock.a6697750d607098bae8d6baa11ef8063_name"}
    try:
        await opp.services.async_call(LOCK_DOMAIN, SERVICE_LOCK, data, blocking=True)
    except OpenPeerPowerError as err:
        last_err = err
    assert (
        str(last_err)
        == "A6697750D607098BAE8D6BAA11EF8063 Name: This should bubble up as its user consumable"
    )


async def test_inoperative_locks_are_filtered_out(opp):
    """Ensure inoperative locks do not get setup."""
    august_operative_lock = await _mock_operative_august_lock_detail(opp)
    august_inoperative_lock = await _mock_inoperative_august_lock_detail(opp)
    await _create_august_with_devices(
        opp, [august_operative_lock, august_inoperative_lock]
    )

    lock_abc_name = opp.states.get("lock.abc_name")
    assert lock_abc_name is None
    lock_a6697750d607098bae8d6baa11ef8063_name = opp.states.get(
        "lock.a6697750d607098bae8d6baa11ef8063_name"
    )
    assert lock_a6697750d607098bae8d6baa11ef8063_name.state == STATE_LOCKED


async def test_lock_has_doorsense(opp):
    """Check to see if a lock has doorsense."""
    doorsenselock = await _mock_doorsense_enabled_august_lock_detail(opp)
    nodoorsenselock = await _mock_doorsense_missing_august_lock_detail(opp)
    await _create_august_with_devices(opp, [doorsenselock, nodoorsenselock])

    binary_sensor_online_with_doorsense_name_open = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name_open.state == STATE_ON
    binary_sensor_missing_doorsense_id_name_open = opp.states.get(
        "binary_sensor.missing_doorsense_id_name_open"
    )
    assert binary_sensor_missing_doorsense_id_name_open is None


async def test_auth_fails(opp):
    """Config entry state is SETUP_ERROR when auth fails."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=_mock_get_config()[DOMAIN],
        title="August august",
    )
    config_entry.add_to_opp(opp)
    assert opp.config_entries.flow.async_progress() == []

    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(
        "yalexs.authenticator_async.AuthenticatorAsync.async_authenticate",
        side_effect=ClientResponseError(None, None, status=401),
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = opp.config_entries.flow.async_progress()

    assert flows[0]["step_id"] == "reauth_validate"


async def test_bad_password(opp):
    """Config entry state is SETUP_ERROR when the password has been changed."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=_mock_get_config()[DOMAIN],
        title="August august",
    )
    config_entry.add_to_opp(opp)
    assert opp.config_entries.flow.async_progress() == []

    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(
        "yalexs.authenticator_async.AuthenticatorAsync.async_authenticate",
        return_value=_mock_august_authentication(
            "original_token", 1234, AuthenticationState.BAD_PASSWORD
        ),
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = opp.config_entries.flow.async_progress()

    assert flows[0]["step_id"] == "reauth_validate"


async def test_http_failure(opp):
    """Config entry state is SETUP_RETRY when august is offline."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=_mock_get_config()[DOMAIN],
        title="August august",
    )
    config_entry.add_to_opp(opp)
    assert opp.config_entries.flow.async_progress() == []

    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(
        "yalexs.authenticator_async.AuthenticatorAsync.async_authenticate",
        side_effect=ClientResponseError(None, None, status=500),
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY

    assert opp.config_entries.flow.async_progress() == []


async def test_unknown_auth_state(opp):
    """Config entry state is SETUP_ERROR when august is in an unknown auth state."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=_mock_get_config()[DOMAIN],
        title="August august",
    )
    config_entry.add_to_opp(opp)
    assert opp.config_entries.flow.async_progress() == []

    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(
        "yalexs.authenticator_async.AuthenticatorAsync.async_authenticate",
        return_value=_mock_august_authentication("original_token", 1234, None),
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = opp.config_entries.flow.async_progress()

    assert flows[0]["step_id"] == "reauth_validate"


async def test_requires_validation_state(opp):
    """Config entry state is SETUP_ERROR when august requires validation."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=_mock_get_config()[DOMAIN],
        title="August august",
    )
    config_entry.add_to_opp(opp)
    assert opp.config_entries.flow.async_progress() == []

    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(
        "yalexs.authenticator_async.AuthenticatorAsync.async_authenticate",
        return_value=_mock_august_authentication(
            "original_token", 1234, AuthenticationState.REQUIRES_VALIDATION
        ),
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR

    assert len(opp.config_entries.flow.async_progress()) == 1
    assert opp.config_entries.flow.async_progress()[0]["context"]["source"] == "reauth"


async def test_unknown_auth_http_401(opp):
    """Config entry state is SETUP_ERROR when august gets an http."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=_mock_get_config()[DOMAIN],
        title="August august",
    )
    config_entry.add_to_opp(opp)
    assert opp.config_entries.flow.async_progress() == []

    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(
        "yalexs.authenticator_async.AuthenticatorAsync.async_authenticate",
        return_value=_mock_august_authentication("original_token", 1234, None),
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = opp.config_entries.flow.async_progress()

    assert flows[0]["step_id"] == "reauth_validate"


async def test_load_unload(opp):
    """Config entry can be unloaded."""

    august_operative_lock = await _mock_operative_august_lock_detail(opp)
    august_inoperative_lock = await _mock_inoperative_august_lock_detail(opp)
    config_entry = await _create_august_with_devices(
        opp, [august_operative_lock, august_inoperative_lock]
    )

    assert config_entry.state is ConfigEntryState.LOADED

    await opp.config_entries.async_unload(config_entry.entry_id)
    await opp.async_block_till_done()
