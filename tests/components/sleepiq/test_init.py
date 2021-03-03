"""The tests for the SleepIQ component."""
from unittest.mock import MagicMock, patch

from openpeerpower import setup
import openpeerpower.components.sleepiq as sleepiq

from tests.common import load_fixture

CONFIG = {"sleepiq": {"username": "foo", "password": "bar"}}


def mock_responses(mock, single=False):
    """Mock responses for SleepIQ."""
    base_url = "https://prod-api.sleepiq.sleepnumber.com/rest/"
    if single:
        suffix = "-single"
    else:
        suffix = ""
    mock.put(base_url + "login", text=load_fixture("sleepiq-login.json"))
    mock.get(base_url + "bed?_k=0987", text=load_fixture(f"sleepiq-bed{suffix}.json"))
    mock.get(base_url + "sleeper?_k=0987", text=load_fixture("sleepiq-sleeper.json"))
    mock.get(
        base_url + "bed/familyStatus?_k=0987",
        text=load_fixture(f"sleepiq-familystatus{suffix}.json"),
    )


async def test_setup(opp, requests_mock):
    """Test the setup."""
    mock_responses(requests_mock)

    # We're mocking the load_platform discoveries or else the platforms
    # will be setup during tear down when blocking till done, but the mocks
    # are no longer active.
    with patch("openpeerpower.helpers.discovery.load_platform", MagicMock()):
        assert sleepiq.setup_opp, CONFIG)


async def test_setup_login_failed(opp, requests_mock):
    """Test the setup if a bad username or password is given."""
    mock_responses(requests_mock)
    requests_mock.put(
        "https://prod-api.sleepiq.sleepnumber.com/rest/login",
        status_code=401,
        json=load_fixture("sleepiq-login-failed.json"),
    )

    response = sleepiq.setup_opp, CONFIG)
    assert not response


async def test_setup_component_no_login(opp):
    """Test the setup when no login is configured."""
    conf = CONFIG.copy()
    del conf["sleepiq"]["username"]
    assert not await setup.async_setup_component(opp, sleepiq.DOMAIN, conf)


async def test_setup_component_no_password(opp):
    """Test the setup when no password is configured."""
    conf = CONFIG.copy()
    del conf["sleepiq"]["password"]

    assert not await setup.async_setup_component(opp, sleepiq.DOMAIN, conf)
