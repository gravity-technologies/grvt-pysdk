import asyncio
import os

from pysdk import types
from pysdk.grvt_api_async import GrvtApiAsync
from pysdk.grvt_api_base import GrvtApiConfig, GrvtError
from pysdk.grvt_env import GrvtEnv


def get_config() -> GrvtApiConfig:
    conf = GrvtApiConfig(
        env=GrvtEnv(os.getenv("GRVT_ENV", "dev")),
        trading_account_id=os.getenv("GRVT_SUB_ACCOUNT_ID"),
        private_key=os.getenv("GRVT_PRIVATE_KEY"),
        api_key=os.getenv("GRVT_API_KEY"),
        logger=None,
    )
    print(conf)  # noqa: T201
    return conf


async def get_all_instruments() -> None:
    api = GrvtApiAsync(config=get_config())
    resp = await api.get_all_instruments_v1(
        types.ApiGetAllInstrumentsRequest(is_active=True)
    )
    if isinstance(resp, GrvtError):
        raise ValueError(f"Received error: {resp}")
    if resp.results is None:
        raise ValueError("Expected results to be non-null")
    if len(resp.results) == 0:
        raise ValueError("Expected results to be non-empty")


async def open_orders() -> None:
    api = GrvtApiAsync(config=get_config())

    # Skip test if trading account id is not set
    if api.config.trading_account_id is None:
        return None

    resp = await api.open_orders_v1(
        types.ApiOpenOrdersRequest(
            sub_account_id=str(api.config.trading_account_id),
            kind=[types.Kind.PERPETUAL],
            underlying=[types.Currency.BTC, types.Currency.ETH],
            quote=[types.Currency.USDT],
        )
    )
    if isinstance(resp, GrvtError):
        print(f"Received error: {resp}")  # noqa: T201
        return None
    if resp.orders is None:
        raise ValueError("Expected orders to be non-null")
    if len(resp.orders) == 0:
        print("Expected orders to be non-empty")  # noqa: T201


def test_get_all_instruments() -> None:
    asyncio.run(get_all_instruments())


def test_open_orders() -> None:
    asyncio.run(open_orders())
