"""Tests for Vizio config flow."""
import pytest
import voluptuous as vol

from openpeerpower import data_entry_flow
from openpeerpower.components.media_player import DEVICE_CLASS_SPEAKER, DEVICE_CLASS_TV
from openpeerpower.components.vizio.config_flow import _get_config_schema
from openpeerpower.components.vizio.const import (
    CONF_APPS,
    CONF_APPS_TO_INCLUDE_OR_EXCLUDE,
    CONF_INCLUDE,
    CONF_VOLUME_STEP,
    DEFAULT_NAME,
    DEFAULT_VOLUME_STEP,
    DOMAIN,
    VIZIO_SCHEMA,
)
from openpeerpower.config_entries import (
    SOURCE_IGNORE,
    SOURCE_IMPORT,
    SOURCE_USER,
    SOURCE_ZEROCONF,
)
from openpeerpower.const import (
    CONF_ACCESS_TOKEN,
    CONF_DEVICE_CLASS,
    CONF_HOST,
    CONF_NAME,
    CONF_PIN,
    CONF_PORT,
)
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import (
    ACCESS_TOKEN,
    CURRENT_APP,
    HOST,
    HOST2,
    MOCK_IMPORT_VALID_TV_CONFIG,
    MOCK_INCLUDE_APPS,
    MOCK_INCLUDE_NO_APPS,
    MOCK_PIN_CONFIG,
    MOCK_SPEAKER_CONFIG,
    MOCK_TV_CONFIG_NO_TOKEN,
    MOCK_TV_WITH_ADDITIONAL_APPS_CONFIG,
    MOCK_TV_WITH_EXCLUDE_CONFIG,
    MOCK_USER_VALID_TV_CONFIG,
    MOCK_ZEROCONF_SERVICE_INFO,
    NAME,
    NAME2,
    UNIQUE_ID,
    VOLUME_STEP,
)

from tests.common import MockConfigEntry


async def test_user_flow_minimum_fields(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test user config flow with minimum fields."""
    # test form shows
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_SPEAKER_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == DEVICE_CLASS_SPEAKER


async def test_user_flow_all_fields(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test user config flow with all fields."""
    # test form shows
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_VALID_TV_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == DEVICE_CLASS_TV
    assert result["data"][CONF_ACCESS_TOKEN] == ACCESS_TOKEN
    assert CONF_APPS not in result["data"]


async def test_speaker_options_flow(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_update: pytest.fixture,
) -> None:
    """Test options config flow for speaker."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_SPEAKER_CONFIG
    )
    await opp.async_block_till_done()
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    entry = result["result"]

    result = await opp.config_entries.options.async_init(entry.entry_id, data=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_VOLUME_STEP: VOLUME_STEP}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"][CONF_VOLUME_STEP] == VOLUME_STEP
    assert CONF_APPS not in result["data"]


async def test_tv_options_flow_no_apps(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_update: pytest.fixture,
) -> None:
    """Test options config flow for TV without providing apps option."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_VALID_TV_CONFIG
    )
    await opp.async_block_till_done()
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    entry = result["result"]

    result = await opp.config_entries.options.async_init(entry.entry_id, data=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    options = {CONF_VOLUME_STEP: VOLUME_STEP}
    options.update(MOCK_INCLUDE_NO_APPS)

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input=options
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"][CONF_VOLUME_STEP] == VOLUME_STEP
    assert CONF_APPS not in result["data"]


async def test_tv_options_flow_with_apps(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_update: pytest.fixture,
) -> None:
    """Test options config flow for TV with providing apps option."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_VALID_TV_CONFIG
    )
    await opp.async_block_till_done()
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    entry = result["result"]

    result = await opp.config_entries.options.async_init(entry.entry_id, data=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    options = {CONF_VOLUME_STEP: VOLUME_STEP}
    options.update(MOCK_INCLUDE_APPS)

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input=options
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"][CONF_VOLUME_STEP] == VOLUME_STEP
    assert CONF_APPS in result["data"]
    assert result["data"][CONF_APPS] == {CONF_INCLUDE: [CURRENT_APP]}


async def test_tv_options_flow_start_with_volume(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_update: pytest.fixture,
) -> None:
    """Test options config flow for TV with providing apps option after providing volume step in initial config."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_VALID_TV_CONFIG
    )
    await opp.async_block_till_done()
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    entry = result["result"]

    result = await opp.config_entries.options.async_init(
        entry.entry_id, data={CONF_VOLUME_STEP: VOLUME_STEP}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

    assert entry.options
    assert entry.options == {CONF_VOLUME_STEP: VOLUME_STEP}
    assert CONF_APPS not in entry.options
    assert CONF_APPS_TO_INCLUDE_OR_EXCLUDE not in entry.options

    result = await opp.config_entries.options.async_init(entry.entry_id, data=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    options = {CONF_VOLUME_STEP: VOLUME_STEP}
    options.update(MOCK_INCLUDE_APPS)

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input=options
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"][CONF_VOLUME_STEP] == VOLUME_STEP
    assert CONF_APPS in result["data"]
    assert result["data"][CONF_APPS] == {CONF_INCLUDE: [CURRENT_APP]}


async def test_user_host_already_configured(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test host is already configured during user setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_SPEAKER_CONFIG,
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        unique_id=UNIQUE_ID,
    )
    entry.add_to.opp.opp)
    fail_entry = MOCK_SPEAKER_CONFIG.copy()
    fail_entry[CONF_NAME] = "newtestname"

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=fail_entry
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_HOST: "existing_config_entry_found"}


