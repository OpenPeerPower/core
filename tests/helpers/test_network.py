"""Test network helper."""
from unittest.mock import Mock, patch

import pytest

from openpeerpower.components import cloud
from openpeerpower.config import async_process_op_core_config
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.network import (
    NoURLAvailableError,
    _get_cloud_url,
    _get_external_url,
    _get_internal_url,
    _get_request_host,
    get_url,
    is_internal_request,
)

from tests.common import mock_component


async def test_get_url_internal(opp: OpenPeerPower):
    """Test getting an instance URL when the user has set an internal URL."""
    assert opp.config.internal_url is None

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_current_request=True)

    # Test with internal URL: http://example.local:8123
    await async_process_op_core_config(
        opp,
        {"internal_url": "http://example.local:8123"},
    )

    assert opp.config.internal_url == "http://example.local:8123"
    assert _get_internal_url(opp) == "http://example.local:8123"
    assert _get_internal_url(opp, allow_ip=False) == "http://example.local:8123"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_current_request=True)

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="example.local"
    ):
        assert (
            _get_internal_url(opp, require_current_request=True)
            == "http://example.local:8123"
        )

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(
                opp. require_current_request=True, require_standard_port=True
            )

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(opp, require_current_request=True, require_ssl=True)

    with patch(
        "openpeerpower.helpers.network._get_request_host",
        return_value="no_match.example.local",
    ), pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_current_request=True)

    # Test with internal URL: https://example.local:8123
    await async_process_op_core_config(
        opp,
        {"internal_url": "https://example.local:8123"},
    )

    assert opp.config.internal_url == "https://example.local:8123"
    assert _get_internal_url(opp) == "https://example.local:8123"
    assert _get_internal_url(opp, allow_ip=False) == "https://example.local:8123"
    assert _get_internal_url(opp, require_ssl=True) == "https://example.local:8123"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_standard_port=True)

    # Test with internal URL: http://example.local:80/
    await async_process_op_core_config(
        opp,
        {"internal_url": "http://example.local:80/"},
    )

    assert opp.config.internal_url == "http://example.local:80/"
    assert _get_internal_url(opp) == "http://example.local"
    assert _get_internal_url(opp, allow_ip=False) == "http://example.local"
    assert _get_internal_url(opp, require_standard_port=True) == "http://example.local"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_ssl=True)

    # Test with internal URL: https://example.local:443
    await async_process_op_core_config(
        opp,
        {"internal_url": "https://example.local:443"},
    )

    assert opp.config.internal_url == "https://example.local:443"
    assert _get_internal_url(opp) == "https://example.local"
    assert _get_internal_url(opp, allow_ip=False) == "https://example.local"
    assert (
        _get_internal_url(opp, require_standard_port=True) == "https://example.local"
    )
    assert _get_internal_url(opp, require_ssl=True) == "https://example.local"

    # Test with internal URL: https://192.168.0.1
    await async_process_op_core_config(
        opp,
        {"internal_url": "https://192.168.0.1"},
    )

    assert opp.config.internal_url == "https://192.168.0.1"
    assert _get_internal_url(opp) == "https://192.168.0.1"
    assert _get_internal_url(opp, require_standard_port=True) == "https://192.168.0.1"
    assert _get_internal_url(opp, require_ssl=True) == "https://192.168.0.1"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, allow_ip=False)

    # Test with internal URL: http://192.168.0.1:8123
    await async_process_op_core_config(
        opp,
        {"internal_url": "http://192.168.0.1:8123"},
    )

    assert opp.config.internal_url == "http://192.168.0.1:8123"
    assert _get_internal_url(opp) == "http://192.168.0.1:8123"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, allow_ip=False)

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="192.168.0.1"
    ):
        assert (
            _get_internal_url(opp, require_current_request=True)
            == "http://192.168.0.1:8123"
        )

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(opp, require_current_request=True, allow_ip=False)

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(
                opp. require_current_request=True, require_standard_port=True
            )

        with pytest.raises(NoURLAvailableError):
            _get_internal_url(opp, require_current_request=True, require_ssl=True)


