"""The tests for Mobile App device actions."""
from openpeerpower.components import automation, device_automation
from openpeerpower.components.mobile_app import DATA_DEVICES, DOMAIN, util
from openpeerpower.setup import async_setup_component

from tests.common import async_get_device_automations, patch


async def test_get_actions.opp, push_registration):
    """Test we get the expected actions from a mobile_app."""
    webhook_id = push_registration["webhook_id"]
    device_id = opp.data[DOMAIN][DATA_DEVICES][webhook_id].id

    assert await async_get_device_automations.opp, "action", device_id) == [
        {"domain": DOMAIN, "device_id": device_id, "type": "notify"}
    ]

    capabilitites = await device_automation._async_get_device_automation_capabilities(
       .opp, "action", {"domain": DOMAIN, "device_id": device_id, "type": "notify"}
    )
    assert "extra_fields" in capabilitites


async def test_action.opp, push_registration):
    """Test for turn_on and turn_off actions."""
    webhook_id = push_registration["webhook_id"]

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_notify",
                    },
                    "action": [
                        {"variables": {"name": "Paulus"}},
                        {
                            "domain": DOMAIN,
                            "device_id":.opp.data[DOMAIN]["devices"][webhook_id].id,
                            "type": "notify",
                            "message": "Hello {{ name }}",
                        },
                    ],
                },
            ]
        },
    )

    service_name = util.get_notify_service.opp, webhook_id)

    # Make sure it was actually registered
    assert.opp.services.has_service("notify", service_name)

    with patch(
        "openpeerpower.components.mobile_app.notify.MobileAppNotificationService.async_send_message"
    ) as mock_send_message:
       .opp.bus.async_fire("test_notify")
        await opp.async_block_till_done()
        assert len(mock_send_message.mock_calls) == 1

    assert mock_send_message.mock_calls[0][2] == {
        "target": [webhook_id],
        "message": "Hello Paulus",
        "data": None,
    }
