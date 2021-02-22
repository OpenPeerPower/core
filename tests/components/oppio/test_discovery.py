"""Test config flow."""
from unittest.mock import Mock, patch

from openpeerpower.components.oppio.handler import HassioAPIError
from openpeerpower.const import EVENT_OPENPEERPOWER_START
from openpeerpower.setup import async_setup_component


async def test.oppio_discovery_startup.opp, aioclient_mock, oppio_client):
    """Test startup and discovery after event."""
    aioclient_mock.get(
        "http://127.0.0.1/discovery",
        json={
            "result": "ok",
            "data": {
                "discovery": [
                    {
                        "service": "mqtt",
                        "uuid": "test",
                        "addon": "mosquitto",
                        "config": {
                            "broker": "mock-broker",
                            "port": 1883,
                            "username": "mock-user",
                            "password": "mock-pass",
                            "protocol": "3.1.1",
                        },
                    }
                ]
            },
        },
    )
    aioclient_mock.get(
        "http://127.0.0.1/addons/mosquitto/info",
        json={"result": "ok", "data": {"name": "Mosquitto Test"}},
    )

    assert aioclient_mock.call_count == 0

    with patch(
        "openpeerpower.components.mqtt.config_flow.FlowHandler.async_step.oppio",
        return_value={"type": "abort"},
    ) as mock_mqtt:
        opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
        await opp.async_block_till_done()

        assert aioclient_mock.call_count == 2
        assert mock_mqtt.called
        mock_mqtt.assert_called_with(
            {
                "broker": "mock-broker",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",
                "addon": "Mosquitto Test",
            }
        )


async def test.oppio_discovery_startup_done.opp, aioclient_mock, oppio_client):
    """Test startup and discovery with.opp discovery."""
    aioclient_mock.post(
        "http://127.0.0.1/supervisor/options",
        json={"result": "ok", "data": {}},
    )
    aioclient_mock.get(
        "http://127.0.0.1/discovery",
        json={
            "result": "ok",
            "data": {
                "discovery": [
                    {
                        "service": "mqtt",
                        "uuid": "test",
                        "addon": "mosquitto",
                        "config": {
                            "broker": "mock-broker",
                            "port": 1883,
                            "username": "mock-user",
                            "password": "mock-pass",
                            "protocol": "3.1.1",
                        },
                    }
                ]
            },
        },
    )
    aioclient_mock.get(
        "http://127.0.0.1/addons/mosquitto/info",
        json={"result": "ok", "data": {"name": "Mosquitto Test"}},
    )

    with patch(
        "openpeerpower.components.oppio.HassIO.update.opp_api",
        return_value={"result": "ok"},
    ), patch(
        "openpeerpower.components.oppio.HassIO.get_info",
        Mock(side_effect=HassioAPIError()),
    ), patch(
        "openpeerpower.components.mqtt.config_flow.FlowHandler.async_step.oppio",
        return_value={"type": "abort"},
    ) as mock_mqtt:
        await opp.async_start()
        await async_setup_component.opp,  opp.o", {})
        await opp.async_block_till_done()

        assert aioclient_mock.call_count == 2
        assert mock_mqtt.called
        mock_mqtt.assert_called_with(
            {
                "broker": "mock-broker",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",
                "addon": "Mosquitto Test",
            }
        )


async def test.oppio_discovery_webhook.opp, aioclient_mock, oppio_client):
    """Test discovery webhook."""
    aioclient_mock.get(
        "http://127.0.0.1/discovery/testuuid",
        json={
            "result": "ok",
            "data": {
                "service": "mqtt",
                "uuid": "test",
                "addon": "mosquitto",
                "config": {
                    "broker": "mock-broker",
                    "port": 1883,
                    "username": "mock-user",
                    "password": "mock-pass",
                    "protocol": "3.1.1",
                },
            },
        },
    )
    aioclient_mock.get(
        "http://127.0.0.1/addons/mosquitto/info",
        json={"result": "ok", "data": {"name": "Mosquitto Test"}},
    )

    with patch(
        "openpeerpower.components.mqtt.config_flow.FlowHandler.async_step.oppio",
        return_value={"type": "abort"},
    ) as mock_mqtt:
        resp = await oppio_client.post(
            "/api.oppio_push/discovery/testuuid",
            json={"addon": "mosquitto", "service": "mqtt", "uuid": "testuuid"},
        )
        await opp.async_block_till_done()

        assert resp.status == 200
        assert aioclient_mock.call_count == 2
        assert mock_mqtt.called
        mock_mqtt.assert_called_with(
            {
                "broker": "mock-broker",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",
                "addon": "Mosquitto Test",
            }
        )
