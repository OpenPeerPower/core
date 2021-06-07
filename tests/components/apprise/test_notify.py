"""The tests for the apprise notification platform."""
from unittest.mock import MagicMock, patch

from openpeerpower.setup import async_setup_component

BASE_COMPONENT = "notify"


async def test_apprise_config_load_fail01(opp):
    """Test apprise configuration failures 1."""

    config = {
        BASE_COMPONENT: {"name": "test", "platform": "apprise", "config": "/path/"}
    }

    with patch("apprise.AppriseConfig.add", return_value=False):
        assert await async_setup_component(opp, BASE_COMPONENT, config)
        await opp.async_block_till_done()

        # Test that our service failed to load
        assert not opp.services.has_service(BASE_COMPONENT, "test")


async def test_apprise_config_load_fail02(opp):
    """Test apprise configuration failures 2."""

    config = {
        BASE_COMPONENT: {"name": "test", "platform": "apprise", "config": "/path/"}
    }

    with patch("apprise.Apprise.add", return_value=False), patch(
        "apprise.AppriseConfig.add", return_value=True
    ):
        assert await async_setup_component(opp, BASE_COMPONENT, config)
        await opp.async_block_till_done()

        # Test that our service failed to load
        assert not opp.services.has_service(BASE_COMPONENT, "test")


async def test_apprise_config_load_okay(opp, tmp_path):
    """Test apprise configuration failures."""

    # Test cases where our URL is invalid
    d = tmp_path / "apprise-config"
    d.mkdir()
    f = d / "apprise"
    f.write_text("mailto://user:pass@example.com/")

    config = {BASE_COMPONENT: {"name": "test", "platform": "apprise", "config": str(f)}}

    assert await async_setup_component(opp, BASE_COMPONENT, config)
    await opp.async_block_till_done()

    # Valid configuration was loaded; our service is good
    assert opp.services.has_service(BASE_COMPONENT, "test")


async def test_apprise_url_load_fail(opp):
    """Test apprise url failure."""

    config = {
        BASE_COMPONENT: {
            "name": "test",
            "platform": "apprise",
            "url": "mailto://user:pass@example.com",
        }
    }
    with patch("apprise.Apprise.add", return_value=False):
        assert await async_setup_component(opp, BASE_COMPONENT, config)
        await opp.async_block_till_done()

        # Test that our service failed to load
        assert not opp.services.has_service(BASE_COMPONENT, "test")


async def test_apprise_notification(opp):
    """Test apprise notification."""

    config = {
        BASE_COMPONENT: {
            "name": "test",
            "platform": "apprise",
            "url": "mailto://user:pass@example.com",
        }
    }

    # Our Message
    data = {"title": "Test Title", "message": "Test Message"}

    with patch("apprise.Apprise") as mock_apprise:
        obj = MagicMock()
        obj.add.return_value = True
        obj.notify.return_value = True
        mock_apprise.return_value = obj
        assert await async_setup_component(opp, BASE_COMPONENT, config)
        await opp.async_block_till_done()

        # Test the existence of our service
        assert opp.services.has_service(BASE_COMPONENT, "test")

        # Test the call to our underlining notify() call
        await opp.services.async_call(BASE_COMPONENT, "test", data)
        await opp.async_block_till_done()

        # Validate calls were made under the hood correctly
        obj.add.assert_called_once_with([config[BASE_COMPONENT]["url"]])
        obj.notify.assert_called_once_with(
            **{"body": data["message"], "title": data["title"], "tag": None}
        )


async def test_apprise_notification_with_target(opp, tmp_path):
    """Test apprise notification with a target."""

    # Test cases where our URL is invalid
    d = tmp_path / "apprise-config"
    d.mkdir()
    f = d / "apprise"

    # Write 2 config entries each assigned to different tags
    f.write_text("devops=mailto://user:pass@example.com/\r\n")
    f.write_text("system,alert=syslog://\r\n")

    config = {BASE_COMPONENT: {"name": "test", "platform": "apprise", "config": str(f)}}

    # Our Message, only notify the services tagged with "devops"
    data = {"title": "Test Title", "message": "Test Message", "target": ["devops"]}

    with patch("apprise.Apprise") as mock_apprise:
        apprise_obj = MagicMock()
        apprise_obj.add.return_value = True
        apprise_obj.notify.return_value = True
        mock_apprise.return_value = apprise_obj
        assert await async_setup_component(opp, BASE_COMPONENT, config)
        await opp.async_block_till_done()

        # Test the existence of our service
        assert opp.services.has_service(BASE_COMPONENT, "test")

        # Test the call to our underlining notify() call
        await opp.services.async_call(BASE_COMPONENT, "test", data)
        await opp.async_block_till_done()

        # Validate calls were made under the hood correctly
        apprise_obj.notify.assert_called_once_with(
            **{"body": data["message"], "title": data["title"], "tag": data["target"]}
        )
