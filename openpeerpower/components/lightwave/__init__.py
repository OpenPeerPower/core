"""Support for device connected via Lightwave WiFi-link hub."""
from lightwave.lightwave import LWLink
import voluptuous as vol

from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import CONF_HOST, CONF_LIGHTS, CONF_NAME, CONF_SWITCHES
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.discovery import async_load_platform

CONF_SERIAL = "serial"
CONF_PROXY_IP = "proxy_ip"
CONF_PROXY_PORT = "proxy_port"
CONF_TRV = "trv"
CONF_TRVS = "trvs"
DEFAULT_PROXY_PORT = 7878
DEFAULT_PROXY_IP = "127.0.0.1"
DOMAIN = "lightwave"
LIGHTWAVE_LINK = f"{DOMAIN}_link"
LIGHTWAVE_TRV_PROXY = f"{DOMAIN}_proxy"
LIGHTWAVE_TRV_PROXY_PORT = f"{DOMAIN}_proxy_port"


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            vol.All(
                cv.has_at_least_one_key(CONF_LIGHTS, CONF_SWITCHES, CONF_TRV),
                {
                    vol.Required(CONF_HOST): cv.string,
                    vol.Optional(CONF_LIGHTS, default={}): {
                        cv.string: vol.Schema({vol.Required(CONF_NAME): cv.string})
                    },
                    vol.Optional(CONF_SWITCHES, default={}): {
                        cv.string: vol.Schema({vol.Required(CONF_NAME): cv.string})
                    },
                    vol.Optional(CONF_TRV, default={}): {
                        vol.Optional(
                            CONF_PROXY_PORT, default=DEFAULT_PROXY_PORT
                        ): cv.port,
                        vol.Optional(
                            CONF_PROXY_IP, default=DEFAULT_PROXY_IP
                        ): cv.string,
                        vol.Required(CONF_TRVS, default={}): {
                            cv.string: vol.Schema(
                                {
                                    vol.Required(CONF_NAME): cv.string,
                                    vol.Required(CONF_SERIAL): cv.string,
                                }
                            )
                        },
                    },
                },
            )
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Try to start embedded Lightwave broker."""
    host = config[DOMAIN][CONF_HOST]
    lwlink = LWLink(host)
    opp.data[LIGHTWAVE_LINK] = lwlink

    lights = config[DOMAIN][CONF_LIGHTS]
    if lights:
        opp.async_create_task(async_load_platform(opp, "light", DOMAIN, lights, config))

    switches = config[DOMAIN][CONF_SWITCHES]
    if switches:
        opp.async_create_task(
            async_load_platform(opp, "switch", DOMAIN, switches, config)
        )

    trv = config[DOMAIN][CONF_TRV]
    if trv:
        trvs = trv[CONF_TRVS]
        proxy_ip = trv[CONF_PROXY_IP]
        proxy_port = trv[CONF_PROXY_PORT]
        lwlink.set_trv_proxy(proxy_ip, proxy_port)

        platforms = [CLIMATE_DOMAIN, SENSOR_DOMAIN]
        for platform in platforms:
            opp.async_create_task(
                async_load_platform(opp, platform, DOMAIN, trvs, config)
            )

    return True
