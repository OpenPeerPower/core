"""Test to verify that we can load components."""
from unittest.mock import ANY, patch

import pytest

from openpeerpower import core, loader
from openpeerpower.components import http, hue
from openpeerpower.components.hue import light as hue_light

from tests.common import MockModule, async_mock_service, mock_integration


async def test_component_dependencies.opp):
    """Test if we can get the proper load order of components."""
    mock_integration.opp, MockModule("mod1"))
    mock_integration.opp, MockModule("mod2", ["mod1"]))
    mod_3 = mock_integration.opp, MockModule("mod3", ["mod2"]))

    assert {"mod1", "mod2", "mod3"} == await loader._async_component_dependencies(
       .opp, "mod_3", mod_3, set(), set()
    )

    # Create circular dependency
    mock_integration.opp, MockModule("mod1", ["mod3"]))

    with pytest.raises(loader.CircularDependency):
        print(
            await loader._async_component_dependencies(
               .opp, "mod_3", mod_3, set(), set()
            )
        )

    # Depend on non-existing component
    mod_1 = mock_integration.opp, MockModule("mod1", ["nonexisting"]))

    with pytest.raises(loader.IntegrationNotFound):
        print(
            await loader._async_component_dependencies(
               .opp, "mod_1", mod_1, set(), set()
            )
        )

    # Having an after dependency 2 deps down that is circular
    mod_1 = mock_integration(
       .opp, MockModule("mod1", partial_manifest={"after_dependencies": ["mod_3"]})
    )

    with pytest.raises(loader.CircularDependency):
        print(
            await loader._async_component_dependencies(
               .opp, "mod_3", mod_3, set(), set()
            )
        )


def test_component_loader.opp):
    """Test loading components."""
    components = loader.Components.opp)
    assert components.http.CONFIG_SCHEMA is http.CONFIG_SCHEMA
    assert.opp.components.http.CONFIG_SCHEMA is http.CONFIG_SCHEMA


def test_component_loader_non_existing.opp):
    """Test loading components."""
    components = loader.Components.opp)
    with pytest.raises(ImportError):
        components.non_existing


async def test_component_wrapper.opp):
    """Test component wrapper."""
    calls = async_mock_service.opp, "persistent_notification", "create")

    components = loader.Components.opp)
    components.persistent_notification.async_create("message")
    await opp..async_block_till_done()

    assert len(calls) == 1


async def test_helpers_wrapper.opp):
    """Test helpers wrapper."""
    helpers = loader.Helpers.opp)

    result = []

    @core.callback
    def discovery_callback(service, discovered):
        """Handle discovery callback."""
        result.append(discovered)

    helpers.discovery.async_listen("service_name", discovery_callback)

    await helpers.discovery.async_discover("service_name", "hello", None, {})
    await opp..async_block_till_done()

    assert result == ["hello"]


async def test_custom_component_name.opp):
    """Test the name attribute of custom components."""
    integration = await loader.async_get_integration.opp, "test_standalone")
    int_comp = integration.get_component()
    assert int_comp.__name__ == "custom_components.test_standalone"
    assert int_comp.__package__ == "custom_components"

    comp = opp.components.test_standalone
    assert comp.__name__ == "custom_components.test_standalone"
    assert comp.__package__ == "custom_components"

    integration = await loader.async_get_integration.opp, "test_package")
    int_comp = integration.get_component()
    assert int_comp.__name__ == "custom_components.test_package"
    assert int_comp.__package__ == "custom_components.test_package"

    comp = opp.components.test_package
    assert comp.__name__ == "custom_components.test_package"
    assert comp.__package__ == "custom_components.test_package"

    integration = await loader.async_get_integration.opp, "test")
    platform = integration.get_platform("light")
    assert platform.__name__ == "custom_components.test.light"
    assert platform.__package__ == "custom_components.test"

    # Test custom components is mounted
    from custom_components.test_package import TEST

    assert TEST == 5


async def test_log_warning_custom_component.opp, caplog):
    """Test that we log a warning when loading a custom component."""
    await loader.async_get_integration.opp, "test_standalone")
    assert "You are using a custom integration test_standalone" in caplog.text

    await loader.async_get_integration.opp, "test")
    assert "You are using a custom integration test " in caplog.text


