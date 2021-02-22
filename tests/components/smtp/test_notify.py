"""The tests for the notify smtp platform."""
from os import path
import re
from unittest.mock import patch

import pytest

from openpeerpower import config as.opp_config
import openpeerpower.components.notify as notify
from openpeerpower.components.smtp import DOMAIN
from openpeerpower.components.smtp.notify import MailNotificationService
from openpeerpower.const import SERVICE_RELOAD
from openpeerpower.setup import async_setup_component


class MockSMTP(MailNotificationService):
    """Test SMTP object that doesn't need a working server."""

    def _send_email(self, msg):
        """Just return string for testing."""
        return msg.as_string()


async def test_reload_notify.opp):
    """Verify we can reload the notify service."""

    with patch(
        "openpeerpower.components.smtp.notify.MailNotificationService.connection_is_valid"
    ):
        assert await async_setup_component(
            opp.
            notify.DOMAIN,
            {
                notify.DOMAIN: [
                    {
                        "name": DOMAIN,
                        "platform": DOMAIN,
                        "recipient": "test@example.com",
                        "sender": "test@example.com",
                    },
                ]
            },
        )
        await opp.async_block_till_done()

    assert.opp.services.has_service(notify.DOMAIN, DOMAIN)

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "smtp/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path), patch(
        "openpeerpower.components.smtp.notify.MailNotificationService.connection_is_valid"
    ):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert not.opp.services.has_service(notify.DOMAIN, DOMAIN)
    assert.opp.services.has_service(notify.DOMAIN, "smtp_reloaded")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))


@pytest.fixture
def message():
    """Return MockSMTP object with test data."""
    mailer = MockSMTP(
        "localhost",
        25,
        5,
        "test@test.com",
        1,
        "testuser",
        "testpass",
        ["recip1@example.com", "testrecip@test.com"],
        "Open Peer Power",
        0,
    )
    yield mailer


HTML = """
        <!DOCTYPE html>
        <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <head><meta charset="UTF-8"></head>
            <body>
              <div>
                <h1>Intruder alert at apartment!!</h1>
              </div>
              <div>
                <img alt="tests/testing_config/notify/test.jpg" src="cid:tests/testing_config/notify/test.jpg"/>
              </div>
            </body>
        </html>"""


EMAIL_DATA = [
    (
        "Test msg",
        {"images": ["tests/testing_config/notify/test.jpg"]},
        "Content-Type: multipart/related",
    ),
    (
        "Test msg",
        {"html": HTML, "images": ["tests/testing_config/notify/test.jpg"]},
        "Content-Type: multipart/related",
    ),
    (
        "Test msg",
        {"html": HTML, "images": ["test.jpg"]},
        "Content-Type: multipart/related",
    ),
    (
        "Test msg",
        {"html": HTML, "images": ["tests/testing_config/notify/test.pdf"]},
        "Content-Type: multipart/related",
    ),
]


@pytest.mark.parametrize(
    "message_data, data, content_type",
    EMAIL_DATA,
    ids=[
        "Tests when sending text message and images.",
        "Tests when sending text message, HTML Template and images.",
        "Tests when image does not exist at mentioned location.",
        "Tests when image type cannot be detected or is of wrong type.",
    ],
)
def test_send_message(message_data, data, content_type, opp, message):
    """Verify if we can send messages of all types correctly."""
    sample_email = "<mock@mock>"
    with patch("email.utils.make_msgid", return_value=sample_email):
        result = message.send_message(message_data, data=data)
        assert content_type in result


def test_send_text_message.opp, message):
    """Verify if we can send simple text message."""
    expected = (
        '^Content-Type: text/plain; charset="us-ascii"\n'
        "MIME-Version: 1.0\n"
        "Content-Transfer-Encoding: 7bit\n"
        "Subject: Open Peer Power\n"
        "To: recip1@example.com,testrecip@test.com\n"
        "From: Open Peer Power <test@test.com>\n"
        "X-Mailer: Open Peer Power\n"
        "Date: [^\n]+\n"
        "Message-Id: <[^@]+@[^>]+>\n"
        "\n"
        "Test msg$"
    )
    sample_email = "<mock@mock>"
    message_data = "Test msg"
    with patch("email.utils.make_msgid", return_value=sample_email):
        result = message.send_message(message_data)
        assert re.search(expected, result)
