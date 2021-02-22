"""Mockup Nuki device."""
from openpeerpower import setup

from tests.common import MockConfigEntry

NAME = "Nuki_Bridge_75BCD15"
HOST = "1.1.1.1"
MAC = "01:23:45:67:89:ab"

HW_ID = 123456789

MOCK_INFO = {"ids": {"hardwareId": HW_ID}}


async def setup_nuki_integration.opp):
    """Create the Nuki device."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    entry = MockConfigEntry(
        domain="nuki",
        unique_id=HW_ID,
        data={"host": HOST, "port": 8080, "token": "test-token"},
    )
    entry.add_to.opp.opp)

    return entry
