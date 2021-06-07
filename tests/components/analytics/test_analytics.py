"""The tests for the analytics ."""
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import aiohttp
import pytest

from openpeerpower.components.analytics.analytics import Analytics
from openpeerpower.components.analytics.const import (
    ANALYTICS_ENDPOINT_URL,
    ANALYTICS_ENDPOINT_URL_DEV,
    ATTR_BASE,
    ATTR_DIAGNOSTICS,
    ATTR_PREFERENCES,
    ATTR_STATISTICS,
    ATTR_USAGE,
)
from openpeerpower.components.api import ATTR_UUID
from openpeerpower.const import ATTR_DOMAIN
from openpeerpower.loader import IntegrationNotFound
from openpeerpower.setup import async_setup_component

MOCK_UUID = "abcdefg"
MOCK_VERSION = "1970.1.0"
MOCK_VERSION_DEV = "1970.1.0.dev0"
MOCK_VERSION_NIGHTLY = "1970.1.0.dev19700101"


async def test_no_send(opp, caplog, aioclient_mock):
    """Test send when no prefrences are defined."""
    analytics = Analytics(opp)
    with patch(
        "openpeerpower.components.oppio.is_oppio",
        side_effect=Mock(return_value=False),
    ):
        assert not analytics.preferences[ATTR_BASE]

        await analytics.send_analytics()

    assert "Nothing to submit" in caplog.text
    assert len(aioclient_mock.mock_calls) == 0


async def test_load_with_supervisor_diagnostics(opp):
    """Test loading with a supervisor that has diagnostics enabled."""
    analytics = Analytics(opp)
    assert not analytics.preferences[ATTR_DIAGNOSTICS]
    with patch(
        "openpeerpower.components.oppio.get_supervisor_info",
        side_effect=Mock(return_value={"diagnostics": True}),
    ), patch(
        "openpeerpower.components.oppio.is_oppio",
        side_effect=Mock(return_value=True),
    ):
        await analytics.load()
    assert analytics.preferences[ATTR_DIAGNOSTICS]


async def test_load_with_supervisor_without_diagnostics(opp):
    """Test loading with a supervisor that has not diagnostics enabled."""
    analytics = Analytics(opp)
    analytics._data[ATTR_PREFERENCES][ATTR_DIAGNOSTICS] = True

    assert analytics.preferences[ATTR_DIAGNOSTICS]

    with patch(
        "openpeerpower.components.oppio.get_supervisor_info",
        side_effect=Mock(return_value={"diagnostics": False}),
    ), patch(
        "openpeerpower.components.oppio.is_oppio",
        side_effect=Mock(return_value=True),
    ):
        await analytics.load()

    assert not analytics.preferences[ATTR_DIAGNOSTICS]


async def test_failed_to_send(opp, caplog, aioclient_mock):
    """Test failed to send payload."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=400)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True})
    assert analytics.preferences[ATTR_BASE]

    with patch("openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION):
        await analytics.send_analytics()
    assert (
        f"Sending analytics failed with statuscode 400 from {ANALYTICS_ENDPOINT_URL}"
        in caplog.text
    )


async def test_failed_to_send_raises(opp, caplog, aioclient_mock):
    """Test raises when failed to send payload."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, exc=aiohttp.ClientError())
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True})
    assert analytics.preferences[ATTR_BASE]

    with patch("openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION):
        await analytics.send_analytics()
    assert "Error sending analytics" in caplog.text


async def test_send_base(opp, caplog, aioclient_mock):
    """Test send base prefrences are defined."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)

    await analytics.save_preferences({ATTR_BASE: True})
    assert analytics.preferences[ATTR_BASE]

    with patch("uuid.UUID.hex", new_callable=PropertyMock) as hex, patch(
        "openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION
    ):
        hex.return_value = MOCK_UUID
        await analytics.send_analytics()

    assert f"'uuid': '{MOCK_UUID}'" in caplog.text
    assert f"'version': '{MOCK_VERSION}'" in caplog.text
    assert "'installation_type':" in caplog.text
    assert "'integration_count':" not in caplog.text
    assert "'integrations':" not in caplog.text


async def test_send_base_with_supervisor(opp, caplog, aioclient_mock):
    """Test send base prefrences are defined."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)

    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True})
    assert analytics.preferences[ATTR_BASE]

    with patch(
        "openpeerpower.components.oppio.get_supervisor_info",
        side_effect=Mock(
            return_value={"supported": True, "healthy": True, "arch": "amd64"}
        ),
    ), patch(
        "openpeerpower.components.oppio.get_os_info",
        side_effect=Mock(return_value={"board": "blue", "version": "123"}),
    ), patch(
        "openpeerpower.components.oppio.get_info",
        side_effect=Mock(return_value={}),
    ), patch(
        "openpeerpower.components.oppio.get_host_info",
        side_effect=Mock(return_value={}),
    ), patch(
        "openpeerpower.components.oppio.is_oppio",
        side_effect=Mock(return_value=True),
    ), patch(
        "uuid.UUID.hex", new_callable=PropertyMock
    ) as hex, patch(
        "openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION
    ):
        hex.return_value = MOCK_UUID
        await analytics.load()

        await analytics.send_analytics()

    assert f"'uuid': '{MOCK_UUID}'" in caplog.text
    assert f"'version': '{MOCK_VERSION}'" in caplog.text
    assert (
        "'supervisor': {'healthy': True, 'supported': True, 'arch': 'amd64'}"
        in caplog.text
    )
    assert "'operating_system': {'board': 'blue', 'version': '123'}" in caplog.text
    assert "'installation_type':" in caplog.text
    assert "'integration_count':" not in caplog.text
    assert "'integrations':" not in caplog.text


