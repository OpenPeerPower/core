"""Tests for the services module."""
from pyheos import CommandFailedError, HeosError, const

from openpeerpower.components.heos.const import (
    ATTR_PASSWORD,
    ATTR_USERNAME,
    DOMAIN,
    SERVICE_SIGN_IN,
    SERVICE_SIGN_OUT,
)
from openpeerpower.setup import async_setup_component


async def setup_component.opp, config_entry):
    """Set up the component for testing."""
    config_entry.add_to.opp.opp)
    assert await async_setup_component.opp, DOMAIN, {})
    await.opp.async_block_till_done()


async def test_sign_in.opp, config_entry, controller):
    """Test the sign-in service."""
    await setup_component.opp, config_entry)

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SIGN_IN,
        {ATTR_USERNAME: "test@test.com", ATTR_PASSWORD: "password"},
        blocking=True,
    )

    controller.sign_in.assert_called_once_with("test@test.com", "password")


async def test_sign_in_not_connected.opp, config_entry, controller, caplog):
    """Test sign-in service logs error when not connected."""
    await setup_component.opp, config_entry)
    controller.connection_state = const.STATE_RECONNECTING

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SIGN_IN,
        {ATTR_USERNAME: "test@test.com", ATTR_PASSWORD: "password"},
        blocking=True,
    )

    assert controller.sign_in.call_count == 0
    assert "Unable to sign in because HEOS is not connected" in caplog.text


async def test_sign_in_failed.opp, config_entry, controller, caplog):
    """Test sign-in service logs error when not connected."""
    await setup_component.opp, config_entry)
    controller.sign_in.side_effect = CommandFailedError("", "Invalid credentials", 6)

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SIGN_IN,
        {ATTR_USERNAME: "test@test.com", ATTR_PASSWORD: "password"},
        blocking=True,
    )

    controller.sign_in.assert_called_once_with("test@test.com", "password")
    assert "Sign in failed: Invalid credentials (6)" in caplog.text


async def test_sign_in_unknown_error(opp, config_entry, controller, caplog):
    """Test sign-in service logs error for failure."""
    await setup_component.opp, config_entry)
    controller.sign_in.side_effect = HeosError()

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SIGN_IN,
        {ATTR_USERNAME: "test@test.com", ATTR_PASSWORD: "password"},
        blocking=True,
    )

    controller.sign_in.assert_called_once_with("test@test.com", "password")
    assert "Unable to sign in" in caplog.text


async def test_sign_out.opp, config_entry, controller):
    """Test the sign-out service."""
    await setup_component.opp, config_entry)

    await.opp.services.async_call(DOMAIN, SERVICE_SIGN_OUT, {}, blocking=True)

    assert controller.sign_out.call_count == 1


async def test_sign_out_not_connected.opp, config_entry, controller, caplog):
    """Test the sign-out service."""
    await setup_component.opp, config_entry)
    controller.connection_state = const.STATE_RECONNECTING

    await.opp.services.async_call(DOMAIN, SERVICE_SIGN_OUT, {}, blocking=True)

    assert controller.sign_out.call_count == 0
    assert "Unable to sign out because HEOS is not connected" in caplog.text


async def test_sign_out_unknown_error(opp, config_entry, controller, caplog):
    """Test the sign-out service."""
    await setup_component.opp, config_entry)
    controller.sign_out.side_effect = HeosError()

    await.opp.services.async_call(DOMAIN, SERVICE_SIGN_OUT, {}, blocking=True)

    assert controller.sign_out.call_count == 1
    assert "Unable to sign out" in caplog.text
