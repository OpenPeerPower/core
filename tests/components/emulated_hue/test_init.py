"""Test the Emulated Hue component."""
from datetime import timedelta

from openpeerpower.components.emulated_hue import (
    DATA_KEY,
    DATA_VERSION,
    SAVE_DELAY,
    Config,
)
from openpeerpower.util import utcnow

from tests.common import async_fire_time_changed


async def test_config_google_home_entity_id_to_number(opp, opp_storage):
    """Test config adheres to the type."""
    conf = Config(opp, {"type": "google_home"})
    opp_storage[DATA_KEY] = {
        "version": DATA_VERSION,
        "key": DATA_KEY,
        "data": {"1": "light.test2"},
    }

    await conf.async_setup()

    number = conf.entity_id_to_number("light.test")
    assert number == "2"

    async_fire_time_changed(opp, utcnow() + timedelta(seconds=SAVE_DELAY))
    await opp.async_block_till_done()
    assert opp_storage[DATA_KEY]["data"] == {
        "1": "light.test2",
        "2": "light.test",
    }

    number = conf.entity_id_to_number("light.test")
    assert number == "2"

    number = conf.entity_id_to_number("light.test2")
    assert number == "1"

    entity_id = conf.number_to_entity_id("1")
    assert entity_id == "light.test2"


async def test_config_google_home_entity_id_to_number_altered(opp, opp_storage):
    """Test config adheres to the type."""
    conf = Config(opp, {"type": "google_home"})
    opp_storage[DATA_KEY] = {
        "version": DATA_VERSION,
        "key": DATA_KEY,
        "data": {"21": "light.test2"},
    }

    await conf.async_setup()

    number = conf.entity_id_to_number("light.test")
    assert number == "22"

    async_fire_time_changed(opp, utcnow() + timedelta(seconds=SAVE_DELAY))
    await opp.async_block_till_done()
    assert opp_storage[DATA_KEY]["data"] == {
        "21": "light.test2",
        "22": "light.test",
    }

    number = conf.entity_id_to_number("light.test")
    assert number == "22"

    number = conf.entity_id_to_number("light.test2")
    assert number == "21"

    entity_id = conf.number_to_entity_id("21")
    assert entity_id == "light.test2"


async def test_config_google_home_entity_id_to_number_empty(opp, opp_storage):
    """Test config adheres to the type."""
    conf = Config(opp, {"type": "google_home"})
    opp_storage[DATA_KEY] = {"version": DATA_VERSION, "key": DATA_KEY, "data": {}}

    await conf.async_setup()

    number = conf.entity_id_to_number("light.test")
    assert number == "1"

    async_fire_time_changed(opp, utcnow() + timedelta(seconds=SAVE_DELAY))
    await opp.async_block_till_done()
    assert opp_storage[DATA_KEY]["data"] == {"1": "light.test"}

    number = conf.entity_id_to_number("light.test")
    assert number == "1"

    number = conf.entity_id_to_number("light.test2")
    assert number == "2"

    entity_id = conf.number_to_entity_id("2")
    assert entity_id == "light.test2"


def test_config_alexa_entity_id_to_number():
    """Test config adheres to the type."""
    conf = Config(None, {"type": "alexa"})

    number = conf.entity_id_to_number("light.test")
    assert number == "light.test"

    number = conf.entity_id_to_number("light.test")
    assert number == "light.test"

    number = conf.entity_id_to_number("light.test2")
    assert number == "light.test2"

    entity_id = conf.number_to_entity_id("light.test")
    assert entity_id == "light.test"