async def test_get_url_internal_fallback(opp: OpenPeerPower):
    """Test getting an instance URL when the user has not set an internal URL."""
    assert opp.config.internal_url is None

    opp.config.api = Mock(use_ssl=False, port=8123, local_ip="192.168.123.123")
    assert _get_internal_url(opp) == "http://192.168.123.123:8123"

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, allow_ip=False)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_ssl=True)

    opp.config.api = Mock(use_ssl=False, port=80, local_ip="192.168.123.123")
    assert _get_internal_url(opp) == "http://192.168.123.123"
    assert (
        _get_internal_url(opp, require_standard_port=True) == "http://192.168.123.123"
    )

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, allow_ip=False)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_ssl=True)

    opp.config.api = Mock(use_ssl=True, port=443)
    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, allow_ip=False)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_ssl=True)

    # Do no accept any local loopback address as fallback
    opp.config.api = Mock(use_ssl=False, port=80, local_ip="127.0.0.1")
    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, allow_ip=False)

    with pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_ssl=True)


async def test_get_url_external(opp: OpenPeerPower):
    """Test getting an instance URL when the user has set an external URL."""
    assert opp.config.external_url is None

    with pytest.raises(NoURLAvailableError):
        _get_external_url(opp, require_current_request=True)

    # Test with external URL: http://example.com:8123
    await async_process_op_core_config(
        opp,
        {"external_url": "http://example.com:8123"},
    )

    assert opp.config.external_url == "http://example.com:8123"
    assert _get_external_url(opp) == "http://example.com:8123"
    assert _get_external_url(opp, allow_cloud=False) == "http://example.com:8123"
    assert _get_external_url(opp, allow_ip=False) == "http://example.com:8123"
    assert _get_external_url(opp, prefer_cloud=True) == "http://example.com:8123"

    with pytest.raises(NoURLAvailableError):
        _get_external_url(opp, require_standard_port=True)

    with pytest.raises(NoURLAvailableError):
        _get_external_url(opp, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        _get_external_url(opp, require_current_request=True)

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="example.com"
    ):
        assert (
            _get_external_url(opp, require_current_request=True)
            == "http://example.com:8123"
        )

        with pytest.raises(NoURLAvailableError):
            _get_external_url(
                opp. require_current_request=True, require_standard_port=True
            )

        with pytest.raises(NoURLAvailableError):
            _get_external_url(opp, require_current_request=True, require_ssl=True)

    with patch(
        "openpeerpower.helpers.network._get_request_host",
        return_value="no_match.example.com",
    ), pytest.raises(NoURLAvailableError):
        _get_external_url(opp, require_current_request=True)

    # Test with external URL: http://example.com:80/
    await async_process_op_core_config(
        opp,
        {"external_url": "http://example.com:80/"},
    )

    assert opp.config.external_url == "http://example.com:80/"
    assert _get_external_url(opp) == "http://example.com"
    assert _get_external_url(opp, allow_cloud=False) == "http://example.com"
    assert _get_external_url(opp, allow_ip=False) == "http://example.com"
    assert _get_external_url(opp, prefer_cloud=True) == "http://example.com"
    assert _get_external_url(opp, require_standard_port=True) == "http://example.com"

    with pytest.raises(NoURLAvailableError):
        _get_external_url(opp, require_ssl=True)

    # Test with external url: https://example.com:443/
    await async_process_op_core_config(
        opp,
        {"external_url": "https://example.com:443/"},
    )
    assert opp.config.external_url == "https://example.com:443/"
    assert _get_external_url(opp) == "https://example.com"
    assert _get_external_url(opp, allow_cloud=False) == "https://example.com"
    assert _get_external_url(opp, allow_ip=False) == "https://example.com"
    assert _get_external_url(opp, prefer_cloud=True) == "https://example.com"
    assert _get_external_url(opp, require_ssl=False) == "https://example.com"
    assert _get_external_url(opp, require_standard_port=True) == "https://example.com"

    # Test with external URL: https://example.com:80
    await async_process_op_core_config(
        opp,
        {"external_url": "https://example.com:80"},
    )
    assert opp.config.external_url == "https://example.com:80"
    assert _get_external_url(opp) == "https://example.com:80"
    assert _get_external_url(opp, allow_cloud=False) == "https://example.com:80"
    assert _get_external_url(opp, allow_ip=False) == "https://example.com:80"
    assert _get_external_url(opp, prefer_cloud=True) == "https://example.com:80"
    assert _get_external_url(opp, require_ssl=True) == "https://example.com:80"

    with pytest.raises(NoURLAvailableError):
        _get_external_url(opp, require_standard_port=True)

    # Test with external URL: https://192.168.0.1
    await async_process_op_core_config(
        opp,
        {"external_url": "https://192.168.0.1"},
    )
    assert opp.config.external_url == "https://192.168.0.1"
    assert _get_external_url(opp) == "https://192.168.0.1"
    assert _get_external_url(opp, allow_cloud=False) == "https://192.168.0.1"
    assert _get_external_url(opp, prefer_cloud=True) == "https://192.168.0.1"
    assert _get_external_url(opp, require_standard_port=True) == "https://192.168.0.1"

    with pytest.raises(NoURLAvailableError):
        _get_external_url(opp, allow_ip=False)

    with pytest.raises(NoURLAvailableError):
        _get_external_url(opp, require_ssl=True)

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="192.168.0.1"
    ):
        assert (
            _get_external_url(opp, require_current_request=True)
            == "https://192.168.0.1"
        )

        with pytest.raises(NoURLAvailableError):
            _get_external_url(opp, require_current_request=True, allow_ip=False)

        with pytest.raises(NoURLAvailableError):
            _get_external_url(opp, require_current_request=True, require_ssl=True)


