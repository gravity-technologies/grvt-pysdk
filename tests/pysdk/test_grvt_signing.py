from pysdk import types
from pysdk.grvt_api_base import GrvtError
from pysdk.grvt_api_sync import GrvtApiSync

from .test_utils import get_config, get_test_order


def test_create_order_with_signing() -> None:
    api = GrvtApiSync(config=get_config())

    order = get_test_order(api)
    resp = api.create_order_v1(types.ApiCreateOrderRequest(order=order))

    if isinstance(resp, GrvtError):
        raise ValueError(f"Received error: {resp}")
    if resp.order is None:
        raise ValueError("Expected order to be non-null")
