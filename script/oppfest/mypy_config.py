"""Generate mypy config."""
from __future__ import annotations

import configparser
import io
import os
from pathlib import Path
from typing import Final

from .model import Config, Integration

# Modules which have type hints which known to be broken.
# If you are an author of component listed here, please fix these errors and
# remove your component from this list to enable type checks.
# Do your best to not add anything new here.
IGNORED_MODULES: Final[list[str]] = [
    "openpeerpower.components.adguard.*",
    "openpeerpower.components.aemet.*",
    "openpeerpower.components.alarmdecoder.*",
    "openpeerpower.components.alexa.*",
    "openpeerpower.components.almond.*",
    "openpeerpower.components.amcrest.*",
    "openpeerpower.components.analytics.*",
    "openpeerpower.components.asuswrt.*",
    "openpeerpower.components.atag.*",
    "openpeerpower.components.aurora.*",
    "openpeerpower.components.awair.*",
    "openpeerpower.components.azure_devops.*",
    "openpeerpower.components.azure_event_hub.*",
    "openpeerpower.components.blueprint.*",
    "openpeerpower.components.bmw_connected_drive.*",
    "openpeerpower.components.bsblan.*",
    "openpeerpower.components.cast.*",
    "openpeerpower.components.cert_expiry.*",
    "openpeerpower.components.climate.*",
    "openpeerpower.components.cloud.*",
    "openpeerpower.components.cloudflare.*",
    "openpeerpower.components.config.*",
    "openpeerpower.components.control4.*",
    "openpeerpower.components.conversation.*",
    "openpeerpower.components.deconz.*",
    "openpeerpower.components.demo.*",
    "openpeerpower.components.denonavr.*",
    "openpeerpower.components.devolo_home_control.*",
    "openpeerpower.components.dhcp.*",
    "openpeerpower.components.directv.*",
    "openpeerpower.components.doorbird.*",
    "openpeerpower.components.dsmr.*",
    "openpeerpower.components.dynalite.*",
    "openpeerpower.components.eafm.*",
    "openpeerpower.components.edl21.*",
    "openpeerpower.components.elkm1.*",
    "openpeerpower.components.enphase_envoy.*",
    "openpeerpower.components.entur_public_transport.*",
    "openpeerpower.components.evohome.*",
    "openpeerpower.components.fan.*",
    "openpeerpower.components.filter.*",
    "openpeerpower.components.fints.*",
    "openpeerpower.components.fireservicerota.*",
    "openpeerpower.components.firmata.*",
    "openpeerpower.components.flo.*",
    "openpeerpower.components.fortios.*",
    "openpeerpower.components.foscam.*",
    "openpeerpower.components.freebox.*",
    "openpeerpower.components.geniushub.*",
    "openpeerpower.components.glances.*",
    "openpeerpower.components.gogogate2.*",
    "openpeerpower.components.google_assistant.*",
    "openpeerpower.components.google_maps.*",
    "openpeerpower.components.google_pubsub.*",
    "openpeerpower.components.gpmdp.*",
    "openpeerpower.components.gree.*",
    "openpeerpower.components.growatt_server.*",
    "openpeerpower.components.gtfs.*",
    "openpeerpower.components.guardian.*",
    "openpeerpower.components.habitica.*",
    "openpeerpower.components.harmony.*",
    "openpeerpower.components.oppio.*",
    "openpeerpower.components.hdmi_cec.*",
    "openpeerpower.components.here_travel_time.*",
    "openpeerpower.components.hisense_aehw4a1.*",
    "openpeerpower.components.home_connect.*",
    "openpeerpower.components.openpeerpower.*",
    "openpeerpower.components.homekit.*",
    "openpeerpower.components.homekit_controller.*",
    "openpeerpower.components.homematicip_cloud.*",
    "openpeerpower.components.honeywell.*",
    "openpeerpower.components.huisbaasje.*",
    "openpeerpower.components.humidifier.*",
    "openpeerpower.components.iaqualink.*",
    "openpeerpower.components.icloud.*",
    "openpeerpower.components.image.*",
    "openpeerpower.components.incomfort.*",
    "openpeerpower.components.influxdb.*",
    "openpeerpower.components.input_boolean.*",
    "openpeerpower.components.input_datetime.*",
    "openpeerpower.components.input_number.*",
    "openpeerpower.components.insteon.*",
    "openpeerpower.components.ipp.*",
    "openpeerpower.components.isy994.*",
    "openpeerpower.components.izone.*",
    "openpeerpower.components.kaiterra.*",
    "openpeerpower.components.keenetic_ndms2.*",
    "openpeerpower.components.kodi.*",
    "openpeerpower.components.konnected.*",
    "openpeerpower.components.kulersky.*",
    "openpeerpower.components.lifx.*",
    "openpeerpower.components.litejet.*",
    "openpeerpower.components.litterrobot.*",
    "openpeerpower.components.lovelace.*",
    "openpeerpower.components.luftdaten.*",
    "openpeerpower.components.lutron_caseta.*",
    "openpeerpower.components.lyric.*",
    "openpeerpower.components.marytts.*",
    "openpeerpower.components.media_source.*",
    "openpeerpower.components.melcloud.*",
    "openpeerpower.components.meteo_france.*",
    "openpeerpower.components.metoffice.*",
    "openpeerpower.components.minecraft_server.*",
    "openpeerpower.components.mobile_app.*",
    "openpeerpower.components.motion_blinds.*",
    "openpeerpower.components.mqtt.*",
    "openpeerpower.components.mullvad.*",
    "openpeerpower.components.mysensors.*",
    "openpeerpower.components.neato.*",
    "openpeerpower.components.ness_alarm.*",
    "openpeerpower.components.netatmo.*",
    "openpeerpower.components.netio.*",
    "openpeerpower.components.nightscout.*",
    "openpeerpower.components.nilu.*",
    "openpeerpower.components.nmap_tracker.*",
    "openpeerpower.components.norway_air.*",
    "openpeerpower.components.notion.*",
    "openpeerpower.components.nuki.*",
    "openpeerpower.components.nws.*",
    "openpeerpower.components.nzbget.*",
    "openpeerpower.components.omnilogic.*",
    "openpeerpower.components.onboarding.*",
    "openpeerpower.components.ondilo_ico.*",
    "openpeerpower.components.onvif.*",
    "openpeerpower.components.ovo_energy.*",
    "openpeerpower.components.ozw.*",
    "openpeerpower.components.panasonic_viera.*",
    "openpeerpower.components.philips_js.*",
    "openpeerpower.components.pilight.*",
    "openpeerpower.components.ping.*",
    "openpeerpower.components.pioneer.*",
    "openpeerpower.components.plaato.*",
    "openpeerpower.components.plex.*",
    "openpeerpower.components.plugwise.*",
    "openpeerpower.components.plum_lightpad.*",
    "openpeerpower.components.point.*",
    "openpeerpower.components.profiler.*",
    "openpeerpower.components.proxmoxve.*",
    "openpeerpower.components.rachio.*",
    "openpeerpower.components.rainmachine.*",
    "openpeerpower.components.recollect_waste.*",
    "openpeerpower.components.recorder.*",
    "openpeerpower.components.reddit.*",
    "openpeerpower.components.ring.*",
    "openpeerpower.components.roku.*",
    "openpeerpower.components.rpi_power.*",
    "openpeerpower.components.ruckus_unleashed.*",
    "openpeerpower.components.sabnzbd.*",
    "openpeerpower.components.script.*",
    "openpeerpower.components.search.*",
    "openpeerpower.components.sense.*",
    "openpeerpower.components.sesame.*",
    "openpeerpower.components.sharkiq.*",
    "openpeerpower.components.sma.*",
    "openpeerpower.components.smart_meter_texas.*",
    "openpeerpower.components.smartthings.*",
    "openpeerpower.components.smarttub.*",
    "openpeerpower.components.smarty.*",
    "openpeerpower.components.solaredge.*",
    "openpeerpower.components.solarlog.*",
    "openpeerpower.components.somfy.*",
    "openpeerpower.components.somfy_mylink.*",
    "openpeerpower.components.sonarr.*",
    "openpeerpower.components.songpal.*",
    "openpeerpower.components.sonos.*",
    "openpeerpower.components.spotify.*",
    "openpeerpower.components.stt.*",
    "openpeerpower.components.surepetcare.*",
    "openpeerpower.components.switchbot.*",
    "openpeerpower.components.switcher_kis.*",
    "openpeerpower.components.synology_srm.*",
    "openpeerpower.components.system_health.*",
    "openpeerpower.components.system_log.*",
    "openpeerpower.components.tado.*",
    "openpeerpower.components.tasmota.*",
    "openpeerpower.components.telegram_bot.*",
    "openpeerpower.components.template.*",
    "openpeerpower.components.tesla.*",
    "openpeerpower.components.timer.*",
    "openpeerpower.components.todoist.*",
    "openpeerpower.components.toon.*",
    "openpeerpower.components.tplink.*",
    "openpeerpower.components.trace.*",
    "openpeerpower.components.tradfri.*",
    "openpeerpower.components.tuya.*",
    "openpeerpower.components.unifi.*",
    "openpeerpower.components.updater.*",
    "openpeerpower.components.upnp.*",
    "openpeerpower.components.velbus.*",
    "openpeerpower.components.vera.*",
    "openpeerpower.components.verisure.*",
    "openpeerpower.components.volumio.*",
    "openpeerpower.components.webostv.*",
    "openpeerpower.components.wemo.*",
    "openpeerpower.components.wink.*",
    "openpeerpower.components.withings.*",
    "openpeerpower.components.wunderground.*",
    "openpeerpower.components.xbox.*",
    "openpeerpower.components.xiaomi_aqara.*",
    "openpeerpower.components.xiaomi_miio.*",
    "openpeerpower.components.yamaha.*",
    "openpeerpower.components.yeelight.*",
    "openpeerpower.components.zerproc.*",
    "openpeerpower.components.zha.*",
    "openpeerpower.components.zwave.*",
]

