"""Test the python_script component."""
import logging
from unittest.mock import mock_open, patch

from openpeerpower.components.python_script import DOMAIN, FOLDER, execute
from openpeerpower.helpers.service import async_get_all_descriptions
from openpeerpower.setup import async_setup_component

from tests.common import patch_yaml_files


async def test_setup_opp):
    """Test we can discover scripts."""
    scripts = [
        "/some/config/dir/python_scripts/hello.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]
    with patch(
        "openpeerpower.components.python_script.os.path.isdir", return_value=True
    ), patch("openpeerpower.components.python_script.glob.iglob", return_value=scripts):
        res = await async_setup_component.opp, "python_script", {})

    assert res
    assert.opp.services.has_service("python_script", "hello")
    assert.opp.services.has_service("python_script", "world_beer")

    with patch(
        "openpeerpower.components.python_script.open",
        mock_open(read_data="fake source"),
        create=True,
    ), patch("openpeerpower.components.python_script.execute") as mock_ex:
        await opp.services.async_call(
            "python_script", "hello", {"some": "data"}, blocking=True
        )

    assert len(mock_ex.mock_calls) == 1
   .opp, script, source, data = mock_ex.mock_calls[0][1]

    assert.opp is.opp
    assert script == "hello.py"
    assert source == "fake source"
    assert data == {"some": "data"}


async def test_setup_fails_on_no_dir.opp, caplog):
    """Test we fail setup when no dir found."""
    with patch(
        "openpeerpower.components.python_script.os.path.isdir", return_value=False
    ):
        res = await async_setup_component.opp, "python_script", {})

    assert not res
    assert "Folder python_scripts not found in configuration folder" in caplog.text


async def test_execute_with_data.opp, caplog):
    """Test executing a script."""
    caplog.set_level(logging.WARNING)
    source = """
opp.states.set('test.entity', data.get('name', 'not set'))
    """

   .opp.async_add_executor_job(execute, opp, "test.py", source, {"name": "paulus"})
    await opp.async_block_till_done()

    assert.opp.states.is_state("test.entity", "paulus")

    # No errors logged = good
    assert caplog.text == ""


async def test_execute_warns_print.opp, caplog):
    """Test print triggers warning."""
    caplog.set_level(logging.WARNING)
    source = """
print("This triggers warning.")
    """

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert "Don't use print() inside scripts." in caplog.text


async def test_execute_logging.opp, caplog):
    """Test logging works."""
    caplog.set_level(logging.INFO)
    source = """
logger.info('Logging from inside script')
    """

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert "Logging from inside script" in caplog.text


async def test_execute_compile_error(opp, caplog):
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)
    source = """
this is not valid Python
    """

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert "Error loading script test.py" in caplog.text


async def test_execute_runtime_error(opp, caplog):
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)
    source = """
raise Exception('boom')
    """

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert "Error executing script: boom" in caplog.text


async def test_accessing_async_methods.opp, caplog):
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)
    source = """
opp.async_stop()
    """

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert "Not allowed to access async methods" in caplog.text


async def test_using_complex_structures.opp, caplog):
    """Test that dicts and lists work."""
    caplog.set_level(logging.INFO)
    source = """
mydict = {"a": 1, "b": 2}
mylist = [1, 2, 3, 4]
logger.info('Logging from inside script: %s %s' % (mydict["a"], mylist[2]))
    """

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert "Logging from inside script: 1 3" in caplog.text


async def test_accessing_forbidden_methods.opp, caplog):
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)

    for source, name in {
        .opp.stop()": "OpenPeerPower.stop",
        "dt_util.set_default_time_zone()": "module.set_default_time_zone",
        "datetime.non_existing": "module.non_existing",
        "time.tzset()": "TimeWrapper.tzset",
    }.items():
        caplog.records.clear()
       .opp.async_add_executor_job(execute, opp, "test.py", source, {})
        await opp.async_block_till_done()
        assert f"Not allowed to access {name}" in caplog.text


async def test_iterating.opp):
    """Test compile error logs error."""
    source = """
for i in [1, 2]:
   .opp.states.set('hello.{}'.format(i), 'world')
    """

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert.opp.states.is_state("hello.1", "world")
    assert.opp.states.is_state("hello.2", "world")


async def test_unpacking_sequence.opp, caplog):
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)
    source = """
a,b = (1,2)
ab_list = [(a,b) for a,b in [(1, 2), (3, 4)]]
opp.states.set('hello.a', a)
opp.states.set('hello.b', b)
opp.states.set('hello.ab_list', '{}'.format(ab_list))
"""

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert.opp.states.is_state("hello.a", "1")
    assert.opp.states.is_state("hello.b", "2")
    assert.opp.states.is_state("hello.ab_list", "[(1, 2), (3, 4)]")

    # No errors logged = good
    assert caplog.text == ""


async def test_execute_sorted.opp, caplog):
    """Test sorted() function."""
    caplog.set_level(logging.ERROR)
    source = """
a  = sorted([3,1,2])
assert(a == [1,2,3])
opp.states.set('hello.a', a[0])
opp.states.set('hello.b', a[1])
opp.states.set('hello.c', a[2])
"""
   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert.opp.states.is_state("hello.a", "1")
    assert.opp.states.is_state("hello.b", "2")
    assert.opp.states.is_state("hello.c", "3")
    # No errors logged = good
    assert caplog.text == ""


