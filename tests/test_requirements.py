"""Test requirements module."""
import os
from unittest.mock import call, patch

import pytest

from openpeerpower import loader, setup
from openpeerpower.requirements import (
    CONSTRAINT_FILE,
    RequirementsNotFound,
    async_get_integration_with_requirements,
    async_process_requirements,
)

from tests.common import MockModule, mock_integration


def env_without_wheel_links():
    """Return env without wheel links."""
    env = dict(os.environ)
    env.pop("WHEEL_LINKS", None)
    return env


async def test_requirement_installed_in_venv(opp):
    """Test requirement installed in virtual environment."""
    with patch("os.path.dirname", return_value="op_package_path"), patch(
        "openpeerpower.util.package.is_virtual_env", return_value=True
    ), patch("openpeerpower.util.package.is_docker_env", return_value=False), patch(
        "openpeerpower.util.package.install_package", return_value=True
    ) as mock_install, patch.dict(
        os.environ, env_without_wheel_links(), clear=True
    ):
        opp.config.skip_pip = False
        mock_integration(opp, MockModule("comp", requirements=["package==0.0.1"]))
        assert await setup.async_setup_component(opp, "comp", {})
        assert "comp" in opp.config.components
        assert mock_install.call_args == call(
            "package==0.0.1",
            constraints=os.path.join("op_package_path", CONSTRAINT_FILE),
            no_cache_dir=False,
        )


async def test_requirement_installed_in_deps(opp):
    """Test requirement installed in deps directory."""
    with patch("os.path.dirname", return_value="op_package_path"), patch(
        "openpeerpower.util.package.is_virtual_env", return_value=False
    ), patch("openpeerpower.util.package.is_docker_env", return_value=False), patch(
        "openpeerpower.util.package.install_package", return_value=True
    ) as mock_install, patch.dict(
        os.environ, env_without_wheel_links(), clear=True
    ):
        opp.config.skip_pip = False
        mock_integration(opp, MockModule("comp", requirements=["package==0.0.1"]))
        assert await setup.async_setup_component(opp, "comp", {})
        assert "comp" in opp.config.components
        assert mock_install.call_args == call(
            "package==0.0.1",
            target.opp.config.path("deps"),
            constraints=os.path.join("op_package_path", CONSTRAINT_FILE),
            no_cache_dir=False,
        )


async def test_install_existing_package(opp):
    """Test an install attempt on an existing package."""
    with patch(
        "openpeerpower.util.package.install_package", return_value=True
    ) as mock_inst:
        await async_process_requirements(opp, "test_component", ["hello==1.0.0"])

    assert len(mock_inst.mock_calls) == 1

    with patch("openpeerpower.util.package.is_installed", return_value=True), patch(
        "openpeerpower.util.package.install_package"
    ) as mock_inst:
        await async_process_requirements(opp, "test_component", ["hello==1.0.0"])

    assert len(mock_inst.mock_calls) == 0


async def test_install_missing_package(opp):
    """Test an install attempt on an existing package."""
    with patch(
        "openpeerpower.util.package.install_package", return_value=False
    ) as mock_inst:
        with pytest.raises(RequirementsNotFound):
            await async_process_requirements(opp, "test_component", ["hello==1.0.0"])

    assert len(mock_inst.mock_calls) == 1


async def test_get_integration_with_requirements(opp):
    """Check getting an integration with loaded requirements."""
    opp.config.skip_pip = False
    mock_integration(
        opp, MockModule("test_component_dep", requirements=["test-comp-dep==1.0.0"])
    )
    mock_integration(
        opp,
        MockModule(
            "test_component_after_dep", requirements=["test-comp-after-dep==1.0.0"]
        ),
    )
    mock_integration(
        opp,
        MockModule(
            "test_component",
            requirements=["test-comp==1.0.0"],
            dependencies=["test_component_dep"],
            partial_manifest={"after_dependencies": ["test_component_after_dep"]},
        ),
    )

    with patch(
        "openpeerpower.util.package.is_installed", return_value=False
    ) as mock_is_installed, patch(
        "openpeerpower.util.package.install_package", return_value=True
    ) as mock_inst:

        integration = await async_get_integration_with_requirements(
            opp, "test_component"
        )
        assert integration
        assert integration.domain == "test_component"

    assert len(mock_is_installed.mock_calls) == 3
    assert sorted(mock_call[1][0] for mock_call in mock_is_installed.mock_calls) == [
        "test-comp-after-dep==1.0.0",
        "test-comp-dep==1.0.0",
        "test-comp==1.0.0",
    ]

    assert len(mock_inst.mock_calls) == 3
    assert sorted(mock_call[1][0] for mock_call in mock_inst.mock_calls) == [
        "test-comp-after-dep==1.0.0",
        "test-comp-dep==1.0.0",
        "test-comp==1.0.0",
    ]