async def test_user_serial_number_already_exists(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test serial_number is already configured with different host and name during user setup."""
    # Set up new entry
    MockConfigEntry(
        domain=DOMAIN, data=MOCK_SPEAKER_CONFIG, unique_id=UNIQUE_ID
    ).add_to.opp.opp)

    # Set up new entry with same unique_id but different host and name
    fail_entry = MOCK_SPEAKER_CONFIG.copy()
    fail_entry[CONF_HOST] = HOST2
    fail_entry[CONF_NAME] = NAME2

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=fail_entry
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_HOST: "existing_config_entry_found"}


async def test_user_error_on_could_not_connect(
    opp. OpenPeerPowerType, vizio_no_unique_id: pytest.fixture
) -> None:
    """Test with could_not_connect during user setup due to no connectivity."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_VALID_TV_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_HOST: "cannot_connect"}


async def test_user_error_on_could_not_connect_invalid_token(
    opp. OpenPeerPowerType, vizio_cant_connect: pytest.fixture
) -> None:
    """Test with could_not_connect during user setup due to invalid token."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_VALID_TV_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_tv_pairing_no_apps(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_complete_pairing: pytest.fixture,
) -> None:
    """Test pairing config flow when access token not provided for tv during user entry and no apps configured."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_TV_CONFIG_NO_TOKEN
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "pair_tv"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_PIN_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "pairing_complete"

    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == DEVICE_CLASS_TV
    assert CONF_APPS not in result["data"]


async def test_user_start_pairing_failure(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_start_pairing_failure: pytest.fixture,
) -> None:
    """Test failure to start pairing from user config flow."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_TV_CONFIG_NO_TOKEN
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_invalid_pin(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_invalid_pin_failure: pytest.fixture,
) -> None:
    """Test failure to complete pairing from user config flow."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_TV_CONFIG_NO_TOKEN
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "pair_tv"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_PIN_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "pair_tv"
    assert result["errors"] == {CONF_PIN: "complete_pairing_failed"}


async def test_user_ignore(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test user config flow doesn't throw an error when there's an existing ignored source."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_SPEAKER_CONFIG,
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        source=SOURCE_IGNORE,
    )
    entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_SPEAKER_CONFIG
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_import_flow_minimum_fields(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test import config flow with minimum fields."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(
            {CONF_HOST: HOST, CONF_DEVICE_CLASS: DEVICE_CLASS_SPEAKER}
        ),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"][CONF_NAME] == DEFAULT_NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == DEVICE_CLASS_SPEAKER
    assert result["data"][CONF_VOLUME_STEP] == DEFAULT_VOLUME_STEP


async def test_import_flow_all_fields(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test import config flow with all fields."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_IMPORT_VALID_TV_CONFIG),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == DEVICE_CLASS_TV
    assert result["data"][CONF_ACCESS_TOKEN] == ACCESS_TOKEN
    assert result["data"][CONF_VOLUME_STEP] == VOLUME_STEP


async def test_import_entity_already_configured(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test entity is already configured during import setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_SPEAKER_CONFIG),
        options={CONF_VOLUME_STEP: VOLUME_STEP},
    )
    entry.add_to.opp.opp)
    fail_entry = vol.Schema(VIZIO_SCHEMA)(MOCK_SPEAKER_CONFIG.copy())

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=fail_entry
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured_device"


