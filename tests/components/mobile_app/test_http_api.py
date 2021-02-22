"""Tests for the mobile_app HTTP API."""
import json
from unittest.mock import patch

import pytest

from openpeerpower.components.mobile_app.const import CONF_SECRET, DOMAIN
from openpeerpower.const import CONF_WEBHOOK_ID
from openpeerpower.setup import async_setup_component

from .const import REGISTER, REGISTER_CLEARTEXT, RENDER_TEMPLATE

from tests.common import mock_coro


async def test_registration.opp,.opp_client,.opp_admin_user):
    """Test that registrations happen."""
    await async_setup_component.opp, DOMAIN, {DOMAIN: {}})

    api_client = await.opp_client()

    with patch(
        "openpeerpower.components.person.async_add_user_device_tracker",
        spec=True,
        return_value=mock_coro(),
    ) as add_user_dev_track:
        resp = await api_client.post(
            "/api/mobile_app/registrations", json=REGISTER_CLEARTEXT
        )

    assert len(add_user_dev_track.mock_calls) == 1
    assert add_user_dev_track.mock_calls[0][1][1] ==.opp_admin_user.id
    assert add_user_dev_track.mock_calls[0][1][2] == "device_tracker.test_1"

    assert resp.status == 201
    register_json = await resp.json()
    assert CONF_WEBHOOK_ID in register_json
    assert CONF_SECRET in register_json

    entries = opp.config_entries.async_entries(DOMAIN)

    assert entries[0].unique_id == "io.openpeerpower.mobile_app_test-mock-device-id"
    assert entries[0].data["device_id"] == REGISTER_CLEARTEXT["device_id"]
    assert entries[0].data["app_data"] == REGISTER_CLEARTEXT["app_data"]
    assert entries[0].data["app_id"] == REGISTER_CLEARTEXT["app_id"]
    assert entries[0].data["app_name"] == REGISTER_CLEARTEXT["app_name"]
    assert entries[0].data["app_version"] == REGISTER_CLEARTEXT["app_version"]
    assert entries[0].data["device_name"] == REGISTER_CLEARTEXT["device_name"]
    assert entries[0].data["manufacturer"] == REGISTER_CLEARTEXT["manufacturer"]
    assert entries[0].data["model"] == REGISTER_CLEARTEXT["model"]
    assert entries[0].data["os_name"] == REGISTER_CLEARTEXT["os_name"]
    assert entries[0].data["os_version"] == REGISTER_CLEARTEXT["os_version"]
    assert (
        entries[0].data["supports_encryption"]
        == REGISTER_CLEARTEXT["supports_encryption"]
    )


async def test_registration_encryption.opp,.opp_client):
    """Test that registrations happen."""
    try:
        from nacl.encoding import Base64Encoder
        from nacl.secret import SecretBox
    except (ImportError, OSError):
        pytest.skip("libnacl/libsodium is not installed")
        return

    await async_setup_component.opp, DOMAIN, {DOMAIN: {}})

    api_client = await.opp_client()

    resp = await api_client.post("/api/mobile_app/registrations", json=REGISTER)

    assert resp.status == 201
    register_json = await resp.json()

    keylen = SecretBox.KEY_SIZE
    key = register_json[CONF_SECRET].encode("utf-8")
    key = key[:keylen]
    key = key.ljust(keylen, b"\0")

    payload = json.dumps(RENDER_TEMPLATE["data"]).encode("utf-8")

    data = SecretBox(key).encrypt(payload, encoder=Base64Encoder).decode("utf-8")

    container = {"type": "render_template", "encrypted": True, "encrypted_data": data}

    resp = await api_client.post(
        "/api/webhook/{}".format(register_json[CONF_WEBHOOK_ID]), json=container
    )

    assert resp.status == 200

    webhook_json = await resp.json()
    assert "encrypted_data" in webhook_json

    decrypted_data = SecretBox(key).decrypt(
        webhook_json["encrypted_data"], encoder=Base64Encoder
    )
    decrypted_data = decrypted_data.decode("utf-8")

    assert json.loads(decrypted_data) == {"one": "Hello world"}
