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
from enum import Enum

import websockets
from dacite import Config, from_dict

from . import grvt_exceptions as grvt_exceptions
from . import grvt_raw_types as grvt_types

# import requests
# from env import ENDPOINTS
from .grvt_ccxt_env import (
    GRVT_WS_STREAMS,
    GrvtEndpointType,
    GrvtEnv,
    get_grvt_ws_endpoint,
)
from .grvt_ccxt_pro import GrvtCcxtPro
from .grvt_raw_base import GrvtError

WS_READ_TIMEOUT = 5

#### THESE ARE TO BE MOVED OUT AND AUTO GENERATED ####

# TODO - auto generate full set

# GrvtStreamType defines the available streams to subscribe to
# This should be auto generated from the API documentation
class GrvtStreamType(str, Enum):
    MINI_TICKER_SNAPHOT = "mini.s"
    MINI_TICKER_DELTA = "mini.d"

class GrvtParams:
    def get_feed(self) ->str:
        pass

class GrvtTickerInterval(int, Enum):
    INTERVAL_500 = 500

### One of these should be generated for each type of data that can be subscribed
### The client script simply instantiates the ones they're interested in and passes them
### to the GrvtBaseWSAsync.subscribe() method
class GrvtMiniTickerParams(GrvtParams):
    def __init__(self,
                 instrument: str,
                 interval: GrvtTickerInterval) -> None:
        self.instrument = instrument
        self.interval = interval

    def get_feed(self) ->str:
        return f"{self.instrument}@{self.interval}" 

### This interface should be auto generated from the API documentation
### The client script needs to implement this interface and pass it to a 
### GrvtStream derived class such as MiniTickerSnapStream
class GrvtMessageHandler:
    def handle_mini_ticker_snapshot(self, data: grvt_types.WSMiniTickerFeedDataV1, subscription_id: int):
        pass

    def handle_mini_ticker_delta(self, data: grvt_types.WSMiniTickerFeedDataV1, subscription_id: int):
        pass

    def handle_error(self, error: GrvtError):
        pass

class GrvtStream:
    def get_stream(self) -> str:
        pass
    def handle_message(self, json_data: any):
        pass

### We need to auto gen one of these for each type of data that can be recieved
### The client script simply instantiates the ones they're interested in and passes them
### to the GrvtBaseWSAsync.subscribe() method
class MiniTickerSnapStream(GrvtStream):
    def __init__(
            self,
            callback: GrvtMessageHandler,
            ):
        self.callback = callback

    def get_stream(self) -> str:
        return "mini.s"

    def handle_message(self, raw_data: any, subscription_id: int):
        if raw_data.get("code"):
            self.callback.handle_error(grvt_types.GrvtError(**raw_data))
            return
        data_type = from_dict(grvt_types.WSMiniTickerFeedDataV1, raw_data, Config(cast=[Enum]))
        self.callback.handle_mini_ticker_snapshot(grvt_types.WSMiniTickerFeedDataV1(data_type), subscription_id)


#### END --------------------------------------- ####

