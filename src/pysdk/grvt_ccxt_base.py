# ruff: noqa: D200
# ruff: noqa: D204
# ruff: noqa: D205
# ruff: noqa: D404
# ruff: noqa: W291
# ruff: noqa: D400
# ruff: noqa: E501

import logging
import time
from typing import get_args

from .grvt_ccxt_env import GrvtEnv
from .grvt_ccxt_types import (
    CandlestickInterval,
    CandlestickType,
    GrvtInvalidOrder,
    GrvtOrderSide,
    GrvtOrderType,
    Num,
    ccxt_interval_to_grvt_candlestick_interval,
)
from .grvt_ccxt_utils import get_kuq_from_symbol

# COOKIE_REFRESH_INTERVAL_SECS = 60 * 60  # 30 minutes


class GrvtCcxtBase:
    """
    GrvtCcxtBase is an abstract class for other Grvt Rest
        and WebSocket connectivity classes.

    Args:
        env: GrvtCcxtBase (DEV, TESTNET, PROD)
        logger (logging.Logger, optional). Defaults to None.
        parameters: (dict, optional). Dict with trading_account_id, private_key, api_key etc
                defaults to empty.
    """

    def __init__(
        self,
        env: GrvtEnv,
        logger: logging.Logger | None = None,
        parameters: dict = {},
    ):
        """Initialize the GrvtCcxtBase part."""
        self.logger = logger or logging.getLogger(__name__)
        self.env: GrvtEnv = env
        self._trading_account_id = parameters.get("trading_account_id")
        self._private_key = parameters.get("private_key")
        self._api_key = parameters.get("api_key")
        self._path_return_value_map: dict = {}
        self._cookie: dict | None = None
        self.markets: dict | None = None
        self._clsname: str = type(self).__name__
        self.logger.info(f"GrvtCcxtBase: {self.env=}, {self._trading_account_id=}")

    def should_refresh_cookie(self) -> bool:
        """
        Retuns:
            True if this object has API key and the session cookie should be refreshed.
            False - otherwise.
        """
        if not self._api_key:
            return False
        time_till_expiration = None
        if self._cookie and "expires" in self._cookie:
            time_till_expiration = self._cookie["expires"] - time.time()
        is_cookie_fresh = time_till_expiration is not None and time_till_expiration > 5
        if not is_cookie_fresh:
            self.logger.info(
                f"cookie should be refreshed {self._cookie=} now={time.time()}"
                f" {time_till_expiration=} secs"
            )
        return not is_cookie_fresh

    def get_path_return_value_map(self) -> dict:
        """Returns the path return value map."""
        return self._path_return_value_map

    def get_endpoint_return_value(self, endpoint: str) -> dict:
        """Returns the return value for the endpoint."""
        return self._path_return_value_map.get(endpoint)

    def was_path_called(self, path: str) -> bool:
        """Returns True if the path was called."""
        return path in self._path_return_value_map

    # PRIVATE API CALLS

    def _check_order_arguments(
        self, order_type: GrvtOrderType, side: GrvtOrderSide, amount: Num, price: Num
    ) -> None:
        if order_type not in get_args(GrvtOrderType):
            raise GrvtInvalidOrder(
                f"{self._clsname} create_order() order_type should be one of "
                f"{get_args(GrvtOrderType)}"
            )
        if side not in get_args(GrvtOrderSide):
            raise GrvtInvalidOrder(
                f"{self._clsname} create_order() side should be one of {get_args(GrvtOrderSide)}"
            )
        if order_type == "limit":
            if price is None or price <= 0:
                raise GrvtInvalidOrder(
                    f"{self._clsname} create_order() requires a price argument for a limit order"
                )
        elif order_type == "market":
            if price:
                raise GrvtInvalidOrder(
                    f"{self._clsname} create_order() should not have a positive price argument"
                    " for a market order"
                )
        if not amount or amount < 0:
            raise GrvtInvalidOrder(
                f"{self._clsname} create_order() amount should be above 0"
            )

    def _check_account_auth(self) -> bool:
        if not self._trading_account_id:
            raise GrvtInvalidOrder(
                f"{self._clsname}: this action requires a trading_account_id"
            )
        return True

    def _check_valid_symbol(self, symbol: str) -> bool:
        if not self.markets:
            raise GrvtInvalidOrder(f"{self._clsname}: markets not loaded")
        market = self.markets.get(symbol)
        if not market:
            raise GrvtInvalidOrder(f"{self._clsname}: {symbol=} not found")
        return True

    def _get_payload_fetch_markets(self, params: dict) -> dict:
        payload = {}
        if params.get("kind"):
            payload["kind"] = [params.get("kind")]
        if params.get("base"):
            payload["base"] = [params.get("base")]
        if params.get("quote"):
            payload["quote"] = [params.get("quote")]
        payload["limit"] = params.get("limit", 20)
        payload["is_active"] = params.get("is_active", True)
        return payload

    def _get_payload_fetch_my_trades(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict = {},
    ) -> dict:
        """
        prepares payload for fetch_my_trades() method.<br>.

        Args:
            symbol: get trades for this symbol only.<br>
            since: fetch trades since this timestamp in nanoseconds.<br>
            limit: maximum number of trades to fetch.<br>
            params: dictionary with parameters. Valid keys:<br>
                `cursor` (str): cursor for the pagination.
                            If cursor is present then we ignore other filters.<br>
                `kind` (str): instrument kind. Valid values: 'PERPETUAL'.<br>
                `base` (str): base currency. If missing/empty then fetch
                                    orders for all base currencies.<br>
                `quote` (str): quote currency. Default: 'USDT'.<br>
                `end_time` (int): fetch trades until this timestamp in nanoseconds.<br>

        Returns:
            a dictionary with a payload for Rest API call to fetch trades.<br>
        """
        payload = {"sub_account_id": str(self._trading_account_id)}
        if params.get("cursor"):
            payload["cursor"] = params["cursor"]
        else:
            if symbol:
                payload["instrument"] = symbol
            else:
                if "kind" in params:
                    payload["kind"] = [params["kind"]]
                if "base" in params:
                    payload["base"] = [params["base"]]
                if "quote" in params:
                    payload["quote"] = [params["quote"]]
            if since:
                payload["start_time"] = since
            if params.get("end_time"):
                payload["end_time"] = params["end_time"]
            if limit:
                payload["limit"] = limit
        return payload

    def _get_payload_fetch_trades(
        self,
        symbol: str,
        since: int | None = None,
        limit: int = 20,
        params: dict = {},
    ) -> dict:
        """
        prepares payload for fetch_trades() method.<br>.

        Args:
            symbol: get trades for this symbol only.<br>
            since: fetch trades since this timestamp in nanoseconds.<br>
            limit: maximum number of trades to fetch.<br>
            params: dictionary with parameters. Valid keys:<br>
                `cursor` (str): cursor for the pagination.
                            If cursor is present then we ignore other filters.<br>
                `kind` (str): instrument kind. Valid values: 'PERPETUAL'.<br>
                `base` (str): base currency. If missing/empty then fetch
                                    orders for all base currencies.<br>
                `quote` (str): quote currency. Default: 'USDT'.<br>

        Returns:
            a dictionary with a payload for Rest API call to fetch trades.<br>
        """
        payload = {
            "sub_account_id": str(self._trading_account_id),
            "instrument": symbol,
        }
        if params.get("cursor"):
            payload["cursor"] = params["cursor"]
        else:
            if since:
                payload["start_time"] = since
            if params.get("end_time"):
                payload["end_time"] = params["end_time"]
            payload["limit"] = limit | 20
        return payload

    def _get_payload_fetch_account_history(self, params: dict = {}) -> dict:
        """
        prepares payload for fetch_my_trades() method.<br>.

        Args:
            params: dictionary with parameters. Valid keys:<br>
                `start_time` (int): fetch orders since this timestamp in nanoseconds.<br>
                `end_time` (int): fetch orders until this timestamp in nanoseconds.<br>
                `cursor` (int):cursor for the pagination. If cursor is present then we ignore
                        `start_time` and `end_time`.<br>
        Returns:
            a dictionary with a payload for Rest API call to fetch account history.<br>
        """
        payload = {"sub_account_id": str(self._trading_account_id)}
        if params.get("cursor"):
            payload["cursor"] = params["cursor"]
        else:
            start_time = params.get("start_time")
            end_time = params.get("end_time")
            if start_time:
                payload["start_time"] = start_time
            if end_time:
                payload["end_time"] = end_time
        return payload

    def _get_payload_fetch_positions(self, symbols: list[str] = [], params={}) -> dict:
        """
        prepares payload for fetch_positions() method.<br>.

        Args:
            symbols: list(str) get positions for these symbols only.<br>

        Returns: a dictionary with a payload for Rest API call to fetch positions.<br>
        """
        payload = {"sub_account_id": str(self._trading_account_id)}
        if symbols:
            ks, us, qs = [], [], []
            for symbol in symbols:
                try:
                    k, u, q = get_kuq_from_symbol(symbol)
                    ks.append(k)
                    us.append(u)
                    qs.append(q)
                except Exception as e:
                    raise GrvtInvalidOrder(
                        f"Invalid symbol {symbol} in fetch_positions {e}"
                    )
            payload["kind"] = list(set(ks))
            payload["base"] = list(set(us))
            payload["quote"] = list(set(qs))
        else:
            if "kind" in params:
                payload["kind"] = [params["kind"]]
            if "base" in params:
                payload["base"] = [params["base"]]
            if "quote" in params:
                payload["quote"] = [params["quote"]]
        return payload

    def _get_payload_fetch_order_history(
        self,
        params: dict,
    ) -> dict:
        """
        prepares payload for fetch_order_history() method.<br>.

        Args:
            params: (dict) with possible keys as:.<br>
                `kind`: (str) - The kind filter to apply. Defaults to all kinds.<br>
                `base`: (str) - The base currency filter. Defaults to all base currencies.<br>
                `quote`: (str) - The quote currency filter. Defaults to all quote currencies.<br>
                `expiration`: (int)	The expiration time in nanoseconds. Defaults to all.<br>
                `strike_price`: (str) The strike price to apply. Defaults to all strike prices.<br>
                `limit`: (int) The limit to query for. Defaults to 500; Max 1000.<br>
                `cursor`: (str) The cursor to use for pagination. If nil, return the first page.<br>
        Returns: a dictionary with a payload for Rest API call to fetch order history.<br>
        """
        payload = {"sub_account_id": str(self._trading_account_id)}
        if "limit" in params:
            payload["limit"] = params["limit"]
        if params.get("cursor"):
            payload["cursor"] = params["cursor"]
        else:
            if "kind" in params:
                payload["kind"] = [params["kind"]]
            if "base" in params:
                payload["base"] = [params["base"]]
            if "quote" in params:
                payload["quote"] = [params["quote"]]
            if "expiration" in params:
                payload["expiration"] = [params["expiration"]]
            if "strike_price" in params:
                payload["strike_price"] = [params["strike_price"]]
        return payload

    def _get_payload_fetch_open_orders(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict = {},
    ) -> dict:
        """
        prepares payload for fetch_order_history() method.<br>.

        Args:
            params: (dict) with possible keys as:.<br>
                `kind`: (str) - The kind filter to apply. Defaults to all kinds.<br>
                `base`: (str) - The base currency filter. Defaults to all base currencies.<br>
                `quote`: (str) - The quote currency filter. Defaults to all quote currencies.<br>
                `limit`: (int) The limit to query for. Defaults to 500; Max 1000.<br>
                `cursor`: (str) The cursor to use for pagination. If nil, return the first page.<br>
        Returns: a dictionary with a payload for Rest API call to fetch order history.<br>
        """
        payload = {"sub_account_id": str(self._trading_account_id)}
        if symbol:
            try:
                k, u, q = get_kuq_from_symbol(symbol)
                payload["kind"] = [k]
                payload["base"] = [u]
                payload["quote"] = [q]
            except Exception as e:
                raise GrvtInvalidOrder(
                    f"Invalid symbol {symbol} in fetch_open_orders {e}"
                )
        else:
            if "kind" in params:
                payload["kind"] = [params["kind"]]
            if "base" in params:
                payload["base"] = [params["base"]]
            if "quote" in params:
                payload["quote"] = [params["quote"]]
        if since:
            payload["start_time"] = since
        if limit:
            payload["limit"] = limit
        return payload

    def _get_payload_fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        limit: int,
        params={},
    ) -> dict:
        """
        prepares payload for fetch_ohlcv() method.<br>.

        Args:
            symbol: The instrument name.<br>
            timeframe: The timeframe of the ohlc.
                        See `ccxt_interval_to_grvt_candlestick_interval`.<br>
            since: fetch ohlc since this timestamp in nanoseconds.<br>
            limit: maximum number of ohlc to fetch.<br>
            params: dictionary with parameters. Valid keys:<br>
                `cursor` (str): cursor for the pagination.
                            If cursor is present then we ignore other filters.<br>
                `end_time` (int): end time in nanoseconds.<br>
                `candle_type` (str): candle type. Valid values: 'TRADE', 'MARK', 'INDEX'.<br>

        Returns: a dictionary with a payload for Rest API call to fetch_ohlcv.<br>
        See [Candlestick] (https://api-docs.grvt.io/market_data_api/#candlestick_1)
            for more details.<br>
        """
        if timeframe not in ccxt_interval_to_grvt_candlestick_interval:
            raise ValueError(f"Invalid timeframe {timeframe}")
        interval: CandlestickInterval = ccxt_interval_to_grvt_candlestick_interval[
            timeframe
        ]
        payload = {"instrument": symbol}
        if params.get("cursor"):
            payload["cursor"] = params["cursor"]
        else:
            if interval:
                payload["interval"] = interval.value
            candle_type = CandlestickType.TRADE
            if "candle_type" in params:
                candle_type = CandlestickType[params["candle_type"]]
            payload["type"] = candle_type.value
            if since:
                payload["start_time"] = since
            if "end_time" in params:
                payload["end_time"] = params["end_time"]
            if limit:
                payload["limit"] = limit
        return payload