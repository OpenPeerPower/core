"""Tests for tag triggers."""

import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.tag import async_scan_tag
from openpeerpower.components.tag.const import DEVICE_ID, DOMAIN, TAG_ID
from openpeerpower.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF
from openpeerpowerr.setup import async_setup_component

from tests.common import async_mock_service
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def tag_setup.opp,.opp_storage):
    """Tag setup."""

    async def _storage(items=None):
        if items is None:
           .opp_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": [{"id": "test tag"}]},
            }
        else:
           .opp_storage[DOMAIN] = items
        config = {DOMAIN: {}}
        return await async_setup_component.opp, DOMAIN, config)

    return _storage


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service.opp, "test", "automation")


async def test_triggers.opp, tag_setup, calls):
    """Test tag triggers."""
    assert await tag_setup()
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "alias": "test",
                    "trigger": {"platform": DOMAIN, TAG_ID: "abc123"},
                    "action": {
                        "service": "test.automation",
                        "data": {"message": "service called"},
                    },
                }
            ]
        },
    )

    await.opp.async_block_till_done()

    await async_scan_tag.opp, "abc123", None)
    await.opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data["message"] == "service called"

    await.opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "automation.test"},
        blocking=True,
    )

    await async_scan_tag.opp, "abc123", None)
    await.opp.async_block_till_done()

    assert len(calls) == 1


async def test_exception_bad_trigger.opp, calls, caplog):
    """Test for exception on event triggers firing."""

    await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"trigger": {"platform": DOMAIN, "oops": "abc123"}},
                    "action": {
                        "service": "test.automation",
                        "data": {"message": "service called"},
                    },
                }
            ]
        },
    )
    await.opp.async_block_till_done()
    assert "Invalid config for [automation]" in caplog.text


async def test_multiple_tags_and_devices_trigger.opp, tag_setup, calls):
    """Test multiple tags and devices triggers."""
    assert await tag_setup()
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": DOMAIN,
                        TAG_ID: ["abc123", "def456"],
                        DEVICE_ID: ["ghi789", "jkl0123"],
                    },
                    "action": {
                        "service": "test.automation",
                        "data": {"message": "service called"},
                    },
                }
            ]
        },
    )

    await.opp.async_block_till_done()

    # Should not trigger
    await async_scan_tag.opp, tag_id="abc123", device_id=None)
    await async_scan_tag.opp, tag_id="abc123", device_id="invalid")
    await.opp.async_block_till_done()

    # Should trigger
    await async_scan_tag.opp, tag_id="abc123", device_id="ghi789")
    await.opp.async_block_till_done()
    await async_scan_tag.opp, tag_id="abc123", device_id="jkl0123")
    await.opp.async_block_till_done()
    await async_scan_tag.opp, "def456", device_id="ghi789")
    await.opp.async_block_till_done()
    await async_scan_tag.opp, "def456", device_id="jkl0123")
    await.opp.async_block_till_done()

    assert len(calls) == 4
    assert calls[0].data["message"] == "service called"
    assert calls[1].data["message"] == "service called"
    assert calls[2].data["message"] == "service called"
    assert calls[3].data["message"] == "service called"
