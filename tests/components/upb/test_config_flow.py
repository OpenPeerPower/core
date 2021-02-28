"""Test the UPB Control config flow."""

from unittest.mock import MagicMock, PropertyMock, patch

from openpeerpower import config_entries, setup
from openpeerpower.components.upb.const import DOMAIN


def mocked_upb(sync_complete=True, config_ok=True):
    """Mock UPB lib."""

    def _upb_lib_connect(callback):
        callback()

    upb_mock = MagicMock()
    type(upb_mock).network_id = PropertyMock(return_value="42")
    type(upb_mock).config_ok = PropertyMock(return_value=config_ok)
    if sync_complete:
        upb_mock.connect.side_effect = _upb_lib_connect
    return patch(
        "openpeerpower.components.upb.config_flow.upb_lib.UpbPim", return_value=upb_mock
    )


async def valid_tcp_flow(opp, sync_complete=True, config_ok=True):
    """Get result dict that are standard for most tests."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    with mocked_upb(sync_complete, config_ok), patch(
        "openpeerpower.components.upb.async_setup_entry", return_value=True
    ):
        flow = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await opp.config_entries.flow.async_configure(
            flow["flow_id"],
            {"protocol": "TCP", "address": "1.2.3.4", "file_path": "upb.upe"},
        )
    return result


async def test_full_upb_flow_with_serial_port(opp):
    """Test a full UPB config flow with serial port."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    with mocked_upb(), patch(
        "openpeerpower.components.upb.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.upb.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        flow = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await opp.config_entries.flow.async_configure(
            flow["flow_id"],
            {
                "protocol": "Serial port",
                "address": "/dev/ttyS0:115200",
                "file_path": "upb.upe",
            },
        )
        await opp.async_block_till_done()

    assert flow["type"] == "form"
    assert flow["errors"] == {}
    assert result["type"] == "create_entry"
    assert result["title"] == "UPB"
    assert result["data"] == {
        "host": "serial:///dev/ttyS0:115200",
        "file_path": "upb.upe",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_user_with_tcp_upb(opp):
    """Test we can setup a serial upb."""
    result = await valid_tcp_flow(opp)
    assert result["type"] == "create_entry"
    assert result["data"] == {"host": "tcp://1.2.3.4", "file_path": "upb.upe"}
    await opp.async_block_till_done()


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    from asyncio import TimeoutError

    with patch(
        "openpeerpower.components.upb.config_flow.async_timeout.timeout",
        side_effect=TimeoutError,
    ):
        result = await valid_tcp_flow(opp, sync_complete=False)

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_missing_upb_file(opp):
    """Test we handle cannot connect error."""
    result = await valid_tcp_flow(opp, config_ok=False)
    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_upb_file"}


async def test_form_user_with_already_configured(opp):
    """Test we can setup a TCP upb."""
    _ = await valid_tcp_flow(opp)
    result2 = await valid_tcp_flow(opp)
    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"
    await opp.async_block_till_done()


async def test_form_import(opp):
    """Test we get the form with import source."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    with mocked_upb(), patch(
        "openpeerpower.components.upb.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.upb.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": "tcp://42.4.2.42", "file_path": "upb.upe"},
        )
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == "UPB"

    assert result["data"] == {"host": "tcp://42.4.2.42", "file_path": "upb.upe"}
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_junk_input(opp):
    """Test we get the form with import source."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    with mocked_upb():
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"foo": "goo", "goo": "foo"},
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "unknown"}

    await opp.async_block_till_done()