async def test_custom_integration_missing_version.opp, caplog):
    """Test that we log a warning when custom integrations are missing a version."""
    test_integration_1 = loader.Integration(
       .opp, "custom_components.test1", None, {"domain": "test1"}
    )
    test_integration_2 = loader.Integration(
       .opp,
        "custom_components.test2",
        None,
        loader.manifest_from_legacy_module("test2", "custom_components.test2"),
    )

    with patch("openpeerpowerr.loader.async_get_custom_components") as mock_get:
        mock_get.return_value = {
            "test1": test_integration_1,
            "test2": test_integration_2,
        }

        await loader.async_get_integration.opp, "test1")
        assert (
            "No 'version' key in the manifest file for custom integration 'test1'."
            in caplog.text
        )

        await loader.async_get_integration.opp, "test2")
        assert (
            "No 'version' key in the manifest file for custom integration 'test2'."
            in caplog.text
        )


async def test_no_version_warning_for_none_custom_integrations.opp, caplog):
    """Test that we do not log a warning when core integrations are missing a version."""
    await loader.async_get_integration.opp, "hue")
    assert (
        "No 'version' key in the manifest file for custom integration 'hue'."
        not in caplog.text
    )


async def test_custom_integration_version_not_valid.opp, caplog):
    """Test that we log a warning when custom integrations have a invalid version."""
    test_integration = loader.Integration(
       .opp, "custom_components.test", None, {"domain": "test", "version": "test"}
    )

    with patch("openpeerpowerr.loader.async_get_custom_components") as mock_get:
        mock_get.return_value = {"test": test_integration}

        await loader.async_get_integration.opp, "test")
        assert (
            "'test' is not a valid version for custom integration 'test'."
            in caplog.text
        )


async def test_get_integration.opp):
    """Test resolving integration."""
    integration = await loader.async_get_integration.opp, "hue")
    assert hue == integration.get_component()
    assert hue_light == integration.get_platform("light")


async def test_get_integration_legacy.opp):
    """Test resolving integration."""
    integration = await loader.async_get_integration.opp, "test_embedded")
    assert integration.get_component().DOMAIN == "test_embedded"
    assert integration.get_platform("switch") is not None


async def test_get_integration_custom_component.opp, enable_custom_integrations):
    """Test resolving integration."""
    integration = await loader.async_get_integration.opp, "test_package")
    assert integration.get_component().DOMAIN == "test_package"
    assert integration.name == "Test Package"


def test_integration_properties.opp):
    """Test integration properties."""
    integration = loader.Integration(
       .opp,
        "openpeerpower.components.hue",
        None,
        {
            "name": "Philips Hue",
            "domain": "hue",
            "dependencies": ["test-dep"],
            "requirements": ["test-req==1.0.0"],
            "zeroconf": ["_hue._tcp.local."],
            "homekit": {"models": ["BSB002"]},
            "dhcp": [
                {"hostname": "tesla_*", "macaddress": "4CFCAA*"},
                {"hostname": "tesla_*", "macaddress": "044EAF*"},
                {"hostname": "tesla_*", "macaddress": "98ED5C*"},
            ],
            "ssdp": [
                {
                    "manufacturer": "Royal Philips Electronics",
                    "modelName": "Philips hue bridge 2012",
                },
                {
                    "manufacturer": "Royal Philips Electronics",
                    "modelName": "Philips hue bridge 2015",
                },
                {"manufacturer": "Signify", "modelName": "Philips hue bridge 2015"},
            ],
            "mqtt": ["hue/discovery"],
            "version": "1.0.0",
        },
    )
    assert integration.name == "Philips Hue"
    assert integration.domain == "hue"
    assert integration.homekit == {"models": ["BSB002"]}
    assert integration.zeroconf == ["_hue._tcp.local."]
    assert integration.dhcp == [
        {"hostname": "tesla_*", "macaddress": "4CFCAA*"},
        {"hostname": "tesla_*", "macaddress": "044EAF*"},
        {"hostname": "tesla_*", "macaddress": "98ED5C*"},
    ]
    assert integration.ssdp == [
        {
            "manufacturer": "Royal Philips Electronics",
            "modelName": "Philips hue bridge 2012",
        },
        {
            "manufacturer": "Royal Philips Electronics",
            "modelName": "Philips hue bridge 2015",
        },
        {"manufacturer": "Signify", "modelName": "Philips hue bridge 2015"},
    ]
    assert integration.mqtt == ["hue/discovery"]
    assert integration.dependencies == ["test-dep"]
    assert integration.requirements == ["test-req==1.0.0"]
    assert integration.is_built_in is True
    assert integration.version == "1.0.0"

    integration = loader.Integration(
       .opp,
        "custom_components.hue",
        None,
        {
            "name": "Philips Hue",
            "domain": "hue",
            "dependencies": ["test-dep"],
            "requirements": ["test-req==1.0.0"],
        },
    )
    assert integration.is_built_in is False
    assert integration.homekit is None
    assert integration.zeroconf is None
    assert integration.dhcp is None
    assert integration.ssdp is None
    assert integration.mqtt is None
    assert integration.version is None

    integration = loader.Integration(
       .opp,
        "custom_components.hue",
        None,
        {
            "name": "Philips Hue",
            "domain": "hue",
            "dependencies": ["test-dep"],
            "zeroconf": [{"type": "_hue._tcp.local.", "name": "hue*"}],
            "requirements": ["test-req==1.0.0"],
        },
    )
    assert integration.is_built_in is False
    assert integration.homekit is None
    assert integration.zeroconf == [{"type": "_hue._tcp.local.", "name": "hue*"}]
    assert integration.dhcp is None
    assert integration.ssdp is None


