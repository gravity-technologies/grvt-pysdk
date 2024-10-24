import os
import time
import traceback

from pysdk.grvt_ccxt import GrvtCcxt
from pysdk.grvt_ccxt_env import GrvtEnv
from pysdk.grvt_ccxt_logging_selector import logger
from pysdk.grvt_ccxt_test_utils import validate_return_values
from pysdk.grvt_ccxt_utils import rand_uint32


def get_open_orders(api: GrvtCcxt) -> int:
    open_orders = api.fetch_open_orders(
        symbol="BTC_USDT_Perp",
        params={"kind": "PERPETUAL"},
    )
    logger.info(f"open_orders: {open_orders=}")
    return open_orders


def fetch_order_history(api: GrvtCcxt) -> int:
    order_history = api.fetch_order_history(
        params={"kind": "PERPETUAL", "limit": 3},
    )
    logger.info(f"order_history: {order_history=}")
    return order_history


def cancel_orders(api: GrvtCcxt, open_orders: list) -> int:
    FN = "cancel_orders"
    order_count = 0
    for order_dict in open_orders:
        client_order_id = order_dict["metadata"].get("client_order_id")
        if client_order_id:
            # Cancel
            logger.info(f"{FN} cancel order by id:{order_dict['order_id']}")
            success = api.cancel_order(id=order_dict["order_id"])
            order_count += int(success)
        else:
            logger.warning(f"{FN} client_order_id not found in {order_dict=}")
    return order_count


def cancel_all_orders(api: GrvtCcxt) -> bool:
    FN = "cancel_all_orders"
    logger.info(f"{FN} START")
    cancel_response = api.cancel_all_orders()
    logger.info(f"{FN} {cancel_response=}")
    return cancel_response


def print_instruments(api: GrvtCcxt):
    logger.info("print_instruments: START")
    if not api.markets:
        return
    for market in api.markets.values():
        logger.info(f"{market=}")
        instrument = market["instrument"]
        logger.info(f"fetch_market: {instrument=}, {api.fetch_market(instrument)}")
        logger.info(
            f"fetch_mini_ticker: {instrument=}, " f"{api.fetch_mini_ticker(instrument)}"
        )
        logger.info(f"fetch_ticker: {instrument=}, " f"{api.fetch_ticker(instrument)}")
        logger.info(
            f"fetch_order_book {instrument=}, "
            f"{api.fetch_order_book(instrument, limit=10)}"
        )
        logger.info(
            f"fetch_recent_trades {instrument=}, "
            f"{api.fetch_recent_trades(instrument, limit=5)}"
        )
        logger.info(
            f"fetch_trades {instrument=}, " f"{api.fetch_trades(instrument, limit=5)}"
        )
        logger.info(
            f"fetch_funding_rate_history {instrument=}, "
            f"{api.fetch_funding_rate_history(instrument, limit=5)}"
        )
        for type in ["TRADE", "MARK", "INDEX", "MID"]:
            ohlc = api.fetch_ohlcv(
                instrument, timeframe="5m", limit=5, params={"candle_type": type}
            )
            logger.info(f"fetch_ohlcv {type} {instrument=}, {ohlc}")


def send_order(api: GrvtCcxt, side: str, client_order_id: int) -> dict:
    price = 64_000 if side == "buy" else 65_000
    send_order_response = api.create_order(
        symbol="BTC_USDT_Perp",
        order_type="limit",
        side=side,
        amount=0.01,
        price=price,
        params={"client_order_id": client_order_id},
    )
    logger.info(f"send order: {send_order_response=} {client_order_id=}")
    return send_order_response


# Test scenarios, called by the __main__ test routine
def send_fetch_order(api: GrvtCcxt):
    client_order_id = rand_uint32()
    _ = send_order(api, side="buy", client_order_id=client_order_id)
    order_status = api.fetch_order(
        id=None,
        symbol="BTC_USDT_Perp",
        params={"client_order_id": client_order_id},
    )
    logger.info(f"result of fetch_order: {order_status=}")


