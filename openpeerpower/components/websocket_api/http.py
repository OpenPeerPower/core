"""View to accept incoming websocket connection."""
import asyncio
from contextlib import suppress
import logging
from typing import Optional

from aiohttp import WSMsgType, web
import async_timeout

from openpeerpower.components.http import OpenPeerPowerView
from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import callback
from openpeerpower.helpers.event import async_call_later

from .auth import AuthPhase, auth_required_message
from .const import (
    CANCELLATION_ERRORS,
    DATA_CONNECTIONS,
    MAX_PENDING_MSG,
    PENDING_MSG_PEAK,
    PENDING_MSG_PEAK_TIME,
    SIGNAL_WEBSOCKET_CONNECTED,
    SIGNAL_WEBSOCKET_DISCONNECTED,
    URL,
)
from .error import Disconnect
from .messages import message_to_json

# mypy: allow-untyped-calls, allow-untyped-defs, no-check-untyped-defs
_WS_LOGGER = logging.getLogger(f"{__name__}.connection")


class WebsocketAPIView(OpenPeerPowerView):
    """View to serve a websockets endpoint."""

    name = "websocketapi"
    url = URL
    requires_auth = False

    async def get(self, request: web.Request) -> web.WebSocketResponse:
        """Handle an incoming websocket connection."""
        return await WebSocketHandler(request.app["opp"], request).async_handle()


class WebSocketAdapter(logging.LoggerAdapter):
    """Add connection id to websocket messages."""

    def process(self, msg, kwargs):
        """Add connid to websocket log messages."""
        return f'[{self.extra["connid"]}] {msg}', kwargs


class WebSocketHandler:
    """Handle an active websocket client connection."""

    def __init__(self, opp, request):
        """Initialize an active connection."""
        self.opp = opp
        self.request = request
        self.wsock: Optional[web.WebSocketResponse] = None
        self._to_write: asyncio.Queue = asyncio.Queue(maxsize=MAX_PENDING_MSG)
        self._handle_task = None
        self._writer_task = None
        self._logger = WebSocketAdapter(_WS_LOGGER, {"connid": id(self)})
        self._peak_checker_unsub = None

    async def _writer(self):
        """Write outgoing messages."""
        # Exceptions if Socket disconnected or cancelled by connection handler
        with suppress(RuntimeError, ConnectionResetError, *CANCELLATION_ERRORS):
            while not self.wsock.closed:
                message = await self._to_write.get()
                if message is None:
                    break

                self._logger.debug("Sending %s", message)

                if not isinstance(message, str):
                    message = message_to_json(message)

                await self.wsock.send_str(message)

        # Clean up the peaker checker when we shut down the writer
        if self._peak_checker_unsub:
            self._peak_checker_unsub()
            self._peak_checker_unsub = None

    @callback
    def _send_message(self, message):
        """Send a message to the client.

        Closes connection if the client is not reading the messages.

        Async friendly.
        """
        try:
            self._to_write.put_nowait(message)
        except asyncio.QueueFull:
            self._logger.error(
                "Client exceeded max pending messages [2]: %s", MAX_PENDING_MSG
            )

            self._cancel()

        if self._to_write.qsize() < PENDING_MSG_PEAK:
            if self._peak_checker_unsub:
                self._peak_checker_unsub()
                self._peak_checker_unsub = None
            return

        if self._peak_checker_unsub is None:
            self._peak_checker_unsub = async_call_later(
                self.opp, PENDING_MSG_PEAK_TIME, self._check_write_peak
            )

    @callback
    def _check_write_peak(self, _):
        """Check that we are no longer above the write peak."""
        self._peak_checker_unsub = None

        if self._to_write.qsize() < PENDING_MSG_PEAK:
            return

        self._logger.error(
            "Client unable to keep up with pending messages. Stayed over %s for %s seconds",
            PENDING_MSG_PEAK,
            PENDING_MSG_PEAK_TIME,
        )
        self._cancel()

    @callback
    def _cancel(self):
        """Cancel the connection."""
        self._handle_task.cancel()
        self._writer_task.cancel()

    async def async_handle(self) -> web.WebSocketResponse:
        """Handle a websocket response."""
        request = self.request
        wsock = self.wsock = web.WebSocketResponse(heartbeat=55)
        await wsock.prepare(request)
        self._logger.debug("Connected from %s", request.remote)
        self._handle_task = asyncio.current_task()

        @callback
        def handle_opp_stop(event):
            """Cancel this connection."""
            self._cancel()

        unsub_stop = self.opp.bus.async_listen(
            EVENT_OPENPEERPOWER_STOP, handle_opp_stop
        )

        # As the webserver is now started before the start
        # event we do not want to block for websocket responses
        self._writer_task = asyncio.create_task(self._writer())

        auth = AuthPhase(self._logger, self.opp, self._send_message, request)
        connection = None
        disconnect_warn = None

        try:
            self._send_message(auth_required_message())

            # Auth Phase
            try:
                with async_timeout.timeout(10):
                    msg = await wsock.receive()
            except asyncio.TimeoutError as err:
                disconnect_warn = "Did not receive auth message within 10 seconds"
                raise Disconnect from err

            if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING):
                raise Disconnect

            if msg.type != WSMsgType.TEXT:
                disconnect_warn = "Received non-Text message."
                raise Disconnect

            try:
                msg_data = msg.json()
            except ValueError as err:
                disconnect_warn = "Received invalid JSON."
                raise Disconnect from err

            self._logger.debug("Received %s", msg_data)
            connection = await auth.async_handle(msg_data)
            self.opp.data[DATA_CONNECTIONS] = self.opp.data.get(DATA_CONNECTIONS, 0) + 1
            self.opp.helpers.dispatcher.async_dispatcher_send(
                SIGNAL_WEBSOCKET_CONNECTED
            )

            # Command phase
            while not wsock.closed:
                msg = await wsock.receive()

                if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING):
                    break

                if msg.type != WSMsgType.TEXT:
                    disconnect_warn = "Received non-Text message."
                    break

                try:
                    msg_data = msg.json()
                except ValueError:
                    disconnect_warn = "Received invalid JSON."
                    break

                self._logger.debug("Received %s", msg_data)
                connection.async_handle(msg_data)

        except asyncio.CancelledError:
            self._logger.info("Connection closed by client")

        except Disconnect:
            pass

        except Exception:  # pylint: disable=broad-except
            self._logger.exception("Unexpected error inside websocket API")

        finally:
            unsub_stop()

            if connection is not None:
                connection.async_close()

            try:
                self._to_write.put_nowait(None)
                # Make sure all error messages are written before closing
                await self._writer_task
                await wsock.close()
            except asyncio.QueueFull:  # can be raised by put_nowait
                self._writer_task.cancel()

            finally:
                if disconnect_warn is None:
                    self._logger.debug("Disconnected")
                else:
                    self._logger.warning("Disconnected: %s", disconnect_warn)

                if connection is not None:
                    self.opp.data[DATA_CONNECTIONS] -= 1
                self.opp.helpers.dispatcher.async_dispatcher_send(
                    SIGNAL_WEBSOCKET_DISCONNECTED
                )

        return wsock
