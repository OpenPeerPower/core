"""Test HTML5 notify platform."""
import json
from unittest.mock import MagicMock, mock_open, patch

from aiohttp.hdrs import AUTHORIZATION

import openpeerpower.components.html5.notify as html5
from openpeerpower.const import HTTP_INTERNAL_SERVER_ERROR
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.setup import async_setup_component

CONFIG_FILE = "file.conf"

VAPID_CONF = {
    "vapid_pub_key": "BJMA2gDZEkHaXRhf1fhY_"
    + "QbKbhVIHlSJXI0bFyo0eJXnUPOjdgycCAbj-2bMKMKNKs"
    + "_rM8JoSnyKGCXAY2dbONI",
    "vapid_prv_key": "ZwPgwKpESGuGLMZYU39vKgrekrWzCijo-LsBM3CZ9-c",
    "vapid_email": "someone@example.com",
}

SUBSCRIPTION_1 = {
    "browser": "chrome",
    "subscription": {
        "endpoint": "https://googleapis.com",
        "keys": {"auth": "auth", "p256dh": "p256dh"},
    },
}
SUBSCRIPTION_2 = {
    "browser": "firefox",
    "subscription": {
        "endpoint": "https://example.com",
        "keys": {"auth": "bla", "p256dh": "bla"},
    },
}
SUBSCRIPTION_3 = {
    "browser": "chrome",
    "subscription": {
        "endpoint": "https://example.com/not_exist",
        "keys": {"auth": "bla", "p256dh": "bla"},
    },
}
SUBSCRIPTION_4 = {
    "browser": "chrome",
    "subscription": {
        "endpoint": "https://googleapis.com",
        "expirationTime": None,
        "keys": {"auth": "auth", "p256dh": "p256dh"},
    },
}

SUBSCRIPTION_5 = {
    "browser": "chrome",
    "subscription": {
        "endpoint": "https://fcm.googleapis.com/fcm/send/LONG-RANDOM-KEY",
        "expirationTime": None,
        "keys": {"auth": "auth", "p256dh": "p256dh"},
    },
}

REGISTER_URL = "/api/notify.html5"
PUBLISH_URL = "/api/notify.html5/callback"


async def mock_client.opp, opp_client, registrations=None):
    """Create a test client for HTML5 views."""
    if registrations is None:
        registrations = {}

    with patch(
        "openpeerpower.components.html5.notify._load_config", return_value=registrations
    ):
        await async_setup_component.opp, "notify", {"notify": {"platform": "html5"}})
        await opp.async_block_till_done()

    return await opp_client()