def check_cancel_check_orders(api: GrvtCcxt):
    logger.info("check_cancel_check_orders: START")
    open_orders = get_open_orders(api)
    if open_orders:
        cancel_orders(api, open_orders)
        get_open_orders(api)


def fetch_my_trades(api: GrvtCcxt):
    logger.info("fetch_my_trades: START")
    my_trades = api.fetch_my_trades(
        symbol="BTC_USDT_Perp",
        limit=10,
        params={},
    )
    logger.info(f"my_trades: num trades:{len(my_trades)}")
    logger.info(f"my_trades: {my_trades=}")


def send_cancel_order(api: GrvtCcxt):
    logger.info("send_cancel_order: START")
    order_response = send_order(api, side="sell", client_order_id=rand_uint32())
    if order_response:
        # Get status
        client_order_id = order_response.get("metadata", {}).get("client_order_id")
        logger.info(f"fetch_order by {client_order_id=}")
        order_status = api.fetch_order(params={"client_order_id": client_order_id})
        logger.info(f"{order_status=}")
        # Cancel
        time.sleep(10)
        logger.info(f"cancel order by {client_order_id=}")
        success = api.cancel_order(params={"client_order_id": client_order_id})
        logger.info(f"cancel_order: {success=}")
    else:
        logger.warning("send_cancel_order: order_response is None")


def print_markets(api: GrvtCcxt):
    logger.info("print_markets: START")
    if api.markets:
        logger.info(f"MARKETS:{len(api.markets)}")
        for market in api.markets.values():
            logger.info(f"MARKET:{market}")


def fetch_all_markets(api: GrvtCcxt):
    logger.info("fetch_all_markets: START")
    instruments = api.fetch_all_markets()
    logger.info(f"fetch_all_markets: num instruments={len(instruments)}")


def print_account_summary(api: GrvtCcxt):
    try:
        logger.info(
            f"sub-account summary:\n{api.get_account_summary(type='sub-account')}"
        )
        logger.info(
            f"funding-account summary:\n{api.get_account_summary(type='funding')}"
        )
        logger.info(
            f"aggregated-account summary:\n{api.get_account_summary(type='aggregated')}"
        )
    except Exception as e:
        logger.error(f"account summary failed: {e}")


def print_account_history(api: GrvtCcxt):
    try:
        hist = api.fetch_account_history(params={})
        logger.info(f"account history:\n{hist}")
    except Exception as e:
        logger.error(f"account history failed: {e}")


def print_positions(api: GrvtCcxt):
    try:
        logger.info(f"positions:\n{api.fetch_positions(symbols=['BTC_USDT_Perp'])}")
    except Exception as e:
        logger.error(f"positions failed: {e}")


def test_grvt_ccxt():
    params = {
        "api_key": os.getenv("GRVT_API_KEY"),
        "trading_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
        "private_key": os.getenv("GRVT_PRIVATE_KEY"),
    }
    env = GrvtEnv(os.getenv("GRVT_ENV", "testnet"))
    test_api = GrvtCcxt(env, logger, parameters=params)
    function_list = [
        fetch_all_markets,
        print_markets,
        print_instruments,
        print_account_summary,
        print_account_history,
        # print_positions,
        # -------- TRADE related
        # fetch_my_trades,
        fetch_order_history,
        # # -------- order related
        send_fetch_order,
        fetch_my_trades,
        print_positions,
        check_cancel_check_orders,
        send_cancel_order,
        get_open_orders,
        send_fetch_order,
        get_open_orders,
        cancel_all_orders,
        get_open_orders,
    ]
    for f in function_list:  # [get_open_orders]:
        try:
            f(test_api)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e} {traceback.format_exc()}")
    validate_return_values(test_api, "test_results_sync.csv")


if __name__ == "__main__":
    test_grvt_ccxt()