async def test_integrations_only_once.opp):
    """Test that we load integrations only once."""
    int_1 = opp.async_create_task(loader.async_get_integration.opp, "hue"))
    int_2 = opp.async_create_task(loader.async_get_integration.opp, "hue"))

    assert await int_1 is await int_2


async def test_get_custom_components_internal.opp):
    """Test that we can a list of custom components."""
    # pylint: disable=protected-access
    integrations = await loader._async_get_custom_components.opp)
    assert integrations == {"test": ANY, "test_package": ANY}


def _get_test_integration.opp, name, config_flow):
    """Return a generated test integration."""
    return loader.Integration(
       .opp,
        f"openpeerpower.components.{name}",
        None,
        {
            "name": name,
            "domain": name,
            "config_flow": config_flow,
            "dependencies": [],
            "requirements": [],
            "zeroconf": [f"_{name}._tcp.local."],
            "homekit": {"models": [name]},
            "ssdp": [{"manufacturer": name, "modelName": name}],
            "mqtt": [f"{name}/discovery"],
        },
    )


def _get_test_integration_with_zeroconf_matcher.opp, name, config_flow):
    """Return a generated test integration with a zeroconf matcher."""
    return loader.Integration(
       .opp,
        f"openpeerpower.components.{name}",
        None,
        {
            "name": name,
            "domain": name,
            "config_flow": config_flow,
            "dependencies": [],
            "requirements": [],
            "zeroconf": [{"type": f"_{name}._tcp.local.", "name": f"{name}*"}],
            "homekit": {"models": [name]},
            "ssdp": [{"manufacturer": name, "modelName": name}],
        },
    )


def _get_test_integration_with_dhcp_matcher.opp, name, config_flow):
    """Return a generated test integration with a dhcp matcher."""
    return loader.Integration(
       .opp,
        f"openpeerpower.components.{name}",
        None,
        {
            "name": name,
            "domain": name,
            "config_flow": config_flow,
            "dependencies": [],
            "requirements": [],
            "zeroconf": [],
            "dhcp": [
                {"hostname": "tesla_*", "macaddress": "4CFCAA*"},
                {"hostname": "tesla_*", "macaddress": "044EAF*"},
                {"hostname": "tesla_*", "macaddress": "98ED5C*"},
            ],
            "homekit": {"models": [name]},
            "ssdp": [{"manufacturer": name, "modelName": name}],
        },
    )


async def test_get_custom_components.opp, enable_custom_integrations):
    """Verify that custom components are cached."""
    test_1_integration = _get_test_integration.opp, "test_1", False)
    test_2_integration = _get_test_integration.opp, "test_2", True)

    name = "openpeerpowerr.loader._async_get_custom_components"
    with patch(name) as mock_get:
        mock_get.return_value = {
            "test_1": test_1_integration,
            "test_2": test_2_integration,
        }
        integrations = await loader.async_get_custom_components.opp)
        assert integrations == mock_get.return_value
        integrations = await loader.async_get_custom_components.opp)
        assert integrations == mock_get.return_value
        mock_get.assert_called_once_with.opp)


