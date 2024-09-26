from pysdk import types
from pysdk.grvt_api_base import GrvtError
from pysdk.grvt_api_sync import GrvtApiSync

from .test_utils import get_config, get_test_order


def test_get_all_instruments() -> None:
    api = GrvtApiSync(config=get_config())
    resp = api.get_all_instruments_v1(types.ApiGetAllInstrumentsRequest(is_active=True))
    if isinstance(resp, GrvtError):
        raise ValueError(f"Received error: {resp}")
    if resp.results is None:
        raise ValueError("Expected results to be non-null")
    if len(resp.results) == 0:
        raise ValueError("Expected results to be non-empty")


def test_open_orders() -> None:
    api = GrvtApiSync(config=get_config())

    # Skip test if trading account id is not set
    if api.config.trading_account_id is None:
        return None

    resp = api.open_orders_v1(
        types.ApiOpenOrdersRequest(
            # sub_account_id=233, Uncomment to test error path with invalid sub account id
            sub_account_id=str(api.config.trading_account_id),
            kind=[types.Kind.PERPETUAL],
            underlying=[types.Currency.BTC, types.Currency.ETH],
            quote=[types.Currency.USDT],
        )
    )
    if isinstance(resp, GrvtError):
        api.logger.error(f"Received error: {resp}")
        return None
    if resp.orders is None:
        raise ValueError("Expected orders to be non-null")
    if len(resp.orders) == 0:
        api.logger.info("Expected orders to be non-empty")


def test_create_order_with_signing() -> None:
    api = GrvtApiSync(config=get_config())

    order = get_test_order(api)
    resp = api.create_order_v1(types.ApiCreateOrderRequest(order=order))

    if isinstance(resp, GrvtError):
        raise ValueError(f"Received error: {resp}")
    if resp.order is None:
        raise ValueError("Expected order to be non-null")
