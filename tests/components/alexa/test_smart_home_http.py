"""Test Smart Home HTTP endpoints."""
import json

from openpeerpower.components.alexa import DOMAIN, smart_home_http
from openpeerpower.const import CONTENT_TYPE_JSON, HTTP_NOT_FOUND
from openpeerpower.setup import async_setup_component

from . import get_new_request


async def do_http_discovery(config, opp, opp_client):
    """Submit a request to the Smart Home HTTP API."""
    await async_setup_component.opp, DOMAIN, config)
    http_client = await opp_client()

    request = get_new_request("Alexa.Discovery", "Discover")
    response = await http_client.post(
        smart_home_http.SMART_HOME_HTTP_ENDPOINT,
        data=json.dumps(request),
        headers={"content-type": CONTENT_TYPE_JSON},
    )
    return response


async def test_http_api.opp, opp_client):
    """With `smart_home:` HTTP API is exposed."""
    config = {"alexa": {"smart_home": None}}

    response = await do_http_discovery(config, opp, opp_client)
    response_data = await response.json()

    # Here we're testing just the HTTP view glue -- details of discovery are
    # covered in other tests.
    assert response_data["event"]["header"]["name"] == "Discover.Response"


async def test_http_api_disabled.opp, opp_client):
    """Without `smart_home:`, the HTTP API is disabled."""
    config = {"alexa": {}}
    response = await do_http_discovery(config, opp, opp_client)

    assert response.status == HTTP_NOT_FOUND