async def test_install_with_wheels_index(opp):
    """Test an install attempt with wheels index URL."""
    opp.config.skip_pip = False
    mock_integration(opp, MockModule("comp", requirements=["hello==1.0.0"]))

    with patch("openpeerpower.util.package.is_installed", return_value=False), patch(
        "openpeerpower.util.package.is_docker_env", return_value=True
    ), patch("openpeerpower.util.package.install_package") as mock_inst, patch.dict(
        os.environ, {"WHEELS_LINKS": "https://wheels.opp.io/test"}
    ), patch(
        "os.path.dirname"
    ) as mock_dir:
        mock_dir.return_value = "op_package_path"
        assert await setup.async_setup_component(opp, "comp", {})
        assert "comp" in opp.config.components

        assert mock_inst.call_args == call(
            "hello==1.0.0",
            find_links="https://wheels.opp.io/test",
            constraints=os.path.join("op_package_path", CONSTRAINT_FILE),
            no_cache_dir=True,
        )


async def test_install_on_docker(opp):
    """Test an install attempt on an docker system env."""
    opp.config.skip_pip = False
    mock_integration(opp, MockModule("comp", requirements=["hello==1.0.0"]))

    with patch("openpeerpower.util.package.is_installed", return_value=False), patch(
        "openpeerpower.util.package.is_docker_env", return_value=True
    ), patch("openpeerpower.util.package.install_package") as mock_inst, patch(
        "os.path.dirname"
    ) as mock_dir, patch.dict(
        os.environ, env_without_wheel_links(), clear=True
    ):
        mock_dir.return_value = "op_package_path"
        assert await setup.async_setup_component(opp, "comp", {})
        assert "comp" in opp.config.components

        assert mock_inst.call_args == call(
            "hello==1.0.0",
            constraints=os.path.join("op_package_path", CONSTRAINT_FILE),
            no_cache_dir=True,
        )


async def test_discovery_requirements_mqtt(opp):
    """Test that we load discovery requirements."""
    opp.config.skip_pip = False
    mqtt = await loader.async_get_integration(opp, "mqtt")

    mock_integration(
        opp, MockModule("mqtt_comp", partial_manifest={"mqtt": ["foo/discovery"]})
    )
    with patch(
        "openpeerpower.requirements.async_process_requirements",
    ) as mock_process:
        await async_get_integration_with_requirements(opp, "mqtt_comp")

    assert len(mock_process.mock_calls) == 2  # mqtt also depends on http
    assert mock_process.mock_calls[0][1][2] == mqtt.requirements


async def test_discovery_requirements_ssdp(opp):
    """Test that we load discovery requirements."""
    opp.config.skip_pip = False
    ssdp = await loader.async_get_integration(opp, "ssdp")

    mock_integration(
        opp, MockModule("ssdp_comp", partial_manifest={"ssdp": [{"st": "roku:ecp"}]})
    )
    with patch(
        "openpeerpower.requirements.async_process_requirements",
    ) as mock_process:
        await async_get_integration_with_requirements(opp, "ssdp_comp")

    assert len(mock_process.mock_calls) == 3
    assert mock_process.mock_calls[0][1][2] == ssdp.requirements
    # Ensure zeroconf is a dep for ssdp
    assert mock_process.mock_calls[1][1][1] == "zeroconf"


@pytest.mark.parametrize(
    "partial_manifest",
    [{"zeroconf": ["_googlecast._tcp.local."]}, {"homekit": {"models": ["LIFX"]}}],
)
async def test_discovery_requirements_zeroconf(opp, partial_manifest):
    """Test that we load discovery requirements."""
    opp.config.skip_pip = False
    zeroconf = await loader.async_get_integration(opp, "zeroconf")

    mock_integration(
        opp,
        MockModule("comp", partial_manifest=partial_manifest),
    )

    with patch(
        "openpeerpower.requirements.async_process_requirements",
    ) as mock_process:
        await async_get_integration_with_requirements(opp, "comp")

    assert len(mock_process.mock_calls) == 2  # zeroconf also depends on http
    assert mock_process.mock_calls[0][1][2] == zeroconf.requirements


async def test_discovery_requirements_dhcp(opp):
    """Test that we load dhcp discovery requirements."""
    opp.config.skip_pip = False
    dhcp = await loader.async_get_integration(opp, "dhcp")

    mock_integration(
        opp,
        MockModule(
            "comp",
            partial_manifest={
                "dhcp": [{"hostname": "somfy_*", "macaddress": "B8B7F1*"}]
            },
        ),
    )
    with patch(
        "openpeerpower.requirements.async_process_requirements",
    ) as mock_process:
        await async_get_integration_with_requirements(opp, "comp")

    assert len(mock_process.mock_calls) == 1  # dhcp does not depend on http
    assert mock_process.mock_calls[0][1][2] == dhcp.requirements
