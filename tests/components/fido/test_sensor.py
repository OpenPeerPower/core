"""The test for the fido sensor platform."""
import logging
from unittest.mock import MagicMock, patch

from pyfido.client import PyFidoError

from openpeerpower.bootstrap import async_setup_component
from openpeerpower.components.fido import sensor as fido

from tests.common import assert_setup_component

CONTRACT = "123456789"


class FidoClientMock:
    """Fake Fido client."""

    def __init__(self, username, password, timeout=None, httpsession=None):
        """Fake Fido client init."""
        pass

    def get_phone_numbers(self):
        """Return Phone numbers."""
        return ["1112223344"]

    def get_data(self):
        """Return fake fido data."""
        return {"balance": 160.12, "1112223344": {"data_remaining": 100.33}}

    async def fetch_data(self):
        """Return fake fetching data."""
        pass


class FidoClientMockError(FidoClientMock):
    """Fake Fido client error."""

    async def fetch_data(self):
        """Return fake fetching data."""
        raise PyFidoError("Fake Error")


async def test_fido_sensor(loop, opp):
    """Test the Fido number sensor."""
    with patch("openpeerpower.components.fido.sensor.FidoClient", new=FidoClientMock):
        config = {
            "sensor": {
                "platform": "fido",
                "name": "fido",
                "username": "myusername",
                "password": "password",
                "monitored_variables": ["balance", "data_remaining"],
            }
        }
        with assert_setup_component(1):
            await async_setup_component.opp, "sensor", config)
            await.opp.async_block_till_done()
        state =.opp.states.get("sensor.fido_1112223344_balance")
        assert state.state == "160.12"
        assert state.attributes.get("number") == "1112223344"
        state =.opp.states.get("sensor.fido_1112223344_data_remaining")
        assert state.state == "100.33"


async def test_error(opp, caplog):
    """Test the Fido sensor errors."""
    caplog.set_level(logging.ERROR)

    config = {}
    fake_async_add_entities = MagicMock()
    with patch("openpeerpower.components.fido.sensor.FidoClient", FidoClientMockError):
        await fido.async_setup_platform.opp, config, fake_async_add_entities)
    assert fake_async_add_entities.called is False
