import asyncio
import os
import signal
import sys
import traceback
import logging

from pysdk.grvt_ccxt_env import GrvtEnv
from pysdk.grvt_ccxt_logging_selector import logger
from pysdk.grvt_base_ws_async import GrvtBaseWSAsync
from pysdk.grvt_base_ws_async import MiniTickerSnapStreamer
from pysdk.grvt_base_ws_async import GrvtMiniTickerParams
from pysdk.grvt_base_ws_async import GrvtTickerInterval
from pysdk import grvt_raw_types


## general example of a notifier class
class OurMessageHandler:
    def __init__(
        self,
        logger: logging.Logger,
    ):
        self.logger = logger

    def handle_mini_ticker_snapshot(self, data: grvt_raw_types.WSMiniTickerFeedDataV1, 
                                    subscription_id: int):
        self.logger.info(f"handle_mini_ticker_snapshot: {data} {subscription_id}")

    def handle_mini_ticker_delta(self, data: grvt_raw_types.WSMiniTickerFeedDataV1, 
                                 subscription_id: int):
        self.logger.info(f"handle_mini_ticker_snapshot: {data} {subscription_id}")

    def handle_error(self, error: grvt_raw_types.GrvtError):
        self.logger.info(f"handle_mini_ticker_snapshot: {error}")


async def test_miniticker_stream(loop):
    global test_api
    params = {
        "api_key": os.getenv("GRVT_API_KEY"),
        "trading_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
        "api_ws_version": os.getenv("GRVT_WS_STREAM_VERSION", "v1"),
    }
    if os.getenv("GRVT_PRIVATE_KEY"):
        params["private_key"] = os.getenv("GRVT_PRIVATE_KEY")
    env = GrvtEnv(os.getenv("GRVT_ENV", "dev"))

    test_api = GrvtBaseWSAsync(env, loop, logger, parameters=params)
    message_handler = OurMessageHandler(logger)
    mini_ticker_streamer = MiniTickerSnapStreamer(message_handler)
    await test_api.initialize()

    mini_ticker_params = GrvtMiniTickerParams("BTC_USDT_Perp", 
                                              GrvtTickerInterval.INTERVAL_500)
    await test_api.subscribe(mini_ticker_streamer, 1, mini_ticker_params)


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
    loop.run_until_complete(test_miniticker_stream(loop))
    loop.run_forever()
    loop.close()

