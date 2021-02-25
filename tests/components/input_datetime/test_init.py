"""Tests for the Input slider component."""
# pylint: disable=protected-access
import datetime
from unittest.mock import patch

import pytest
import voluptuous as vol

from openpeerpower.components.input_datetime import (
    ATTR_DATE,
    ATTR_DATETIME,
    ATTR_EDITABLE,
    ATTR_TIME,
    ATTR_TIMESTAMP,
    CONF_HAS_DATE,
    CONF_HAS_TIME,
    CONF_ID,
    CONF_INITIAL,
    CONF_NAME,
    CONFIG_SCHEMA,
    DEFAULT_TIME,
    DOMAIN,
    FMT_DATE,
    FMT_DATETIME,
    FMT_TIME,
    SERVICE_RELOAD,
)
from openpeerpower.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME, ATTR_NAME
from openpeerpower.core import Context, CoreState, State
from openpeerpower.exceptions import Unauthorized
from openpeerpower.helpers import entity_registry
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt as dt_util

from tests.common import mock_restore_cache

INITIAL_DATE = "2020-01-10"
INITIAL_TIME = "23:45:56"
INITIAL_DATETIME = f"{INITIAL_DATE} {INITIAL_TIME}"

ORIG_TIMEZONE = dt_util.DEFAULT_TIME_ZONE


@pytest.fixture
def storage_setup_opp, opp_storage):
    """Storage setup."""

    async def _storage(items=None, config=None):
        if items is None:
            opp.storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {
                    "items": [
                        {
                            CONF_ID: "from_storage",
                            CONF_NAME: "datetime from storage",
                            CONF_INITIAL: INITIAL_DATETIME,
                            CONF_HAS_DATE: True,
                            CONF_HAS_TIME: True,
                        }
                    ]
                },
            }
        else:
            opp.storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": items},
            }
        if config is None:
            config = {DOMAIN: {}}
        return await async_setup_component(opp, DOMAIN, config)

    return _storage


async def async_set_date_and_time(opp, entity_id, dt_value):
    """Set date and / or time of input_datetime."""
    await opp.services.async_call(
        DOMAIN,
        "set_datetime",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_DATE: dt_value.date(),
            ATTR_TIME: dt_value.time(),
        },
        blocking=True,
    )


async def async_set_datetime(opp, entity_id, dt_value):
    """Set date and / or time of input_datetime."""
    await opp.services.async_call(
        DOMAIN,
        "set_datetime",
        {ATTR_ENTITY_ID: entity_id, ATTR_DATETIME: dt_value},
        blocking=True,
    )


async def async_set_timestamp(opp, entity_id, timestamp):
    """Set date and / or time of input_datetime."""
    await opp.services.async_call(
        DOMAIN,
        "set_datetime",
        {ATTR_ENTITY_ID: entity_id, ATTR_TIMESTAMP: timestamp},
        blocking=True,
    )


@pytest.mark.parametrize(
    "config",
    [
        None,
        {"name with space": None},
        {"test_no_value": {"has_time": False, "has_date": False}},
    ],
)
def test_invalid_configs(config):
    """Test config."""
    with pytest.raises(vol.Invalid):
        CONFIG_SCHEMA({DOMAIN: config})


async def test_set_datetime.opp):
    """Test set_datetime method using date & time."""
    await async_setup_component(
        opp. DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46, 30, tzinfo=datetime.timezone.utc)

    await async_set_date_and_time(opp, entity_id, dt_obj)

    state = opp.states.get(entity_id)
    assert state.state == dt_obj.strftime(FMT_DATETIME)
    assert state.attributes["has_time"]
    assert state.attributes["has_date"]

    assert state.attributes["year"] == 2017
    assert state.attributes["month"] == 9
    assert state.attributes["day"] == 7
    assert state.attributes["hour"] == 19
    assert state.attributes["minute"] == 46
    assert state.attributes["second"] == 30
    assert state.attributes["timestamp"] == dt_obj.timestamp()