class TestHtml5Notify:
    """Tests for HTML5 notify platform."""

    def test_get_service_with_no_json(self):
        """Test empty json file."""
        opp.=MagicMock()

        m = mock_open()
        with patch("openpeerpower.util.json.open", m, create=True):
            service = html5.get_service.opp, {})

        assert service is not None

    @patch("openpeerpower.components.html5.notify.WebPusher")
    def test_dismissing_message(self, mock_wp):
        """Test dismissing message."""
        opp.=MagicMock()

        data = {"device": SUBSCRIPTION_1}

        m = mock_open(read_data=json.dumps(data))
        with patch("openpeerpower.util.json.open", m, create=True):
            service = html5.get_service.opp, {"gcm_sender_id": "100"})

        assert service is not None

        service.dismiss(target=["device", "non_existing"], data={"tag": "test"})

        assert len(mock_wp.mock_calls) == 3

        # WebPusher constructor
        assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_1["subscription"]
        # Third mock_call checks the status_code of the response.
        assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"

        # Call to send
        payload = json.loads(mock_wp.mock_calls[1][1][0])

        assert payload["dismiss"] is True
        assert payload["tag"] == "test"

    @patch("openpeerpower.components.html5.notify.WebPusher")
    def test_sending_message(self, mock_wp):
        """Test sending message."""
        opp.=MagicMock()

        data = {"device": SUBSCRIPTION_1}

        m = mock_open(read_data=json.dumps(data))
        with patch("openpeerpower.util.json.open", m, create=True):
            service = html5.get_service.opp, {"gcm_sender_id": "100"})

        assert service is not None

        service.send_message(
            "Hello", target=["device", "non_existing"], data={"icon": "beer.png"}
        )

        assert len(mock_wp.mock_calls) == 3

        # WebPusher constructor
        assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_1["subscription"]
        # Third mock_call checks the status_code of the response.
        assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"

        # Call to send
        payload = json.loads(mock_wp.mock_calls[1][1][0])

        assert payload["body"] == "Hello"
        assert payload["icon"] == "beer.png"

    @patch("openpeerpower.components.html5.notify.WebPusher")
    def test_gcm_key_include(self, mock_wp):
        """Test if the gcm_key is only included for GCM endpoints."""
        opp.=MagicMock()

        data = {"chrome": SUBSCRIPTION_1, "firefox": SUBSCRIPTION_2}

        m = mock_open(read_data=json.dumps(data))
        with patch("openpeerpower.util.json.open", m, create=True):
            service = html5.get_service(
                opp. {"gcm_sender_id": "100", "gcm_api_key": "Y6i0JdZ0mj9LOaSI"}
            )

        assert service is not None

        service.send_message("Hello", target=["chrome", "firefox"])

        assert len(mock_wp.mock_calls) == 6

        # WebPusher constructor
        assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_1["subscription"]
        assert mock_wp.mock_calls[3][1][0] == SUBSCRIPTION_2["subscription"]

        # Third mock_call checks the status_code of the response.
        assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"
        assert mock_wp.mock_calls[5][0] == "().send().status_code.__eq__"

        # Get the keys passed to the WebPusher's send method
        assert mock_wp.mock_calls[1][2]["gcm_key"] is not None
        assert mock_wp.mock_calls[4][2]["gcm_key"] is None

    @patch("openpeerpower.components.html5.notify.WebPusher")
    def test_fcm_key_include(self, mock_wp):
        """Test if the FCM header is included."""
        opp.=MagicMock()

        data = {"chrome": SUBSCRIPTION_5}

        m = mock_open(read_data=json.dumps(data))
        with patch("openpeerpower.util.json.open", m, create=True):
            service = html5.get_service.opp, VAPID_CONF)

        assert service is not None

        service.send_message("Hello", target=["chrome"])

        assert len(mock_wp.mock_calls) == 3
        # WebPusher constructor
        assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_5["subscription"]

        # Third mock_call checks the status_code of the response.
        assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"

        # Get the keys passed to the WebPusher's send method
        assert mock_wp.mock_calls[1][2]["headers"]["Authorization"] is not None

    @patch("openpeerpower.components.html5.notify.WebPusher")
    def test_fcm_send_with_unknown_priority(self, mock_wp):
        """Test if the gcm_key is only included for GCM endpoints."""
        opp.=MagicMock()

        data = {"chrome": SUBSCRIPTION_5}

        m = mock_open(read_data=json.dumps(data))
        with patch("openpeerpower.util.json.open", m, create=True):
            service = html5.get_service.opp, VAPID_CONF)

        assert service is not None

        service.send_message("Hello", target=["chrome"], priority="undefined")

        assert len(mock_wp.mock_calls) == 3
        # WebPusher constructor
        assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_5["subscription"]

        # Third mock_call checks the status_code of the response.
        assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"

        # Get the keys passed to the WebPusher's send method
        assert mock_wp.mock_calls[1][2]["headers"]["priority"] == "normal"

    @patch("openpeerpower.components.html5.notify.WebPusher")
    def test_fcm_no_targets(self, mock_wp):
        """Test if the gcm_key is only included for GCM endpoints."""
        opp.=MagicMock()

        data = {"chrome": SUBSCRIPTION_5}

        m = mock_open(read_data=json.dumps(data))
        with patch("openpeerpower.util.json.open", m, create=True):
            service = html5.get_service.opp, VAPID_CONF)

        assert service is not None

        service.send_message("Hello")

        assert len(mock_wp.mock_calls) == 3
        # WebPusher constructor
        assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_5["subscription"]

        # Third mock_call checks the status_code of the response.
        assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"

        # Get the keys passed to the WebPusher's send method
        assert mock_wp.mock_calls[1][2]["headers"]["priority"] == "normal"

    @patch("openpeerpower.components.html5.notify.WebPusher")
    def test_fcm_additional_data(self, mock_wp):
        """Test if the gcm_key is only included for GCM endpoints."""
        opp.=MagicMock()

        data = {"chrome": SUBSCRIPTION_5}

        m = mock_open(read_data=json.dumps(data))
        with patch("openpeerpower.util.json.open", m, create=True):
            service = html5.get_service.opp, VAPID_CONF)

        assert service is not None

        service.send_message("Hello", data={"mykey": "myvalue"})

        assert len(mock_wp.mock_calls) == 3
        # WebPusher constructor
        assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_5["subscription"]

        # Third mock_call checks the status_code of the response.
        assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"

        # Get the keys passed to the WebPusher's send method
        assert mock_wp.mock_calls[1][2]["headers"]["priority"] == "normal"


def test_create_vapid_withoutvapid():
    """Test creating empty vapid."""
    resp = html5.create_vapid_headers(
        vapid_email=None, vapid_private_key=None, subscription_info=None
    )
    assert resp is None


