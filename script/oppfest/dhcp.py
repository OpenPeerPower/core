"""Generate dhcp file."""
from __future__ import annotations

import json

from .model import Config, Integration

BASE = """
\"\"\"Automatically generated by oppfest.

To update, run python3 -m script.oppfest
\"\"\"

# fmt: off

DHCP = {}
""".strip()


def generate_and_validate(integrations: list[dict[str, str]]):
    """Validate and generate dhcp data."""
    match_list = []

    for domain in sorted(integrations):
        integration = integrations[domain]

        if not integration.manifest:
            continue

        match_types = integration.manifest.get("dhcp", [])

        if not match_types:
            continue

        for entry in match_types:
            match_list.append({"domain": domain, **entry})

    return BASE.format(json.dumps(match_list, indent=4))


def validate(integrations: dict[str, Integration], config: Config):
    """Validate dhcp file."""
    dhcp_path = config.root / "openpeerpower/generated/dhcp.py"
    config.cache["dhcp"] = content = generate_and_validate(integrations)

    if config.specific_integrations:
        return

    with open(str(dhcp_path)) as fp:
        current = fp.read().strip()
        if current != content:
            config.add_error(
                "dhcp",
                "File dhcp.py is not up to date. Run python3 -m script.oppfest",
                fixable=True,
            )
        return


def generate(integrations: dict[str, Integration], config: Config):
    """Generate dhcp file."""
    dhcp_path = config.root / "openpeerpower/generated/dhcp.py"
    with open(str(dhcp_path), "w") as fp:
        fp.write(f"{config.cache['dhcp']}\n")
