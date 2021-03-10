"""Provide info to system health."""
from opp_net import Cloud
from yarl import URL

from openpeerpower.components import system_health
from openpeerpower.core import OpenPeerPower, callback

from .client import CloudClient
from .const import DOMAIN


@callback
def async_register(
    opp: OpenPeerPower, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info, "/config/cloud")


async def system_health_info(opp):
    """Get info for the info page."""
    cloud: Cloud = opp.data[DOMAIN]
    client: CloudClient = cloud.client

    data = {
        "logged_in": cloud.is_logged_in,
    }

    if cloud.is_logged_in:
        data["subscription_expiration"] = cloud.expiration_date
        data["relayer_connected"] = cloud.is_connected
        data["remote_enabled"] = client.prefs.remote_enabled
        data["remote_connected"] = cloud.remote.is_connected
        data["alexa_enabled"] = client.prefs.alexa_enabled
        data["google_enabled"] = client.prefs.google_enabled

    data["can_reach_cert_server"] = system_health.async_check_can_reach_url(
        opp, cloud.acme_directory_server
    )
    data["can_reach_cloud_auth"] = system_health.async_check_can_reach_url(
        opp,
        f"https://cognito-idp.{cloud.region}.amazonaws.com/{cloud.user_pool_id}/.well-known/jwks.json",
    )
    data["can_reach_cloud"] = system_health.async_check_can_reach_url(
        opp, URL(cloud.relayer).with_scheme("https").with_path("/status")
    )

    return data