HEADER: Final = """
# Automatically generated by oppfest.
#
# To update, run python3 -m script.oppfest

""".lstrip()

GENERAL_SETTINGS: Final[dict[str, str]] = {
    "python_version": "3.8",
    "show_error_codes": "true",
    "follow_imports": "silent",
    # Enable some checks globally.
    "ignore_missing_imports": "true",
    "strict_equality": "true",
    "warn_incomplete_stub": "true",
    "warn_redundant_casts": "true",
    "warn_unused_configs": "true",
    "warn_unused_ignores": "true",
}

# This is basically the list of checks which is enabled for "strict=true".
# But "strict=true" is applied globally, so we need to list all checks manually.
STRICT_SETTINGS: Final[list[str]] = [
    "check_untyped_defs",
    "disallow_incomplete_defs",
    "disallow_subclassing_any",
    "disallow_untyped_calls",
    "disallow_untyped_decorators",
    "disallow_untyped_defs",
    "no_implicit_optional",
    "warn_return_any",
    "warn_unreachable",
    # TODO: turn these on, address issues
    # "disallow_any_generics",
    # "no_implicit_reexport",
]


def generate_and_validate(config: Config) -> str:
    """Validate and generate mypy config."""

    config_path = config.root / ".strict-typing"

    with config_path.open() as fp:
        lines = fp.readlines()

    # Filter empty and commented lines.
    strict_modules: list[str] = [
        line.strip()
        for line in lines
        if line.strip() != "" and not line.startswith("#")
    ]

    ignored_modules_set: set[str] = set(IGNORED_MODULES)
    for module in strict_modules:
        if (
            not module.startswith("openpeerpower.components.")
            and module != "openpeerpower.components"
        ):
            config.add_error(
                "mypy_config", f"Only components should be added: {module}"
            )
        if module in ignored_modules_set:
            config.add_error(
                "mypy_config", f"Module '{module}' is in ignored list in mypy_config.py"
            )

    # Validate that all modules exist.
    all_modules = strict_modules + IGNORED_MODULES
    for module in all_modules:
        if module.endswith(".*"):
            module_path = Path(module[:-2].replace(".", os.path.sep))
            if not module_path.is_dir():
                config.add_error("mypy_config", f"Module '{module} is not a folder")
        else:
            module = module.replace(".", os.path.sep)
            module_path = Path(f"{module}.py")
            if module_path.is_file():
                continue
            module_path = Path(module) / "__init__.py"
            if not module_path.is_file():
                config.add_error("mypy_config", f"Module '{module} doesn't exist")

    # Don't generate mypy.ini if there're errors found because it will likely crash.
    if any(err.plugin == "mypy_config" for err in config.errors):
        return ""

    mypy_config = configparser.ConfigParser()

    general_section = "mypy"
    mypy_config.add_section(general_section)
    for key, value in GENERAL_SETTINGS.items():
        mypy_config.set(general_section, key, value)
    for key in STRICT_SETTINGS:
        mypy_config.set(general_section, key, "true")

    # By default strict checks are disabled for components.
    components_section = "mypy-openpeerpower.components.*"
    mypy_config.add_section(components_section)
    for key in STRICT_SETTINGS:
        mypy_config.set(components_section, key, "false")

    for strict_module in strict_modules:
        strict_section = f"mypy-{strict_module}"
        mypy_config.add_section(strict_section)
        for key in STRICT_SETTINGS:
            mypy_config.set(strict_section, key, "true")

    # Disable strict checks for tests
    tests_section = "mypy-tests.*"
    mypy_config.add_section(tests_section)
    for key in STRICT_SETTINGS:
        mypy_config.set(tests_section, key, "false")

    for ignored_module in IGNORED_MODULES:
        ignored_section = f"mypy-{ignored_module}"
        mypy_config.add_section(ignored_section)
        mypy_config.set(ignored_section, "ignore_errors", "true")

    with io.StringIO() as fp:
        mypy_config.write(fp)
        fp.seek(0)
        return HEADER + fp.read().strip()


def validate(integrations: dict[str, Integration], config: Config) -> None:
    """Validate mypy config."""
    config_path = config.root / "mypy.ini"
    config.cache["mypy_config"] = content = generate_and_validate(config)

    if any(err.plugin == "mypy_config" for err in config.errors):
        return

    with open(str(config_path)) as fp:
        if fp.read().strip() != content:
            config.add_error(
                "mypy_config",
                "File mypy.ini is not up to date. Run python3 -m script.oppfest",
                fixable=True,
            )


def generate(integrations: dict[str, Integration], config: Config) -> None:
    """Generate mypy config."""
    config_path = config.root / "mypy.ini"
    with open(str(config_path), "w") as fp:
        fp.write(f"{config.cache['mypy_config']}\n")
