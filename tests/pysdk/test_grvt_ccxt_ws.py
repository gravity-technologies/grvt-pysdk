import asyncio
import os
import signal
import sys
import traceback

from pysdk.grvt_ccxt_env import GrvtEnv
from pysdk.grvt_ccxt_logging_selector import logger
from pysdk.grvt_ccxt_ws import GrvtCcxtWS


# Utility functions , not called directly by the __main__ test routine
async def callback_general(message: dict) -> None:
    message.get("params", {}).get("channel")
    market = message.get("feed", {}).get("instrument")
    logger.info(f"callback_general(): market:{market} message:{message}")


async def grvt_ws_subscribe(api: GrvtCcxtWS, args_list: dict) -> None:
    """Subscribes to Websocket channels/feeds in args list."""
    for stream, (callback, params) in args_list.items():
        logger.info(f"Subscribing to {stream} {params=}")
        await api.subscribe(stream=stream, callback=callback, params=params)
        await asyncio.sleep(0)


test_api = None


async def run_test(loop):
    global test_api
    params = {
        "api_key": os.getenv("GRVT_API_KEY"),
        "trading_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
        "api_ws_version": os.getenv("GRVT_WS_STREAM_VERSION", "v1"),
    }
    if os.getenv("GRVT_PRIVATE_KEY"):
        params["private_key"] = os.getenv("GRVT_PRIVATE_KEY")
    env = GrvtEnv(os.getenv("GRVT_ENV", "dev"))

    test_api = GrvtCcxtWS(env, loop, logger, parameters=params)
    await test_api.initialize()
    pub_args_dict = {
        # ********* Market Data *********
        "mini.s": (callback_general, {"instrument": "BTC_USDT_Perp"}),
        "mini.d": (callback_general, {"instrument": "BTC_USDT_Perp"}),
        "ticker.s": (callback_general, {"instrument": "BTC_USDT_Perp"}),
        "ticker.d": (callback_general, {"instrument": "BTC_USDT_Perp"}),
        "book.s": (callback_general, {"instrument": "BTC_USDT_Perp"}),
        "book.d": (callback_general, {"instrument": "BTC_USDT_Perp"}),
        "trade": (callback_general, {"instrument": "BTC_USDT_Perp"}),
        "candle": (
            callback_general,
            {
                "instrument": "BTC_USDT_Perp",
                "interval": "CI_1_M",
                "type": "TRADE",
            },
        ),
    }
    prv_args_dict = {
        # ********* Trade Data *********
        "position": (
            callback_general,
            {
                "sub_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
                "instrument": "BTC_USDT_Perp",
            },
        ),
        "order": (
            callback_general,
            {
                "sub_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
                "instrument": "BTC_USDT_Perp",
            },
        ),
        "state": (
            callback_general,
            {
                "sub_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
                "instrument": "BTC_USDT_Perp",
            },
        ),
        "fill": (
            callback_general,
            {
                "sub_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
                "instrument": "BTC_USDT_Perp",
            },
        ),
        "deposit": (callback_general, {}),
        "transfer": (callback_general, {}),
        "withdrawal": (callback_general, {}),
    }
    try:
        if "private_key" in params:
            await grvt_ws_subscribe(test_api, {**pub_args_dict, **prv_args_dict})
        else:  # not private_key , subscribe to public feeds only
            await grvt_ws_subscribe(test_api, pub_args_dict)
    except Exception as e:
        logger.error(f"Error in grvt_ws_subscribe: {e} {traceback.format_exc()}")


async def shutdown(loop):
    """Clean up resources and stop the bot gracefully."""
    global test_api
    logger.info("Shutting down gracefully...")
    if test_api:
        for stream, message in test_api._last_message.items():
            logger.info(f"Last message: {stream=} {message=}")
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)]
    _ = [task.cancel() for task in tasks]
    logger.info(f"Cancelling {len(tasks)=}")
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Shutdown complete.")
    sys.exit(0)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))
    logger.info(f"Event loop created:{loop}.")
    loop.run_until_complete(run_test(loop))
    loop.run_forever()
    loop.close()
