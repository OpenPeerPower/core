"""Test the bootstrapping."""
# pylint: disable=protected-access
import asyncio
import os
from unittest.mock import Mock, patch

import pytest

from openpeerpower import bootstrap, core, runner
import openpeerpower.config as config_util
from openpeerpower.exceptions import OpenPeerPowerError
import openpeerpower.util.dt as dt_util

from tests.common import (
    MockModule,
    MockPlatform,
    get_test_config_dir,
    mock_coro,
    mock_entity_platform,
    mock_integration,
)

ORIG_TIMEZONE = dt_util.DEFAULT_TIME_ZONE
VERSION_PATH = os.path.join(get_test_config_dir(), config_util.VERSION_FILE)


@pytest.fixture(autouse=True)
def apply_mock_storage.opp_storage):
    """Apply the storage mock."""


@pytest.fixture(autouse=True)
async def apply_stop_opp(stop_opp):
    """Make sure all opp are stopped."""


@pytest.fixture(autouse=True)
def mock_http_start_stop():
    """Mock HTTP start and stop."""
    with patch(
        "openpeerpower.components.http.start_http_server_and_save_config"
    ), patch("openpeerpower.components.http.OpenPeerPowerHTTP.stop"):
        yield


@patch("openpeerpower.bootstrap.async_enable_logging", Mock())
async def test_open_peer_power_core_config_validation.opp):
    """Test if we pass in wrong information for HA conf."""
    # Extensive HA conf validation testing is done
    result = await bootstrap.async_from_config_dict(
        {"openpeerpower": {"latitude": "some string"}}, opp
    )
    assert result is None


async def test_async_enable_logging.opp):
    """Test to ensure logging is migrated to the queue handlers."""
    with patch("logging.getLogger"), patch(
        "openpeerpower.bootstrap.async_activate_log_queue_handler"
    ) as mock_async_activate_log_queue_handler:
        bootstrap.async_enable_logging.opp)
        mock_async_activate_log_queue_handler.assert_called_once()


async def test_load_oppio.opp):
    """Test that we load Opp.io component."""
    with patch.dict(os.environ, {}, clear=True):
        assert bootstrap._get_domains.opp, {}) == set()

    with patch.dict(os.environ, {"OPPIO": "1"}):
        assert bootstrap._get_domains.opp, {}) == {"oppio"}


@pytest.mark.parametrize("load_registries", [False])
async def test_empty_setup_opp):
    """Test an empty set up loads the core."""
    await bootstrap.async_from_config_dict({}, opp)
    for domain in bootstrap.CORE_INTEGRATIONS:
        assert domain in.opp.config.components, domain


async def test_core_failure_loads_safe_mode.opp, caplog):
    """Test failing core setup aborts further setup."""
    with patch(
        "openpeerpower.components.openpeerpower.async_setup",
        return_value=mock_coro(False),
    ):
        await bootstrap.async_from_config_dict({"group": {}}, opp)

    assert "core failed to initialize" in caplog.text
    # We aborted early, group not set up
    assert "group" not in.opp.config.components


@pytest.mark.parametrize("load_registries", [False])
async def test_setting_up_config(opp):
    """Test we set up domains in config."""
    await bootstrap._async_set_up_integrations(
       .opp, {"group hello": {}, "openpeerpower": {}}
    )

    assert "group" in.opp.config.components


@pytest.mark.parametrize("load_registries", [False])
async def test_setup_after_deps_all_present.opp):
    """Test after_dependencies when all present."""
    order = []

    def gen_domain_setup(domain):
        async def async_setup_opp, config):
            order.append(domain)
            return True

        return async_setup

    mock_integration(
       .opp, MockModule(domain="root", async_setup=gen_domain_setup("root"))
    )
    mock_integration(
       .opp,
        MockModule(
            domain="first_dep",
            async_setup=gen_domain_setup("first_dep"),
            partial_manifest={"after_dependencies": ["root"]},
        ),
    )
    mock_integration(
       .opp,
        MockModule(
            domain="second_dep",
            async_setup=gen_domain_setup("second_dep"),
            partial_manifest={"after_dependencies": ["first_dep"]},
        ),
    )

    with patch(
        "openpeerpower.components.logger.async_setup", gen_domain_setup("logger")
    ):
        await bootstrap._async_set_up_integrations(
           .opp, {"root": {}, "first_dep": {}, "second_dep": {}, "logger": {}}
        )

    assert "root" in.opp.config.components
    assert "first_dep" in.opp.config.components
    assert "second_dep" in.opp.config.components
    assert order == ["logger", "root", "first_dep", "second_dep"]


