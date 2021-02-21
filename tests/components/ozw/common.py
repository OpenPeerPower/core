"""Helpers for tests."""
import json
from unittest.mock import Mock, patch

from openpeerpower import config_entries
from openpeerpower.components.ozw.const import DOMAIN

from tests.common import MockConfigEntry


async def setup_ozw.opp, entry=None, fixture=None):
    """Set up OZW and load a dump."""
    mqtt_entry = MockConfigEntry(domain="mqtt", state=config_entries.ENTRY_STATE_LOADED)
    mqtt_entry.add_to_opp.opp)

    if entry is None:
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Z-Wave",
            connection_class=config_entries.CONN_CLASS_LOCAL_PUSH,
        )

        entry.add_to_opp.opp)

    with patch("openpeerpower.components.mqtt.async_subscribe") as mock_subscribe:
        mock_subscribe.return_value = Mock()
        assert await.opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    assert "ozw" in.opp.config.components
    assert len(mock_subscribe.mock_calls) == 1
    receive_message = mock_subscribe.mock_calls[0][1][2]

    if fixture is not None:
        for line in fixture.split("\n"):
            line = line.strip()
            if not line:
                continue
            topic, payload = line.split(",", 1)
            receive_message(Mock(topic=topic, payload=payload))

        await opp.async_block_till_done()

    return receive_message


class MQTTMessage:
    """Represent a mock MQTT message."""

    def __init__(self, topic, payload):
        """Set up message."""
        self.topic = topic
        self.payload = payload

    def decode(self):
        """Decode message payload from a string to a json dict."""
        self.payload = json.loads(self.payload)

    def encode(self):
        """Encode message payload into a string."""
        self.payload = json.dumps(self.payload)
