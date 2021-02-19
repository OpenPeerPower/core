"""Blueprints conftest."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def stub_blueprint_populate():
    """Stub copying the blueprint automations to the config folder."""
    with patch(
        "openpeerpower.components.blueprint.models.DomainBlueprints.async_populate"
    ):
        yield
