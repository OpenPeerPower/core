"""Test integration initialization."""
from unittest.mock import patch

from openpeerpower import config_entries
from openpeerpower.components.oppio.handler import OppioAPIError
from openpeerpower.components.ozw import DOMAIN, PLATFORMS, const
from openpeerpower.const import ATTR_RESTORED, STATE_UNAVAILABLE

from .common import setup_ozw

from tests.common import MockConfigEntry


async def test_init_entry(opp, generic_data):
    """Test setting up config entry."""
    await setup_ozw(opp, fixture=generic_data)

    # Verify integration + platform loaded.
    assert "ozw" in opp.config.components
    for platform in PLATFORMS:
        assert platform in opp.config.components, platform
        assert f"{platform}.{DOMAIN}" in opp.config.components, f"{platform}.{DOMAIN}"

    # Verify services registered
    assert opp.services.has_service(DOMAIN, const.SERVICE_ADD_NODE)
    assert opp.services.has_service(DOMAIN, const.SERVICE_REMOVE_NODE)


async def test_setup_entry_without_mqtt(opp):
    """Test setting up config entry without mqtt integration setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="OpenZWave",
    )
    entry.add_to_opp(opp)

    assert not await opp.config_entries.async_setup(entry.entry_id)


async def test_publish_without_mqtt(opp, caplog):
    """Test publish without mqtt integration setup."""
    with patch("openpeerpower.components.ozw.OZWOptions") as ozw_options:
        await setup_ozw(opp)

        send_message = ozw_options.call_args[1]["send_message"]

        mqtt_entries = opp.config_entries.async_entries("mqtt")
        mqtt_entry = mqtt_entries[0]
        await opp.config_entries.async_remove(mqtt_entry.entry_id)
        await opp.async_block_till_done()

        assert not opp.config_entries.async_entries("mqtt")

        # Sending a message should not error with the MQTT integration not set up.
        send_message("test_topic", "test_payload")
        await opp.async_block_till_done()

    assert "MQTT integration is not set up" in caplog.text


async def test_unload_entry(opp, generic_data, switch_msg, caplog):
    """Test unload the config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave",
    )
    entry.add_to_opp(opp)
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED

    receive_message = await setup_ozw(opp, entry=entry, fixture=generic_data)

    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert len(opp.states.async_entity_ids("switch")) == 1

    await opp.config_entries.async_unload(entry.entry_id)

    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
    entities = opp.states.async_entity_ids("switch")
    assert len(entities) == 1
    for entity in entities:
        assert opp.states.get(entity).state == STATE_UNAVAILABLE
        assert opp.states.get(entity).attributes.get(ATTR_RESTORED)

    # Send a message for a switch from the broker to check that
    # all entity topic subscribers are unsubscribed.
    receive_message(switch_msg)
    await opp.async_block_till_done()

    assert len(opp.states.async_entity_ids("switch")) == 1
    for entity in entities:
        assert opp.states.get(entity).state == STATE_UNAVAILABLE
        assert opp.states.get(entity).attributes.get(ATTR_RESTORED)

    # Load the integration again and check that there are no errors when
    # adding the entities.
    # This asserts that we have unsubscribed the entity addition signals
    # when unloading the integration previously.
    await setup_ozw(opp, entry=entry, fixture=generic_data)
    await opp.async_block_till_done()

    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert len(opp.states.async_entity_ids("switch")) == 1
    for record in caplog.records:
        assert record.levelname != "ERROR"


async def test_remove_entry(opp, stop_addon, uninstall_addon, caplog):
    """Test remove the config entry."""
    # test successful remove without created add-on
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave",
        data={"integration_created_addon": False},
    )
    entry.add_to_opp(opp)
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1

    await opp.config_entries.async_remove(entry.entry_id)

    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0

    # test successful remove with created add-on
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave",
        data={"integration_created_addon": True},
    )
    entry.add_to_opp(opp)
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1

    await opp.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert uninstall_addon.call_count == 1
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0
    stop_addon.reset_mock()
    uninstall_addon.reset_mock()

    # test add-on stop failure
    entry.add_to_opp(opp)
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    stop_addon.side_effect = OppioAPIError()

    await opp.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert uninstall_addon.call_count == 0
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0
    assert "Failed to stop the OpenZWave add-on" in caplog.text
    stop_addon.side_effect = None
    stop_addon.reset_mock()
    uninstall_addon.reset_mock()

    # test add-on uninstall failure
    entry.add_to_opp(opp)
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    uninstall_addon.side_effect = OppioAPIError()

    await opp.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert uninstall_addon.call_count == 1
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0
    assert "Failed to uninstall the OpenZWave add-on" in caplog.text


async def test_setup_entry_with_addon(opp, get_addon_discovery_info):
    """Test set up entry using OpenZWave add-on."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="OpenZWave",
        data={"use_addon": True},
    )
    entry.add_to_opp(opp)

    with patch("openpeerpower.components.ozw.MQTTClient", autospec=True) as mock_client:
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    assert mock_client.return_value.start_client.call_count == 1

    # Verify integration + platform loaded.
    assert "ozw" in opp.config.components
    for platform in PLATFORMS:
        assert platform in opp.config.components, platform
        assert f"{platform}.{DOMAIN}" in opp.config.components, f"{platform}.{DOMAIN}"

    # Verify services registered
    assert opp.services.has_service(DOMAIN, const.SERVICE_ADD_NODE)
    assert opp.services.has_service(DOMAIN, const.SERVICE_REMOVE_NODE)


async def test_setup_entry_without_addon_info(opp, get_addon_discovery_info):
    """Test set up entry using OpenZWave add-on but missing discovery info."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="OpenZWave",
        data={"use_addon": True},
    )
    entry.add_to_opp(opp)

    get_addon_discovery_info.return_value = None

    with patch("openpeerpower.components.ozw.MQTTClient", autospec=True) as mock_client:
        assert not await opp.config_entries.async_setup(entry.entry_id)

    assert mock_client.return_value.start_client.call_count == 0
    assert entry.state is config_entries.ConfigEntryState.SETUP_RETRY


async def test_unload_entry_with_addon(
    opp, get_addon_discovery_info, generic_data, switch_msg, caplog
):
    """Test unload the config entry using the OpenZWave add-on."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="OpenZWave",
        data={"use_addon": True},
    )
    entry.add_to_opp(opp)

    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED

    with patch("openpeerpower.components.ozw.MQTTClient", autospec=True) as mock_client:
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    assert mock_client.return_value.start_client.call_count == 1
    assert entry.state is config_entries.ConfigEntryState.LOADED

    await opp.config_entries.async_unload(entry.entry_id)

    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