async def test_registering_new_device_view.opp, opp_client):
    """Test that the HTML view works."""
    client = await mock_client.opp, opp_client)

    with patch("openpeerpower.components.html5.notify.save_json") as mock_save:
        resp = await client.post(REGISTER_URL, data=json.dumps(SUBSCRIPTION_1))

    assert resp.status == 200
    assert len(mock_save.mock_calls) == 1
    assert mock_save.mock_calls[0][1][1] == {"unnamed device": SUBSCRIPTION_1}


async def test_registering_new_device_view_with_name.opp, opp_client):
    """Test that the HTML view works with name attribute."""
    client = await mock_client.opp, opp_client)

    SUB_WITH_NAME = SUBSCRIPTION_1.copy()
    SUB_WITH_NAME["name"] = "test device"

    with patch("openpeerpower.components.html5.notify.save_json") as mock_save:
        resp = await client.post(REGISTER_URL, data=json.dumps(SUB_WITH_NAME))

    assert resp.status == 200
    assert len(mock_save.mock_calls) == 1
    assert mock_save.mock_calls[0][1][1] == {"test device": SUBSCRIPTION_1}


async def test_registering_new_device_expiration_view.opp, opp_client):
    """Test that the HTML view works."""
    client = await mock_client.opp, opp_client)

    with patch("openpeerpower.components.html5.notify.save_json") as mock_save:
        resp = await client.post(REGISTER_URL, data=json.dumps(SUBSCRIPTION_4))

    assert resp.status == 200
    assert mock_save.mock_calls[0][1][1] == {"unnamed device": SUBSCRIPTION_4}


async def test_registering_new_device_fails_view.opp, opp_client):
    """Test subs. are not altered when registering a new device fails."""
    registrations = {}
    client = await mock_client.opp, opp_client, registrations)

    with patch(
        "openpeerpower.components.html5.notify.save_json",
        side_effect=OpenPeerPowerError(),
    ):
        resp = await client.post(REGISTER_URL, data=json.dumps(SUBSCRIPTION_4))

    assert resp.status == HTTP_INTERNAL_SERVER_ERROR
    assert registrations == {}


async def test_registering_existing_device_view.opp, opp_client):
    """Test subscription is updated when registering existing device."""
    registrations = {}
    client = await mock_client.opp, opp_client, registrations)

    with patch("openpeerpower.components.html5.notify.save_json") as mock_save:
        await client.post(REGISTER_URL, data=json.dumps(SUBSCRIPTION_1))
        resp = await client.post(REGISTER_URL, data=json.dumps(SUBSCRIPTION_4))

    assert resp.status == 200
    assert mock_save.mock_calls[0][1][1] == {"unnamed device": SUBSCRIPTION_4}
    assert registrations == {"unnamed device": SUBSCRIPTION_4}


async def test_registering_existing_device_view_with_name.opp, opp_client):
    """Test subscription is updated when reg'ing existing device with name."""
    registrations = {}
    client = await mock_client.opp, opp_client, registrations)

    SUB_WITH_NAME = SUBSCRIPTION_1.copy()
    SUB_WITH_NAME["name"] = "test device"

    with patch("openpeerpower.components.html5.notify.save_json") as mock_save:
        await client.post(REGISTER_URL, data=json.dumps(SUB_WITH_NAME))
        resp = await client.post(REGISTER_URL, data=json.dumps(SUBSCRIPTION_4))

    assert resp.status == 200
    assert mock_save.mock_calls[0][1][1] == {"test device": SUBSCRIPTION_4}
    assert registrations == {"test device": SUBSCRIPTION_4}


async def test_registering_existing_device_fails_view.opp, opp_client):
    """Test sub. is not updated when registering existing device fails."""
    registrations = {}
    client = await mock_client.opp, opp_client, registrations)

    with patch("openpeerpower.components.html5.notify.save_json") as mock_save:
        await client.post(REGISTER_URL, data=json.dumps(SUBSCRIPTION_1))
        mock_save.side_effect = OpenPeerPowerError
        resp = await client.post(REGISTER_URL, data=json.dumps(SUBSCRIPTION_4))

    assert resp.status == HTTP_INTERNAL_SERVER_ERROR
    assert registrations == {"unnamed device": SUBSCRIPTION_1}