async def test_set_datetime_2.opp):
    """Test set_datetime method using datetime."""
    await async_setup_component(
        opp. DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46, 30, tzinfo=datetime.timezone.utc)

    await async_set_datetime(opp, entity_id, dt_obj)

    state = opp.states.get(entity_id)
    assert state.state == dt_obj.strftime(FMT_DATETIME)
    assert state.attributes["has_time"]
    assert state.attributes["has_date"]

    assert state.attributes["year"] == 2017
    assert state.attributes["month"] == 9
    assert state.attributes["day"] == 7
    assert state.attributes["hour"] == 19
    assert state.attributes["minute"] == 46
    assert state.attributes["second"] == 30
    assert state.attributes["timestamp"] == dt_obj.timestamp()


async def test_set_datetime_3.opp):
    """Test set_datetime method using timestamp."""
    await async_setup_component(
        opp. DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46, 30, tzinfo=datetime.timezone.utc)

    await async_set_timestamp(opp, entity_id, dt_util.as_utc(dt_obj).timestamp())

    state = opp.states.get(entity_id)
    assert state.state == dt_obj.strftime(FMT_DATETIME)
    assert state.attributes["has_time"]
    assert state.attributes["has_date"]

    assert state.attributes["year"] == 2017
    assert state.attributes["month"] == 9
    assert state.attributes["day"] == 7
    assert state.attributes["hour"] == 19
    assert state.attributes["minute"] == 46
    assert state.attributes["second"] == 30
    assert state.attributes["timestamp"] == dt_obj.timestamp()


async def test_set_datetime_time.opp):
    """Test set_datetime method with only time."""
    await async_setup_component(
        opp. DOMAIN, {DOMAIN: {"test_time": {"has_time": True, "has_date": False}}}
    )

    entity_id = "input_datetime.test_time"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46, 30)

    await async_set_date_and_time(opp, entity_id, dt_obj)

    state = opp.states.get(entity_id)
    assert state.state == dt_obj.strftime(FMT_TIME)
    assert state.attributes["has_time"]
    assert not state.attributes["has_date"]

    assert state.attributes["timestamp"] == (19 * 3600) + (46 * 60) + 30


async def test_set_invalid.opp):
    """Test set_datetime method with only time."""
    initial = "2017-01-01"
    await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_date": {"has_time": False, "has_date": True, "initial": initial}
            }
        },
    )

    entity_id = "input_datetime.test_date"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46)
    time_portion = dt_obj.time()

    with pytest.raises(vol.Invalid):
        await opp.services.async_call(
            "input_datetime",
            "set_datetime",
            {"entity_id": entity_id, "time": time_portion},
            blocking=True,
        )

    state = opp.states.get(entity_id)
    assert state.state == initial


async def test_set_invalid_2.opp):
    """Test set_datetime method with date and datetime."""
    initial = "2017-01-01"
    await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_date": {"has_time": False, "has_date": True, "initial": initial}
            }
        },
    )

    entity_id = "input_datetime.test_date"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46)
    time_portion = dt_obj.time()

    with pytest.raises(vol.Invalid):
        await opp.services.async_call(
            "input_datetime",
            "set_datetime",
            {"entity_id": entity_id, "time": time_portion, "datetime": dt_obj},
            blocking=True,
        )

    state = opp.states.get(entity_id)
    assert state.state == initial


async def test_set_datetime_date.opp):
    """Test set_datetime method with only date."""
    await async_setup_component(
        opp. DOMAIN, {DOMAIN: {"test_date": {"has_time": False, "has_date": True}}}
    )

    entity_id = "input_datetime.test_date"

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46)
    date_portion = dt_obj.date()

    await async_set_date_and_time(opp, entity_id, dt_obj)

    state = opp.states.get(entity_id)
    assert state.state == str(date_portion)
    assert not state.attributes["has_time"]
    assert state.attributes["has_date"]

    date_dt_obj = datetime.datetime(2017, 9, 7)
    assert state.attributes["timestamp"] == date_dt_obj.timestamp()


