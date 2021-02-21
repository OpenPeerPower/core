"""The tests for the notify.group platform."""
from os import path
from unittest.mock import MagicMock, patch

from openpeerpower import config as.opp_config
import openpeerpower.components.demo.notify as demo
from openpeerpower.components.group import SERVICE_RELOAD
import openpeerpower.components.group.notify as group
import openpeerpower.components.notify as notify
from openpeerpowerr.setup import async_setup_component


async def test_send_message_with_data.opp):
    """Test sending a message with to a notify group."""
    service1 = demo.DemoNotificationService.opp)
    service2 = demo.DemoNotificationService.opp)

    service1.send_message = MagicMock(autospec=True)
    service2.send_message = MagicMock(autospec=True)

    def mock_get_service.opp, config, discovery_info=None):
        if config["name"] == "demo1":
            return service1
        return service2

    assert await async_setup_component(
       .opp,
        "group",
        {},
    )
    await opp.async_block_till_done()

    with patch.object(demo, "get_service", mock_get_service):
        await async_setup_component(
           .opp,
            notify.DOMAIN,
            {
                "notify": [
                    {"name": "demo1", "platform": "demo"},
                    {"name": "demo2", "platform": "demo"},
                ]
            },
        )
        await opp.async_block_till_done()

    service = await group.async_get_service(
       .opp,
        {
            "services": [
                {"service": "demo1"},
                {
                    "service": "demo2",
                    "data": {
                        "target": "unnamed device",
                        "data": {"test": "message"},
                    },
                },
            ]
        },
    )

    """Test sending a message with to a notify group."""
    await service.async_send_message(
        "Hello", title="Test notification", data={"hello": "world"}
    )

    await opp.async_block_till_done()

    assert service1.send_message.mock_calls[0][1][0] == "Hello"
    assert service1.send_message.mock_calls[0][2] == {
        "title": "Test notification",
        "data": {"hello": "world"},
    }
    assert service2.send_message.mock_calls[0][1][0] == "Hello"
    assert service2.send_message.mock_calls[0][2] == {
        "target": ["unnamed device"],
        "title": "Test notification",
        "data": {"hello": "world", "test": "message"},
    }


async def test_reload_notify.opp):
    """Verify we can reload the notify service."""

    assert await async_setup_component(
       .opp,
        "group",
        {},
    )
    await opp.async_block_till_done()

    assert await async_setup_component(
       .opp,
        notify.DOMAIN,
        {
            notify.DOMAIN: [
                {"name": "demo1", "platform": "demo"},
                {"name": "demo2", "platform": "demo"},
                {
                    "name": "group_notify",
                    "platform": "group",
                    "services": [{"service": "demo1"}],
                },
            ]
        },
    )
    await opp.async_block_till_done()

    assert.opp.services.has_service(notify.DOMAIN, "demo1")
    assert.opp.services.has_service(notify.DOMAIN, "demo2")
    assert.opp.services.has_service(notify.DOMAIN, "group_notify")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "group/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await.opp.services.async_call(
            "group",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert.opp.services.has_service(notify.DOMAIN, "demo1")
    assert.opp.services.has_service(notify.DOMAIN, "demo2")
    assert not.opp.services.has_service(notify.DOMAIN, "group_notify")
    assert.opp.services.has_service(notify.DOMAIN, "new_group_notify")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
