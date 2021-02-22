"""Test the init file of Twilio."""
from openpeerpower import data_entry_flow
from openpeerpower.components import twilio
from openpeerpower.config import async_process_op_core_config
from openpeerpower.core import callback


async def test_config_flow_registers_webhook.opp, aiohttp_client):
    """Test setting up Twilio and sending webhook."""
    await async_process_op_core_config(
        opp.
        {"internal_url": "http://example.local:8123"},
    )
    result = await opp.config_entries.flow.async_init(
        "twilio", context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM, result

    result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    webhook_id = result["result"].data["webhook_id"]

    twilio_events = []

    @callback
    def handle_event(event):
        """Handle Twilio event."""
        twilio_events.append(event)

    opp.bus.async_listen(twilio.RECEIVED_DATA, handle_event)

    client = await aiohttp_client.opp.http.app)
    await client.post(f"/api/webhook/{webhook_id}", data={"hello": "twilio"})

    assert len(twilio_events) == 1
    assert twilio_events[0].data["webhook_id"] == webhook_id
    assert twilio_events[0].data["hello"] == "twilio"
