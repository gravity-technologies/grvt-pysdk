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

# TODO - auto generate full set
# GrvtStreamType defines the available streams to subscribe to
class GrvtStreamType(str, Enum):
    MINI_TICKER_SNAPHOT = "mini.s"
    MINI_TICKER_DELTA = "mini.d"


# 
class GrvtRawWSAsync(GrvtCcxtPro):
    """
    GrvtRawWSAsync class to interact with Grvt WebSockets in asynchronous mode.

    Exceptions:
        websockets.exceptions.ConnectionClosedError: handle closed connection
        websockets.exceptions.ConnectionClosedOK: handle closed connection

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

    def subscribe(self, 
                  subscription: GrvtStreamType,
                  callback: Callable[[any, int], None],
                  subscription_id: int,
                  params: dict | None = None):
        """
        Subscribe to a channel to receive callbacks with incoming messages
        A new web socket connection will be created if needed
        """
        ws_stream = GRVT_WS_STREAMS.get(GrvtStreamType)

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
        # return True  if connection successful
        return self.is_endpoint_connected(grvt_endpoint_type)



