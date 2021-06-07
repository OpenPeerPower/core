"""Test util methods."""
from datetime import timedelta
import os
import sqlite3
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from openpeerpower.components.recorder import run_information_with_session, util
from openpeerpower.components.recorder.const import DATA_INSTANCE, SQLITE_URL_PREFIX
from openpeerpower.components.recorder.models import RecorderRuns
from openpeerpower.components.recorder.util import end_incomplete_runs, session_scope
from openpeerpower.util import dt as dt_util

from .common import corrupt_db_file

from tests.common import async_init_recorder_component


def test_session_scope_not_setup(opp_recorder):
    """Try to create a session scope when not setup."""
    opp = opp_recorder()
    with patch.object(
        opp.data[DATA_INSTANCE], "get_session", return_value=None
    ), pytest.raises(RuntimeError):
        with util.session_scope(opp.opp):
            pass


def test_recorder_bad_commit(opp_recorder):
    """Bad _commit should retry 3 times."""
    opp = opp_recorder()

    def work(session):
        """Bad work."""
        session.execute(text("select * from notthere"))

    with patch(
        "openpeerpower.components.recorder.time.sleep"
    ) as e_mock, util.session_scope(opp.opp) as session:
        res = util.commit(session, work)
    assert res is False
    assert e_mock.call_count == 3


def test_recorder_bad_execute(opp_recorder):
    """Bad execute, retry 3 times."""
    from sqlalchemy.exc import SQLAlchemyError

    opp_recorder()

    def to_native(validate_entity_id=True):
        """Raise exception."""
        raise SQLAlchemyError()

    mck1 = MagicMock()
    mck1.to_native = to_native

    with pytest.raises(SQLAlchemyError), patch(
        "openpeerpower.components.recorder.time.sleep"
    ) as e_mock:
        util.execute((mck1,), to_native=True)

    assert e_mock.call_count == 2


def test_validate_or_move_away_sqlite_database(opp, tmpdir, caplog):
    """Ensure a malformed sqlite database is moved away."""

    test_dir = tmpdir.mkdir("test_validate_or_move_away_sqlite_database")
    test_db_file = f"{test_dir}/broken.db"
    dburl = f"{SQLITE_URL_PREFIX}{test_db_file}"

    assert util.validate_sqlite_database(test_db_file) is False
    assert os.path.exists(test_db_file) is True
    assert util.validate_or_move_away_sqlite_database(dburl) is False

    corrupt_db_file(test_db_file)

    assert util.validate_sqlite_database(dburl) is False

    assert util.validate_or_move_away_sqlite_database(dburl) is False

    assert "corrupt or malformed" in caplog.text

    assert util.validate_sqlite_database(dburl) is False

    assert util.validate_or_move_away_sqlite_database(dburl) is True


async def test_last_run_was_recently_clean(opp):
    """Test we can check if the last recorder run was recently clean."""
    await async_init_recorder_component(opp)
    await opp.async_block_till_done()

    cursor = opp.data[DATA_INSTANCE].engine.raw_connection().cursor()

    assert (
        await opp.async_add_executor_job(util.last_run_was_recently_clean, cursor)
        is False
    )

    await opp.async_add_executor_job(opp.data[DATA_INSTANCE]._end_session)
    await opp.async_block_till_done()

    assert (
        await opp.async_add_executor_job(util.last_run_was_recently_clean, cursor)
        is True
    )

    thirty_min_future_time = dt_util.utcnow() + timedelta(minutes=30)

    with patch(
        "openpeerpower.components.recorder.dt_util.utcnow",
        return_value=thirty_min_future_time,
    ):
        assert (
            await opp.async_add_executor_job(util.last_run_was_recently_clean, cursor)
            is False
        )


def test_setup_connection_for_dialect_mysql():
    """Test setting up the connection for a mysql dialect."""
    execute_mock = MagicMock()
    close_mock = MagicMock()

    def _make_cursor_mock(*_):
        return MagicMock(execute=execute_mock, close=close_mock)

    dbapi_connection = MagicMock(cursor=_make_cursor_mock)

    util.setup_connection_for_dialect("mysql", dbapi_connection, True)

    assert execute_mock.call_args[0][0] == "SET session wait_timeout=28800"