async def test_get_cloud_url(opp: OpenPeerPower):
    """Test getting an instance URL when the user has set an external URL."""
    assert opp.config.external_url is None
    opp.config.components.add("cloud")

    with patch.object(
        opp.components.cloud,
        "async_remote_ui_url",
        return_value="https://example.nabu.casa",
    ):
        assert _get_cloud_url(opp) == "https://example.nabu.casa"

        with pytest.raises(NoURLAvailableError):
            _get_cloud_url(opp, require_current_request=True)

        with patch(
            "openpeerpower.helpers.network._get_request_host",
            return_value="example.nabu.casa",
        ):
            assert (
                _get_cloud_url(opp, require_current_request=True)
                == "https://example.nabu.casa"
            )

        with patch(
            "openpeerpower.helpers.network._get_request_host",
            return_value="no_match.nabu.casa",
        ), pytest.raises(NoURLAvailableError):
            _get_cloud_url(opp, require_current_request=True)

    with patch.object(
        opp.components.cloud,
        "async_remote_ui_url",
        side_effect=cloud.CloudNotAvailable,
    ):
        with pytest.raises(NoURLAvailableError):
            _get_cloud_url(opp)


async def test_get_external_url_cloud_fallback(opp: OpenPeerPower):
    """Test getting an external instance URL with cloud fallback."""
    assert opp.config.external_url is None

    # Test with external URL: http://1.1.1.1:8123
    await async_process_op_core_config(
        opp,
        {"external_url": "http://1.1.1.1:8123"},
    )

    assert opp.config.external_url == "http://1.1.1.1:8123"
    assert _get_external_url(opp, prefer_cloud=True) == "http://1.1.1.1:8123"

    # Add Cloud to the previous test
    opp.config.components.add("cloud")
    with patch.object(
        opp.components.cloud,
        "async_remote_ui_url",
        return_value="https://example.nabu.casa",
    ):
        assert _get_external_url(opp, allow_cloud=False) == "http://1.1.1.1:8123"
        assert _get_external_url(opp, allow_ip=False) == "https://example.nabu.casa"
        assert _get_external_url(opp, prefer_cloud=False) == "http://1.1.1.1:8123"
        assert _get_external_url(opp, prefer_cloud=True) == "https://example.nabu.casa"
        assert _get_external_url(opp, require_ssl=True) == "https://example.nabu.casa"
        assert (
            _get_external_url(opp, require_standard_port=True)
            == "https://example.nabu.casa"
        )

    # Test with external URL: https://example.com
    await async_process_op_core_config(
        opp,
        {"external_url": "https://example.com"},
    )

    assert opp.config.external_url == "https://example.com"
    assert _get_external_url(opp, prefer_cloud=True) == "https://example.com"

    # Add Cloud to the previous test
    opp.config.components.add("cloud")
    with patch.object(
        opp.components.cloud,
        "async_remote_ui_url",
        return_value="https://example.nabu.casa",
    ):
        assert _get_external_url(opp, allow_cloud=False) == "https://example.com"
        assert _get_external_url(opp, allow_ip=False) == "https://example.com"
        assert _get_external_url(opp, prefer_cloud=False) == "https://example.com"
        assert _get_external_url(opp, prefer_cloud=True) == "https://example.nabu.casa"
        assert _get_external_url(opp, require_ssl=True) == "https://example.com"
        assert (
            _get_external_url(opp, require_standard_port=True) == "https://example.com"
        )
        assert (
            _get_external_url(opp, prefer_cloud=True, allow_cloud=False)
            == "https://example.com"
        )


