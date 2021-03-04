"""Test the HomeKit config flow."""
from unittest.mock import patch

import pytest

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.homekit.const import DOMAIN, SHORT_BRIDGE_NAME
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_NAME, CONF_PORT

from tests.common import MockConfigEntry


def _mock_config_entry_with_options_populated():
    """Create a mock config entry with options populated."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
        options={
            "filter": {
                "include_domains": [
                    "fan",
                    "humidifier",
                    "vacuum",
                    "media_player",
                    "climate",
                    "alarm_control_panel",
                ],
                "exclude_entities": ["climate.front_gate"],
            },
        },
    )


async def test_setup_in_bridge_mode(opp):
    """Test we can setup a new instance in bridge mode."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"include_domains": ["light"]},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "pairing"

    with patch(
        "openpeerpower.components.homekit.config_flow.async_find_next_available_port",
        return_value=12345,
    ), patch(
        "openpeerpower.components.homekit.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.homekit.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    bridge_name = (result3["title"].split(":"))[0]
    assert bridge_name == SHORT_BRIDGE_NAME
    assert result3["data"] == {
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["light"],
            "include_entities": [],
        },
        "exclude_accessory_mode": True,
        "mode": "bridge",
        "name": bridge_name,
        "port": 12345,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_setup_in_bridge_mode_name_taken(opp):
    """Test we can setup a new instance in bridge mode when the name is taken."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: SHORT_BRIDGE_NAME, CONF_PORT: 8000},
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"include_domains": ["light"]},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "pairing"

    with patch(
        "openpeerpower.components.homekit.config_flow.async_find_next_available_port",
        return_value=12345,
    ), patch(
        "openpeerpower.components.homekit.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.homekit.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result3["title"] != SHORT_BRIDGE_NAME
    assert result3["title"].startswith(SHORT_BRIDGE_NAME)
    bridge_name = (result3["title"].split(":"))[0]
    assert result3["data"] == {
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["light"],
            "include_entities": [],
        },
        "exclude_accessory_mode": True,
        "mode": "bridge",
        "name": bridge_name,
        "port": 12345,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 2


async def test_setup_creates_entries_for_accessory_mode_devices(opp):
    """Test we can setup a new instance and we create entries for accessory mode devices."""
    opp.states.async_set("camera.one", "on")
    opp.states.async_set("camera.existing", "on")
    opp.states.async_set("media_player.two", "on", {"device_class": "tv"})

    bridge_mode_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "bridge", CONF_PORT: 8001},
        options={
            "mode": "bridge",
            "filter": {
                "include_entities": ["camera.existing"],
            },
        },
    )
    bridge_mode_entry.add_to_opp(opp)
    accessory_mode_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "accessory", CONF_PORT: 8000},
        options={
            "mode": "accessory",
            "filter": {
                "include_entities": ["camera.existing"],
            },
        },
    )
    accessory_mode_entry.add_to_opp(opp)

    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"include_domains": ["camera", "media_player", "light"]},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "pairing"

    with patch(
        "openpeerpower.components.homekit.config_flow.async_find_next_available_port",
        return_value=12345,
    ), patch(
        "openpeerpower.components.homekit.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.homekit.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result3["title"][:11] == "OPP Bridge"
    bridge_name = (result3["title"].split(":"))[0]
    assert result3["data"] == {
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["media_player", "light"],
            "include_entities": [],
        },
        "exclude_accessory_mode": True,
        "mode": "bridge",
        "name": bridge_name,
        "port": 12345,
    }
    assert len(mock_setup.mock_calls) == 1
    #
    # Existing accessory mode entries should get setup but not duplicated
    #
    # 1 - existing accessory for camera.existing
    # 2 - existing bridge for camera.one
    # 3 - new bridge
    # 4 - camera.one in accessory mode
    # 5 - media_player.two in accessory mode
    assert len(mock_setup_entry.mock_calls) == 5


async def test_import(opp):
    """Test we can import instance."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_NAME: "mock_name", CONF_PORT: 12345}
    )
    entry.add_to_opp(opp)
    await opp.async_block_till_done()

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "port_name_in_use"

    with patch(
        "openpeerpower.components.homekit.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.homekit.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_NAME: "othername", CONF_PORT: 56789},
        )
        await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "othername:56789"
    assert result2["data"] == {
        "name": "othername",
        "port": 56789,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 2


@pytest.mark.parametrize("auto_start", [True, False])
async def test_options_flow_exclude_mode_advanced(auto_start, opp):
    """Test config flow options in exclude mode with advanced options."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_opp(opp)

    opp.states.async_set("climate.old", "off")
    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["fan", "vacuum", "climate", "humidifier"]},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "include_exclude"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entities": ["climate.old"], "include_exclude_mode": "exclude"},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "advanced"

    with patch("openpeerpower.components.homekit.async_setup_entry", return_value=True):
        result3 = await opp.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={"auto_start": auto_start},
        )

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        "auto_start": auto_start,
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["climate.old"],
            "include_domains": ["fan", "vacuum", "climate", "humidifier"],
            "include_entities": [],
        },
    }


async def test_options_flow_exclude_mode_basic(opp):
    """Test config flow options in exclude mode."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_opp(opp)

    opp.states.async_set("climate.old", "off")
    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["fan", "vacuum", "climate"]},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "include_exclude"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entities": ["climate.old"], "include_exclude_mode": "exclude"},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        "auto_start": True,
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["climate.old"],
            "include_domains": ["fan", "vacuum", "climate"],
            "include_entities": [],
        },
    }


