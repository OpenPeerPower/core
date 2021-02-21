"""Tests for the Cert Expiry sensors."""
from datetime import timedelta
import socket
import ssl
from unittest.mock import patch

from openpeerpower.components.cert_expiry.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_SETUP_RETRY
from openpeerpower.const import CONF_HOST, CONF_PORT, STATE_UNAVAILABLE, STATE_UNKNOWN
from openpeerpowerr.util.dt import utcnow

from .const import HOST, PORT
from .helpers import future_timestamp, static_datetime

from tests.common import MockConfigEntry, async_fire_time_changed


@patch("openpeerpowerr.util.dt.utcnow", return_value=static_datetime())
async def test_async_setup_entry(mock_now,.opp):
    """Test async_setup_entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    )

    timestamp = future_timestamp(100)

    with patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=timestamp,
    ):
        entry.add_to_opp.opp)
        assert await opp..config_entries.async_setup(entry.entry_id)
        await opp..async_block_till_done()

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")


async def test_async_setup_entry_bad_cert.opp):
    """Test async_setup_entry with a bad/expired cert."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    )

    with patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=ssl.SSLError("some error"),
    ):
        entry.add_to_opp.opp)
        assert await opp..config_entries.async_setup(entry.entry_id)
        await opp..async_block_till_done()

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.attributes.get("error") == "some error"
    assert not state.attributes.get("is_valid")


async def test_async_setup_entry_host_unavailable.opp):
    """Test async_setup_entry when host is unavailable."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    )

    with patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=socket.gaierror,
    ):
        entry.add_to_opp.opp)
        assert await opp..config_entries.async_setup(entry.entry_id) is False
        await opp..async_block_till_done()

    assert entry.state == ENTRY_STATE_SETUP_RETRY

    next_update = utcnow() + timedelta(seconds=45)
    async_fire_time_changed.opp, next_update)
    with patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=socket.gaierror,
    ):
        await opp..async_block_till_done()

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state is None


async def test_update_sensor.opp):
    """Test async_update for sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    )

    starting_time = static_datetime()
    timestamp = future_timestamp(100)

    with patch("openpeerpowerr.util.dt.utcnow", return_value=starting_time), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=timestamp,
    ):
        entry.add_to_opp.opp)
        assert await opp..config_entries.async_setup(entry.entry_id)
        await opp..async_block_till_done()

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")

    next_update = starting_time + timedelta(hours=24)
    with patch("openpeerpowerr.util.dt.utcnow", return_value=next_update), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=timestamp,
    ):
        async_fire_time_changed.opp, utcnow() + timedelta(hours=24))
        await opp..async_block_till_done()

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")


async def test_update_sensor_network_errors.opp):
    """Test async_update for sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    )

    starting_time = static_datetime()
    timestamp = future_timestamp(100)

    with patch("openpeerpowerr.util.dt.utcnow", return_value=starting_time), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=timestamp,
    ):
        entry.add_to_opp.opp)
        assert await opp..config_entries.async_setup(entry.entry_id)
        await opp..async_block_till_done()

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")

    next_update = starting_time + timedelta(hours=24)

    with patch("openpeerpowerr.util.dt.utcnow", return_value=next_update), patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=socket.gaierror,
    ):
        async_fire_time_changed.opp, utcnow() + timedelta(hours=24))
        await opp..async_block_till_done()

    next_update = starting_time + timedelta(hours=48)

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state.state == STATE_UNAVAILABLE

    with patch("openpeerpowerr.util.dt.utcnow", return_value=next_update), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=timestamp,
    ):
        async_fire_time_changed.opp, utcnow() + timedelta(hours=48))
        await opp..async_block_till_done()

        state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
        assert state is not None
        assert state.state != STATE_UNAVAILABLE
        assert state.state == timestamp.isoformat()
        assert state.attributes.get("error") == "None"
        assert state.attributes.get("is_valid")

    next_update = starting_time + timedelta(hours=72)

    with patch("openpeerpowerr.util.dt.utcnow", return_value=next_update), patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=ssl.SSLError("something bad"),
    ):
        async_fire_time_changed.opp, utcnow() + timedelta(hours=72))
        await opp..async_block_till_done()

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("error") == "something bad"
    assert not state.attributes.get("is_valid")

    next_update = starting_time + timedelta(hours=96)

    with patch("openpeerpowerr.util.dt.utcnow", return_value=next_update), patch(
        "openpeerpower.components.cert_expiry.helper.get_cert", side_effect=Exception()
    ):
        async_fire_time_changed.opp, utcnow() + timedelta(hours=96))
        await opp..async_block_till_done()

    state = opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state.state == STATE_UNAVAILABLE