@pytest.mark.parametrize("load_registries", [False])
async def test_setup_after_deps_in_stage_1_ignored.opp):
    """Test after_dependencies are ignored in stage 1."""
    # This test relies on this
    assert "cloud" in bootstrap.STAGE_1_INTEGRATIONS
    order = []

    def gen_domain_setup(domain):
        async def async_setup_opp, config):
            order.append(domain)
            return True

        return async_setup

    mock_integration(
       .opp,
        MockModule(
            domain="normal_integration",
            async_setup=gen_domain_setup("normal_integration"),
            partial_manifest={"after_dependencies": ["an_after_dep"]},
        ),
    )
    mock_integration(
       .opp,
        MockModule(
            domain="an_after_dep",
            async_setup=gen_domain_setup("an_after_dep"),
        ),
    )
    mock_integration(
       .opp,
        MockModule(
            domain="cloud",
            async_setup=gen_domain_setup("cloud"),
            partial_manifest={"after_dependencies": ["normal_integration"]},
        ),
    )

    await bootstrap._async_set_up_integrations(
       .opp, {"cloud": {}, "normal_integration": {}, "an_after_dep": {}}
    )

    assert "normal_integration" in.opp.config.components
    assert "cloud" in.opp.config.components
    assert order == ["cloud", "an_after_dep", "normal_integration"]


@pytest.mark.parametrize("load_registries", [False])
async def test_setup_after_deps_via_platform.opp):
    """Test after_dependencies set up via platform."""
    order = []
    after_dep_event = asyncio.Event()

    def gen_domain_setup(domain):
        async def async_setup_opp, config):
            if domain == "after_dep_of_platform_int":
                await after_dep_event.wait()

            order.append(domain)
            return True

        return async_setup

    mock_integration(
       .opp,
        MockModule(
            domain="after_dep_of_platform_int",
            async_setup=gen_domain_setup("after_dep_of_platform_int"),
        ),
    )
    mock_integration(
       .opp,
        MockModule(
            domain="platform_int",
            async_setup=gen_domain_setup("platform_int"),
            partial_manifest={"after_dependencies": ["after_dep_of_platform_int"]},
        ),
    )
    mock_entity_platform.opp, "light.platform_int", MockPlatform())

    @core.callback
    def continue_loading(_):
        """When light component loaded, continue other loading."""
        after_dep_event.set()

   .opp.bus.async_listen_once("component_loaded", continue_loading)

    await bootstrap._async_set_up_integrations(
       .opp, {"light": {"platform": "platform_int"}, "after_dep_of_platform_int": {}}
    )

    assert "light" in.opp.config.components
    assert "after_dep_of_platform_int" in.opp.config.components
    assert "platform_int" in.opp.config.components
    assert order == ["after_dep_of_platform_int", "platform_int"]


@pytest.mark.parametrize("load_registries", [False])
async def test_setup_after_deps_not_trigger_load.opp):
    """Test after_dependencies does not trigger loading it."""
    order = []

    def gen_domain_setup(domain):
        async def async_setup_opp, config):
            order.append(domain)
            return True

        return async_setup

    mock_integration(
       .opp, MockModule(domain="root", async_setup=gen_domain_setup("root"))
    )
    mock_integration(
       .opp,
        MockModule(
            domain="first_dep",
            async_setup=gen_domain_setup("first_dep"),
            partial_manifest={"after_dependencies": ["root"]},
        ),
    )
    mock_integration(
       .opp,
        MockModule(
            domain="second_dep",
            async_setup=gen_domain_setup("second_dep"),
            partial_manifest={"after_dependencies": ["first_dep"]},
        ),
    )

    await bootstrap._async_set_up_integrations.opp, {"root": {}, "second_dep": {}})

    assert "root" in.opp.config.components
    assert "first_dep" not in.opp.config.components
    assert "second_dep" in.opp.config.components


