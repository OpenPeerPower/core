"""Support for RESTful API."""
import logging

import httpx

from openpeerpower.helpers.httpx_client import get_async_client

DEFAULT_TIMEOUT = 10

_LOGGER = logging.getLogger(__name__)


class RestData:
    """Class for handling the data retrieval."""

    def __init__(
        self,
        opp,
        method,
        resource,
        auth,
        headers,
        params,
        data,
        verify_ssl,
        timeout=DEFAULT_TIMEOUT,
    ):
        """Initialize the data object."""
        self._opp = opp
        self._method = method
        self._resource = resource
        self._auth = auth
        self._headers = headers
        self._params = params
        self._request_data = data
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._async_client = None
        self.data = None
        self.headers = None

    def set_url(self, url):
        """Set url."""
        self._resource = url

    async def async_update(self):
        """Get the latest data from REST service with provided method."""
        if not self._async_client:
            self._async_client = get_async_client(
                self._opp, verify_ssl=self._verify_ssl
            )

        _LOGGER.debug("Updating from %s", self._resource)
        try:
            response = await self._async_client.request(
                self._method,
                self._resource,
                headers=self._headers,
                params=self._params,
                auth=self._auth,
                data=self._request_data,
                timeout=self._timeout,
            )
            self.data = response.text
            self.headers = response.headers
        except httpx.RequestError as ex:
            _LOGGER.error("Error fetching data: %s failed with %s", self._resource, ex)
            self.data = None
            self.headers = None