async def test_restore_state.opp):
    """Ensure states are restored on startup."""
    mock_restore_cache(
        opp,
        (
            State("input_datetime.test_time", "19:46:00"),
            State("input_datetime.test_date", "2017-09-07"),
            State("input_datetime.test_datetime", "2017-09-07 19:46:00"),
            State("input_datetime.test_bogus_data", "this is not a date"),
            State("input_datetime.test_was_time", "19:46:00"),
            State("input_datetime.test_was_date", "2017-09-07"),
        ),
    )

    opp.state = CoreState.starting

    initial = datetime.datetime(2017, 1, 1, 23, 42)
    default = datetime.datetime.combine(datetime.date.today(), DEFAULT_TIME)

    await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_time": {"has_time": True, "has_date": False},
                "test_date": {"has_time": False, "has_date": True},
                "test_datetime": {"has_time": True, "has_date": True},
                "test_bogus_data": {
                    "has_time": True,
                    "has_date": True,
                    "initial": initial.strftime(FMT_DATETIME),
                },
                "test_was_time": {"has_time": False, "has_date": True},
                "test_was_date": {"has_time": True, "has_date": False},
            }
        },
    )

    dt_obj = datetime.datetime(2017, 9, 7, 19, 46)
    state_time = opp.states.get("input_datetime.test_time")
    assert state_time.state == dt_obj.strftime(FMT_TIME)

    state_date = opp.states.get("input_datetime.test_date")
    assert state_date.state == dt_obj.strftime(FMT_DATE)

    state_datetime = opp.states.get("input_datetime.test_datetime")
    assert state_datetime.state == dt_obj.strftime(FMT_DATETIME)

    state_bogus = opp.states.get("input_datetime.test_bogus_data")
    assert state_bogus.state == initial.strftime(FMT_DATETIME)

    state_was_time = opp.states.get("input_datetime.test_was_time")
    assert state_was_time.state == default.strftime(FMT_DATE)

    state_was_date = opp.states.get("input_datetime.test_was_date")
    assert state_was_date.state == default.strftime(FMT_TIME)


async def test_default_value.opp):
    """Test default value if none has been set via initial or restore state."""
    await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                "test_time": {"has_time": True, "has_date": False},
                "test_date": {"has_time": False, "has_date": True},
                "test_datetime": {"has_time": True, "has_date": True},
            }
        },
    )

    dt_obj = datetime.datetime.combine(datetime.date.today(), DEFAULT_TIME)
    state_time = opp.states.get("input_datetime.test_time")
    assert state_time.state == dt_obj.strftime(FMT_TIME)
    assert state_time.attributes.get("timestamp") is not None

    state_date = opp.states.get("input_datetime.test_date")
    assert state_date.state == dt_obj.strftime(FMT_DATE)
    assert state_date.attributes.get("timestamp") is not None

    state_datetime = opp.states.get("input_datetime.test_datetime")
    assert state_datetime.state == dt_obj.strftime(FMT_DATETIME)
    assert state_datetime.attributes.get("timestamp") is not None


async def test_input_datetime_context(opp, opp_admin_user):
    """Test that input_datetime context works."""
    assert await async_setup_component(
        opp. "input_datetime", {"input_datetime": {"only_date": {"has_date": True}}}
    )

    state = opp.states.get("input_datetime.only_date")
    assert state is not None

    await opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {"entity_id": state.entity_id, "date": "2018-01-02"},
        blocking=True,
        context=Context(user_id.opp_admin_user.id),
    )

    state2 = opp.states.get("input_datetime.only_date")
    assert state2 is not None
    assert state.state != state2.state
    assert state2.context.user_id == opp_admin_user.id


