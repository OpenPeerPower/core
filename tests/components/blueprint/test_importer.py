"""Test blueprint importing."""
import json

import pytest

from openpeerpower.components.blueprint import importer
from openpeerpower.exceptions import OpenPeerPowerError

from tests.common import load_fixture


@pytest.fixture(scope="session")
def community_post():
    """Topic JSON with a codeblock marked as auto syntax."""
    return load_fixture("blueprint/community_post.json")


COMMUNITY_POST_INPUTS = {
    "remote": {
        "name": "Remote",
        "description": "IKEA remote to use",
        "selector": {
            "device": {
                "integration": "zha",
                "manufacturer": "IKEA of Sweden",
                "model": "TRADFRI remote control",
            }
        },
    },
    "light": {
        "name": "Light(s)",
        "description": "The light(s) to control",
        "selector": {"target": {"entity": {"domain": "light"}}},
    },
    "force_brightness": {
        "name": "Force turn on brightness",
        "description": 'Force the brightness to the set level below, when the "on" button on the remote is pushed and lights turn on.\n',
        "default": False,
        "selector": {"boolean": {}},
    },
    "brightness": {
        "name": "Brightness",
        "description": "Brightness of the light(s) when turning on",
        "default": 50,
        "selector": {
            "number": {
                "min": 0.0,
                "max": 100.0,
                "mode": "slider",
                "step": 1.0,
                "unit_of_measurement": "%",
            }
        },
    },
    "button_left_short": {
        "name": "Left button - short press",
        "description": "Action to run on short left button press",
        "default": [],
        "selector": {"action": {}},
    },
    "button_left_long": {
        "name": "Left button - long press",
        "description": "Action to run on long left button press",
        "default": [],
        "selector": {"action": {}},
    },
    "button_right_short": {
        "name": "Right button - short press",
        "description": "Action to run on short right button press",
        "default": [],
        "selector": {"action": {}},
    },
    "button_right_long": {
        "name": "Right button - long press",
        "description": "Action to run on long right button press",
        "default": [],
        "selector": {"action": {}},
    },
}


def test_extract_blueprint_from_community_topic(community_post):
    """Test extracting blueprint."""
    imported_blueprint = importer._extract_blueprint_from_community_topic(
        "http://example.com", json.loads(community_post)
    )
    assert imported_blueprint is not None
    assert imported_blueprint.blueprint.domain == "automation"
    assert imported_blueprint.blueprint.inputs == COMMUNITY_POST_INPUTS


def test_extract_blueprint_from_community_topic_invalid_yaml():
    """Test extracting blueprint with invalid YAML."""
    with pytest.raises(OpenPeerPowerError):
        importer._extract_blueprint_from_community_topic(
            "http://example.com",
            {
                "post_stream": {
                    "posts": [
                        {"cooked": '<code class="lang-yaml">invalid: yaml: 2</code>'}
                    ]
                }
            },
        )