async def test_send_usage(opp, caplog, aioclient_mock):
    """Test send usage prefrences are defined."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True, ATTR_USAGE: True})

    assert analytics.preferences[ATTR_BASE]
    assert analytics.preferences[ATTR_USAGE]
    opp.config.components = ["default_config"]

    with patch("openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION):
        await analytics.send_analytics()

    assert "'integrations': ['default_config']" in caplog.text
    assert "'integration_count':" not in caplog.text


async def test_send_usage_with_supervisor(opp, caplog, aioclient_mock):
    """Test send usage with supervisor prefrences are defined."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)

    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True, ATTR_USAGE: True})
    assert analytics.preferences[ATTR_BASE]
    assert analytics.preferences[ATTR_USAGE]
    opp.config.components = ["default_config"]

    with patch(
        "openpeerpower.components.oppio.get_supervisor_info",
        side_effect=Mock(
            return_value={
                "healthy": True,
                "supported": True,
                "arch": "amd64",
                "addons": [{"slug": "test_addon"}],
            }
        ),
    ), patch(
        "openpeerpower.components.oppio.get_os_info",
        side_effect=Mock(return_value={}),
    ), patch(
        "openpeerpower.components.oppio.get_info",
        side_effect=Mock(return_value={}),
    ), patch(
        "openpeerpower.components.oppio.get_host_info",
        side_effect=Mock(return_value={}),
    ), patch(
        "openpeerpower.components.oppio.async_get_addon_info",
        side_effect=AsyncMock(
            return_value={
                "slug": "test_addon",
                "protected": True,
                "version": "1",
                "auto_update": False,
            }
        ),
    ), patch(
        "openpeerpower.components.oppio.is_oppio",
        side_effect=Mock(return_value=True),
    ), patch(
        "openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION
    ):
        await analytics.send_analytics()
    assert (
        "'addons': [{'slug': 'test_addon', 'protected': True, 'version': '1', 'auto_update': False}]"
        in caplog.text
    )
    assert "'addon_count':" not in caplog.text