async def test_registering_new_device_validation.opp, opp_client):
    """Test various errors when registering a new device."""
    client = await mock_client.opp, opp_client)

    resp = await client.post(
        REGISTER_URL,
        data=json.dumps({"browser": "invalid browser", "subscription": "sub info"}),
    )
    assert resp.status == 400

    resp = await client.post(REGISTER_URL, data=json.dumps({"browser": "chrome"}))
    assert resp.status == 400

    with patch("openpeerpower.components.html5.notify.save_json", return_value=False):
        resp = await client.post(
            REGISTER_URL,
            data=json.dumps({"browser": "chrome", "subscription": "sub info"}),
        )
    assert resp.status == 400


async def test_unregistering_device_view.opp, opp_client):
    """Test that the HTML unregister view works."""
    registrations = {"some device": SUBSCRIPTION_1, "other device": SUBSCRIPTION_2}
    client = await mock_client.opp, opp_client, registrations)

    with patch("openpeerpower.components.html5.notify.save_json") as mock_save:
        resp = await client.delete(
            REGISTER_URL,
            data=json.dumps({"subscription": SUBSCRIPTION_1["subscription"]}),
        )

    assert resp.status == 200
    assert len(mock_save.mock_calls) == 1
    assert registrations == {"other device": SUBSCRIPTION_2}


async def test_unregister_device_view_handle_unknown_subscription.opp, opp_client):
    """Test that the HTML unregister view handles unknown subscriptions."""
    registrations = {}
    client = await mock_client.opp, opp_client, registrations)

    with patch("openpeerpower.components.html5.notify.save_json") as mock_save:
        resp = await client.delete(
            REGISTER_URL,
            data=json.dumps({"subscription": SUBSCRIPTION_3["subscription"]}),
        )

    assert resp.status == 200, resp.response
    assert registrations == {}
    assert len(mock_save.mock_calls) == 0


async def test_unregistering_device_view_handles_save_error(opp, opp_client):
    """Test that the HTML unregister view handles save errors."""
    registrations = {"some device": SUBSCRIPTION_1, "other device": SUBSCRIPTION_2}
    client = await mock_client.opp, opp_client, registrations)

    with patch(
        "openpeerpower.components.html5.notify.save_json",
        side_effect=OpenPeerPowerError(),
    ):
        resp = await client.delete(
            REGISTER_URL,
            data=json.dumps({"subscription": SUBSCRIPTION_1["subscription"]}),
        )

    assert resp.status == HTTP_INTERNAL_SERVER_ERROR, resp.response
    assert registrations == {
        "some device": SUBSCRIPTION_1,
        "other device": SUBSCRIPTION_2,
    }


async def test_callback_view_no_jwt.opp, opp_client):
    """Test that the notification callback view works without JWT."""
    client = await mock_client.opp, opp_client)
    resp = await client.post(
        PUBLISH_URL,
        data=json.dumps(
            {"type": "push", "tag": "3bc28d69-0921-41f1-ac6a-7a627ba0aa72"}
        ),
    )

    assert resp.status == 401


async def test_callback_view_with_jwt.opp, opp_client):
    """Test that the notification callback view works with JWT."""
    registrations = {"device": SUBSCRIPTION_1}
    client = await mock_client.opp, opp_client, registrations)

    with patch("openpeerpower.components.html5.notify.WebPusher") as mock_wp:
        await opp.services.async_call(
            "notify",
            "notify",
            {"message": "Hello", "target": ["device"], "data": {"icon": "beer.png"}},
            blocking=True,
        )

    assert len(mock_wp.mock_calls) == 3

    # WebPusher constructor
    assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_1["subscription"]
    # Third mock_call checks the status_code of the response.
    assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"

    # Call to send
    push_payload = json.loads(mock_wp.mock_calls[1][1][0])

    assert push_payload["body"] == "Hello"
    assert push_payload["icon"] == "beer.png"

    bearer_token = "Bearer {}".format(push_payload["data"]["jwt"])

    resp = await client.post(
        PUBLISH_URL, json={"type": "push"}, headers={AUTHORIZATION: bearer_token}
    )

    assert resp.status == 200
    body = await resp.json()
    assert body == {"event": "push", "status": "ok"}


async def test_send_fcm_without_targets.opp, opp_client):
    """Test that the notification is send with FCM without targets."""
    registrations = {"device": SUBSCRIPTION_5}
    await mock_client.opp, opp_client, registrations)
    with patch("openpeerpower.components.html5.notify.WebPusher") as mock_wp:
        await opp.services.async_call(
            "notify",
            "notify",
            {"message": "Hello", "target": ["device"], "data": {"icon": "beer.png"}},
            blocking=True,
        )

    assert len(mock_wp.mock_calls) == 3

    # WebPusher constructor
    assert mock_wp.mock_calls[0][1][0] == SUBSCRIPTION_5["subscription"]
    # Third mock_call checks the status_code of the response.
    assert mock_wp.mock_calls[2][0] == "().send().status_code.__eq__"
