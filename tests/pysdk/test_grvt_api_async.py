import asyncio

from pysdk import types
from pysdk.grvt_api_async import GrvtApiAsync
from pysdk.grvt_api_base import GrvtError

from .test_utils import get_config, get_test_order


async def get_all_instruments() -> None:
    api = GrvtApiAsync(config=get_config())
    resp = await api.get_all_instruments_v1(
        types.ApiGetAllInstrumentsRequest(is_active=True)
    )
    if isinstance(resp, GrvtError):
        raise ValueError(f"Received error: {resp}")
    if resp.result is None:
        raise ValueError("Expected results to be non-null")
    if len(resp.result) == 0:
        raise ValueError("Expected results to be non-empty")


async def open_orders() -> None:
    api = GrvtApiAsync(config=get_config())

    # Skip test if trading account id is not set
    if api.config.trading_account_id is None or api.config.api_key is None:
        return None  # Skip test if configs are not set

    resp = await api.open_orders_v1(
        types.ApiOpenOrdersRequest(
            sub_account_id=str(api.config.trading_account_id),
            kind=[types.Kind.PERPETUAL],
            base=[types.Currency.BTC, types.Currency.ETH],
            quote=[types.Currency.USDT],
        )
    )
    if isinstance(resp, GrvtError):
        api.logger.error(f"Received error: {resp}")
        return None
    if resp.result is None:
        raise ValueError("Expected orders to be non-null")
    if len(resp.result) == 0:
        api.logger.info("Expected orders to be non-empty")


async def create_order_with_signing() -> None:
    api = GrvtApiAsync(config=get_config())

    inst_resp = await api.get_all_instruments_v1(
        types.ApiGetAllInstrumentsRequest(is_active=True)
    )
    if isinstance(inst_resp, GrvtError):
        raise ValueError(f"Received error: {inst_resp}")

    order = get_test_order(api, {inst.instrument: inst for inst in inst_resp.result})
    if order is None:
        return None  # Skip test if configs are not set
    resp = await api.create_order_v1(types.ApiCreateOrderRequest(order=order))

    if isinstance(resp, GrvtError):
        raise ValueError(f"Received error: {resp}")
    if resp.result is None:
        raise ValueError("Expected order to be non-null")


def test_get_all_instruments() -> None:
    asyncio.run(get_all_instruments())


def test_open_orders() -> None:
    asyncio.run(open_orders())


def test_create_order_with_signing() -> None:
    asyncio.run(create_order_with_signing())