async def test_reload(opp, opp_admin_user, opp_read_only_user):
    """Test reload service."""
    count_start = len.opp.states.async_entity_ids())
    ent_reg = await entity_registry.async_get_registry.opp)

    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                "dt1": {"has_time": False, "has_date": True, "initial": "2019-1-1"},
                "dt3": {CONF_HAS_TIME: True, CONF_HAS_DATE: True},
            }
        },
    )

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_datetime.dt1")
    state_2 = opp.states.get("input_datetime.dt2")
    state_3 = opp.states.get("input_datetime.dt3")

    dt_obj = datetime.datetime(2019, 1, 1, 0, 0)
    assert state_1 is not None
    assert state_2 is None
    assert state_3 is not None
    assert dt_obj.strftime(FMT_DATE) == state_1.state
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "dt1") == f"{DOMAIN}.dt1"
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "dt2") is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "dt3") == f"{DOMAIN}.dt3"

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "dt1": {"has_time": True, "has_date": False, "initial": "23:32"},
                "dt2": {"has_time": True, "has_date": True},
            }
        },
    ):
        with pytest.raises(Unauthorized):
            await opp.services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                blocking=True,
                context=Context(user_id.opp_read_only_user.id),
            )
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )

    assert count_start + 2 == len.opp.states.async_entity_ids())

    state_1 = opp.states.get("input_datetime.dt1")
    state_2 = opp.states.get("input_datetime.dt2")
    state_3 = opp.states.get("input_datetime.dt3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert state_1.state == DEFAULT_TIME.strftime(FMT_TIME)
    assert state_2.state == datetime.datetime.combine(
        datetime.date.today(), DEFAULT_TIME
    ).strftime(FMT_DATETIME)

    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "dt1") == f"{DOMAIN}.dt1"
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "dt2") == f"{DOMAIN}.dt2"
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, "dt3") is None


async def test_load_from_storage(opp, storage_setup):
    """Test set up from storage."""
    assert await storage_setup()
    state = opp.states.get(f"{DOMAIN}.datetime_from_storage")
    assert state.state == INITIAL_DATETIME
    assert state.attributes.get(ATTR_EDITABLE)


async def test_editable_state_attribute(opp, storage_setup):
    """Test editable attribute."""
    assert await storage_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    CONF_HAS_DATE: True,
                    CONF_HAS_TIME: True,
                    CONF_NAME: "yaml datetime",
                    CONF_INITIAL: "2001-01-02 12:34:56",
                }
            }
        }
    )

    state = opp.states.get(f"{DOMAIN}.datetime_from_storage")
    assert state.state == INITIAL_DATETIME
    assert state.attributes.get(ATTR_EDITABLE)

    state = opp.states.get(f"{DOMAIN}.from_yaml")
    assert state.state == "2001-01-02 12:34:56"
    assert not state.attributes[ATTR_EDITABLE]


async def test_ws_list(opp, opp_ws_client, storage_setup):
    """Test listing via WS."""
    assert await storage_setup(config={DOMAIN: {"from_yaml": {CONF_HAS_DATE: True}}})

    client = await opp_ws_client.opp)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    storage_ent = "from_storage"
    yaml_ent = "from_yaml"
    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 1
    assert storage_ent in result
    assert yaml_ent not in result
    assert result[storage_ent][ATTR_NAME] == "datetime from storage"


async def test_ws_delete(opp, opp_ws_client, storage_setup):
    """Test WS delete cleans up entity registry."""
    assert await storage_setup()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.datetime_from_storage"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state is not None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) == input_entity_id

    client = await opp_ws_client.opp)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/delete", f"{DOMAIN}_id": f"{input_id}"}
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None


async def test_update(opp, opp_ws_client, storage_setup):
    """Test updating min/max updates the state."""

    assert await storage_setup()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.datetime_from_storage"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state.attributes[ATTR_FRIENDLY_NAME] == "datetime from storage"
    assert state.state == INITIAL_DATETIME
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) == input_entity_id

    client = await opp_ws_client.opp)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            ATTR_NAME: "even newer name",
            CONF_HAS_DATE: False,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state.state == INITIAL_TIME
    assert state.attributes[ATTR_FRIENDLY_NAME] == "even newer name"


async def test_ws_create(opp, opp_ws_client, storage_setup):
    """Test create WS."""
    assert await storage_setup(items=[])

    input_id = "new_datetime"
    input_entity_id = f"{DOMAIN}.{input_id}"
    ent_reg = await entity_registry.async_get_registry.opp)

    state = opp.states.get(input_entity_id)
    assert state is None
    assert ent_reg.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None

    client = await opp_ws_client.opp)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            CONF_NAME: "New DateTime",
            CONF_INITIAL: "1991-01-02 01:02:03",
            CONF_HAS_DATE: True,
            CONF_HAS_TIME: True,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = opp.states.get(input_entity_id)
    assert state.state == "1991-01-02 01:02:03"
    assert state.attributes[ATTR_FRIENDLY_NAME] == "New DateTime"
    assert state.attributes[ATTR_EDITABLE]


