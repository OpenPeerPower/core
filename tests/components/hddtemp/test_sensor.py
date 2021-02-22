"""The tests for the hddtemp platform."""
import socket
from unittest.mock import patch

import pytest

from openpeerpower.const import TEMP_CELSIUS
from openpeerpower.setup import async_setup_component

VALID_CONFIG_MINIMAL = {"sensor": {"platform": "hddtemp"}}

VALID_CONFIG_NAME = {"sensor": {"platform": "hddtemp", "name": "FooBar"}}

VALID_CONFIG_ONE_DISK = {"sensor": {"platform": "hddtemp", "disks": ["/dev/sdd1"]}}

VALID_CONFIG_WRONG_DISK = {"sensor": {"platform": "hddtemp", "disks": ["/dev/sdx1"]}}

VALID_CONFIG_MULTIPLE_DISKS = {
    "sensor": {
        "platform": "hddtemp",
        "host": "foobar.local",
        "disks": ["/dev/sda1", "/dev/sdb1", "/dev/sdc1"],
    }
}

VALID_CONFIG_HOST_REFUSED = {"sensor": {"platform": "hddtemp", "host": "alice.local"}}

VALID_CONFIG_HOST_UNREACHABLE = {"sensor": {"platform": "hddtemp", "host": "bob.local"}}

REFERENCE = {
    "/dev/sda1": {
        "device": "/dev/sda1",
        "temperature": "29",
        "unit_of_measurement": TEMP_CELSIUS,
        "model": "WDC WD30EZRX-12DC0B0",
    },
    "/dev/sdb1": {
        "device": "/dev/sdb1",
        "temperature": "32",
        "unit_of_measurement": TEMP_CELSIUS,
        "model": "WDC WD15EADS-11P7B2",
    },
    "/dev/sdc1": {
        "device": "/dev/sdc1",
        "temperature": "29",
        "unit_of_measurement": TEMP_CELSIUS,
        "model": "WDC WD20EARX-22MMMB0",
    },
    "/dev/sdd1": {
        "device": "/dev/sdd1",
        "temperature": "32",
        "unit_of_measurement": TEMP_CELSIUS,
        "model": "WDC WD15EARS-00Z5B1",
    },
}


class TelnetMock:
    """Mock class for the telnetlib.Telnet object."""

    def __init__(self, host, port, timeout=0):
        """Initialize Telnet object."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sample_data = bytes(
            "|/dev/sda1|WDC WD30EZRX-12DC0B0|29|C|"
            + "|/dev/sdb1|WDC WD15EADS-11P7B2|32|C|"
            + "|/dev/sdc1|WDC WD20EARX-22MMMB0|29|C|"
            + "|/dev/sdd1|WDC WD15EARS-00Z5B1|89|F|",
            "ascii",
        )

    def read_all(self):
        """Return sample values."""
        if self.host == "alice.local":
            raise ConnectionRefusedError
        if self.host == "bob.local":
            raise socket.gaierror
        return self.sample_data


@pytest.fixture
def telnetmock():
    """Mock telnet."""
    with patch("telnetlib.Telnet", new=TelnetMock):
        yield


async def test_hddtemp_min_config(opp, telnetmock):
    """Test minimal hddtemp configuration."""
    assert await async_setup_component.opp, "sensor", VALID_CONFIG_MINIMAL)
    await.opp.async_block_till_done()

    entity_id =.opp.states.async_all()[0].entity_id
    state =.opp.states.get(entity_id)

    reference = REFERENCE[state.attributes.get("device")]

    assert state.state == reference["temperature"]
    assert state.attributes.get("device") == reference["device"]
    assert state.attributes.get("model") == reference["model"]
    assert (
        state.attributes.get("unit_of_measurement") == reference["unit_of_measurement"]
    )
    assert (
        state.attributes.get("friendly_name") == f"HD Temperature {reference['device']}"
    )


async def test_hddtemp_rename_config(opp, telnetmock):
    """Test hddtemp configuration with different name."""
    assert await async_setup_component.opp, "sensor", VALID_CONFIG_NAME)
    await.opp.async_block_till_done()

    entity_id =.opp.states.async_all()[0].entity_id
    state =.opp.states.get(entity_id)

    reference = REFERENCE[state.attributes.get("device")]

    assert state.attributes.get("friendly_name") == f"FooBar {reference['device']}"


async def test_hddtemp_one_disk.opp, telnetmock):
    """Test hddtemp one disk configuration."""
    assert await async_setup_component.opp, "sensor", VALID_CONFIG_ONE_DISK)
    await.opp.async_block_till_done()

    state =.opp.states.get("sensor.hd_temperature_dev_sdd1")

    reference = REFERENCE[state.attributes.get("device")]

    assert state.state == reference["temperature"]
    assert state.attributes.get("device") == reference["device"]
    assert state.attributes.get("model") == reference["model"]
    assert (
        state.attributes.get("unit_of_measurement") == reference["unit_of_measurement"]
    )
    assert (
        state.attributes.get("friendly_name") == f"HD Temperature {reference['device']}"
    )


async def test_hddtemp_wrong_disk.opp, telnetmock):
    """Test hddtemp wrong disk configuration."""
    assert await async_setup_component.opp, "sensor", VALID_CONFIG_WRONG_DISK)
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1
    state =.opp.states.get("sensor.hd_temperature_dev_sdx1")
    assert state.attributes.get("friendly_name") == "HD Temperature /dev/sdx1"


async def test_hddtemp_multiple_disks.opp, telnetmock):
    """Test hddtemp multiple disk configuration."""
    assert await async_setup_component.opp, "sensor", VALID_CONFIG_MULTIPLE_DISKS)
    await.opp.async_block_till_done()

    for sensor in [
        "sensor.hd_temperature_dev_sda1",
        "sensor.hd_temperature_dev_sdb1",
        "sensor.hd_temperature_dev_sdc1",
    ]:

        state =.opp.states.get(sensor)

        reference = REFERENCE[state.attributes.get("device")]

        assert state.state == reference["temperature"]
        assert state.attributes.get("device") == reference["device"]
        assert state.attributes.get("model") == reference["model"]
        assert (
            state.attributes.get("unit_of_measurement")
            == reference["unit_of_measurement"]
        )
        assert (
            state.attributes.get("friendly_name")
            == f"HD Temperature {reference['device']}"
        )


async def test_hddtemp_host_refused.opp, telnetmock):
    """Test hddtemp if host is refused."""
    assert await async_setup_component.opp, "sensor", VALID_CONFIG_HOST_REFUSED)
    await.opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


async def test_hddtemp_host_unreachable.opp, telnetmock):
    """Test hddtemp if host unreachable."""
    assert await async_setup_component.opp, "sensor", VALID_CONFIG_HOST_UNREACHABLE)
    await.opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0