def test_setup_connection_for_dialect_sqlite():
    """Test setting up the connection for a sqlite dialect."""
    execute_mock = MagicMock()
    close_mock = MagicMock()

    def _make_cursor_mock(*_):
        return MagicMock(execute=execute_mock, close=close_mock)

    dbapi_connection = MagicMock(cursor=_make_cursor_mock)

    util.setup_connection_for_dialect("sqlite", dbapi_connection, True)

    assert len(execute_mock.call_args_list) == 2
    assert execute_mock.call_args_list[0][0][0] == "PRAGMA journal_mode=WAL"
    assert execute_mock.call_args_list[1][0][0] == "PRAGMA cache_size = -8192"

    execute_mock.reset_mock()
    util.setup_connection_for_dialect("sqlite", dbapi_connection, False)

    assert len(execute_mock.call_args_list) == 1
    assert execute_mock.call_args_list[0][0][0] == "PRAGMA cache_size = -8192"


def test_basic_sanity_check(opp_recorder):
    """Test the basic sanity checks with a missing table."""
    opp = opp_recorder()

    cursor = opp.data[DATA_INSTANCE].engine.raw_connection().cursor()

    assert util.basic_sanity_check(cursor) is True

    cursor.execute("DROP TABLE states;")

    with pytest.raises(sqlite3.DatabaseError):
        util.basic_sanity_check(cursor)


def test_combined_checks(opp_recorder, caplog):
    """Run Checks on the open database."""
    opp = opp_recorder()

    cursor = opp.data[DATA_INSTANCE].engine.raw_connection().cursor()

    assert util.run_checks_on_open_db("fake_db_path", cursor) is None
    assert "could not validate that the sqlite3 database" in caplog.text

    caplog.clear()

    # We are patching recorder.util here in order
    # to avoid creating the full database on disk
    with patch(
        "openpeerpower.components.recorder.util.basic_sanity_check", return_value=False
    ):
        caplog.clear()
        assert util.run_checks_on_open_db("fake_db_path", cursor) is None
        assert "could not validate that the sqlite3 database" in caplog.text

    # We are patching recorder.util here in order
    # to avoid creating the full database on disk
    with patch("openpeerpower.components.recorder.util.last_run_was_recently_clean"):
        caplog.clear()
        assert util.run_checks_on_open_db("fake_db_path", cursor) is None
        assert "restarted cleanly and passed the basic sanity check" in caplog.text

    caplog.clear()
    with patch(
        "openpeerpower.components.recorder.util.last_run_was_recently_clean",
        side_effect=sqlite3.DatabaseError,
    ), pytest.raises(sqlite3.DatabaseError):
        util.run_checks_on_open_db("fake_db_path", cursor)

    caplog.clear()
    with patch(
        "openpeerpower.components.recorder.util.last_run_was_recently_clean",
        side_effect=sqlite3.DatabaseError,
    ), pytest.raises(sqlite3.DatabaseError):
        util.run_checks_on_open_db("fake_db_path", cursor)

    cursor.execute("DROP TABLE events;")

    caplog.clear()
    with pytest.raises(sqlite3.DatabaseError):
        util.run_checks_on_open_db("fake_db_path", cursor)

    caplog.clear()
    with pytest.raises(sqlite3.DatabaseError):
        util.run_checks_on_open_db("fake_db_path", cursor)


def test_end_incomplete_runs(opp_recorder, caplog):
    """Ensure we can end incomplete runs."""
    opp = opp_recorder()

    with session_scope(opp.opp) as session:
        run_info = run_information_with_session(session)
        assert isinstance(run_info, RecorderRuns)
        assert run_info.closed_incorrect is False

        now = dt_util.utcnow()
        now_without_tz = now.replace(tzinfo=None)
        end_incomplete_runs(session, now)
        run_info = run_information_with_session(session)
        assert run_info.closed_incorrect is True
        assert run_info.end == now_without_tz
        session.flush()

        later = dt_util.utcnow()
        end_incomplete_runs(session, later)
        run_info = run_information_with_session(session)
        assert run_info.end == now_without_tz

    assert "Ended unfinished session" in caplog.text


def test_perodic_db_cleanups(opp_recorder):
    """Test perodic db cleanups."""
    opp = opp_recorder()
    with patch.object(opp.data[DATA_INSTANCE].engine, "execute") as execute_mock:
        util.perodic_db_cleanups(opp.data[DATA_INSTANCE])
    assert execute_mock.call_args[0][0] == "PRAGMA wal_checkpoint(TRUNCATE);"