async def test_import_flow_update_options(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_update: pytest.fixture,
) -> None:
    """Test import config flow with updated options."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_SPEAKER_CONFIG),
    )
    await opp.async_block_till_done()

    assert result["result"].options == {CONF_VOLUME_STEP: DEFAULT_VOLUME_STEP}
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    entry_id = result["result"].entry_id

    updated_config = MOCK_SPEAKER_CONFIG.copy()
    updated_config[CONF_VOLUME_STEP] = VOLUME_STEP + 1
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(updated_config),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "updated_entry"
    config_entry = opp.config_entries.async_get_entry(entry_id)
    assert config_entry.options[CONF_VOLUME_STEP] == VOLUME_STEP + 1


async def test_import_flow_update_name_and_apps(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_update: pytest.fixture,
) -> None:
    """Test import config flow with updated name and apps."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_IMPORT_VALID_TV_CONFIG),
    )
    await opp.async_block_till_done()

    assert result["result"].data[CONF_NAME] == NAME
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    entry_id = result["result"].entry_id

    updated_config = MOCK_IMPORT_VALID_TV_CONFIG.copy()
    updated_config[CONF_NAME] = NAME2
    updated_config[CONF_APPS] = {CONF_INCLUDE: [CURRENT_APP]}
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(updated_config),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "updated_entry"
    config_entry = opp.config_entries.async_get_entry(entry_id)
    assert config_entry.data[CONF_NAME] == NAME2
    assert config_entry.data[CONF_APPS] == {CONF_INCLUDE: [CURRENT_APP]}
    assert config_entry.options[CONF_APPS] == {CONF_INCLUDE: [CURRENT_APP]}


async def test_import_flow_update_remove_apps(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_update: pytest.fixture,
) -> None:
    """Test import config flow with removed apps."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_TV_WITH_EXCLUDE_CONFIG),
    )
    await opp.async_block_till_done()

    assert result["result"].data[CONF_NAME] == NAME
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    config_entry = opp.config_entries.async_get_entry(result["result"].entry_id)
    assert CONF_APPS in config_entry.data
    assert CONF_APPS in config_entry.options

    updated_config = MOCK_TV_WITH_EXCLUDE_CONFIG.copy()
    updated_config.pop(CONF_APPS)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(updated_config),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "updated_entry"
    assert CONF_APPS not in config_entry.data
    assert CONF_APPS not in config_entry.options


async def test_import_needs_pairing(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_complete_pairing: pytest.fixture,
) -> None:
    """Test pairing config flow when access token not provided for tv during import."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=MOCK_TV_CONFIG_NO_TOKEN
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_TV_CONFIG_NO_TOKEN
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "pair_tv"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_PIN_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "pairing_complete_import"

    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == DEVICE_CLASS_TV


async def test_import_with_apps_needs_pairing(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_complete_pairing: pytest.fixture,
) -> None:
    """Test pairing config flow when access token not provided for tv but apps are included during import."""
    import_config = MOCK_TV_CONFIG_NO_TOKEN.copy()
    import_config[CONF_APPS] = {CONF_INCLUDE: [CURRENT_APP]}

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=import_config
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # Mock inputting info without apps to make sure apps get stored
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_get_config_schema(MOCK_TV_CONFIG_NO_TOKEN)(MOCK_TV_CONFIG_NO_TOKEN),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "pair_tv"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_PIN_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "pairing_complete_import"

    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == DEVICE_CLASS_TV
    assert result["data"][CONF_APPS][CONF_INCLUDE] == [CURRENT_APP]