# THIS NEEDS REFACTORING WITH grvt_ccxt_ws.py from which much of this code is taken
class GrvtBaseWSAsync(GrvtCcxtPro):
    """
    GrvtRawWSAsync class to interact with Grvt WebSockets in asynchronous mode.

    Exceptions:
        websockets.exceptions.ConnectionClosedError: handle closed connection
        websockets.exceptions.ConnectionClosedOK: handle closed connection

    Args:
        env: GrvtCcxtPro (DEV, TESTNET, PROD)
        parameters: dict with trading_account_id, private_key, api_key etc

    Examples:
        ### TODO
        >>> from grvt_api_pro import GrvtCcxtPro
        >>> from grvt_env import GrvtEnv
        >>> grvt = GrvtCcxtPro(env=GrvtEnv.TESTNET)
        >>> await ......
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
        self.tasks: dict[GrvtEndpointType, asyncio.Task] = {}

    async def __aexit__(self):
        for grvt_endpoint_type in [
            GrvtEndpointType.MARKET_DATA,
            GrvtEndpointType.TRADE_DATA,
        ]:
            await self._close_connection(grvt_endpoint_type)

    async def initialize(self):
        """
        Prepares the GrvtCcxtPro instance and connects to WS server.
        """
        await self.refresh_cookie()

    def setup_ws_endpoints(self, grvt_endpoint_type: GrvtEndpointType):
            self.api_url[grvt_endpoint_type] = get_grvt_ws_endpoint(
                self.env.value, grvt_endpoint_type
            )
            self.callbacks[grvt_endpoint_type] = {}
            self.subscribed_streams[grvt_endpoint_type] = {}
            self.ws[grvt_endpoint_type] = None
            task = self._loop.create_task(self._recv(grvt_endpoint_type))
            self.tasks[grvt_endpoint_type] = task

    def is_endpoint_connected(self, grvt_endpoint_type: GrvtEndpointType) -> bool:
        """
        For  MARKET_DATA returns True if connection is open.
        for TRADE_DATA returns True if one of the following is true:
            1. No cookie - this means this is public connection and we can't connect to TRADE_DATA
            2. Connection to TRADE_DATA is open
        """
        if grvt_endpoint_type not in self.ws:
            return False
        connection_is_open = self.ws[grvt_endpoint_type].open
        if grvt_endpoint_type == GrvtEndpointType.MARKET_DATA:
            return connection_is_open
        if grvt_endpoint_type == GrvtEndpointType.TRADE_DATA:
            return bool(not self._cookie or connection_is_open)
        raise ValueError(f"Unknown endpoint type {grvt_endpoint_type}")


    async def connect_channel(self, grvt_endpoint_type: GrvtEndpointType) -> bool:
        """
        Try to connect to a web socket end point
        Both websockets.exceptions.ConnectionClosedOK and websockets.exceptions.ConnectionClosed 
        exceptions should be handled by the calling process
        """
        FN = f"{self._clsname} connect_channel {grvt_endpoint_type.value}"
        try:
            if self.is_endpoint_connected(grvt_endpoint_type):
                self.logger.info(f"{FN} Already connected")
                return True
            self.is_connecting[grvt_endpoint_type] = True
            self.setup_ws_endpoints(grvt_endpoint_type)
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
        finally:
            self.is_connecting[grvt_endpoint_type] = False
        # If we get to here, there should be no exception thrown and we should be connected
        return True

    async def subscribe(self, 
                  callback: GrvtStream,
                  subscription_id: int,
                  params: GrvtParams | None = None):
        """
        Subscribe to a channel to receive callbacks with incoming messages
        A new web socket connection will be created if needed
        """
        ws_stream = GRVT_WS_STREAMS.get(callback.get_stream())
        if ws_stream is None:
            raise grvt_exceptions.UnknownStreamError(ws_stream)
        ws_isconnecting = self.is_connecting.get(ws_stream)
        if ws_isconnecting:
            raise grvt_exceptions.ConnectionInProgress
        ws_isconnected = self.ws.get(ws_stream)
        if not ws_isconnected:
            await self.connect_channel(ws_stream)
        if GrvtStreamType not in self.callbacks:
            self.callbacks[GrvtStreamType] = {}
        self.callbacks[GrvtStreamType][(ws_stream, params.get_feed())] = callback

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

    async def _send(self, end_point_type: GrvtEndpointType, message: str):
        if self.ws[end_point_type] and self.ws[end_point_type].open:
            self.logger.info(f"{self._clsname} _send() {end_point_type=} {message=}")
            await self.ws[end_point_type].send(message)

    def _get_decoder(self, grvt_endpoint_type: GrvtEndpointType, message: dict) -> GrvtStream:
        stream_subscribed: str = message.get("stream")
        if not stream_subscribed:
            self.logger.warning("Received a message without a stream", message)
        if not self.subscribed_streams[grvt_endpoint_type].get(stream_subscribed):
            raise Exception("message stream unregistered " + stream_subscribed)
        return GrvtStream(self.subscribed_streams[grvt_endpoint_type].get(stream_subscribed))

    async def _recv(self, grvt_endpoint_type: GrvtEndpointType):
        FN = f"{self._clsname} _recv {grvt_endpoint_type.value}"
        while True:
            if self.ws.get(grvt_endpoint_type) and self.ws[grvt_endpoint_type].open:
                try:
                    self.logger.debug(f"{FN} waiting for message")
                    response = await asyncio.wait_for(
                        self.ws[grvt_endpoint_type].recv(), timeout=WS_READ_TIMEOUT
                    )
                    message = json.loads(response)
                    self.logger.debug(f"{FN} received {message=}")
                    stream_subscribed: str = message.get("stream")
                    self._check_susbcribed_stream(grvt_endpoint_type, message)
                    if "feed" not in message:
                        self.logger.debug(f"{FN} Non-actionable message:{message}")
                    else:
                        stream_subscribed: str | None = message.get("stream")
                        if stream_subscribed is None:
                            self.logger.warning(f"{FN} missing stream in {message=}")
                        if stream_subscribed:
                            dec = self._get_decoder(message)
                            dec.handle_message(message)
                except (
                    websockets.exceptions.ConnectionClosedError,
                    websockets.exceptions.ConnectionClosedOK,
                ):
                    self.logger.exception(
                        f"{FN} connection closed {traceback.format_exc()}"
                    )
                    raise
                except asyncio.TimeoutError:  # noqa: UP041
                    self.logger.debug(f"{FN} Timeout {WS_READ_TIMEOUT} secs")
                    raise
                except Exception:
                    self.logger.exception(
                        f"{FN} connection failed {traceback.format_exc()}"
                    )
                    raise
            else:
                self.logger.info(f"{FN} not ready")
                await asyncio.sleep(2)







