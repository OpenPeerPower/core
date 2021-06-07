"""Test the translation helper."""
import asyncio
from os import path
import pathlib
from unittest.mock import Mock, patch

import pytest

from openpeerpower.generated import config_flows
from openpeerpower.helpers import translation
from openpeerpower.loader import async_get_integration
from openpeerpower.setup import async_setup_component, setup_component


@pytest.fixture
def mock_config_flows():
    """Mock the config flows."""
    flows = []
    with patch.object(config_flows, "FLOWS", flows):
        yield flows


def test_recursive_flatten():
    """Test the flatten function."""
    data = {"parent1": {"child1": "data1", "child2": "data2"}, "parent2": "data3"}

    flattened = translation.recursive_flatten("prefix.", data)

    assert flattened == {
        "prefix.parent1.child1": "data1",
        "prefix.parent1.child2": "data2",
        "prefix.parent2": "data3",
    }


async def test_component_translation_path(opp, enable_custom_integrations):
    """Test the component translation file function."""
    assert await async_setup_component(
        opp,
        "switch",
        {"switch": [{"platform": "test"}, {"platform": "test_embedded"}]},
    )
    assert await async_setup_component(opp, "test_package", {"test_package"})

    (int_test, int_test_embedded, int_test_package,) = await asyncio.gather(
        async_get_integration(opp, "test"),
        async_get_integration(opp, "test_embedded"),
        async_get_integration(opp, "test_package"),
    )

    assert path.normpath(
        translation.component_translation_path("switch.test", "en", int_test)
    ) == path.normpath(
        opp.config.path("custom_components", "test", "translations", "switch.en.json")
    )

    assert path.normpath(
        translation.component_translation_path(
            "switch.test_embedded", "en", int_test_embedded
        )
    ) == path.normpath(
        opp.config.path(
            "custom_components", "test_embedded", "translations", "switch.en.json"
        )
    )

    assert path.normpath(
        translation.component_translation_path("test_package", "en", int_test_package)
    ) == path.normpath(
        opp.config.path("custom_components", "test_package", "translations", "en.json")
    )


def test_load_translations_files(opp):
    """Test the load translation files function."""
    # Test one valid and one invalid file
    file1 = opp.config.path(
        "custom_components", "test", "translations", "switch.en.json"
    )
    file2 = opp.config.path(
        "custom_components", "test", "translations", "invalid.json"
    )
    assert translation.load_translations_files(
        {"switch.test": file1, "invalid": file2}
    ) == {
        "switch.test": {
            "state": {"string1": "Value 1", "string2": "Value 2"},
            "something": "else",
        },
        "invalid": {},
    }


async def test_get_translations(opp, mock_config_flows, enable_custom_integrations):
    """Test the get translations helper."""
    translations = await translation.async_get_translations(opp, "en", "state")
    assert translations == {}

    assert await async_setup_component(opp, "switch", {"switch": {"platform": "test"}})
    await opp.async_block_till_done()

    translations = await translation.async_get_translations(opp, "en", "state")

    assert translations["component.switch.state.string1"] == "Value 1"
    assert translations["component.switch.state.string2"] == "Value 2"

    translations = await translation.async_get_translations(opp, "de", "state")
    assert "component.switch.something" not in translations
    assert translations["component.switch.state.string1"] == "German Value 1"
    assert translations["component.switch.state.string2"] == "German Value 2"

    # Test a partial translation
    translations = await translation.async_get_translations(opp, "es", "state")
    assert translations["component.switch.state.string1"] == "Spanish Value 1"
    assert translations["component.switch.state.string2"] == "Value 2"

    # Test that an untranslated language falls back to English.
    translations = await translation.async_get_translations(
        opp, "invalid-language", "state"
    )
    assert translations["component.switch.state.string1"] == "Value 1"
    assert translations["component.switch.state.string2"] == "Value 2"


async def test_get_translations_loads_config_flows(opp, mock_config_flows):
    """Test the get translations helper loads config flow translations."""
    mock_config_flows.append("component1")
    integration = Mock(file_path=pathlib.Path(__file__))
    integration.name = "Component 1"

    with patch(
        "openpeerpower.helpers.translation.component_translation_path",
        return_value="bla.json",
    ), patch(
        "openpeerpower.helpers.translation.load_translations_files",
        return_value={"component1": {"title": "world"}},
    ), patch(
        "openpeerpower.helpers.translation.async_get_integration",
        return_value=integration,
    ):
        translations = await translation.async_get_translations(
            opp, "en", "title", config_flow=True
        )
        translations_again = await translation.async_get_translations(
            opp, "en", "title", config_flow=True
        )

        assert translations == translations_again

    assert translations == {
        "component.component1.title": "world",
    }

    assert "component1" not in opp.config.components

    mock_config_flows.append("component2")
    integration = Mock(file_path=pathlib.Path(__file__))
    integration.name = "Component 2"

    with patch(
        "openpeerpower.helpers.translation.component_translation_path",
        return_value="bla.json",
    ), patch(
        "openpeerpower.helpers.translation.load_translations_files",
        return_value={"component2": {"title": "world"}},
    ), patch(
        "openpeerpower.helpers.translation.async_get_integration",
        return_value=integration,
    ):
        translations = await translation.async_get_translations(
            opp, "en", "title", config_flow=True
        )
        translations_again = await translation.async_get_translations(
            opp, "en", "title", config_flow=True
        )

        assert translations == translations_again

    assert translations == {
        "component.component1.title": "world",
        "component.component2.title": "world",
    }

    translations_all_cached = await translation.async_get_translations(
        opp, "en", "title", config_flow=True
    )
    assert translations == translations_all_cached

    assert "component1" not in opp.config.components
    assert "component2" not in opp.config.components