async def test_setup_no_config(opp, opp_admin_user):
    """Test component setup with no config."""
    count_start = len.opp.states.async_entity_ids())
    assert await async_setup_component(opp, DOMAIN, {})

    with patch(
        "openpeerpower.config.load_yaml_config_file", autospec=True, return_value={}
    ):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id.opp_admin_user.id),
        )

    assert count_start == len.opp.states.async_entity_ids())


async def test_timestamp.opp):
    """Test timestamp."""
    try:
        dt_util.set_default_time_zone(dt_util.get_time_zone("America/Los_Angeles"))

        assert await async_setup_component(
            opp,
            DOMAIN,
            {
                DOMAIN: {
                    "test_datetime_initial_with_tz": {
                        "has_time": True,
                        "has_date": True,
                        "initial": "2020-12-13 10:00:00+01:00",
                    },
                    "test_datetime_initial_without_tz": {
                        "has_time": True,
                        "has_date": True,
                        "initial": "2020-12-13 10:00:00",
                    },
                    "test_time_initial": {
                        "has_time": True,
                        "has_date": False,
                        "initial": "10:00:00",
                    },
                }
            },
        )

        # initial has been converted to the set timezone
        state_with_tz = opp.states.get("input_datetime.test_datetime_initial_with_tz")
        assert state_with_tz is not None
        # Timezone LA is UTC-8 => timestamp carries +01:00 => delta is -9 => 10:00 - 09:00 => 01:00
        assert state_with_tz.state == "2020-12-13 01:00:00"
        assert (
            dt_util.as_local(
                dt_util.utc_from_timestamp(state_with_tz.attributes[ATTR_TIMESTAMP])
            ).strftime(FMT_DATETIME)
            == "2020-12-13 01:00:00"
        )

        # initial has been interpreted as being part of set timezone
        state_without_tz = opp.states.get(
            "input_datetime.test_datetime_initial_without_tz"
        )
        assert state_without_tz is not None
        assert state_without_tz.state == "2020-12-13 10:00:00"
        # Timezone LA is UTC-8 => timestamp has no zone (= assumed local) => delta to UTC is +8 => 10:00 + 08:00 => 18:00
        assert (
            dt_util.utc_from_timestamp(
                state_without_tz.attributes[ATTR_TIMESTAMP]
            ).strftime(FMT_DATETIME)
            == "2020-12-13 18:00:00"
        )
        assert (
            dt_util.as_local(
                dt_util.utc_from_timestamp(state_without_tz.attributes[ATTR_TIMESTAMP])
            ).strftime(FMT_DATETIME)
            == "2020-12-13 10:00:00"
        )
        # Use datetime.datetime.fromtimestamp
        assert (
            dt_util.as_local(
                datetime.datetime.fromtimestamp(
                    state_without_tz.attributes[ATTR_TIMESTAMP], datetime.timezone.utc
                )
            ).strftime(FMT_DATETIME)
            == "2020-12-13 10:00:00"
        )

        # Test initial time sets timestamp correctly.
        state_time = opp.states.get("input_datetime.test_time_initial")
        assert state_time is not None
        assert state_time.state == "10:00:00"
        assert state_time.attributes[ATTR_TIMESTAMP] == 10 * 60 * 60

        # Test that setting the timestamp of an entity works.
        await opp.services.async_call(
            DOMAIN,
            "set_datetime",
            {
                ATTR_ENTITY_ID: "input_datetime.test_datetime_initial_with_tz",
                ATTR_TIMESTAMP: state_without_tz.attributes[ATTR_TIMESTAMP],
            },
            blocking=True,
        )
        state_with_tz_updated = opp.states.get(
            "input_datetime.test_datetime_initial_with_tz"
        )
        assert state_with_tz_updated.state == "2020-12-13 10:00:00"
        assert (
            state_with_tz_updated.attributes[ATTR_TIMESTAMP]
            == state_without_tz.attributes[ATTR_TIMESTAMP]
        )

    finally:
        dt_util.set_default_time_zone(ORIG_TIMEZONE)