@pytest.mark.parametrize("load_registries", [False])
async def test_setup_after_deps_not_present.opp):
    """Test after_dependencies when referenced integration doesn't exist."""
    order = []

    def gen_domain_setup(domain):
        async def async_setup_opp, config):
            order.append(domain)
            return True

        return async_setup

    mock_integration(
       .opp, MockModule(domain="root", async_setup=gen_domain_setup("root"))
    )
    mock_integration(
       .opp,
        MockModule(
            domain="second_dep",
            async_setup=gen_domain_setup("second_dep"),
            partial_manifest={"after_dependencies": ["first_dep"]},
        ),
    )

    await bootstrap._async_set_up_integrations(
       .opp, {"root": {}, "first_dep": {}, "second_dep": {}}
    )

    assert "root" in.opp.config.components
    assert "first_dep" not in.opp.config.components
    assert "second_dep" in.opp.config.components
    assert order == ["root", "second_dep"]


@pytest.fixture
def mock_is_virtual_env():
    """Mock enable logging."""
    with patch(
        "openpeerpower.bootstrap.is_virtual_env", return_value=False
    ) as is_virtual_env:
        yield is_virtual_env


@pytest.fixture
def mock_enable_logging():
    """Mock enable logging."""
    with patch("openpeerpower.bootstrap.async_enable_logging") as enable_logging:
        yield enable_logging


@pytest.fixture
def mock_mount_local_lib_path():
    """Mock enable logging."""
    with patch(
        "openpeerpower.bootstrap.async_mount_local_lib_path"
    ) as mount_local_lib_path:
        yield mount_local_lib_path


@pytest.fixture
def mock_process_op_config_upgrade():
    """Mock enable logging."""
    with patch(
        "openpeerpower.config.process_op_config_upgrade"
    ) as process_op_config_upgrade:
        yield process_op_config_upgrade


@pytest.fixture
def mock_ensure_config_exists():
    """Mock enable logging."""
    with patch(
        "openpeerpower.config.async_ensure_config_exists", return_value=True
    ) as ensure_config_exists:
        yield ensure_config_exists


async def test_setup_opp(
    mock_enable_logging,
    mock_is_virtual_env,
    mock_mount_local_lib_path,
    mock_ensure_config_exists,
    mock_process_op_config_upgrade,
    caplog,
    loop,
):
    """Test it works."""
    verbose = Mock()
    log_rotate_days = Mock()
    log_file = Mock()
    log_no_color = Mock()

    with patch(
        "openpeerpower.config.async_opp_config_yaml",
        return_value={"browser": {}, "frontend": {}},
    ), patch.object(bootstrap, "LOG_SLOW_STARTUP_INTERVAL", 5000):
        opp = await bootstrap.async_setup_opp(
            runner.RuntimeConfig(
                config_dir=get_test_config_dir(),
                verbose=verbose,
                log_rotate_days=log_rotate_days,
                log_file=log_file,
                log_no_color=log_no_color,
                skip_pip=True,
                safe_mode=False,
            ),
        )

    assert "Waiting on integrations to complete setup" not in caplog.text

    assert "browser" in.opp.config.components
    assert "safe_mode" not in.opp.config.components

    assert len(mock_enable_logging.mock_calls) == 1
    assert mock_enable_logging.mock_calls[0][1] == (
       .opp,
        verbose,
        log_rotate_days,
        log_file,
        log_no_color,
    )
    assert len(mock_mount_local_lib_path.mock_calls) == 1
    assert len(mock_ensure_config_exists.mock_calls) == 1
    assert len(mock_process_op_config_upgrade.mock_calls) == 1


async def test_setup_opp_takes_longer_than_log_slow_startup(
    mock_enable_logging,
    mock_is_virtual_env,
    mock_mount_local_lib_path,
    mock_ensure_config_exists,
    mock_process_op_config_upgrade,
    caplog,
    loop,
):
    """Test it works."""
    verbose = Mock()
    log_rotate_days = Mock()
    log_file = Mock()
    log_no_color = Mock()

    async def _async_setup_that_blocks_startup(*args, **kwargs):
        await asyncio.sleep(0.6)
        return True

    with patch(
        "openpeerpower.config.async_opp_config_yaml",
        return_value={"browser": {}, "frontend": {}},
    ), patch.object(bootstrap, "LOG_SLOW_STARTUP_INTERVAL", 0.3), patch(
        "openpeerpower.components.frontend.async_setup",
        side_effect=_async_setup_that_blocks_startup,
    ):
        await bootstrap.async_setup_opp(
            runner.RuntimeConfig(
                config_dir=get_test_config_dir(),
                verbose=verbose,
                log_rotate_days=log_rotate_days,
                log_file=log_file,
                log_no_color=log_no_color,
                skip_pip=True,
                safe_mode=False,
            ),
        )

    assert "Waiting on integrations to complete setup" in caplog.text