async def test_get_url(opp: OpenPeerPower):
    """Test getting an instance URL."""
    assert opp.config.external_url is None
    assert opp.config.internal_url is None

    with pytest.raises(NoURLAvailableError):
        get_url(opp)

    opp.config.api = Mock(use_ssl=False, port=8123, local_ip="192.168.123.123")
    assert get_url(opp) == "http://192.168.123.123:8123"
    assert get_url(opp, prefer_external=True) == "http://192.168.123.123:8123"

    with pytest.raises(NoURLAvailableError):
        get_url(opp, allow_internal=False)

    # Test only external
    opp.config.api = None
    await async_process_op_core_config(
        opp,
        {"external_url": "https://example.com"},
    )
    assert opp.config.external_url == "https://example.com"
    assert opp.config.internal_url is None
    assert get_url(opp) == "https://example.com"

    # Test preference or allowance
    await async_process_op_core_config(
        opp,
        {"internal_url": "http://example.local", "external_url": "https://example.com"},
    )
    assert opp.config.external_url == "https://example.com"
    assert opp.config.internal_url == "http://example.local"
    assert get_url(opp) == "http://example.local"
    assert get_url(opp, prefer_external=True) == "https://example.com"
    assert get_url(opp, allow_internal=False) == "https://example.com"
    assert (
        get_url(opp, prefer_external=True, allow_external=False)
        == "http://example.local"
    )

    with pytest.raises(NoURLAvailableError):
        get_url(opp, allow_external=False, require_ssl=True)

    with pytest.raises(NoURLAvailableError):
        get_url(opp, allow_external=False, allow_internal=False)

    with pytest.raises(NoURLAvailableError):
        get_url(opp, require_current_request=True)

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="example.com"
    ), patch("openpeerpower.components.http.current_request"):
        assert get_url(opp, require_current_request=True) == "https://example.com"
        assert (
            get_url(opp, require_current_request=True, require_ssl=True)
            == "https://example.com"
        )

        with pytest.raises(NoURLAvailableError):
            get_url(opp, require_current_request=True, allow_external=False)

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="example.local"
    ), patch("openpeerpower.components.http.current_request"):
        assert get_url(opp, require_current_request=True) == "http://example.local"

        with pytest.raises(NoURLAvailableError):
            get_url(opp, require_current_request=True, allow_internal=False)

        with pytest.raises(NoURLAvailableError):
            get_url(opp, require_current_request=True, require_ssl=True)

    with patch(
        "openpeerpower.helpers.network._get_request_host",
        return_value="no_match.example.com",
    ), pytest.raises(NoURLAvailableError):
        _get_internal_url(opp, require_current_request=True)