async def test_import_flow_additional_configs(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_update: pytest.fixture,
) -> None:
    """Test import config flow with additional configs defined in CONF_APPS."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_TV_WITH_ADDITIONAL_APPS_CONFIG),
    )
    await opp.async_block_till_done()

    assert result["result"].data[CONF_NAME] == NAME
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    config_entry = opp.config_entries.async_get_entry(result["result"].entry_id)
    assert CONF_APPS in config_entry.data
    assert CONF_APPS not in config_entry.options


async def test_import_error(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test that error is logged when import config has an error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_SPEAKER_CONFIG),
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        unique_id=UNIQUE_ID,
    )
    entry.add_to.opp.opp)
    fail_entry = MOCK_SPEAKER_CONFIG.copy()
    fail_entry[CONF_HOST] = "0.0.0.0"

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(fail_entry),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    # Ensure error gets logged
    vizio_log_list = [
        log
        for log in caplog.records
        if log.name == "openpeerpower.components.vizio.config_flow"
    ]
    assert len(vizio_log_list) == 1


async def test_import_ignore(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
) -> None:
    """Test import config flow doesn't throw an error when there's an existing ignored source."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_SPEAKER_CONFIG,
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        source=SOURCE_IGNORE,
    )
    entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_SPEAKER_CONFIG),
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_zeroconf_flow(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_guess_device_type: pytest.fixture,
) -> None:
    """Test zeroconf config flow."""
    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    # Form should always show even if all required properties are discovered
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # Apply discovery updates to entry to mimic when user hits submit without changing
    # defaults which were set from discovery parameters
    user_input = result["data_schema"](discovery_info)

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_DEVICE_CLASS] == DEVICE_CLASS_SPEAKER


async def test_zeroconf_flow_already_configured(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_guess_device_type: pytest.fixture,
) -> None:
    """Test entity is already configured during zeroconf setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_SPEAKER_CONFIG,
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        unique_id=UNIQUE_ID,
    )
    entry.add_to.opp.opp)

    # Try rediscovering same device
    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    # Flow should abort because device is already setup
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_flow_with_port_in_host(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_guess_device_type: pytest.fixture,
) -> None:
    """Test entity is already configured during zeroconf setup when port is in host."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_SPEAKER_CONFIG,
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        unique_id=UNIQUE_ID,
    )
    entry.add_to.opp.opp)

    # Try rediscovering same device, this time with port already in host
    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    discovery_info[
        CONF_HOST
    ] = f"{discovery_info[CONF_HOST]}:{discovery_info[CONF_PORT]}"
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    # Flow should abort because device is already setup
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_dupe_fail(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_guess_device_type: pytest.fixture,
) -> None:
    """Test zeroconf config flow when device gets discovered multiple times."""
    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    # Form should always show even if all required properties are discovered
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    # Flow should abort because device is already setup
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_in_progress"


async def test_zeroconf_ignore(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_guess_device_type: pytest.fixture,
) -> None:
    """Test zeroconf discovery doesn't throw an error when there's an existing ignored source."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_SPEAKER_CONFIG,
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        source=SOURCE_IGNORE,
    )
    entry.add_to.opp.opp)

    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_zeroconf_no_unique_id(
    opp. OpenPeerPowerType,
    vizio_guess_device_type: pytest.fixture,
    vizio_no_unique_id: pytest.fixture,
) -> None:
    """Test zeroconf discovery aborts when unique_id is None."""

    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "cannot_connect"


async def test_zeroconf_abort_when_ignored(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_guess_device_type: pytest.fixture,
) -> None:
    """Test zeroconf discovery aborts when the same host has been ignored."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_SPEAKER_CONFIG,
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        source=SOURCE_IGNORE,
        unique_id=UNIQUE_ID,
    )
    entry.add_to.opp.opp)

    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_flow_already_configured_hostname(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_hostname_check: pytest.fixture,
    vizio_guess_device_type: pytest.fixture,
) -> None:
    """Test entity is already configured during zeroconf setup when existing entry uses hostname."""
    config = MOCK_SPEAKER_CONFIG.copy()
    config[CONF_HOST] = "hostname"
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=config,
        options={CONF_VOLUME_STEP: VOLUME_STEP},
        unique_id=UNIQUE_ID,
    )
    entry.add_to.opp.opp)

    # Try rediscovering same device
    discovery_info = MOCK_ZEROCONF_SERVICE_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    # Flow should abort because device is already setup
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_import_flow_already_configured_hostname(
    opp. OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_bypass_setup: pytest.fixture,
    vizio_hostname_check: pytest.fixture,
) -> None:
    """Test entity is already configured during import setup when existing entry uses hostname."""
    config = MOCK_SPEAKER_CONFIG.copy()
    config[CONF_HOST] = "hostname"
    entry = MockConfigEntry(
        domain=DOMAIN, data=config, options={CONF_VOLUME_STEP: VOLUME_STEP}
    )
    entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_SPEAKER_CONFIG),
    )

    # Flow should abort because device was updated
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "updated_entry"

    assert entry.data[CONF_HOST] == HOST