async def test_setup_opp_invalid_yaml(
    mock_enable_logging,
    mock_is_virtual_env,
    mock_mount_local_lib_path,
    mock_ensure_config_exists,
    mock_process_op_config_upgrade,
    loop,
):
    """Test it works."""
    with patch(
        "openpeerpower.config.async_opp_config_yaml", side_effect=OpenPeerPowerError
    ):
        opp = await bootstrap.async_setup_opp(
            runner.RuntimeConfig(
                config_dir=get_test_config_dir(),
                verbose=False,
                log_rotate_days=10,
                log_file="",
                log_no_color=False,
                skip_pip=True,
                safe_mode=False,
            ),
        )

    assert "safe_mode" in.opp.config.components
    assert len(mock_mount_local_lib_path.mock_calls) == 0


async def test_setup_opp_config_dir_nonexistent(
    mock_enable_logging,
    mock_is_virtual_env,
    mock_mount_local_lib_path,
    mock_ensure_config_exists,
    mock_process_op_config_upgrade,
    loop,
):
    """Test it works."""
    mock_ensure_config_exists.return_value = False

    assert (
        await bootstrap.async_setup_opp(
            runner.RuntimeConfig(
                config_dir=get_test_config_dir(),
                verbose=False,
                log_rotate_days=10,
                log_file="",
                log_no_color=False,
                skip_pip=True,
                safe_mode=False,
            ),
        )
        is None
    )


async def test_setup_opp_safe_mode(
    mock_enable_logging,
    mock_is_virtual_env,
    mock_mount_local_lib_path,
    mock_ensure_config_exists,
    mock_process_op_config_upgrade,
    loop,
):
    """Test it works."""
    with patch("openpeerpower.components.browser.setup") as browser_setup, patch(
        "openpeerpower.config_entries.ConfigEntries.async_domains",
        return_value=["browser"],
    ):
        opp = await bootstrap.async_setup_opp(
            runner.RuntimeConfig(
                config_dir=get_test_config_dir(),
                verbose=False,
                log_rotate_days=10,
                log_file="",
                log_no_color=False,
                skip_pip=True,
                safe_mode=True,
            ),
        )

    assert "safe_mode" in.opp.config.components
    assert len(mock_mount_local_lib_path.mock_calls) == 0

    # Validate we didn't try to set up config entry.
    assert "browser" not in.opp.config.components
    assert len(browser_setup.mock_calls) == 0


async def test_setup_opp_invalid_core_config(
    mock_enable_logging,
    mock_is_virtual_env,
    mock_mount_local_lib_path,
    mock_ensure_config_exists,
    mock_process_op_config_upgrade,
    loop,
):
    """Test it works."""
    with patch(
        "openpeerpower.config.async_opp_config_yaml",
        return_value={"openpeerpower": {"non-existing": 1}},
    ):
        opp = await bootstrap.async_setup_opp(
            runner.RuntimeConfig(
                config_dir=get_test_config_dir(),
                verbose=False,
                log_rotate_days=10,
                log_file="",
                log_no_color=False,
                skip_pip=True,
                safe_mode=False,
            ),
        )

    assert "safe_mode" in.opp.config.components


async def test_setup_safe_mode_if_no_frontend(
    mock_enable_logging,
    mock_is_virtual_env,
    mock_mount_local_lib_path,
    mock_ensure_config_exists,
    mock_process_op_config_upgrade,
    loop,
):
    """Test we setup safe mode if frontend didn't load."""
    verbose = Mock()
    log_rotate_days = Mock()
    log_file = Mock()
    log_no_color = Mock()

    with patch(
        "openpeerpower.config.async.opp_config_yaml",
        return_value={
            "openpeerpower": {
                "internal_url": "http://192.168.1.100:8123",
                "external_url": "https://abcdef.ui.nabu.casa",
            },
            "map": {},
            "person": {"invalid": True},
        },
    ):
        opp = await bootstrap.async_setup_opp(
            runner.RuntimeConfig(
                config_dir=get_test_config_dir(),
                verbose=verbose,
                log_rotate_days=log_rotate_days,
                log_file=log_file,
                log_no_color=log_no_color,
                skip_pip=True,
                safe_mode=False,
            ),
        )

    assert "safe_mode" in.opp.config.components
    assert.opp.config.config_dir == get_test_config_dir()
    assert.opp.config.skip_pip
    assert.opp.config.internal_url == "http://192.168.1.100:8123"
    assert.opp.config.external_url == "https://abcdef.ui.nabu.casa"