async def test_exposed_modules.opp, caplog):
    """Test datetime and time modules exposed."""
    caplog.set_level(logging.ERROR)
    source = """
opp.states.set('module.time', time.strftime('%Y', time.gmtime(521276400)))
opp.states.set('module.time_strptime',
                time.strftime('%H:%M', time.strptime('12:34', '%H:%M')))
opp.states.set('module.datetime',
                datetime.timedelta(minutes=1).total_seconds())
"""

   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert.opp.states.is_state("module.time", "1986")
    assert.opp.states.is_state("module.time_strptime", "12:34")
    assert.opp.states.is_state("module.datetime", "60.0")

    # No errors logged = good
    assert caplog.text == ""


async def test_execute_functions.opp, caplog):
    """Test functions defined in script can call one another."""
    caplog.set_level(logging.ERROR)
    source = """
def a():
   .opp.states.set('hello.a', 'one')

def b():
    a()
   .opp.states.set('hello.b', 'two')

b()
"""
   .opp.async_add_executor_job(execute, opp, "test.py", source, {})
    await opp.async_block_till_done()

    assert.opp.states.is_state("hello.a", "one")
    assert.opp.states.is_state("hello.b", "two")
    # No errors logged = good
    assert caplog.text == ""


async def test_reload.opp):
    """Test we can re-discover scripts."""
    scripts = [
        "/some/config/dir/python_scripts/hello.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]
    with patch(
        "openpeerpower.components.python_script.os.path.isdir", return_value=True
    ), patch("openpeerpower.components.python_script.glob.iglob", return_value=scripts):
        res = await async_setup_component.opp, "python_script", {})

    assert res
    assert.opp.services.has_service("python_script", "hello")
    assert.opp.services.has_service("python_script", "world_beer")
    assert.opp.services.has_service("python_script", "reload")

    scripts = [
        "/some/config/dir/python_scripts/hello2.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]
    with patch(
        "openpeerpower.components.python_script.os.path.isdir", return_value=True
    ), patch("openpeerpower.components.python_script.glob.iglob", return_value=scripts):
        await opp.services.async_call("python_script", "reload", {}, blocking=True)

    assert not.opp.services.has_service("python_script", "hello")
    assert.opp.services.has_service("python_script", "hello2")
    assert.opp.services.has_service("python_script", "world_beer")
    assert.opp.services.has_service("python_script", "reload")


async def test_service_descriptions.opp):
    """Test that service descriptions are loaded and reloaded correctly."""
    # Test 1: no user-provided services.yaml file
    scripts1 = [
        "/some/config/dir/python_scripts/hello.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]

    service_descriptions1 = (
        "hello:\n"
        "  description: Description of hello.py.\n"
        "  fields:\n"
        "    fake_param:\n"
        "      description: Parameter used by hello.py.\n"
        "      example: 'This is a test of python_script.hello'"
    )
    services_yaml1 = {
        "{}/{}/services.yaml".format(
           .opp.config.config_dir, FOLDER
        ): service_descriptions1
    }

    with patch(
        "openpeerpower.components.python_script.os.path.isdir", return_value=True
    ), patch(
        "openpeerpower.components.python_script.glob.iglob", return_value=scripts1
    ), patch(
        "openpeerpower.components.python_script.os.path.exists", return_value=True
    ), patch_yaml_files(
        services_yaml1
    ):
        await async_setup_component.opp, DOMAIN, {})

        descriptions = await async_get_all_descriptions.opp)

    assert len(descriptions) == 1

    assert descriptions[DOMAIN]["hello"]["description"] == "Description of hello.py."
    assert (
        descriptions[DOMAIN]["hello"]["fields"]["fake_param"]["description"]
        == "Parameter used by hello.py."
    )
    assert (
        descriptions[DOMAIN]["hello"]["fields"]["fake_param"]["example"]
        == "This is a test of python_script.hello"
    )

    assert descriptions[DOMAIN]["world_beer"]["description"] == ""
    assert bool(descriptions[DOMAIN]["world_beer"]["fields"]) is False

    # Test 2: user-provided services.yaml file
    scripts2 = [
        "/some/config/dir/python_scripts/hello2.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]

    service_descriptions2 = (
        "hello2:\n"
        "  description: Description of hello2.py.\n"
        "  fields:\n"
        "    fake_param:\n"
        "      description: Parameter used by hello2.py.\n"
        "      example: 'This is a test of python_script.hello2'"
    )
    services_yaml2 = {
        "{}/{}/services.yaml".format(
           .opp.config.config_dir, FOLDER
        ): service_descriptions2
    }

    with patch(
        "openpeerpower.components.python_script.os.path.isdir", return_value=True
    ), patch(
        "openpeerpower.components.python_script.glob.iglob", return_value=scripts2
    ), patch(
        "openpeerpower.components.python_script.os.path.exists", return_value=True
    ), patch_yaml_files(
        services_yaml2
    ):
        await opp.services.async_call(DOMAIN, "reload", {}, blocking=True)
        descriptions = await async_get_all_descriptions.opp)

    assert len(descriptions) == 1

    assert descriptions[DOMAIN]["hello2"]["description"] == "Description of hello2.py."
    assert (
        descriptions[DOMAIN]["hello2"]["fields"]["fake_param"]["description"]
        == "Parameter used by hello2.py."
    )
    assert (
        descriptions[DOMAIN]["hello2"]["fields"]["fake_param"]["example"]
        == "This is a test of python_script.hello2"
    )


async def test_sleep_warns_one.opp, caplog):
    """Test time.sleep warns once."""
    caplog.set_level(logging.WARNING)
    source = """
time.sleep(2)
time.sleep(5)
"""

    with patch("openpeerpower.components.python_script.time.sleep"):
       .opp.async_add_executor_job(execute, opp, "test.py", source, {})
        await opp.async_block_till_done()

    assert caplog.text.count("time.sleep") == 1
