"""Validate requirements."""
from collections import deque
import json
import operator
import os
import re
import subprocess
import sys
from typing import Dict, Set

from stdlib_list import stdlib_list
from tqdm import tqdm

from openpeerpower.const import REQUIRED_PYTHON_VER
import openpeerpower.util.package as pkg_util
from script.gen_requirements_all import COMMENT_REQUIREMENTS

from .model import Config, Integration

IGNORE_PACKAGES = {
    commented.lower().replace("_", "-") for commented in COMMENT_REQUIREMENTS
}
PACKAGE_REGEX = re.compile(r"^(?:--.+\s)?([-_\.\w\d]+).*==.+$")
PIP_REGEX = re.compile(r"^(--.+\s)?([-_\.\w\d]+.*(?:==|>=|<=|~=|!=|<|>|===)?.*$)")
SUPPORTED_PYTHON_TUPLES = [
    REQUIRED_PYTHON_VER[:2],
    tuple(map(operator.add, REQUIRED_PYTHON_VER, (0, 1, 0)))[:2],
]
SUPPORTED_PYTHON_VERSIONS = [
    ".".join(map(str, version_tuple)) for version_tuple in SUPPORTED_PYTHON_TUPLES
]
STD_LIBS = {version: set(stdlib_list(version)) for version in SUPPORTED_PYTHON_VERSIONS}
PIPDEPTREE_CACHE = None

IGNORE_VIOLATIONS = {
    # Still has standard library requirements.
    "acmeda",
    "blink",
    "ezviz",
    "hdmi_cec",
    "juicenet",
    "lupusec",
    "rainbird",
    "slide",
    "suez_water",
}


def normalize_package_name(requirement: str) -> str:
    """Return a normalized package name from a requirement string."""
    match = PACKAGE_REGEX.search(requirement)
    if not match:
        return ""

    # pipdeptree needs lowercase and dash instead of underscore as separator
    package = match.group(1).lower().replace("_", "-")

    return package


def validate(integrations: Dict[str, Integration], config: Config):
    """Handle requirements for integrations."""
    ensure_cache()

    # check for incompatible requirements

    disable_tqdm = config.specific_integrations or os.environ.get("CI", False)

    for integration in tqdm(integrations.values(), disable=disable_tqdm):
        if not integration.manifest:
            continue

        validate_requirements(integration)


def validate_requirements(integration: Integration):
    """Validate requirements."""
    # Some integrations have not been fixed yet so are allowed to have violations.
    if integration.domain in IGNORE_VIOLATIONS:
        return

    integration_requirements = set()
    integration_packages = set()
    for req in integration.requirements:
        package = normalize_package_name(req)
        if not package:
            integration.add_error(
                "requirements",
                f"Failed to normalize package name from requirement {req}",
            )
            return
        if package in IGNORE_PACKAGES:
            continue
        integration_requirements.add(req)
        integration_packages.add(package)

    install_ok = install_requirements(integration, integration_requirements)

    if not install_ok:
        return

    all_integration_requirements = get_requirements(integration, integration_packages)

    if integration_requirements and not all_integration_requirements:
        integration.add_error(
            "requirements",
            f"Failed to resolve requirements {integration_requirements}",
        )
        return

    # Check for requirements incompatible with standard library.
    for version, std_libs in STD_LIBS.items():
        for req in all_integration_requirements:
            if req in std_libs:
                integration.add_error(
                    "requirements",
                    f"Package {req} is not compatible with Python {version} standard library",
                )


def ensure_cache():
    """Ensure we have a cache of pipdeptree.

    {
        "flake8-docstring": {
            "key": "flake8-docstrings",
            "package_name": "flake8-docstrings",
            "installed_version": "1.5.0"
            "dependencies": {"flake8"}
        }
    }
    """
    global PIPDEPTREE_CACHE

    if PIPDEPTREE_CACHE is not None:
        return

    cache = {}

    for item in json.loads(
        subprocess.run(
            ["pipdeptree", "-w", "silence", "--json"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    ):
        cache[item["package"]["key"]] = {
            **item["package"],
            "dependencies": {dep["key"] for dep in item["dependencies"]},
        }

    PIPDEPTREE_CACHE = cache


def get_requirements(integration: Integration, packages: Set[str]) -> Set[str]:
    """Return all (recursively) requirements for an integration."""
    ensure_cache()

    all_requirements = set()

    to_check = deque(packages)

    while to_check:
        package = to_check.popleft()

        if package in all_requirements:
            continue

        all_requirements.add(package)

        item = PIPDEPTREE_CACHE.get(package)

        if item is None:
            # Only warn if direct dependencies could not be resolved
            if package in packages:
                integration.add_error(
                    "requirements", f"Failed to resolve requirements for {package}"
                )
            continue

        to_check.extend(item["dependencies"])

    return all_requirements


def install_requirements(integration: Integration, requirements: Set[str]) -> bool:
    """Install integration requirements.

    Return True if successful.
    """
    global PIPDEPTREE_CACHE

    ensure_cache()

    for req in requirements:
        match = PIP_REGEX.search(req)

        if not match:
            integration.add_error(
                "requirements",
                f"Failed to parse requirement {req} before installation",
            )
            continue

        install_args = match.group(1)
        requirement_arg = match.group(2)

        is_installed = False

        normalized = normalize_package_name(requirement_arg)

        if normalized and "==" in requirement_arg:
            ver = requirement_arg.split("==")[-1]
            item = PIPDEPTREE_CACHE.get(normalized)
            is_installed = item and item["installed_version"] == ver

        if not is_installed:
            try:
                is_installed = pkg_util.is_installed(req)
            except ValueError:
                is_installed = False

        if is_installed:
            continue

        args = [sys.executable, "-m", "pip", "install", "--quiet"]
        if install_args:
            args.append(install_args)
        args.append(requirement_arg)
        try:
            result = subprocess.run(args, check=True, capture_output=True, text=True)
        except subprocess.SubprocessError:
            integration.add_error(
                "requirements",
                f"Requirement {req} failed to install",
            )
        else:
            # Clear the pipdeptree cache if something got installed
            if "Successfully installed" in result.stdout:
                PIPDEPTREE_CACHE = None

    if integration.errors:
        return False

    return True
