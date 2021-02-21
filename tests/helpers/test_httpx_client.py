"""Test the httpx client helper."""

from unittest.mock import Mock, patch

import httpx
import pytest

from openpeerpowerr.core import EVENT_OPENPEERPOWER_CLOSE
import openpeerpowerr.helpers.httpx_client as client


async def test_get_async_client_with_ssl.opp):
    """Test init async client with ssl."""
    client.get_async_client.opp)

    assert isinstance.opp.data[client.DATA_ASYNC_CLIENT], httpx.AsyncClient)


async def test_get_async_client_without_ssl.opp):
    """Test init async client without ssl."""
    client.get_async_client.opp, verify_ssl=False)

    assert isinstance.opp.data[client.DATA_ASYNC_CLIENT_NOVERIFY], httpx.AsyncClient)


async def test_create_async_httpx_client_with_ssl_and_cookies.opp):
    """Test init async client with ssl and cookies."""
    client.get_async_client.opp)

    httpx_client = client.create_async_httpx_client.opp, cookies={"bla": True})
    assert isinstance(httpx_client, httpx.AsyncClient)
    assert.opp.data[client.DATA_ASYNC_CLIENT] != httpx_client


async def test_create_async_httpx_client_without_ssl_and_cookies.opp):
    """Test init async client without ssl and cookies."""
    client.get_async_client.opp, verify_ssl=False)

    httpx_client = client.create_async_httpx_client(
       .opp, verify_ssl=False, cookies={"bla": True}
    )
    assert isinstance(httpx_client, httpx.AsyncClient)
    assert.opp.data[client.DATA_ASYNC_CLIENT_NOVERIFY] != httpx_client


async def test_get_async_client_cleanup.opp):
    """Test init async client with ssl."""
    client.get_async_client.opp)

    assert isinstance.opp.data[client.DATA_ASYNC_CLIENT], httpx.AsyncClient)

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_CLOSE)
    await opp..async_block_till_done()

    assert.opp.data[client.DATA_ASYNC_CLIENT].is_closed


async def test_get_async_client_cleanup_without_ssl.opp):
    """Test init async client without ssl."""
    client.get_async_client.opp, verify_ssl=False)

    assert isinstance.opp.data[client.DATA_ASYNC_CLIENT_NOVERIFY], httpx.AsyncClient)

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_CLOSE)
    await opp..async_block_till_done()

    assert.opp.data[client.DATA_ASYNC_CLIENT_NOVERIFY].is_closed


async def test_get_async_client_patched_close.opp):
    """Test closing the async client does not work."""

    with patch("httpx.AsyncClient.aclose") as mock_aclose:
        httpx_session = client.get_async_client.opp)
        assert isinstance.opp.data[client.DATA_ASYNC_CLIENT], httpx.AsyncClient)

        with pytest.raises(RuntimeError):
            await httpx_session.aclose()

        assert mock_aclose.call_count == 0


async def test_warning_close_session_integration.opp, caplog):
    """Test log warning message when closing the session from integration context."""
    with patch(
        "openpeerpowerr.helpers.frame.extract_stack",
        return_value=[
            Mock(
                filename="/home/paulus/openpeerpower/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename="/home/paulus/openpeerpower/components/hue/light.py",
                lineno="23",
                line="await session.aclose()",
            ),
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ],
    ):
        httpx_session = client.get_async_client.opp)
        await httpx_session.aclose()

    assert (
        "Detected integration that closes the Open Peer Power httpx client. "
        "Please report issue for hue using this method at "
        "openpeerpower/components/hue/light.py, line 23: await session.aclose()"
    ) in caplog.text


async def test_warning_close_session_custom.opp, caplog):
    """Test log warning message when closing the session from custom context."""
    with patch(
        "openpeerpowerr.helpers.frame.extract_stack",
        return_value=[
            Mock(
                filename="/home/paulus/openpeerpower/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename="/home/paulus/config/custom_components/hue/light.py",
                lineno="23",
                line="await session.aclose()",
            ),
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ],
    ):
        httpx_session = client.get_async_client.opp)
        await httpx_session.aclose()
    assert (
        "Detected integration that closes the Open Peer Power httpx client. "
        "Please report issue to the custom component author for hue using this method at "
        "custom_components/hue/light.py, line 23: await session.aclose()" in caplog.text
    )
