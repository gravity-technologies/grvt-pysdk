# ruff: noqa: D200
# ruff: noqa: D204
# ruff: noqa: D205
# ruff: noqa: D404
# ruff: noqa: W291
# ruff: noqa: D400
# ruff: noqa: E501

import asyncio
import json
import logging
import traceback
from asyncio.events import AbstractEventLoop
from collections.abc import Callable

import websockets

# import requests
# from env import ENDPOINTS
from .grvt_ccxt_env import (
    GRVT_WS_STREAMS,
    GrvtEndpointType,
    GrvtEnv,
    get_grvt_ws_endpoint,
)
from .grvt_ccxt_pro import GrvtCcxtPro

WS_READ_TIMEOUT = 5


class GrvtCcxtWS(GrvtCcxtPro):
    """
    GrvtCcxtPro class to interact with Grvt Rest API and WebSockets in asynchronous mode.

    Args:
        env: GrvtCcxtPro (DEV, TESTNET, PROD)
        parameters: dict with trading_account_id, private_key, api_key etc

    Examples:
        >>> from grvt_api_pro import GrvtCcxtPro
        >>> from grvt_env import GrvtEnv
        >>> grvt = GrvtCcxtPro(env=GrvtEnv.TESTNET)
        >>> await grvt.fetch_markets()
    """

    def __init__(
        self,
        env: GrvtEnv,
        loop: AbstractEventLoop,
        logger: logging.Logger | None = None,
        parameters: dict = {},
    ):
        """Initialize the GrvtCcxt instance."""
        super().__init__(env, logger, parameters)
        self._loop = loop
        self._clsname: str = type(self).__name__
        self.api_ws_version = parameters.get("api_ws_version", "v0")
        self.ws: dict[GrvtEndpointType, websockets.WebSocketClientProtocol | None] = {}
        self.callbacks: dict[GrvtEndpointType, dict[tuple[str, str], Callable]] = {}
        self.subscribed_streams: dict[GrvtEndpointType, dict] = {}
        self.api_url: dict[GrvtEndpointType, str] = {}
        self.is_connecting: dict[GrvtEndpointType, bool] = {}
        self._last_message: dict[str, dict] = {}
        self._request_id = 0
        # Initialize dictionaries for each endpoint type
        for grvt_endpoint_type in [
            GrvtEndpointType.MARKET_DATA,
            GrvtEndpointType.TRADE_DATA,
        ]:
            self.api_url[grvt_endpoint_type] = get_grvt_ws_endpoint(
                self.env.value, grvt_endpoint_type
            )
            self.callbacks[grvt_endpoint_type] = {}
            self.subscribed_streams[grvt_endpoint_type] = {}
            self.ws[grvt_endpoint_type] = None
            self.is_connecting[grvt_endpoint_type] = False
            self._loop.create_task(self._read_messages(grvt_endpoint_type))
        self.logger.info(f"{self._clsname} initialized {self.api_url=}")
        self.logger.info(f"{self._clsname} initialized {self.ws=}")

    async def __aexit__(self):
        for grvt_endpoint_type in [
            GrvtEndpointType.MARKET_DATA,
            GrvtEndpointType.TRADE_DATA,
        ]:
            await self._close_connection(grvt_endpoint_type)

    async def connect(self, grvt_endpoint_type: GrvtEndpointType) -> bool:
        FN = f"{self._clsname} connect {grvt_endpoint_type.value}"
        try:
            self.is_connecting[grvt_endpoint_type] = True
            self.subscribed_streams[grvt_endpoint_type] = {}
            extra_headers = {}
            if grvt_endpoint_type == GrvtEndpointType.TRADE_DATA:
                if self._cookie:
                    extra_headers = {"Cookie": f"gravity={self._cookie['gravity']}"}
                    self.ws[grvt_endpoint_type] = await websockets.connect(
                        uri=self.api_url[grvt_endpoint_type],
                        extra_headers=extra_headers,
                        logger=self.logger,
                    )
                    self.logger.info(
                        f"{FN} Connected to {self.api_url[grvt_endpoint_type]} {extra_headers=}"
                    )
                else:
                    self.logger.info(f"{FN} Waiting for cookie.")
            elif grvt_endpoint_type == GrvtEndpointType.MARKET_DATA:
                self.ws[grvt_endpoint_type] = await websockets.connect(
                    uri=self.api_url[grvt_endpoint_type],
                    logger=self.logger,
                )
                self.logger.info(f"{FN} Connected to {self.api_url[grvt_endpoint_type]}")
        except (
            websockets.exceptions.ConnectionClosedOK,
            websockets.exceptions.ConnectionClosed,
        ) as e:
            self.logger.info(f"{FN} connection already closed:{e}")
            self.ws[grvt_endpoint_type] = None
        except Exception as e:
            self.logger.warning(f"{FN} error:{e} traceback:{traceback.format_exc()}")
            self.ws[grvt_endpoint_type] = None
        finally:
            self.is_connecting[grvt_endpoint_type] = False
        return bool(
            self.ws[grvt_endpoint_type] is not None and self.ws[grvt_endpoint_type].open
        )

    async def _close_connection(self, grvt_endpoint_type: GrvtEndpointType):
        try:
            if self.ws[grvt_endpoint_type]:
                self.logger.info(f"{self._clsname} Closing connection...")
                await self.ws[grvt_endpoint_type].close()
                self.subscribed_streams[grvt_endpoint_type] = {}
                self.logger.info(f"{self._clsname} Connection closed")
            else:
                self.logger.info(f"{self._clsname} No connection to close")
        except Exception:
            self.logger.exception(
                f"{self._clsname} Error when closing connection {traceback.format_exc()}"
            )

    async def _reconnect(self, grvt_endpoint_type: GrvtEndpointType):
        try:
            self.logger.info(
                f"{self._clsname} {grvt_endpoint_type=} reconnect websocket starts"
            )
            if not self.is_connecting[grvt_endpoint_type]:
                await self._close_connection(grvt_endpoint_type)
                await self.connect(grvt_endpoint_type)
                await self._resubscribe(grvt_endpoint_type)
            else:
                self.logger.info(
                    f"{self._clsname} {grvt_endpoint_type=} self.is_connecting = True. Do nothing."
                )
        except Exception:
            self.logger.exception(
                f"{self._clsname} {grvt_endpoint_type=} _reconnect "
                f"failed {traceback.format_exc()}"
            )

    async def _resubscribe(self, grvt_endpoint_type: GrvtEndpointType):
        if self.ws.get(grvt_endpoint_type) and self.ws[grvt_endpoint_type].open:
            for stream, feed in self.callbacks[grvt_endpoint_type]:
                await self._subscribe_to_stream(grvt_endpoint_type, stream, feed)
        else:
            self.logger.warning(f"{self._clsname} _resubscribe - No connection.")

    # **************** PUBLIC API CALLS
    def _check_susbcribed_stream(
        self, grvt_endpoint_type: GrvtEndpointType, message: dict
    ) -> None:
        stream_subscribed: str = message.get("stream")
        if stream_subscribed:
            if not self.subscribed_streams[grvt_endpoint_type].get(stream_subscribed):
                self.logger.info(
                    f"{self._clsname} subscribed to stream:{stream_subscribed}"
                )
                self.subscribed_streams[grvt_endpoint_type][stream_subscribed] = True

    async def _read_messages(self, grvt_endpoint_type: GrvtEndpointType):
        FN = f"{self._clsname} _read_messages {grvt_endpoint_type.value}"
        while True:
            if self.ws.get(grvt_endpoint_type) and self.ws[grvt_endpoint_type].open:
                try:
                    self.logger.info(f"{FN} waiting for message")
                    response = await asyncio.wait_for(
                        self.ws[grvt_endpoint_type].recv(), timeout=WS_READ_TIMEOUT
                    )
                    message = json.loads(response)
                    self.logger.debug(f"{FN} received {message=}")
                    self._check_susbcribed_stream(grvt_endpoint_type, message)
                    if "feed" not in message:
                        self.logger.debug(f"{FN} Non-actionable message:{message}")
                    else:
                        stream_subscribed: str | None = message.get("stream")
                        if stream_subscribed is None:
                            self.logger.warning(f"{FN} missing stream in {message=}")
                        # feed_subscribed: Optional[str] = message.get("feed")
                        # if feed_subscribed is None:
                        #     self.logger.warning(f"{FN} missing feed in {message=}")
                        if stream_subscribed:
                            call_count = 0
                            for (stream, feed), callback in self.callbacks[
                                grvt_endpoint_type
                            ].items():
                                if stream_subscribed.endswith(stream):
                                    self.logger.info(
                                        f"{FN} Stream:{stream_subscribed} {feed=}"
                                        f" callback:{callback.__name__} "
                                        f" message:{message}"
                                    )
                                    await callback(message)
                                    self._last_message[stream_subscribed] = message
                                    call_count += 1
                            if call_count == 0:
                                self.logger.info(
                                    f"{FN} No callback found for {stream_subscribed=} {message=}"
                                )
                            else:
                                self.logger.info(f"{FN} callback count:{call_count}")
                    # yield message
                except (
                    websockets.exceptions.ConnectionClosedError,
                    websockets.exceptions.ConnectionClosedOK,
                ):
                    self.logger.exception(
                        f"{FN} connection closed {traceback.format_exc()}"
                    )
                    await self._reconnect(grvt_endpoint_type)
                except TimeoutError:
                    self.logger.info(f"{FN} Timeout {WS_READ_TIMEOUT} secs")
                    pass
                except Exception:
                    self.logger.exception(
                        f"{FN} connection failed {traceback.format_exc()}"
                    )
                    await asyncio.sleep(1)
            else:
                await self._reconnect(grvt_endpoint_type)
                await asyncio.sleep(1)

    async def _send(self, end_point_type: GrvtEndpointType, message: str):
        try:
            if self.ws[end_point_type] and self.ws[end_point_type].open:
                self.logger.info(f"{self._clsname} _send() {end_point_type=} {message=}")
                await self.ws[end_point_type].send(message)
        except websockets.exceptions.ConnectionClosedError as e:
            self.logger.info(f"{self._clsname} _send() Restarted connection {e}")
            await self._reconnect(end_point_type)
            if self.ws[end_point_type]:
                await self.ws[end_point_type].send(message)
        except Exception:
            self.logger.exception(f"{self._clsname} send failed {traceback.format_exc()}")
            await self._reconnect(end_point_type)

    def _construct_feed(self, stream: str, params: dict | None) -> str:
        feed: str = ""
        # ******** Market Data ********
        if stream.endswith(("mini.s", "mini.d", "ticker.s", "ticker.d")):
            feed = f"{params.get('instrument', '')}@{params.get('rate', '500')}"
        if stream.endswith("book.s"):
            feed = (
                f"{params.get('instrument', '')}@{params.get('rate', '500')}-"
                f"{params.get('depth', '10')}"
            )
        if stream.endswith("book.d"):
            feed = f"{params.get('instrument', '')}@{params.get('rate', '500')}"
        if stream.endswith("trade"):
            feed = f"{params.get('instrument', '')}@{params.get('limit', '100')}"
        if stream.endswith("candle"):
            feed = (
                f"{params.get('instrument', '')}@{params.get('interval', 'CI_1_M')}-"
                f"{params.get('type', 'TRADE')}"
            )
        # ******** Trade Data ********
        if stream.endswith(("order", "state", "position", "fill")):
            if not params:
                feed = f"{params.get('sub_account_id', '')}"
            elif params.get("instrument"):
                feed = f"{params.get('sub_account_id', '')}-{params.get('instrument', '')}"  # @a"
            else:
                feed = (
                    f"{params.get('sub_account_id', '')}-{params.get('kind', '')}-"
                    f"{params.get('base', '')}-{params.get('quote', '')}"
                )
        # Deposit, Transfer, Withdrawal
        if stream.endswith(("deposit", "transfer", "withdrawal")):
            feed = ""
            # f"{params.get('sub_account_id', '')}-{params.get('main_account_id', '')}"

        return feed

    async def subscribe(
        self,
        stream: str,
        callback: Callable,
        params: dict | None = None,
    ) -> None:
        """
        Subscribe to a stream with optional parameters.
        Call the callback function when a message is received.
        callback function should have the following signature:
        (dict) -> None.
        """
        FN = f"{self._clsname} subscribe {stream=}"
        end_point_type = GRVT_WS_STREAMS.get(stream)
        if end_point_type is None:
            self.logger.error(f"{FN} unknown {stream=}")
            return
        feed = self._construct_feed(stream, params)
        self.callbacks[end_point_type][(stream, feed)] = callback
        self.logger.info(
            f"{FN} {end_point_type=} {stream=}/{params=}/{feed=} callback:{callback}"
        )
        await self._subscribe_to_stream(end_point_type, stream, feed)

    async def _subscribe_to_stream(
        self,
        end_point_type: GrvtEndpointType,
        stream: str,
        feed: str,
    ) -> None:
        versioned_stream = (
            stream if self.api_ws_version == "v0" else f"{self.api_ws_version}.{stream}"
        )
        self._request_id += 1
        subscribe_json = json.dumps(
            {
                "request_id": self._request_id,
                "stream": versioned_stream,
                "feed": [feed],
                "method": "subscribe",
                "is_full": True,
            }
        )
        self.logger.info(
            f"{self._clsname} _subscribe_to_stream {end_point_type=} "
            f"{stream=} version={self.api_ws_version} {versioned_stream=} {feed=}"
            f" {subscribe_json=}"
        )
        await self._send(end_point_type, subscribe_json)
        if stream not in self._last_message:
            self._last_message[versioned_stream] = {}
