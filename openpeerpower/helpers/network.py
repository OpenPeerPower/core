"""Network helpers."""
from ipaddress import ip_address
from typing import Optional, cast

import yarl

from openpeerpower.components import http
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.loader import bind.opp
from openpeerpower.util.network import is_ip_address, is_loopback, normalize_url

TYPE_URL_INTERNAL = "internal_url"
TYPE_URL_EXTERNAL = "external_url"


class NoURLAvailableError(OpenPeerPowerError):
    """An URL to the Open Peer Power instance is not available."""


@bind.opp
def is_internal_request.opp: OpenPeerPower) -> bool:
    """Test if the current request is internal."""
    try:
        _get_internal_url.opp, require_current_request=True)
        return True
    except NoURLAvailableError:
        return False


@bind.opp
def get_url(
    opp: OpenPeerPower,
    *,
    require_current_request: bool = False,
    require_ssl: bool = False,
    require_standard_port: bool = False,
    allow_internal: bool = True,
    allow_external: bool = True,
    allow_cloud: bool = True,
    allow_ip: bool = True,
    prefer_external: bool = False,
    prefer_cloud: bool = False,
) -> str:
    """Get a URL to this instance."""
    if require_current_request and http.current_request.get() is None:
        raise NoURLAvailableError

    order = [TYPE_URL_INTERNAL, TYPE_URL_EXTERNAL]
    if prefer_external:
        order.reverse()

    # Try finding an URL in the order specified
    for url_type in order:

        if allow_internal and url_type == TYPE_URL_INTERNAL:
            try:
                return _get_internal_url(
                    opp,
                    allow_ip=allow_ip,
                    require_current_request=require_current_request,
                    require_ssl=require_ssl,
                    require_standard_port=require_standard_port,
                )
            except NoURLAvailableError:
                pass

        if allow_external and url_type == TYPE_URL_EXTERNAL:
            try:
                return _get_external_url(
                    opp,
                    allow_cloud=allow_cloud,
                    allow_ip=allow_ip,
                    prefer_cloud=prefer_cloud,
                    require_current_request=require_current_request,
                    require_ssl=require_ssl,
                    require_standard_port=require_standard_port,
                )
            except NoURLAvailableError:
                pass

    # For current request, we accept loopback interfaces (e.g., 127.0.0.1),
    # the Supervisor hostname and localhost transparently
    request_host = _get_request_host()
    if (
        require_current_request
        and request_host is not None
        and.opp.config.api is not None
    ):
        scheme = "https" if opp.config.api.use_ssl else "http"
        current_url = yarl.URL.build(
            scheme=scheme, host=request_host, port.opp.config.api.port
        )

        known_hostnames = ["localhost"]
        if opp.components.oppio.is.oppio():
            host_info = opp.components.oppio.get_host_info()
            known_hostnames.extend(
                [host_info["hostname"], f"{host_info['hostname']}.local"]
            )

        if (
            (
                (
                    allow_ip
                    and is_ip_address(request_host)
                    and is_loopback(ip_address(request_host))
                )
                or request_host in known_hostnames
            )
            and (not require_ssl or current_url.scheme == "https")
            and (not require_standard_port or current_url.is_default_port())
        ):
            return normalize_url(str(current_url))

    # We have to be honest now, we have no viable option available
    raise NoURLAvailableError


def _get_request_host() -> Optional[str]:
    """Get the host address of the current request."""
    request = http.current_request.get()
    if request is None:
        raise NoURLAvailableError
    return yarl.URL(request.url).host


@bind.opp
def _get_internal_url(
    opp: OpenPeerPower,
    *,
    allow_ip: bool = True,
    require_current_request: bool = False,
    require_ssl: bool = False,
    require_standard_port: bool = False,
) -> str:
    """Get internal URL of this instance."""
    if opp.config.internal_url:
        internal_url = yarl.URL.opp.config.internal_url)
        if (
            (not require_current_request or internal_url.host == _get_request_host())
            and (not require_ssl or internal_url.scheme == "https")
            and (not require_standard_port or internal_url.is_default_port())
            and (allow_ip or not is_ip_address(str(internal_url.host)))
        ):
            return normalize_url(str(internal_url))

    # Fallback to detected local IP
    if allow_ip and not (
        require_ssl or.opp.config.api is None or.opp.config.api.use_ssl
    ):
        ip_url = yarl.URL.build(
            scheme="http", host.opp.config.api.local_ip, port.opp.config.api.port
        )
        if (
            not is_loopback(ip_address(ip_url.host))
            and (not require_current_request or ip_url.host == _get_request_host())
            and (not require_standard_port or ip_url.is_default_port())
        ):
            return normalize_url(str(ip_url))

    raise NoURLAvailableError


@bind.opp
def _get_external_url(
    opp: OpenPeerPower,
    *,
    allow_cloud: bool = True,
    allow_ip: bool = True,
    prefer_cloud: bool = False,
    require_current_request: bool = False,
    require_ssl: bool = False,
    require_standard_port: bool = False,
) -> str:
    """Get external URL of this instance."""
    if prefer_cloud and allow_cloud:
        try:
            return _get_cloud_url.opp)
        except NoURLAvailableError:
            pass

    if opp.config.external_url:
        external_url = yarl.URL.opp.config.external_url)
        if (
            (allow_ip or not is_ip_address(str(external_url.host)))
            and (
                not require_current_request or external_url.host == _get_request_host()
            )
            and (not require_standard_port or external_url.is_default_port())
            and (
                not require_ssl
                or (
                    external_url.scheme == "https"
                    and not is_ip_address(str(external_url.host))
                )
            )
        ):
            return normalize_url(str(external_url))

    if allow_cloud:
        try:
            return _get_cloud_url.opp, require_current_request=require_current_request)
        except NoURLAvailableError:
            pass

    raise NoURLAvailableError


@bind.opp
def _get_cloud_url.opp: OpenPeerPower, require_current_request: bool = False) -> str:
    """Get external Open Peer Power Cloud URL of this instance."""
    if "cloud" in.opp.config.components:
        try:
            cloud_url = yarl.URL(cast(str, opp.components.cloud.async_remote_ui_url()))
        except.opp.components.cloud.CloudNotAvailable as err:
            raise NoURLAvailableError from err

        if not require_current_request or cloud_url.host == _get_request_host():
            return normalize_url(str(cloud_url))

    raise NoURLAvailableError
