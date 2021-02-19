"""Tests for 1-Wire config flow."""
from unittest.mock import patch

from pyownet import protocol

from openpeerpower.components.onewire.const import (
    CONF_MOUNT_DIR,
    CONF_TYPE_OWSERVER,
    CONF_TYPE_SYSBUS,
    DEFAULT_OWSERVER_PORT,
    DEFAULT_SYSBUS_MOUNT_DIR,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import CONF_HOST, CONF_PORT, CONF_TYPE
from openpeerpowerr.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from . import setup_onewire_owserver_integration, setup_onewire_sysbus_integration


async def test_user_owserver.opp):
    """Test OWServer user flow."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert not result["errors"]

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_TYPE: CONF_TYPE_OWSERVER},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "owserver"
    assert not result["errors"]

    # Invalid server
    with patch(
        "openpeerpower.components.onewire.onewirehub.protocol.proxy",
        side_effect=protocol.ConnError,
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
        )

        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "owserver"
        assert result["errors"] == {"base": "cannot_connect"}

    # Valid server
    with patch("openpeerpower.components.onewire.onewirehub.protocol.proxy",), patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
        )

        assert result["type"] == RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "1.2.3.4"
        assert result["data"] == {
            CONF_TYPE: CONF_TYPE_OWSERVER,
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 1234,
        }
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_owserver_duplicate.opp):
    """Test OWServer flow."""
    with patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        await setup_onewire_owserver_integration.opp)
        assert len.opp.config_entries.async_entries(DOMAIN)) == 1

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert not result["errors"]

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_TYPE: CONF_TYPE_OWSERVER},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "owserver"
    assert not result["errors"]

    # Duplicate server
    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_sysbus.opp):
    """Test SysBus flow."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert not result["errors"]

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_TYPE: CONF_TYPE_SYSBUS},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "mount_dir"
    assert not result["errors"]

    # Invalid path
    with patch(
        "openpeerpower.components.onewire.onewirehub.os.path.isdir",
        return_value=False,
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_MOUNT_DIR: "/sys/bus/invalid_directory"},
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "mount_dir"
    assert result["errors"] == {"base": "invalid_path"}

    # Valid path
    with patch(
        "openpeerpower.components.onewire.onewirehub.os.path.isdir",
        return_value=True,
    ), patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_MOUNT_DIR: "/sys/bus/directory"},
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "/sys/bus/directory"
    assert result["data"] == {
        CONF_TYPE: CONF_TYPE_SYSBUS,
        CONF_MOUNT_DIR: "/sys/bus/directory",
    }
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_sysbus_duplicate.opp):
    """Test SysBus duplicate flow."""
    with patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        await setup_onewire_sysbus_integration.opp)
        assert len.opp.config_entries.async_entries(DOMAIN)) == 1

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert not result["errors"]

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_TYPE: CONF_TYPE_SYSBUS},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "mount_dir"
    assert not result["errors"]

    # Valid path
    with patch(
        "openpeerpower.components.onewire.onewirehub.os.path.isdir",
        return_value=True,
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_MOUNT_DIR: DEFAULT_SYSBUS_MOUNT_DIR},
        )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_sysbus.opp):
    """Test import step."""

    with patch(
        "openpeerpower.components.onewire.onewirehub.os.path.isdir",
        return_value=True,
    ), patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={CONF_TYPE: CONF_TYPE_SYSBUS},
        )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DEFAULT_SYSBUS_MOUNT_DIR
    assert result["data"] == {
        CONF_TYPE: CONF_TYPE_SYSBUS,
        CONF_MOUNT_DIR: DEFAULT_SYSBUS_MOUNT_DIR,
    }
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_sysbus_with_mount_dir.opp):
    """Test import step."""

    with patch(
        "openpeerpower.components.onewire.onewirehub.os.path.isdir",
        return_value=True,
    ), patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={
                CONF_TYPE: CONF_TYPE_SYSBUS,
                CONF_MOUNT_DIR: DEFAULT_SYSBUS_MOUNT_DIR,
            },
        )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DEFAULT_SYSBUS_MOUNT_DIR
    assert result["data"] == {
        CONF_TYPE: CONF_TYPE_SYSBUS,
        CONF_MOUNT_DIR: DEFAULT_SYSBUS_MOUNT_DIR,
    }
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_owserver.opp):
    """Test import step."""

    with patch("openpeerpower.components.onewire.onewirehub.protocol.proxy",), patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={
                CONF_TYPE: CONF_TYPE_OWSERVER,
                CONF_HOST: "1.2.3.4",
            },
        )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "1.2.3.4"
    assert result["data"] == {
        CONF_TYPE: CONF_TYPE_OWSERVER,
        CONF_HOST: "1.2.3.4",
        CONF_PORT: DEFAULT_OWSERVER_PORT,
    }
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_owserver_with_port.opp):
    """Test import step."""

    with patch("openpeerpower.components.onewire.onewirehub.protocol.proxy",), patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={
                CONF_TYPE: CONF_TYPE_OWSERVER,
                CONF_HOST: "1.2.3.4",
                CONF_PORT: 1234,
            },
        )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "1.2.3.4"
    assert result["data"] == {
        CONF_TYPE: CONF_TYPE_OWSERVER,
        CONF_HOST: "1.2.3.4",
        CONF_PORT: 1234,
    }
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_owserver_duplicate.opp):
    """Test OWServer flow."""
    # Initialise with single entry
    with patch(
        "openpeerpower.components.onewire.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.onewire.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        await setup_onewire_owserver_integration.opp)
        assert len.opp.config_entries.async_entries(DOMAIN)) == 1

    # Import duplicate entry
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_TYPE: CONF_TYPE_OWSERVER,
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 1234,
        },
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