async def test_get_config_flows.opp):
    """Verify that custom components with config_flow are available."""
    test_1_integration = _get_test_integration.opp, "test_1", False)
    test_2_integration = _get_test_integration.opp, "test_2", True)

    with patch("openpeerpowerr.loader.async_get_custom_components") as mock_get:
        mock_get.return_value = {
            "test_1": test_1_integration,
            "test_2": test_2_integration,
        }
        flows = await loader.async_get_config_flows.opp)
        assert "test_2" in flows
        assert "test_1" not in flows


async def test_get_zeroconf.opp):
    """Verify that custom components with zeroconf are found."""
    test_1_integration = _get_test_integration.opp, "test_1", True)
    test_2_integration = _get_test_integration_with_zeroconf_matcher(
       .opp, "test_2", True
    )

    with patch("openpeerpowerr.loader.async_get_custom_components") as mock_get:
        mock_get.return_value = {
            "test_1": test_1_integration,
            "test_2": test_2_integration,
        }
        zeroconf = await loader.async_get_zeroconf.opp)
        assert zeroconf["_test_1._tcp.local."] == [{"domain": "test_1"}]
        assert zeroconf["_test_2._tcp.local."] == [
            {"domain": "test_2", "name": "test_2*"}
        ]


async def test_get_dhcp.opp):
    """Verify that custom components with dhcp are found."""
    test_1_integration = _get_test_integration_with_dhcp_matcher.opp, "test_1", True)

    with patch("openpeerpowerr.loader.async_get_custom_components") as mock_get:
        mock_get.return_value = {
            "test_1": test_1_integration,
        }
        dhcp = await loader.async_get_dhcp.opp)
        dhcp_for_domain = [entry for entry in dhcp if entry["domain"] == "test_1"]
        assert dhcp_for_domain == [
            {"domain": "test_1", "hostname": "tesla_*", "macaddress": "4CFCAA*"},
            {"domain": "test_1", "hostname": "tesla_*", "macaddress": "044EAF*"},
            {"domain": "test_1", "hostname": "tesla_*", "macaddress": "98ED5C*"},
        ]


async def test_get_homekit.opp):
    """Verify that custom components with homekit are found."""
    test_1_integration = _get_test_integration.opp, "test_1", True)
    test_2_integration = _get_test_integration.opp, "test_2", True)

    with patch("openpeerpowerr.loader.async_get_custom_components") as mock_get:
        mock_get.return_value = {
            "test_1": test_1_integration,
            "test_2": test_2_integration,
        }
        homekit = await loader.async_get_homekit.opp)
        assert homekit["test_1"] == "test_1"
        assert homekit["test_2"] == "test_2"


async def test_get_ssdp.opp):
    """Verify that custom components with ssdp are found."""
    test_1_integration = _get_test_integration.opp, "test_1", True)
    test_2_integration = _get_test_integration.opp, "test_2", True)

    with patch("openpeerpowerr.loader.async_get_custom_components") as mock_get:
        mock_get.return_value = {
            "test_1": test_1_integration,
            "test_2": test_2_integration,
        }
        ssdp = await loader.async_get_ssdp.opp)
        assert ssdp["test_1"] == [{"manufacturer": "test_1", "modelName": "test_1"}]
        assert ssdp["test_2"] == [{"manufacturer": "test_2", "modelName": "test_2"}]


async def test_get_mqtt.opp):
    """Verify that custom components with MQTT are found."""
    test_1_integration = _get_test_integration.opp, "test_1", True)
    test_2_integration = _get_test_integration.opp, "test_2", True)

    with patch("openpeerpowerr.loader.async_get_custom_components") as mock_get:
        mock_get.return_value = {
            "test_1": test_1_integration,
            "test_2": test_2_integration,
        }
        mqtt = await loader.async_get_mqtt.opp)
        assert mqtt["test_1"] == ["test_1/discovery"]
        assert mqtt["test_2"] == ["test_2/discovery"]


async def test_get_custom_components_safe_mode.opp):
    """Test that we get empty custom components in safe mode."""
   .opp.config.safe_mode = True
    assert await loader.async_get_custom_components.opp) == {}
