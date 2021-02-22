"""Configure pytest for Dyson tests."""
from unittest.mock import patch

from libpurecool.dyson_device import DysonDevice
import pytest

from openpeerpower.components.dyson import DOMAIN
from openpeerpower.core import OpenPeerPower

from .common import BASE_PATH, CONFIG

from tests.common import async_setup_component


@pytest.fixture()
async def device.opp: OpenPeerPower, request) -> DysonDevice:
    """Fixture to provide Dyson 360 Eye device."""
    platform = request.module.PLATFORM_DOMAIN
    get_device = request.module.async_get_device
    if hasattr(request, "param"):
        if isinstance(request.param, list):
            device = get_device(*request.param)
        else:
            device = get_device(request.param)
    else:
        device = get_device()
    with patch(f"{BASE_PATH}.DysonAccount.login", return_value=True), patch(
        f"{BASE_PATH}.DysonAccount.devices", return_value=[device]
    ), patch(f"{BASE_PATH}.DYSON_PLATFORMS", [platform]):
        # DYSON_PLATFORMS is patched so that only the platform being tested is set up
        await async_setup_component(
           .opp,
            DOMAIN,
            CONFIG,
        )
        await opp.async_block_till_done()

    return device
