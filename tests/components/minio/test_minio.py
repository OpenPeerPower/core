"""Tests for Minio Hass related code."""
import asyncio
import json
from unittest.mock import MagicMock, call, patch

import pytest

from openpeerpower.components.minio import (
    CONF_ACCESS_KEY,
    CONF_HOST,
    CONF_LISTEN,
    CONF_LISTEN_BUCKET,
    CONF_PORT,
    CONF_SECRET_KEY,
    CONF_SECURE,
    DOMAIN,
    QueueListener,
)
from openpeerpower.core import callback
from openpeerpower.setup import async_setup_component

from tests.components.minio.common import TEST_EVENT


@pytest.fixture(name="minio_client")
def minio_client_fixture():
    """Patch Minio client."""
    with patch("openpeerpower.components.minio.minio_helper.Minio") as minio_mock:
        minio_client_mock = minio_mock.return_value

        yield minio_client_mock


@pytest.fixture(name="minio_client_event")
def minio_client_event_fixture():
    """Patch helper function for minio notification stream."""
    with patch("openpeerpower.components.minio.minio_helper.Minio") as minio_mock:
        minio_client_mock = minio_mock.return_value

        response_mock = MagicMock()
        stream_mock = MagicMock()

        stream_mock.__next__.side_effect = [
            "",
            "",
            bytearray(json.dumps(TEST_EVENT), "utf-8"),
        ]

        response_mock.stream.return_value = stream_mock
        minio_client_mock._url_open.return_value = response_mock

        yield minio_client_mock


async def test_minio_services.opp, caplog, minio_client):
    """Test Minio services."""
   .opp.config.allowlist_external_dirs = {"/test"}

    await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                CONF_HOST: "localhost",
                CONF_PORT: "9000",
                CONF_ACCESS_KEY: "abcdef",
                CONF_SECRET_KEY: "0123456789",
                CONF_SECURE: "true",
            }
        },
    )

    await.opp.async_start()
    await.opp.async_block_till_done()

    assert "Setup of domain minio took" in caplog.text

    # Call services
    await.opp.services.async_call(
        DOMAIN,
        "put",
        {"file_path": "/test/some_file", "key": "some_key", "bucket": "some_bucket"},
        blocking=True,
    )
    assert minio_client.fput_object.call_args == call(
        "some_bucket", "some_key", "/test/some_file"
    )
    minio_client.reset_mock()

    await.opp.services.async_call(
        DOMAIN,
        "get",
        {"file_path": "/test/some_file", "key": "some_key", "bucket": "some_bucket"},
        blocking=True,
    )
    assert minio_client.fget_object.call_args == call(
        "some_bucket", "some_key", "/test/some_file"
    )
    minio_client.reset_mock()

    await.opp.services.async_call(
        DOMAIN, "remove", {"key": "some_key", "bucket": "some_bucket"}, blocking=True
    )
    assert minio_client.remove_object.call_args == call("some_bucket", "some_key")
    minio_client.reset_mock()


async def test_minio_listen.opp, caplog, minio_client_event):
    """Test minio listen on notifications."""
    minio_client_event.presigned_get_object.return_value = "http://url"

    events = []

    @callback
    def event_callback(event):
        """Handle event callbback."""
        events.append(event)

   .opp.bus.async_listen("minio", event_callback)

    await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                CONF_HOST: "localhost",
                CONF_PORT: "9000",
                CONF_ACCESS_KEY: "abcdef",
                CONF_SECRET_KEY: "0123456789",
                CONF_SECURE: "true",
                CONF_LISTEN: [{CONF_LISTEN_BUCKET: "test"}],
            }
        },
    )

    await.opp.async_start()
    await.opp.async_block_till_done()

    assert "Setup of domain minio took" in caplog.text

    while not events:
        await asyncio.sleep(0)

    assert 1 == len(events)
    event = events[0]

    assert DOMAIN == event.event_type
    assert "s3:ObjectCreated:Put" == event.data["event_name"]
    assert "5jJkTAo.jpg" == event.data["file_name"]
    assert "test" == event.data["bucket"]
    assert "5jJkTAo.jpg" == event.data["key"]
    assert "http://url" == event.data["presigned_url"]
    assert 0 == len(event.data["metadata"])


async def test_queue_listener():
    """Tests QueueListener firing events on Open Peer Power event bus."""
    opp =MagicMock()

    queue_listener = QueueListener.opp)
    queue_listener.start()

    queue_entry = {
        "event_name": "s3:ObjectCreated:Put",
        "bucket": "some_bucket",
        "key": "some_dir/some_file.jpg",
        "presigned_url": "http://host/url?signature=secret",
        "metadata": {},
    }

    queue_listener.queue.put(queue_entry)

    queue_listener.stop()

    call_domain, call_event =.opp.bus.fire.call_args[0]

    expected_event = {
        "event_name": "s3:ObjectCreated:Put",
        "file_name": "some_file.jpg",
        "bucket": "some_bucket",
        "key": "some_dir/some_file.jpg",
        "presigned_url": "http://host/url?signature=secret",
        "metadata": {},
    }

    assert DOMAIN == call_domain
    assert json.dumps(expected_event, sort_keys=True) == json.dumps(
        call_event, sort_keys=True
    )