async def test_get_translations_while_loading_components(opp):
    """Test the get translations helper loads config flow translations."""
    integration = Mock(file_path=pathlib.Path(__file__))
    integration.name = "Component 1"
    opp.config.components.add("component1")
    load_count = 0

    def mock_load_translation_files(files):
        """Mock load translation files."""
        nonlocal load_count
        load_count += 1
        # Mimic race condition by loading a component during setup
        setup_component(opp, "persistent_notification", {})
        return {"component1": {"title": "world"}}

    with patch(
        "openpeerpower.helpers.translation.component_translation_path",
        return_value="bla.json",
    ), patch(
        "openpeerpower.helpers.translation.load_translations_files",
        mock_load_translation_files,
    ), patch(
        "openpeerpower.helpers.translation.async_get_integration",
        return_value=integration,
    ):
        tasks = [
            translation.async_get_translations(opp, "en", "title") for _ in range(5)
        ]
        all_translations = await asyncio.gather(*tasks)

    assert all_translations[0] == {
        "component.component1.title": "world",
    }
    assert load_count == 1


async def test_get_translation_categories(opp):
    """Test the get translations helper loads config flow translations."""
    with patch.object(translation, "async_get_config_flows", return_value={"light"}):
        translations = await translation.async_get_translations(
            opp, "en", "title", None, True
        )
        assert "component.light.title" in translations

        translations = await translation.async_get_translations(
            opp, "en", "device_automation", None, True
        )
        assert "component.light.device_automation.action_type.turn_on" in translations


async def test_translation_merging(opp, caplog):
    """Test we merge translations of two integrations."""
    opp.config.components.add("sensor.moon")
    opp.config.components.add("sensor")

    translations = await translation.async_get_translations(opp, "en", "state")

    assert "component.sensor.state.moon__phase.first_quarter" in translations

    opp.config.components.add("sensor.season")

    # Patch in some bad translation data

    orig_load_translations = translation.load_translations_files

    def mock_load_translations_files(files):
        """Mock loading."""
        result = orig_load_translations(files)
        result["sensor.season"] = {"state": "bad data"}
        return result

    with patch(
        "openpeerpower.helpers.translation.load_translations_files",
        side_effect=mock_load_translations_files,
    ):
        translations = await translation.async_get_translations(opp, "en", "state")

        assert "component.sensor.state.moon__phase.first_quarter" in translations

    assert (
        "An integration providing translations for sensor provided invalid data: bad data"
        in caplog.text
    )


async def test_translation_merging_loaded_apart(opp, caplog):
    """Test we merge translations of two integrations when they are not loaded at the same time."""
    opp.config.components.add("sensor")

    translations = await translation.async_get_translations(opp, "en", "state")

    assert "component.sensor.state.moon__phase.first_quarter" not in translations

    opp.config.components.add("sensor.moon")

    translations = await translation.async_get_translations(opp, "en", "state")

    assert "component.sensor.state.moon__phase.first_quarter" in translations

    translations = await translation.async_get_translations(
        opp, "en", "state", integration="sensor"
    )

    assert "component.sensor.state.moon__phase.first_quarter" in translations


async def test_caching(opp):
    """Test we cache data."""
    opp.config.components.add("sensor")
    opp.config.components.add("light")

    # Patch with same method so we can count invocations
    with patch(
        "openpeerpower.helpers.translation._merge_resources",
        side_effect=translation._merge_resources,
    ) as mock_merge:
        load1 = await translation.async_get_translations(opp, "en", "state")
        assert len(mock_merge.mock_calls) == 1

        load2 = await translation.async_get_translations(opp, "en", "state")
        assert len(mock_merge.mock_calls) == 1

        assert load1 == load2

        for key in load1:
            assert key.startswith("component.sensor.state.") or key.startswith(
                "component.light.state."
            )

    load_sensor_only = await translation.async_get_translations(
        opp, "en", "state", integration="sensor"
    )
    assert load_sensor_only
    for key in load_sensor_only:
        assert key.startswith("component.sensor.state.")

    load_light_only = await translation.async_get_translations(
        opp, "en", "state", integration="light"
    )
    assert load_light_only
    for key in load_light_only:
        assert key.startswith("component.light.state.")

    opp.config.components.add("media_player")

    # Patch with same method so we can count invocations
    with patch(
        "openpeerpower.helpers.translation._build_resources",
        side_effect=translation._build_resources,
    ) as mock_build:
        load_sensor_only = await translation.async_get_translations(
            opp, "en", "title", integration="sensor"
        )
        assert load_sensor_only
        for key in load_sensor_only:
            assert key == "component.sensor.title"
        assert len(mock_build.mock_calls) == 0

        assert await translation.async_get_translations(
            opp, "en", "title", integration="sensor"
        )
        assert len(mock_build.mock_calls) == 0

        load_light_only = await translation.async_get_translations(
            opp, "en", "title", integration="media_player"
        )
        assert load_light_only
        for key in load_light_only:
            assert key == "component.media_player.title"
        assert len(mock_build.mock_calls) > 1


async def test_custom_component_translations(opp, enable_custom_integrations):
    """Test getting translation from custom components."""
    opp.config.components.add("test_embedded")
    opp.config.components.add("test_package")
    assert await translation.async_get_translations(opp, "en", "state") == {}