async def test_options_flow_include_mode_basic(opp):
    """Test config flow options in include mode."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_opp(opp)

    opp.states.async_set("climate.old", "off")
    opp.states.async_set("climate.new", "off")

    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["fan", "vacuum", "climate"]},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "include_exclude"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entities": ["climate.new"], "include_exclude_mode": "include"},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        "auto_start": True,
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["fan", "vacuum"],
            "include_entities": ["climate.new"],
        },
    }


async def test_options_flow_exclude_mode_with_cameras(opp):
    """Test config flow options in exclude mode with cameras."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_opp(opp)

    opp.states.async_set("climate.old", "off")
    opp.states.async_set("camera.native_h264", "off")
    opp.states.async_set("camera.transcode_h264", "off")
    opp.states.async_set("camera.excluded", "off")

    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["fan", "vacuum", "climate", "camera"]},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "include_exclude"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": ["climate.old", "camera.excluded"],
            "include_exclude_mode": "exclude",
        },
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "cameras"

    result3 = await opp.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"camera_copy": ["camera.native_h264"]},
    )

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        "auto_start": True,
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["climate.old", "camera.excluded"],
            "include_domains": ["fan", "vacuum", "climate", "camera"],
            "include_entities": [],
        },
        "entity_config": {"camera.native_h264": {"video_codec": "copy"}},
    }

    # Now run though again and verify we can turn off copy

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["fan", "vacuum", "climate", "camera"]},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "include_exclude"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": ["climate.old", "camera.excluded"],
            "include_exclude_mode": "exclude",
        },
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "cameras"

    result3 = await opp.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"camera_copy": ["camera.native_h264"]},
    )

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

    assert config_entry.options == {
        "auto_start": True,
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["climate.old", "camera.excluded"],
            "include_domains": ["fan", "vacuum", "climate", "camera"],
            "include_entities": [],
        },
        "entity_config": {"camera.native_h264": {"video_codec": "copy"}},
    }


