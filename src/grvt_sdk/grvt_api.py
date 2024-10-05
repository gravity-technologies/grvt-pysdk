import json
import logging
from typing import List, Literal, Optional

import requests

from grvt_api_base import GrvtApiBase
from grvt_env import GrvtEnv, get_grvt_endpoint
from grvt_types import (
    GrvtInstrumentKind,
    GrvtInvalidOrder,
    GrvtOrderSide,
    GrvtOrderType,
    Num,
)
from grvt_utils import (
    EnumEncoder,
    GrvtOrder,
    get_cookie_with_expiration,
    get_grvt_order,
    get_order_payload,
)


class GrvtApi(GrvtApiBase):
    """GrvtApi class to interact with Grvt Rest API in synchronous mode.

    Args:
        env: GrvtEnv (DEV, TESTNET, PROD)
        logger: logging.Logger
        parameters: dict with trading_account_id, private_key, api_key etc

    Examples:
        >>> from grvt_api import GrvtApi
        >>> from grvt_env import GrvtEnv
        >>> grvt = GrvtApi(env=GrvtEnv.TESTNET)
        >>> grvt.fetch_markets()
    """

    def __init__(
        self,
        env: GrvtEnv,
        logger: Optional[logging.Logger] = None,
        parameters: dict = {},
    ):
        """
        Initialize the GrvtApi instance.
        """
        super().__init__(env, logger, parameters)
        self._clsname: str = type(self).__name__
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
            }
        )

        # self._cookie: Optional[dict] = None
        self.refresh_cookie()
        # Assign markets here
        self.markets = self.load_markets()

    def refresh_cookie(self) -> Optional[dict]:
        """
        Refresh the session cookie.
        """
        if not self.should_refresh_cookie():
            return self._cookie
        path = get_grvt_endpoint(self.env, "AUTH")
        self._cookie = get_cookie_with_expiration(path, self._api_key)
        self._path_return_value_map[path] = self._cookie
        if self._cookie:
            self.logger.info(f"refresh_cookie cookie={self._cookie}")
            self._session.cookies.update({"gravity": self._cookie["gravity"]})
        return self._cookie

    # PRIVATE API CALLS
    def _auth_and_post(self, path: str, payload: dict) -> dict:
        FN = f"_auth_and_post {path=}"
        MAX_LEN_TO_LOG = 1280
        response: dict = {}
        if not path:
            self.logger.warning(f"{FN} Invalid path {path=} {payload=}")
            raise GrvtInvalidOrder(f"{FN} Invalid path {path=} {payload=}")
        # Always see if need to referesh cookie before sending a request
        self.refresh_cookie()
        payload_json = json.dumps(payload, cls=EnumEncoder)
        self.logger.info(f"{FN} {payload=}\n{payload_json=}")
        return_value = self._session.post(path, data=payload_json)
        try:
            return_text = return_value.text
            response = return_value.json()
            if not return_value.ok:
                self.logger.warning(
                    f"{FN} ERROR {return_value=}\n"
                    f"return_text={return_text}\n"
                    f"response={response=}"
                )
            else:
                if len(return_text) > MAX_LEN_TO_LOG:
                    self.logger.debug(f"{FN} response={response}")
                    self.logger.info(f"{FN} response=**TOO LONG**")
                else:
                    self.logger.info(f"{FN} OK response={response}")
        except Exception as err:
            self.logger.warning(f"{FN} Unable to parse {return_value=} as json. {err=}")
        self._path_return_value_map[path] = response
        return response

    def _create_grvt_order(self, order: GrvtOrder) -> dict:
        """
        Send a GrvtOrder object to the exchange.
        :param order: The GrvtOrder object.
        Return: dictionary representing the order response.
        """
        FN = f"{self._clsname} _create_grvt_order cloid:{order.metadata.client_order_id}"
        order_payload = get_order_payload(
            order,
            private_key=self._private_key,
            env=self.env,
            instruments=self.markets,
        )
        path = get_grvt_endpoint(self.env, "CREATE_ORDER")
        self.logger.info(f"{FN} {path=} {order_payload=}")
        response: dict = self._auth_and_post(path, payload=order_payload)
        if response.get("result") is None:
            self.logger.error(f"{FN} Error: {response}")
            return {}
        else:
            self.logger.info(
                f"{FN} Order created:"
                f"{response.get('result', {}).get('metadata', {}).get('client_order_id')}"
            )
            return response.get("result")

    def create_order(
        self,
        symbol: str,
        order_type: GrvtOrderType,
        side: GrvtOrderSide,
        amount: Num,
        price: Num = None,
        params={},
    ) -> dict:
        """ccxt compliant signature"""
        self._check_account_auth()
        self._check_valid_symbol(symbol)
        # Validate order fields
        self._check_order_arguments(order_type, side, amount, price)
        # create GrvtOrder object
        order_duration_secs = params.get("order_duration_secs", 24 * 60 * 60)
        order = get_grvt_order(
            sub_account_id=self._trading_account_id,
            symbol=symbol,
            order_type=order_type,
            side=side,
            amount=amount,
            limit_price=price,
            order_duration_secs=order_duration_secs,
            params=params,
        )
        return self._create_grvt_order(order)

    def create_limit_order(
        self,
        symbol: str,
        side: GrvtOrderSide,
        amount: Num,
        price: Num = None,
        params={},
    ) -> dict:
        return self.create_order(symbol, "limit", side, amount, price, params)

    def cancel_all_orders(
        self,
        symbol: Optional[str] = None,
        params: dict = {},
    ) -> bool:
        """ccxt compliant signature
        Cancel all orders for a sub-account.
        :param sub_account_id: The sub-account ID.
        """
        self._check_account_auth()
        FN = f"{self._clsname} cancel_all_orders"
        payload: dict = {"sub_account_id": str(self._trading_account_id)}
        path = get_grvt_endpoint(self.env, "CANCEL_ALL_ORDERS")
        response: dict = self._auth_and_post(path, payload)
        cancel_ack = response.get("result", {}).get("ack")

        if not cancel_ack:
            self.logger.warning(f"{FN} failed to cancel orders: {response=}")
            return False
        else:
            self.logger.info(f"{FN} Cancelled {response=}")
            return True

    def cancel_order(
        self,
        id: Optional[str] = None,
        symbol: Optional[str] = None,
        params: Optional[dict] = {},
    ) -> bool:
        """ccxt compliant signature
        Cancel specific order for the account.<br>
        Private call requires authorization.<br>
        See [Cancel order](https://api-docs.grvt.io/trading_api/#cancel-order)
        for details.<br>

        Args:
            id (str): exchange assigned order ID<br>
            symbol (str): trading symbol<br>
            params: client_order_id (str): client assigned order ID<br>
        Returns:
            True if cancel request was acked by exchange. False otherwise.<br>
        """
        FN = f"{self._clsname} cancel_order"
        self._check_account_auth()
        payload: dict = {
            "sub_account_id": str(self._trading_account_id),
        }
        if id:
            payload["order_id"] = str(id)
        elif "client_order_id" in params:
            payload["client_order_id"] = str(params["client_order_id"])
        else:
            raise GrvtInvalidOrder(f"{FN} requires either order_id or client_order_id")

        path = get_grvt_endpoint(self.env, "CANCEL_ORDER")
        self.logger.info(
            f"{FN} Send cancel {payload=} for trading_account_id={self._trading_account_id}"
        )
        response: dict = self._auth_and_post(path, payload)
        cancel_ack = response.get("result", {}).get("ack")

        if not cancel_ack:
            self.logger.warning(f"{FN} failed to cancel order: {response=}")
            return False
        else:
            self.logger.info(f"{FN} Cancelled {response=}")
            return True

    def fetch_open_orders(
        self,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: Optional[int] = None,
        params: dict = {},
    ) -> List[dict]:
        """ccxt compliant signature
        Fetch open orders for the account.<br>
        Private call requires authorization.<br>
        See [Open orders](https://api-docs.grvt.io/trading_api/#open-orders)
        for details.<br>

        Args:
            symbol: (str) get orders for this symbol only.<br>
            since: (int) fetch orders since this timestamp in nanoseconds.<br>
            limit: (int) maximum number of orders to fetch.<br>
            params: dictionary with parameters. Valid keys:<br>
                `sub_account_id` (str): sub account id.<br>
                `kind` (str): instrument kind. Valid values: 'PERPETUAL'.<br>
                `base` (str): base currency. If missing/empty then fetch
                                    orders for all base currencies.<br>
                `quote` (str): quote currency. Defaults to all.<br>
        Returns:
            a list of dictionaries, each dict represent an order.<br>
        """
        self._check_account_auth()
        # Prepare request payload
        payload = self._get_payload_fetch_open_orders(symbol, since, limit, params)
        # Post payload and parse the response
        path = get_grvt_endpoint(self.env, "GET_OPEN_ORDERS")
        response: dict = self._auth_and_post(path, payload)
        open_orders: list = response.get("result", [])
        if symbol:
            open_orders = [
                o for o in open_orders if o.get("legs") and o["legs"][0].get("instrument") == symbol
            ]
        return open_orders

    def fetch_order(
        self,
        id: Optional[str] = None,
        symbol: str = None,
        params: dict = {},
    ) -> dict:
        """ccxt compliant signature
        Get Order status by order_id or client_order_id
        Private call requires authorization.<br>
        See [Open orders](https://api-docs.grvt.io/trading_api/#open-orders)
        for details.<br>
        Args:
            id: (str) order_id to fetch.<br>
            symbol: (str) get orders for this symbol only.<br>
            params: dictionary with parameters. Valid keys:<br>
                `client_order_id` (int): client assigned order ID.<br>
        Return: dict with order's details or {} if order was NOT found.
        """
        self._check_account_auth()
        payload = {
            "sub_account_id": str(self._trading_account_id),
        }
        if id:
            payload["order_id"] = id
        elif "client_order_id" in params:
            payload["client_order_id"] = str(params["client_order_id"])
        else:
            raise GrvtInvalidOrder(
                f"{self._clsname} fetch_order() requires order_id " "or params['client_order_id']"
            )
        path = get_grvt_endpoint(self.env, "GET_ORDER")
        response: dict = self._auth_and_post(path, payload)
        return response

    def fetch_order_history(self, params: dict = {}) -> dict:
        """ccxt compliant signature, HISTORICAL data.<br>
        Get Order status by order_id or client_order_id
        Private call requires authorization.<br>
        See [Order History](https://api-docs.grvt.io/trading_api/#order-history)
            for details.<br>
        Args:
            params: dictionary with parameters. Valid keys:<br>
                `kind`: (str) - The kind filter to apply. Defaults to all kinds.<br>
                `base`: (str) - The base currency filter. Defaults to all base currencies.<br>
                `quote`: (str) - The quote currency filter. Defaults to all quote currencies.<br>
                `expiration`: (int)	The expiration time in nanoseconds. Defaults to all.<br>
                `strike_price`: (str) The strike price to apply. Defaults to all strike prices.<br>
                `limit`: (int) The limit to query for. Defaults to 500; Max 1000.<br>
                `cursor`: (str) The cursor to use for pagination. If nil, return the first page.<br>
        Return: a dictionary with keys:
                `total` : total number of account history snapshots.<br>
                `next` : cursor for the next page.<br>
                `result` : a list of dictionaries, each dict represent an order state.<br>
        """
        self._check_account_auth()
        payload = self._get_payload_fetch_order_history(params)
        path = get_grvt_endpoint(self.env, "GET_ORDER_HISTORY")
        response: dict = self._auth_and_post(path, payload)
        return response

    def get_account_summary(self, type: Literal["sub-account", "funding", "aggregated"]) -> dict:
        """
        Return: The account summary.
        Private call requires authorization.<br>
        See [Account Summary](https://api-docs.grvt.io/trading_api/#account_summary)
        for details.<br>
        Returns: dictionary with account data.<br>
        """
        FN = f"{self._clsname} get_account_summary {type=}"
        self._check_account_auth()
        payload = {}
        if type == "sub-account":
            path = get_grvt_endpoint(self.env, "GET_ACCOUNT_SUMMARY")
            payload = {"sub_account_id": str(self._trading_account_id)}
        elif type == "funding":
            path = get_grvt_endpoint(self.env, "GET_FUNDING_ACCOUNT_SUMMARY")
        elif type == "aggregated":
            path = get_grvt_endpoint(self.env, "GET_AGGREGATED_ACCOUNT_SUMMARY")
        else:
            raise GrvtInvalidOrder(f"{FN} Invalid account summary type {type}")

        response: dict = self._auth_and_post(path, payload=payload)
        sub_account: dict = response.get("result", {})
        if not sub_account:
            self.logger.info(f"{FN} No account summary for {path=} {payload=}")
        return sub_account

    def fetch_account_history(self, params: dict = {}) -> dict:
        """HISTORICAL data.<br>
        Get account history.<br>
        Private call requires authorization.<br>
        See [Account History](https://api-docs.grvt.io/trading_api/#account-history)
            for details.<br>

        Args:
            params: dictionary with parameters. Valid keys:<br>
                `start_time` (int): fetch orders since this timestamp in nanoseconds.<br>
                `end_time` (int): fetch orders until this timestamp in nanoseconds.<br>
                `cursor` (str): cursor for the pagination. If cursor is present then we ignore
                        `start_time` and `end_time`.<br>
        Returns:
            a dictionary with keys:
            `total` : total number of account history snapshots.<br>
            `next` : cursor for the next page.<br>
            `result` : list of account history snapshots.<br>
        """
        self._check_account_auth()
        # Prepare request payload
        payload = self._get_payload_fetch_account_history(params)
        # Post payload and parse the response
        path = get_grvt_endpoint(self.env, "GET_ACCOUNT_HISTORY")
        response: dict = self._auth_and_post(path, payload=payload)
        return response

    def fetch_positions(self, symbols: list[str] = [], params={}):
        """ccxt compliant signature
        Fetch positions for the account.<br>
        Private call requires authorization.<br>
        See [Positions](https://api-docs.grvt.io/trading_api/#positions)
        for details.<br>

        Args:
            symbols: list(str) get positions for these symbols only.<br>

        Returns: list of dictionaries, each dict represent a position.<br>
        """
        self._check_account_auth()
        # Prepare request payload
        payload = self._get_payload_fetch_positions(symbols, params)
        # Post payload and parse the response
        path = get_grvt_endpoint(self.env, "GET_POSITIONS")
        response: dict = self._auth_and_post(path, payload)
        positions: list = response.get("result", [])
        if symbols:
            self.logger.info(f"fetch_positions filter positions by {symbols=}")
            positions = [p for p in positions if p.get("instrument") in symbols]
        return positions

    def fetch_my_trades(
        self,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: Optional[int] = None,
        params: dict = {},
    ) -> dict:
        """ccxt compliant signature, HISTORICAL data.<br>
        Fetch past trades for the account.<br>
        Private call requires authorization.<br>
        See [Private Trade History](https://api-docs.grvt.io/trading_api/#private-trade-history)
        for details.<br>

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
            a dictionary with keys:
                `total` : total number of account history snapshots.<br>
                `next` : cursor for the next page.<br>
                `result` : a list of dictionaries, each dict represent a trade.<br>
        """
        self._check_account_auth()
        # Prepare request payload
        payload = self._get_payload_fetch_my_trades(symbol, since, limit, params)
        # Post payload and parse the response
        path = get_grvt_endpoint(self.env, "GET_FILL_HISTORY")
        response: dict = self._auth_and_post(path, payload=payload)
        if symbol:
            # filter result by symbol
            trades: list = response.get("result", [])
            trades = [t for t in trades if t.get("instrument") == symbol]
            response["result"] = trades
        return response

    # **************** PUBLIC API CALLS
    def load_markets(self) -> dict:
        self.logger.info("load_markets START")
        instruments = self.fetch_markets(
            params={
                "kind": GrvtInstrumentKind.PERPETUAL,
                # "base": "BTC",
                # "quote": "USDT",
            }
        )
        if instruments:
            self.markets = {i.get("instrument"): i for i in instruments if i.get("instrument")}
            self.logger.info(f"load_markets: loaded {len(self.markets)} markets.")
        else:
            self.logger.warning("load_markets: No markets found.")
        return self.markets

    def fetch_markets(
        self,
        params: dict = {},
    ) -> List[dict]:
        """ccxt-compliant signature
        Retrieve the list of all instruments of matching kind, base and quote
                supported by the exchange.

        Params: dict with keys:<br>
            `is_active` (bool) - defaults to True.<br>
            `limit` (int) - defaiults to 20.<br>
            `kind` (str): instrument kind. Valid values: 'PERPETUAL'.<br>
            `base` (str): base currency. If missing/empty then fetch
                            orders for all base currencies.<br>
            `quote` (str): quote currency. Default: 'USDT'.<br>

        Returns: list of dictionaries per instrument with keys:<br>
            `instrument`: symbol e.g. 'BTC_USDT_Perp'.<br>
            `instrument_hash`: hashed symbol for order signing e.g. '0x030501'.<br>
            `base`: base currency e.g. 'BTC'.<br>
            `quote`: quote currency e.g. 'USDT'.<br>
            `kind`: kind of instrument 'PERPETUAL'/'FUTURE'.<br>
            'base_decimals': size multiplier for order signing.<br>
            `tick_size`: price tick size.<br>
            `min_size`: minimum order size.<br>
        """
        # Prepare request payload
        payload = self._get_payload_fetch_markets(params)
        # Make the POST request to get all instruments
        path = get_grvt_endpoint(self.env, "GET_INSTRUMENTS")
        response: dict = self._auth_and_post(path, payload)
        return response.get("result", [])

    def fetch_all_markets(
        self,
        is_active: Optional[bool] = True,
    ) -> List[dict]:
        """
        Retrieve the list of all instruments supported by the exchange.<br>
        Params:<br>
            `is_active` (bool) - defaults to True.<br>

        Returns: list of dictionaries per instrument. See fetch_markets().<br>
        """
        # Prepare request payload
        payload = {"is_active": is_active}
        # Make the POST request to get all instruments
        path = get_grvt_endpoint(self.env, "GET_ALL_INSTRUMENTS")
        response: dict = self._auth_and_post(path, payload)
        return response.get("result", [])

    def fetch_market(self, symbol: str) -> dict:
        """
        Retrieve the instrument object for a given symbol.
        :param symbol: The symbol of the instrument.
        """
        # Make the POST request to get all instruments
        path = get_grvt_endpoint(self.env, "GET_INSTRUMENT")
        response: dict = self._auth_and_post(path, payload={"instrument": symbol})
        return response.get("result", [])

    def fetch_ticker(self, symbol: str, params: dict = {}) -> dict:
        """ccxt-compliant signature
        Retrieve the ticker of a given symbol.
        :param symbol: The instrument name.
        :return: The ticker dictionary of the instrument.
        """
        # {'event_time': '1724252426000000000', 'instrument': 'BTC_USDT_Perp',
        # 'mark_price': '59373870996065', 'index_price': '59395287961367',
        # 'last_price': '99000000000000', 'last_size': '9917000000', 'mid_price': '59569850000000',
        # 'best_bid_price': '59866000000000', 'best_bid_size': '23705000000', 'best_ask_price':
        # '592737000', 'best_ask_size': '21678', 'funding_rate_curr': 2544, 'funding_rate_avg': 0,
        # 'interest_rate': 0, 'forward_price': '0', 'buy_volume_u': '401930000000',
        # 'sell_volume_u': '1218289000000', 'buy_volume_q': '34637817515500',
        # 'sell_volume_q': '68764000329900', 'high_price': '3435450000', 'low_price': '100000',
        # 'open_price': '32554000000000', 'open_interest': '8174350000000',
        # 'long_short_ratio': 1.0948905}
        path = get_grvt_endpoint(self.env, "GET_TICKER")
        response: dict = self._auth_and_post(path, payload={"instrument": symbol})
        return response.get("result", [])

    def fetch_mini_ticker(self, symbol: str) -> dict:
        """
        Retrieve the mini-ticker of a given symbol.
        :param symbol: The instrument name.
        :return: The mini-ticker dictionary of the instrument.
        """
        # {'event_time': '1724252426000000000', 'instrument': 'BTC_USDT_Perp',
        # 'mark_price': '59373870996065', 'index_price': '59395287961367',
        # 'last_price': '99000000000000', 'last_size': '9917000000', 'mid_price': '59569850000000',
        # 'best_bid_price': '59866000000000', 'best_bid_size': '23705000000', 'best_ask_price':
        # '59273700000000', 'best_ask_size': '21678000000'}
        path = get_grvt_endpoint(self.env, "GET_MINI_TICKER")
        response: dict = self._auth_and_post(path, payload={"instrument": symbol})
        return response.get("result", [])

    def fetch_order_book(self, symbol: str, limit: int = 10, params={}) -> dict:
        """ccxt-compliant signature
        Retrieve the order book of a given symbol.
        :param symbol: The instrument name.
        :return: The order book dictionary of the instrument.
        """
        #  {'event_time': '0', 'instrument': 'BTC_USDT_Perp',
        # 'bids': [{'price': '100000000', 'size': '86353000000', 'num_orders': 4},...]
        # 'asks': [{'price': '59273700000000', 'size': '21678000000', 'num_orders': 1}, ...]
        payload = {"instrument": symbol, "aggregate": 1}
        if limit:
            payload["depth"] = limit
        path = get_grvt_endpoint(self.env, "GET_ORDER_BOOK")
        response: dict = self._auth_and_post(path, payload=payload)
        return response.get("result", {})

    def fetch_recent_trades(
        self,
        symbol: str,
        limit: Optional[int] = None,
    ) -> list:
        """
        Retrieve recent trades of a given instrument.
        :param symbol: The instrument name.
        :return: The list of trades for the instrument.
        """
        #  List of {'event_time': '1724248876870635916', 'instrument': 'ETH_USDT_Perp',
        # 'is_taker_buyer': True, 'size': '24000000000', 'price': '2600000000000',
        # 'mark_price': '2591055564869', 'index_price': '2592459142472', 'interest_rate': 0,
        # 'forward_price': '0', 'trade_id': '729726', 'venue': 'ORDERBOOK'}
        payload = {"instrument": symbol}
        if limit:
            payload["limit"] = limit
        path = get_grvt_endpoint(self.env, "GET_TRADES")
        response: dict = self._auth_and_post(path, payload=payload)
        return response.get("result", [])

    def fetch_trades(
        self,
        symbol: str,
        since: Optional[int] = None,
        limit: int = 10,
        params: dict = {},
    ) -> list:
        """ccxt-compliant signature, HISTORICAL data.<br>
        Retrieve trade history of a given instrument.
        :param symbol: The instrument name.
        :return: The list of trades.
        """
        #  List of {'event_time': '1724248876870635916', 'instrument': 'ETH_USDT_Perp',
        # 'is_taker_buyer': True, 'size': '24000000000', 'price': '2600000000000',
        # 'mark_price': '2591055564869', 'index_price': '2592459142472', 'interest_rate': 0,
        # 'forward_price': '0', 'trade_id': '729726', 'venue': 'ORDERBOOK'}
        payload = self._get_payload_fetch_trades(
            symbol,
            since=since,
            limit=limit,
            params=params,
        )
        path = get_grvt_endpoint(self.env, "GET_TRADE_HISTORY")
        response: dict = self._auth_and_post(path, payload=payload)
        return response

    def fetch_funding_rate_history(
        self,
        symbol: str,
        since: int = 0,
        limit: int = 10,
        params: dict = {},
    ) -> list:
        """ccxt-compliant signature, HISTORICAL data.<br>
        Retrieve the funding rates history of a given instrument.<br>
        Args:
            symbol: The instrument name.<br>
            since: fetch trades since this timestamp in nanoseconds.<br>
            limit: maximum number of trades to fetch.<br>
            params: dictionary with parameters. Valid keys:<br>
                `cursor` (str): cursor for the pagination.
                            If cursor is present then we ignore other filters.<br>
                `end_time` (int): end time in nanoseconds.<br>
        Returns:
            list of dictionaries repesenting funding rate at a point in time with fields:<br>
                `instrument` (str): instrument name.<br>
                'funding_rate' (float): funding rate.<br>
                'funding_time' (int): funding time in nanoseconds.<br>
                'mark_price' (float): mark price.<br>
        """
        payload = {"instrument": symbol}
        if params.get("cursor"):
            payload["cursor"] = params["cursor"]
        else:
            if since:
                payload["start_time"] = since
            if params.get("end_time"):
                payload["end_time"] = params["end_time"]
            if limit:
                payload["limit"] = limit

        path = get_grvt_endpoint(self.env, "GET_FUNDING")
        response: dict = self._auth_and_post(path, payload=payload)
        return response

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe="1m",
        since: int = 0,
        limit: int = 10,
        params={},
    ) -> list:
        """
        ccxt-compliant signature, HISTORICAL data.

        Retrieve the ohlc history of a given instrument.

        Args:
            symbol: The instrument name.
            timeframe: The timeframe of the ohlc. See `ccxt_interval_to_grvt_candlestick_interval`.
            since: fetch ohlc since this timestamp in nanoseconds.
            limit: maximum number of ohlc to fetch.
            params: dictionary with parameters. Valid keys:
                `cursor` (str): cursor for the pagination.
                            If cursor is present then we ignore other filters.
                `end_time` (int): end time in nanoseconds.
                `candle_type` (str): candle type. Valid values: 'TRADE', 'MARK', 'INDEX'.
        Returns:
            list of dictionaries repesenting funding rate at a point in time with fields:<br>
                `instrument` (str): instrument name.<br>
                'funding_rate' (float): funding rate.<br>
                'funding_time' (int): funding time in nanoseconds.<br>
                'mark_price' (float): mark price.<br>
        Returns:
            a list of dictionaries, each dict representing a candlestick with fields:<br>
                `instrument` - instrument name.<br>
                `open_time` - start of interval in nanoseconds.<br>
                `close_time` - end of interval in nanoseconds.<br>
                `open` - opening price.<br>
                `close` - closing price.<br>
                `high` - highest price.<br>
                `low` - lowest price.<br>
                `volume_u` - volume in units.<br>
                `volume_q` - volume in quote(USDT).<br>
                `trades` - number of trades.<br>
        """
        FN = f"{self._clsname} fetch_ohlcv"
        payload = self._get_payload_fetch_ohlcv(symbol, timeframe, since, limit, params)
        self.logger.info(f"{FN} {payload=}")
        path = get_grvt_endpoint(self.env, "GET_CANDLESTICK")
        response: dict = self._auth_and_post(path, payload=payload)
        return response
