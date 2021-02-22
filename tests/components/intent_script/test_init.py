"""Test intent_script component."""
from openpeerpower.bootstrap import async_setup_component
from openpeerpower.helpers import intent

from tests.common import async_mock_service


async def test_intent_script.opp):
    """Test intent scripts work."""
    calls = async_mock_service.opp, "test", "service")

    await async_setup_component(
       .opp,
        "intent_script",
        {
            "intent_script": {
                "HelloWorld": {
                    "action": {
                        "service": "test.service",
                        "data_template": {"hello": "{{ name }}"},
                    },
                    "card": {
                        "title": "Hello {{ name }}",
                        "content": "Content for {{ name }}",
                    },
                    "speech": {"text": "Good morning {{ name }}"},
                }
            }
        },
    )

    response = await intent.async_handle(
       .opp, "test", "HelloWorld", {"name": {"value": "Paulus"}}
    )

    assert len(calls) == 1
    assert calls[0].data["hello"] == "Paulus"

    assert response.speech["plain"]["speech"] == "Good morning Paulus"

    assert response.card["simple"]["title"] == "Hello Paulus"
    assert response.card["simple"]["content"] == "Content for Paulus"
