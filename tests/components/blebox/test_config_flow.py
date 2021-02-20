"""Test Open Peer Power config flow for BleBox devices."""

from unittest.mock import DEFAULT, AsyncMock, PropertyMock, patch

import blebox_uniapi
import pytest

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.blebox import config_flow
from openpeerpowerr.setup import async_setup_component

from .conftest import mock_config, mock_only_feature, setup_product_mock


def create_valid_feature_mock(path="openpeerpower.components.blebox.Products"):
    """Return a valid, complete BleBox feature mock."""
    feature = mock_only_feature(
        blebox_uniapi.cover.Cover,
        unique_id="BleBox-gateBox-1afe34db9437-0.position",
        full_name="gateBox-0.position",
        device_class="gate",
        state=0,
        async_update=AsyncMock(),
        current=None,
    )

    product = setup_product_mock("covers", [feature], path)

    type(product).name = PropertyMock(return_value="My gate controller")
    type(product).model = PropertyMock(return_value="gateController")
    type(product).type = PropertyMock(return_value="gateBox")
    type(product).brand = PropertyMock(return_value="BleBox")
    type(product).firmware_version = PropertyMock(return_value="1.23")
    type(product).unique_id = PropertyMock(return_value="abcd0123ef5678")

    return feature


@pytest.fixture(name="valid_feature_mock")
def valid_feature_mock_fixture():
    """Return a valid, complete BleBox feature mock."""
    return create_valid_feature_mock()


@pytest.fixture(name="flow_feature_mock")
def flow_feature_mock_fixture():
    """Return a mocked user flow feature."""
    return create_valid_feature_mock(
        "openpeerpower.components.blebox.config_flow.Products"
    )


async def test_flow_works.opp, valid_feature_mock, flow_feature_mock):
    """Test that config flow works."""

    result = await.opp.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    result = await.opp.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "My gate controller"
    assert result["data"] == {
        config_flow.CONF_HOST: "172.2.3.4",
        config_flow.CONF_PORT: 80,
    }


@pytest.fixture(name="product_class_mock")
def product_class_mock_fixture():
    """Return a mocked feature."""
    path = "openpeerpower.components.blebox.config_flow.Products"
    patcher = patch(path, DEFAULT, blebox_uniapi.products.Products, True, True)
    yield patcher


async def test_flow_with_connection_failure.opp, product_class_mock):
    """Test that config flow works."""
    with product_class_mock as products_class:
        products_class.async_from_host = AsyncMock(
            side_effect=blebox_uniapi.error.ConnectionError
        )

        result = await.opp.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_with_api_failure.opp, product_class_mock):
    """Test that config flow works."""
    with product_class_mock as products_class:
        products_class.async_from_host = AsyncMock(
            side_effect=blebox_uniapi.error.Error
        )

        result = await.opp.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_with_unknown_failure.opp, product_class_mock):
    """Test that config flow works."""
    with product_class_mock as products_class:
        products_class.async_from_host = AsyncMock(side_effect=RuntimeError)
        result = await.opp.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        assert result["errors"] == {"base": "unknown"}


async def test_flow_with_unsupported_version.opp, product_class_mock):
    """Test that config flow works."""
    with product_class_mock as products_class:
        products_class.async_from_host = AsyncMock(
            side_effect=blebox_uniapi.error.UnsupportedBoxVersion
        )

        result = await.opp.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        assert result["errors"] == {"base": "unsupported_version"}


async def test_async_setup.opp):
    """Test async_setup (for coverage)."""
    assert await async_setup_component.opp, "blebox", {"host": "172.2.3.4"})
    await.opp.async_block_till_done()


async def test_already_configured.opp, valid_feature_mock):
    """Test that same device cannot be added twice."""

    config = mock_config("172.2.3.4")
    config.add_to_opp.opp)

    await.opp.config_entries.async_setup(config.entry_id)
    await.opp.async_block_till_done()

    result = await.opp.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "address_already_configured"


async def test_async_setup_entry.opp, valid_feature_mock):
    """Test async_setup_entry (for coverage)."""

    config = mock_config()
    config.add_to_opp.opp)

    assert await.opp.config_entries.async_setup(config.entry_id)
    await.opp.async_block_till_done()

    assert.opp.config_entries.async_entries() == [config]
    assert config.state == config_entries.ENTRY_STATE_LOADED


async def test_async_remove_entry.opp, valid_feature_mock):
    """Test async_setup_entry (for coverage)."""

    config = mock_config()
    config.add_to_opp.opp)

    assert await.opp.config_entries.async_setup(config.entry_id)
    await.opp.async_block_till_done()

    assert await.opp.config_entries.async_remove(config.entry_id)
    await.opp.async_block_till_done()

    assert.opp.config_entries.async_entries() == []
    assert config.state == config_entries.ENTRY_STATE_NOT_LOADED