async def test_options_flow_include_mode_with_cameras(opp):
    """Test config flow options in include mode with cameras."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_opp(opp)

    opp.states.async_set("climate.old", "off")
    opp.states.async_set("camera.native_h264", "off")
    opp.states.async_set("camera.transcode_h264", "off")
    opp.states.async_set("camera.excluded", "off")

    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["fan", "vacuum", "climate", "camera"]},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "include_exclude"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": ["camera.native_h264", "camera.transcode_h264"],
            "include_exclude_mode": "include",
        },
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "cameras"

    result3 = await opp.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"camera_copy": ["camera.native_h264"]},
    )

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        "auto_start": True,
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["fan", "vacuum", "climate"],
            "include_entities": ["camera.native_h264", "camera.transcode_h264"],
        },
        "entity_config": {"camera.native_h264": {"video_codec": "copy"}},
    }

    # Now run though again and verify we can turn off copy

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"
    assert result["data_schema"]({}) == {
        "domains": ["fan", "vacuum", "climate", "camera"],
        "mode": "bridge",
    }
    schema = result["data_schema"].schema
    assert _get_schema_default(schema, "domains") == [
        "fan",
        "vacuum",
        "climate",
        "camera",
    ]
    assert _get_schema_default(schema, "mode") == "bridge"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["fan", "vacuum", "climate", "camera"]},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "include_exclude"
    assert result["data_schema"]({}) == {
        "entities": ["camera.native_h264", "camera.transcode_h264"],
        "include_exclude_mode": "include",
    }
    schema = result["data_schema"].schema
    assert _get_schema_default(schema, "entities") == [
        "camera.native_h264",
        "camera.transcode_h264",
    ]
    assert _get_schema_default(schema, "include_exclude_mode") == "include"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": ["climate.old", "camera.excluded"],
            "include_exclude_mode": "exclude",
        },
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "cameras"
    assert result2["data_schema"]({}) == {"camera_copy": ["camera.native_h264"]}
    schema = result2["data_schema"].schema
    assert _get_schema_default(schema, "camera_copy") == ["camera.native_h264"]

    result3 = await opp.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"camera_copy": []},
    )

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        "auto_start": True,
        "entity_config": {"camera.native_h264": {}},
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["climate.old", "camera.excluded"],
            "include_domains": ["fan", "vacuum", "climate", "camera"],
            "include_entities": [],
        },
        "mode": "bridge",
    }


async def test_options_flow_blocked_when_from_yaml(opp):
    """Test config flow options."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
        options={
            "auto_start": True,
            "filter": {
                "include_domains": [
                    "fan",
                    "humidifier",
                    "vacuum",
                    "media_player",
                    "climate",
                    "alarm_control_panel",
                ],
                "exclude_entities": ["climate.front_gate"],
            },
        },
        source=SOURCE_IMPORT,
    )
    config_entry.add_to_opp(opp)

    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "yaml"

    with patch("openpeerpower.components.homekit.async_setup_entry", return_value=True):
        result2 = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={},
        )
        assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_options_flow_include_mode_basic_accessory(opp):
    """Test config flow options in include mode with a single accessory."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_opp(opp)

    opp.states.async_set("media_player.tv", "off")
    opp.states.async_set("media_player.sonos", "off")

    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"
    assert result["data_schema"]({}) == {
        "domains": [
            "fan",
            "humidifier",
            "vacuum",
            "media_player",
            "climate",
            "alarm_control_panel",
        ],
        "mode": "bridge",
    }

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["media_player"], "mode": "accessory"},
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "include_exclude"
    assert _get_schema_default(result2["data_schema"].schema, "entities") == []

    result3 = await opp.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"entities": "media_player.tv"},
    )
    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        "auto_start": True,
        "mode": "accessory",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": [],
            "include_entities": ["media_player.tv"],
        },
    }


async def test_converting_bridge_to_accessory_mode(opp, hk_driver):
    """Test we can convert a bridge to accessory mode."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"include_domains": ["light"]},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "pairing"

    # We need to actually setup the config entry or the data
    # will not get migrated to options
    with patch(
        "openpeerpower.components.homekit.config_flow.async_find_next_available_port",
        return_value=12345,
    ), patch(
        "openpeerpower.components.homekit.HomeKit.async_start",
        return_value=True,
    ) as mock_async_start:
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result3["title"][:11] == "OPP Bridge"
    bridge_name = (result3["title"].split(":"))[0]
    assert result3["data"] == {
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["light"],
            "include_entities": [],
        },
        "exclude_accessory_mode": True,
        "mode": "bridge",
        "name": bridge_name,
        "port": 12345,
    }
    assert len(mock_async_start.mock_calls) == 1

    config_entry = result3["result"]

    opp.states.async_set("camera.tv", "off")
    opp.states.async_set("camera.sonos", "off")

    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert _get_schema_default(schema, "mode") == "bridge"
    assert _get_schema_default(schema, "domains") == ["light"]

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["camera"], "mode": "accessory"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "include_exclude"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entities": "camera.tv"},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "cameras"

    result3 = await opp.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"camera_copy": ["camera.tv"]},
    )

    assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {
        "auto_start": True,
        "entity_config": {"camera.tv": {"video_codec": "copy"}},
        "mode": "accessory",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": [],
            "include_entities": ["camera.tv"],
        },
    }


def _get_schema_default(schema, key_name):
    """Iterate schema to find a key."""
    for schema_key in schema:
        if schema_key == key_name:
            return schema_key.default()
    raise KeyError(f"{key_name} not found in schema")
