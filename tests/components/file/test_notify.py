"""The tests for the notify file platform."""
import os
from unittest.mock import call, mock_open, patch

import pytest

import openpeerpower.components.notify as notify
from openpeerpower.components.notify import ATTR_TITLE_DEFAULT
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import assert_setup_component


async def test_bad_config(opp):
    """Test set up the platform with bad/missing config."""
    config = {notify.DOMAIN: {"name": "test", "platform": "file"}}
    with assert_setup_component(0) as handle_config:
        assert await async_setup_component(opp, notify.DOMAIN, config)
    assert not handle_config[notify.DOMAIN]


@pytest.mark.parametrize(
    "timestamp",
    [
        False,
        True,
    ],
)
async def test_notify_file(opp, timestamp):
    """Test the notify file output."""
    filename = "mock_file"
    message = "one, two, testing, testing"
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component(
            opp,
            notify.DOMAIN,
            {
                "notify": {
                    "name": "test",
                    "platform": "file",
                    "filename": filename,
                    "timestamp": timestamp,
                }
            },
        )
    assert handle_config[notify.DOMAIN]

    m_open = mock_open()
    with patch("openpeerpower.components.file.notify.open", m_open, create=True), patch(
        "openpeerpower.components.file.notify.os.stat"
    ) as mock_st, patch("openpeerpower.util.dt.utcnow", return_value=dt_util.utcnow()):

        mock_st.return_value.st_size = 0
        title = (
            f"{ATTR_TITLE_DEFAULT} notifications "
            f"(Log started: {dt_util.utcnow().isoformat()})\n{'-' * 80}\n"
        )

        await opp.services.async_call(
            "notify", "test", {"message": message}, blocking=True
        )

        full_filename = os.path.join opp.config.path(), filename)
        assert m_open.call_count == 1
        assert m_open.call_args == call(full_filename, "a")

        assert m_open.return_value.write.call_count == 2
        if not timestamp:
            assert m_open.return_value.write.call_args_list == [
                call(title),
                call(f"{message}\n"),
            ]
        else:
            assert m_open.return_value.write.call_args_list == [
                call(title),
                call(f"{dt_util.utcnow().isoformat()} {message}\n"),
            ]
