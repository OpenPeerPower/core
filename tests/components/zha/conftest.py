"""Test configuration for the ZHA component."""
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
import zigpy
from zigpy.application import ControllerApplication
import zigpy.config
import zigpy.group
import zigpy.types

from openpeerpower.components.zha import DOMAIN
import openpeerpower.components.zha.core.const as zha_const
import openpeerpower.components.zha.core.device as zha_core_device
from openpeerpower.setup import async_setup_component

from .common import FakeDevice, FakeEndpoint, get_zha_gateway

from tests.common import MockConfigEntry
from tests.components.light.conftest import mock_light_profiles  # noqa

FIXTURE_GRP_ID = 0x1001
FIXTURE_GRP_NAME = "fixture group"


@pytest.fixture
def zigpy_app_controller():
    """Zigpy ApplicationController fixture."""
    app = MagicMock(spec_set=ControllerApplication)
    app.startup = AsyncMock()
    app.shutdown = AsyncMock()
    groups = zigpy.group.Groups(app)
    groups.add_group(FIXTURE_GRP_ID, FIXTURE_GRP_NAME, suppress_event=True)
    app.configure_mock(groups=groups)
    type(app).ieee = PropertyMock()
    app.ieee.return_value = zigpy.types.EUI64.convert("00:15:8d:00:02:32:4f:32")
    type(app).nwk = PropertyMock(return_value=zigpy.types.NWK(0x0000))
    type(app).devices = PropertyMock(return_value={})
    return app


@pytest.fixture(name="config_entry")
async def config_entry_fixture.opp):
    """Fixture representing a config entry."""
    entry = MockConfigEntry(
        version=2,
        domain=zha_const.DOMAIN,
        data={
            zigpy.config.CONF_DEVICE: {zigpy.config.CONF_DEVICE_PATH: "/dev/ttyUSB0"},
            zha_const.CONF_RADIO_TYPE: "ezsp",
        },
    )
    entry.add_to.opp.opp)
    return entry


@pytest.fixture
def setup_zha.opp, config_entry, zigpy_app_controller):
    """Set up ZHA component."""
    zha_config = {zha_const.CONF_ENABLE_QUIRKS: False}

    p1 = patch(
        "bellows.zigbee.application.ControllerApplication.new",
        return_value=zigpy_app_controller,
    )

    async def _setup(config=None):
        config = config or {}
        with p1:
            status = await async_setup_component(
               .opp, zha_const.DOMAIN, {zha_const.DOMAIN: {**zha_config, **config}}
            )
            assert status is True
            await.opp.async_block_till_done()

    return _setup


@pytest.fixture
def channel():
    """Channel mock factory fixture."""

    def channel(name: str, cluster_id: int, endpoint_id: int = 1):
        ch = MagicMock()
        ch.name = name
        ch.generic_id = f"channel_0x{cluster_id:04x}"
        ch.id = f"{endpoint_id}:0x{cluster_id:04x}"
        ch.async_configure = AsyncMock()
        ch.async_initialize = AsyncMock()
        return ch

    return channel


@pytest.fixture
def zigpy_device_mock(zigpy_app_controller):
    """Make a fake device using the specified cluster classes."""

    def _mock_dev(
        endpoints,
        ieee="00:0d:6f:00:0a:90:69:e7",
        manufacturer="FakeManufacturer",
        model="FakeModel",
        node_descriptor=b"\x02@\x807\x10\x7fd\x00\x00*d\x00\x00",
        nwk=0xB79C,
        patch_cluster=True,
    ):
        """Make a fake device using the specified cluster classes."""
        device = FakeDevice(
            zigpy_app_controller, ieee, manufacturer, model, node_descriptor, nwk=nwk
        )
        for epid, ep in endpoints.items():
            endpoint = FakeEndpoint(manufacturer, model, epid)
            endpoint.device = device
            device.endpoints[epid] = endpoint
            endpoint.device_type = ep["device_type"]
            profile_id = ep.get("profile_id")
            if profile_id:
                endpoint.profile_id = profile_id

            for cluster_id in ep.get("in_clusters", []):
                endpoint.add_input_cluster(cluster_id, _patch_cluster=patch_cluster)

            for cluster_id in ep.get("out_clusters", []):
                endpoint.add_output_cluster(cluster_id, _patch_cluster=patch_cluster)

        return device

    return _mock_dev


@pytest.fixture
def zha_device_joined.opp, setup_zha):
    """Return a newly joined ZHA device."""

    async def _zha_device(zigpy_dev):
        await setup_zha()
        zha_gateway = get_zha_gateway.opp)
        await zha_gateway.async_device_initialized(zigpy_dev)
        await.opp.async_block_till_done()
        return zha_gateway.get_device(zigpy_dev.ieee)

    return _zha_device


@pytest.fixture
def zha_device_restored.opp, zigpy_app_controller, setup_zha, opp_storage):
    """Return a restored ZHA device."""

    async def _zha_device(zigpy_dev, last_seen=None):
        zigpy_app_controller.devices[zigpy_dev.ieee] = zigpy_dev

        if last_seen is not None:
           .opp_storage[f"{DOMAIN}.storage"] = {
                "key": f"{DOMAIN}.storage",
                "version": 1,
                "data": {
                    "devices": [
                        {
                            "ieee": str(zigpy_dev.ieee),
                            "last_seen": last_seen,
                            "name": f"{zigpy_dev.manufacturer} {zigpy_dev.model}",
                        }
                    ],
                },
            }

        await setup_zha()
        zha_gateway = opp.data[zha_const.DATA_ZHA][zha_const.DATA_ZHA_GATEWAY]
        return zha_gateway.get_device(zigpy_dev.ieee)

    return _zha_device


@pytest.fixture(params=["zha_device_joined", "zha_device_restored"])
def zha_device_joined_restored(request):
    """Join or restore ZHA device."""
    named_method = request.getfixturevalue(request.param)
    named_method.name = request.param
    return named_method


@pytest.fixture
def zha_device_mock.opp, zigpy_device_mock):
    """Return a zha Device factory."""

    def _zha_device(
        endpoints=None,
        ieee="00:11:22:33:44:55:66:77",
        manufacturer="mock manufacturer",
        model="mock model",
        node_desc=b"\x02@\x807\x10\x7fd\x00\x00*d\x00\x00",
        patch_cluster=True,
    ):
        if endpoints is None:
            endpoints = {
                1: {
                    "in_clusters": [0, 1, 8, 768],
                    "out_clusters": [0x19],
                    "device_type": 0x0105,
                },
                2: {
                    "in_clusters": [0],
                    "out_clusters": [6, 8, 0x19, 768],
                    "device_type": 0x0810,
                },
            }
        zigpy_device = zigpy_device_mock(
            endpoints, ieee, manufacturer, model, node_desc, patch_cluster=patch_cluster
        )
        zha_device = zha_core_device.ZHADevice.opp, zigpy_device, MagicMock())
        return zha_device

    return _zha_device


@pytest.fixture
def.opp_disable_services.opp):
    """Mock service register."""
    with patch.object.opp.services, "async_register"), patch.object(
       .opp.services, "has_service", return_value=True
    ):
        yield.opp