async def test_get_request_host(opp: OpenPeerPower):
    """Test getting the host of the current web request from the request context."""
    with pytest.raises(NoURLAvailableError):
        _get_request_host()

    with patch("openpeerpower.components.http.current_request") as mock_request_context:
        mock_request = Mock()
        mock_request.url = "http://example.com:8123/test/request"
        mock_request_context.get = Mock(return_value=mock_request)

        assert _get_request_host() == "example.com"


async def test_get_current_request_url_with_known_host(
    opp: OpenPeerPower, current_request
):
    """Test getting current request URL with known hosts addresses."""
    opp.config.api = Mock(use_ssl=False, port=8123, local_ip="127.0.0.1")
    assert opp.config.internal_url is None

    with pytest.raises(NoURLAvailableError):
        get_url(opp, require_current_request=True)

    # Ensure we accept localhost
    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="localhost"
    ):
        assert get_url(opp, require_current_request=True) == "http://localhost:8123"
        with pytest.raises(NoURLAvailableError):
            get_url(opp, require_current_request=True, require_ssl=True)
        with pytest.raises(NoURLAvailableError):
            get_url(opp, require_current_request=True, require_standard_port=True)

    # Ensure we accept local loopback ip (e.g., 127.0.0.1)
    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="127.0.0.8"
    ):
        assert get_url(opp, require_current_request=True) == "http://127.0.0.8:8123"
        with pytest.raises(NoURLAvailableError):
            get_url(opp, require_current_request=True, allow_ip=False)

    # Ensure hostname from Supervisor is accepted transparently
    mock_component(opp,  opp.o")
    opp.components.oppio.is.oppio = Mock(return_value=True)
    opp.components.oppio.get_host_info = Mock(
        return_value={"hostname": "openpeerpower"}
    )

    with patch(
        "openpeerpower.helpers.network._get_request_host",
        return_value="openpeerpower.local",
    ):
        assert (
            get_url(opp, require_current_request=True)
            == "http://openpeerpower.local:8123"
        )

    with patch(
        "openpeerpower.helpers.network._get_request_host",
        return_value="openpeerpower",
    ):
        assert (
            get_url(opp, require_current_request=True) == "http://openpeerpower:8123"
        )

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="unknown.local"
    ), pytest.raises(NoURLAvailableError):
        get_url(opp, require_current_request=True)


async def test_is_internal_request(opp: OpenPeerPower):
    """Test if accessing an instance on its internal URL."""
    # Test with internal URL: http://example.local:8123
    await async_process_op_core_config(
        opp,
        {"internal_url": "http://example.local:8123"},
    )

    assert opp.config.internal_url == "http://example.local:8123"
    assert not is_internal_request(opp)

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="example.local"
    ):
        assert is_internal_request(opp)

    with patch(
        "openpeerpower.helpers.network._get_request_host",
        return_value="no_match.example.local",
    ):
        assert not is_internal_request(opp)

    # Test with internal URL: http://192.168.0.1:8123
    await async_process_op_core_config(
        opp,
        {"internal_url": "http://192.168.0.1:8123"},
    )

    assert opp.config.internal_url == "http://192.168.0.1:8123"
    assert not is_internal_request(opp)

    with patch(
        "openpeerpower.helpers.network._get_request_host", return_value="192.168.0.1"
    ):
        assert is_internal_request(opp)
