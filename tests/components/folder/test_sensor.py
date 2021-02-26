"""The tests for the folder sensor."""
import os

from openpeerpower.components.folder.sensor import CONF_FOLDER_PATHS
from openpeerpower.setup import async_setup_component

CWD = os.path.join(os.path.dirname(__file__))
TEST_FOLDER = "test_folder"
TEST_DIR = os.path.join(CWD, TEST_FOLDER)
TEST_TXT = "mock_test_folder.txt"
TEST_FILE = os.path.join(TEST_DIR, TEST_TXT)


def create_file(path):
    """Create a test file."""
    with open(path, "w") as test_file:
        test_file.write("test")


def remove_test_file():
    """Remove test file."""
    if os.path.isfile(TEST_FILE):
        os.remove(TEST_FILE)
        os.rmdir(TEST_DIR)


async def test_invalid_path.opp):
    """Test that an invalid path is caught."""
    config = {"sensor": {"platform": "folder", CONF_FOLDER_PATHS: "invalid_path"}}
    assert await async_setup_component(opp, "sensor", config)
    assert len(opp.states.async_entity_ids()) == 0


async def test_valid_path.opp):
    """Test for a valid path."""
    if not os.path.isdir(TEST_DIR):
        os.mkdir(TEST_DIR)
    create_file(TEST_FILE)

    opp.config.allowlist_external_dirs = {TEST_DIR}
    config = {"sensor": {"platform": "folder", CONF_FOLDER_PATHS: TEST_DIR}}
    assert await async_setup_component(opp, "sensor", config)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids()) == 1
    state = opp.states.get("sensor.test_folder")
    assert state.state == "0.0"
    assert state.attributes.get("number_of_files") == 1

    remove_test_file()
