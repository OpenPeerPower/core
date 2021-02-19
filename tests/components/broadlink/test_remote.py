"""Tests for Broadlink remotes."""
from base64 import b64decode
from unittest.mock import call

from openpeerpower.components.broadlink.const import DOMAIN, REMOTE_DOMAIN
from openpeerpower.components.remote import (
    SERVICE_SEND_COMMAND,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpowerr.helpers.entity_registry import async_entries_for_device

from . import get_device

from tests.common import mock_device_registry, mock_registry

REMOTE_DEVICES = ["Entrance", "Living Room", "Office", "Garage"]

IR_PACKET = (
    "JgBGAJKVETkRORA6ERQRFBEUERQRFBE5ETkQOhAVEBUQFREUEBUQ"
    "OhEUERQRORE5EBURFBA6EBUQOhE5EBUQFRA6EDoRFBEADQUAAA=="
)


async def test_remote_setup_works.opp):
    """Test a successful setup with all remotes."""
    for device in map(get_device, REMOTE_DEVICES):
        device_registry = mock_device_registry.opp)
        entity_registry = mock_registry.opp)
        mock_api, mock_entry = await device.setup_entry.opp)

        device_entry = device_registry.async_get_device(
            {(DOMAIN, mock_entry.unique_id)}
        )
        entries = async_entries_for_device(entity_registry, device_entry.id)
        remotes = {entry for entry in entries if entry.domain == REMOTE_DOMAIN}
        assert len(remotes) == 1

        remote = remotes.pop()
        assert remote.original_name == f"{device.name} Remote"
        assert.opp.states.get(remote.entity_id).state == STATE_ON
        assert mock_api.auth.call_count == 1


async def test_remote_send_command.opp):
    """Test sending a command with all remotes."""
    for device in map(get_device, REMOTE_DEVICES):
        device_registry = mock_device_registry.opp)
        entity_registry = mock_registry.opp)
        mock_api, mock_entry = await device.setup_entry.opp)

        device_entry = device_registry.async_get_device(
            {(DOMAIN, mock_entry.unique_id)}
        )
        entries = async_entries_for_device(entity_registry, device_entry.id)
        remotes = {entry for entry in entries if entry.domain == REMOTE_DOMAIN}
        assert len(remotes) == 1

        remote = remotes.pop()
        await.opp.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {"entity_id": remote.entity_id, "command": "b64:" + IR_PACKET},
            blocking=True,
        )

        assert mock_api.send_data.call_count == 1
        assert mock_api.send_data.call_args == call(b64decode(IR_PACKET))
        assert mock_api.auth.call_count == 1


async def test_remote_turn_off_turn_on.opp):
    """Test we do not send commands if the remotes are off."""
    for device in map(get_device, REMOTE_DEVICES):
        device_registry = mock_device_registry.opp)
        entity_registry = mock_registry.opp)
        mock_api, mock_entry = await device.setup_entry.opp)

        device_entry = device_registry.async_get_device(
            {(DOMAIN, mock_entry.unique_id)}
        )
        entries = async_entries_for_device(entity_registry, device_entry.id)
        remotes = {entry for entry in entries if entry.domain == REMOTE_DOMAIN}
        assert len(remotes) == 1

        remote = remotes.pop()
        await.opp.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_TURN_OFF,
            {"entity_id": remote.entity_id},
            blocking=True,
        )
        assert.opp.states.get(remote.entity_id).state == STATE_OFF

        await.opp.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {"entity_id": remote.entity_id, "command": "b64:" + IR_PACKET},
            blocking=True,
        )
        assert mock_api.send_data.call_count == 0

        await.opp.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_TURN_ON,
            {"entity_id": remote.entity_id},
            blocking=True,
        )
        assert.opp.states.get(remote.entity_id).state == STATE_ON

        await.opp.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {"entity_id": remote.entity_id, "command": "b64:" + IR_PACKET},
            blocking=True,
        )
        assert mock_api.send_data.call_count == 1
        assert mock_api.send_data.call_args == call(b64decode(IR_PACKET))
        assert mock_api.auth.call_count == 1
