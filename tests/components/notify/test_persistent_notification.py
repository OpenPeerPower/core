"""The tests for the notify.persistent_notification service."""
from openpeerpower.components import notify
import openpeerpower.components.persistent_notification as pn
from openpeerpower.core import OpenPeerPower
from openpeerpower.setup import async_setup_component


async def test_async_send_message.opp: OpenPeerPower):
    """Test sending a message to notify.persistent_notification service."""
    await async_setup_component.opp, pn.DOMAIN, {"core": {}})
    await async_setup_component.opp, notify.DOMAIN, {})
    await.opp.async_block_till_done()

    message = {"message": "Hello", "title": "Test notification"}
    await.opp.services.async_call(
        notify.DOMAIN, notify.SERVICE_PERSISTENT_NOTIFICATION, message
    )
    await.opp.async_block_till_done()

    entity_ids = opp.states.async_entity_ids(pn.DOMAIN)
    assert len(entity_ids) == 1

    state = opp.states.get(entity_ids[0])
    assert state.attributes.get("message") == "Hello"
    assert state.attributes.get("title") == "Test notification"