async def test_send_statistics(opp, caplog, aioclient_mock):
    """Test send statistics prefrences are defined."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True, ATTR_STATISTICS: True})
    assert analytics.preferences[ATTR_BASE]
    assert analytics.preferences[ATTR_STATISTICS]
    opp.config.components = ["default_config"]

    with patch("openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION):
        await analytics.send_analytics()
    assert (
        "'state_count': 0, 'automation_count': 0, 'integration_count': 1, 'user_count': 0"
        in caplog.text
    )
    assert "'integrations':" not in caplog.text


async def test_send_statistics_one_integration_fails(opp, caplog, aioclient_mock):
    """Test send statistics prefrences are defined."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True, ATTR_STATISTICS: True})
    assert analytics.preferences[ATTR_BASE]
    assert analytics.preferences[ATTR_STATISTICS]
    opp.config.components = ["default_config"]

    with patch(
        "openpeerpower.components.analytics.analytics.async_get_integration",
        side_effect=IntegrationNotFound("any"),
    ), patch("openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION):
        await analytics.send_analytics()

    post_call = aioclient_mock.mock_calls[0]
    assert "uuid" in post_call[2]
    assert post_call[2]["integration_count"] == 0


async def test_send_statistics_async_get_integration_unknown_exception(
    opp, caplog, aioclient_mock
):
    """Test send statistics prefrences are defined."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True, ATTR_STATISTICS: True})
    assert analytics.preferences[ATTR_BASE]
    assert analytics.preferences[ATTR_STATISTICS]
    opp.config.components = ["default_config"]

    with pytest.raises(ValueError), patch(
        "openpeerpower.components.analytics.analytics.async_get_integration",
        side_effect=ValueError,
    ), patch("openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION):
        await analytics.send_analytics()


async def test_send_statistics_with_supervisor(opp, caplog, aioclient_mock):
    """Test send statistics prefrences are defined."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True, ATTR_STATISTICS: True})
    assert analytics.preferences[ATTR_BASE]
    assert analytics.preferences[ATTR_STATISTICS]

    with patch(
        "openpeerpower.components.oppio.get_supervisor_info",
        side_effect=Mock(
            return_value={
                "healthy": True,
                "supported": True,
                "arch": "amd64",
                "addons": [{"slug": "test_addon"}],
            }
        ),
    ), patch(
        "openpeerpower.components.oppio.get_os_info",
        side_effect=Mock(return_value={}),
    ), patch(
        "openpeerpower.components.oppio.get_info",
        side_effect=Mock(return_value={}),
    ), patch(
        "openpeerpower.components.oppio.get_host_info",
        side_effect=Mock(return_value={}),
    ), patch(
        "openpeerpower.components.oppio.async_get_addon_info",
        side_effect=AsyncMock(
            return_value={
                "slug": "test_addon",
                "protected": True,
                "version": "1",
                "auto_update": False,
            }
        ),
    ), patch(
        "openpeerpower.components.oppio.is_oppio",
        side_effect=Mock(return_value=True),
    ), patch(
        "openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION
    ):
        await analytics.send_analytics()
    assert "'addon_count': 1" in caplog.text
    assert "'integrations':" not in caplog.text


async def test_reusing_uuid(opp, aioclient_mock):
    """Test reusing the stored UUID."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)
    analytics._data[ATTR_UUID] = "NOT_MOCK_UUID"

    await analytics.save_preferences({ATTR_BASE: True})

    with patch("uuid.UUID.hex", new_callable=PropertyMock) as hex, patch(
        "openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION
    ):
        # This is not actually called but that in itself prove the test
        hex.return_value = MOCK_UUID
        await analytics.send_analytics()

    assert analytics.uuid == "NOT_MOCK_UUID"


async def test_custom_integrations(opp, aioclient_mock, enable_custom_integrations):
    """Test sending custom integrations."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)
    assert await async_setup_component(opp, "test_package", {"test_package": {}})
    await analytics.save_preferences({ATTR_BASE: True, ATTR_USAGE: True})

    with patch("openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION):
        await analytics.send_analytics()

    payload = aioclient_mock.mock_calls[0][2]
    assert payload["custom_integrations"][0][ATTR_DOMAIN] == "test_package"


async def test_dev_url(opp, aioclient_mock):
    """Test sending payload to dev url."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL_DEV, status=200)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True})

    with patch(
        "openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION_DEV
    ):
        await analytics.send_analytics()

    payload = aioclient_mock.mock_calls[0]
    assert str(payload[1]) == ANALYTICS_ENDPOINT_URL_DEV


async def test_dev_url_error(opp, aioclient_mock, caplog):
    """Test sending payload to dev url that returns error."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL_DEV, status=400)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True})

    with patch(
        "openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION_DEV
    ):

        await analytics.send_analytics()

    payload = aioclient_mock.mock_calls[0]
    assert str(payload[1]) == ANALYTICS_ENDPOINT_URL_DEV
    assert (
        f"Sending analytics failed with statuscode 400 from {ANALYTICS_ENDPOINT_URL_DEV}"
        in caplog.text
    )


async def test_nightly_endpoint(opp, aioclient_mock):
    """Test sending payload to production url when running nightly."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    analytics = Analytics(opp)
    await analytics.save_preferences({ATTR_BASE: True})

    with patch(
        "openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION_NIGHTLY
    ):

        await analytics.send_analytics()

    payload = aioclient_mock.mock_calls[0]
    assert str(payload[1]) == ANALYTICS_ENDPOINT_URL
