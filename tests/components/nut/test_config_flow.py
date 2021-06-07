"""Test the Network UPS Tools (NUT) config flow."""

from unittest.mock import patch

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.nut.const import DOMAIN
from openpeerpower.const import CONF_RESOURCES, CONF_SCAN_INTERVAL

from .util import _get_mock_pynutclient

from tests.common import MockConfigEntry

VALID_CONFIG = {
    "host": "localhost",
    "port": 123,
    "name": "name",
    "resources": ["battery.charge"],
}


async def test_form_zeroconf(opp):
    """Test we can setup from zeroconf."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data={"host": "192.168.1.5", "port": 1234},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_pynut = _get_mock_pynutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    assert result2["step_id"] == "resources"
    assert result2["type"] == "form"

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ), patch(
        "openpeerpower.components.nut.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {"resources": ["battery.voltage", "ups.status", "ups.status.display"]},
        )
        await opp.async_block_till_done()

    assert result3["type"] == "create_entry"
    assert result3["title"] == "192.168.1.5:1234"
    assert result3["data"] == {
        "host": "192.168.1.5",
        "password": "test-password",
        "port": 1234,
        "resources": ["battery.voltage", "ups.status", "ups.status.display"],
        "username": "test-username",
    }
    assert result3["result"].unique_id is None
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_user_one_ups(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_pynut = _get_mock_pynutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
                "port": 2222,
            },
        )

    assert result2["step_id"] == "resources"
    assert result2["type"] == "form"

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ), patch(
        "openpeerpower.components.nut.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {"resources": ["battery.voltage", "ups.status", "ups.status.display"]},
        )
        await opp.async_block_till_done()

    assert result3["type"] == "create_entry"
    assert result3["title"] == "1.1.1.1:2222"
    assert result3["data"] == {
        "host": "1.1.1.1",
        "password": "test-password",
        "port": 2222,
        "resources": ["battery.voltage", "ups.status", "ups.status.display"],
        "username": "test-username",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_user_multiple_ups(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "2.2.2.2", "port": 123, "resources": ["battery.charge"]},
        options={CONF_RESOURCES: ["battery.charge"]},
    )
    config_entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_pynut = _get_mock_pynutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1", "ups2": "UPS2"},
    )

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
                "port": 2222,
            },
        )

    assert result2["step_id"] == "ups"
    assert result2["type"] == "form"

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ):
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {"alias": "ups2"},
        )

    assert result3["step_id"] == "resources"
    assert result3["type"] == "form"

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ), patch(
        "openpeerpower.components.nut.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result4 = await opp.config_entries.flow.async_configure(
            result3["flow_id"],
            {"resources": ["battery.voltage"]},
        )
        await opp.async_block_till_done()

    assert result4["type"] == "create_entry"
    assert result4["title"] == "ups2@1.1.1.1:2222"
    assert result4["data"] == {
        "host": "1.1.1.1",
        "password": "test-password",
        "alias": "ups2",
        "port": 2222,
        "resources": ["battery.voltage"],
        "username": "test-username",
    }
    assert len(mock_setup_entry.mock_calls) == 2


async def test_form_user_one_ups_with_ignored_entry(opp):
    """Test we can setup a new one when there is an ignored one."""
    ignored_entry = MockConfigEntry(
        domain=DOMAIN, data={}, source=config_entries.SOURCE_IGNORE
    )
    ignored_entry.add_to_opp(opp)

    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_pynut = _get_mock_pynutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
                "port": 2222,
            },
        )

    assert result2["step_id"] == "resources"
    assert result2["type"] == "form"

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ), patch(
        "openpeerpower.components.nut.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {"resources": ["battery.voltage", "ups.status", "ups.status.display"]},
        )
        await opp.async_block_till_done()

    assert result3["type"] == "create_entry"
    assert result3["title"] == "1.1.1.1:2222"
    assert result3["data"] == {
        "host": "1.1.1.1",
        "password": "test-password",
        "port": 2222,
        "resources": ["battery.voltage", "ups.status", "ups.status.display"],
        "username": "test-username",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_pynut = _get_mock_pynutclient()

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
                "port": 2222,
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_options_flow(opp):
    """Test config flow options."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="abcde12345",
        data=VALID_CONFIG,
        options={CONF_RESOURCES: ["battery.charge"]},
    )
    config_entry.add_to_opp(opp)

    mock_pynut = _get_mock_pynutclient(
        list_vars={"battery.voltage": "voltage"}, list_ups=["ups1"]
    )

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ), patch("openpeerpower.components.nut.async_setup_entry", return_value=True):
        result = await opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_RESOURCES: ["battery.voltage"]}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options == {
            CONF_RESOURCES: ["battery.voltage"],
            CONF_SCAN_INTERVAL: 60,
        }

    with patch(
        "openpeerpower.components.nut.PyNUTClient",
        return_value=mock_pynut,
    ), patch("openpeerpower.components.nut.async_setup_entry", return_value=True):
        result2 = await opp.config_entries.options.async_init(config_entry.entry_id)

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "init"

        result2 = await opp.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={CONF_RESOURCES: ["battery.voltage"], CONF_SCAN_INTERVAL: 12},
        )

        assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options == {
            CONF_RESOURCES: ["battery.voltage"],
            CONF_SCAN_INTERVAL: 12,
        }
