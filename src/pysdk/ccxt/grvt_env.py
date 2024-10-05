# ruff: noqa: D200
# ruff: noqa: D204
# ruff: noqa: D205
# ruff: noqa: D404
# ruff: noqa: W291
# ruff: noqa: D400
# ruff: noqa: E501

import os
from enum import Enum


class GrvtEnv(str, Enum):
    TESTNET = "testnet"
    DEV = "dev"
    PROD = "prod"


# GrvtEndpointType defines the root path for a family of endpoints
class GrvtEndpointType(str, Enum):
    EDGE = "edge"
    TRADE_DATA = "tdg"
    MARKET_DATA = "mdg"


END_POINT_VERSION = os.getenv("GRVT_END_POINT_VERSION", "v0")


def get_grvt_endpoint_domains(env_name: str) -> dict[GrvtEndpointType, str]:
    if env_name == GrvtEnv.PROD.value:
        return {
            GrvtEndpointType.EDGE: "https://edge.grvt.io",
            GrvtEndpointType.TRADE_DATA: "https://trades.grvt.io",
            GrvtEndpointType.MARKET_DATA: "https://market-data.grvt.io",
        }
    if env_name == GrvtEnv.TESTNET.value:
        return {
            GrvtEndpointType.EDGE: f"https://edge.{env_name}.grvt.io",
            GrvtEndpointType.TRADE_DATA: f"https://trades.{env_name}.grvt.io",
            GrvtEndpointType.MARKET_DATA: f"https://market-data.{env_name}.grvt.io",
        }
    if env_name == GrvtEnv.DEV.value:
        return {
            GrvtEndpointType.EDGE: f"https://edge.{env_name}.gravitymarkets.io",
            GrvtEndpointType.TRADE_DATA: f"https://trades.{env_name}.gravitymarkets.io",
            GrvtEndpointType.MARKET_DATA: f"https://market-data.{env_name}.gravitymarkets.io",
        }
    return {}


def get_grvt_ws_endpoint(
    env: str,
    endpoint_type: GrvtEndpointType,
) -> str | None:
    """Returns string pointing to WS endpoint for given environment and endpoint type."""
    if env == GrvtEnv.PROD.value:
        return {
            GrvtEndpointType.TRADE_DATA: "wss://trades.grvt.io/ws",
            GrvtEndpointType.MARKET_DATA: "wss://market-data.grvt.io/ws",
        }.get(endpoint_type)
    if env == GrvtEnv.TESTNET.value:
        return {
            GrvtEndpointType.TRADE_DATA: f"wss://trades.{env}.grvt.io/ws",
            GrvtEndpointType.MARKET_DATA: f"wss://market-data.{env}.grvt.io/ws",
        }.get(endpoint_type)
    if env == GrvtEnv.DEV.value:
        return {
            GrvtEndpointType.TRADE_DATA: f"wss://trades.{env}.gravitymarkets.io/ws",
            GrvtEndpointType.MARKET_DATA: f"wss://market-data.{env}.gravitymarkets.io/ws",
        }.get(endpoint_type)
    return None


GRVT_WS_STREAMS = {
    # ******* Market Data ********
    "mini.s": GrvtEndpointType.MARKET_DATA,
    "mini.d": GrvtEndpointType.MARKET_DATA,
    "ticker.s": GrvtEndpointType.MARKET_DATA,
    "ticker.d": GrvtEndpointType.MARKET_DATA,
    "book.s": GrvtEndpointType.MARKET_DATA,
    "book.d": GrvtEndpointType.MARKET_DATA,
    "trade": GrvtEndpointType.MARKET_DATA,
    "candle": GrvtEndpointType.MARKET_DATA,
    # ******* Trade Data ********
    "order": GrvtEndpointType.TRADE_DATA,
    "state": GrvtEndpointType.TRADE_DATA,
    "position": GrvtEndpointType.TRADE_DATA,
    "fill": GrvtEndpointType.TRADE_DATA,
    "transfer": GrvtEndpointType.TRADE_DATA,
    "deposit": GrvtEndpointType.TRADE_DATA,
    "withdrawal": GrvtEndpointType.TRADE_DATA,
}


# "wss://market-data.testnet.grvt.io/ws"
#  wss://trades.testnet.grvt.io/ws
# GRVT_ENDPOINTS defines the endpoint paths grouped by endpoint type
GRVT_ENDPOINTS = {
    GrvtEndpointType.EDGE: {
        "GRAPHQL": "query",
        "AUTH": "auth/api_key/login",
    },
    GrvtEndpointType.TRADE_DATA: {
        "CREATE_ORDER": f"full/{END_POINT_VERSION}/create_order",
        "CANCEL_ALL_ORDERS": f"full/{END_POINT_VERSION}/cancel_all_orders",
        "CANCEL_ORDER": f"full/{END_POINT_VERSION}/cancel_order",
        "GET_OPEN_ORDERS": f"full/{END_POINT_VERSION}/open_orders",
        "GET_ACCOUNT_SUMMARY": f"full/{END_POINT_VERSION}/account_summary",
        "GET_FUNDING_ACCOUNT_SUMMARY": f"full/{END_POINT_VERSION}/funding_account_summary",
        "GET_AGGREGATED_ACCOUNT_SUMMARY": f"full/{END_POINT_VERSION}/aggregated_account_summary",
        "GET_ACCOUNT_HISTORY": f"full/{END_POINT_VERSION}/account_history",
        "GET_POSITIONS": f"full/{END_POINT_VERSION}/positions",
        "GET_ORDER": f"full/{END_POINT_VERSION}/order",
        "GET_ORDER_HISTORY": f"full/{END_POINT_VERSION}/order_history",
        "GET_FILL_HISTORY": f"full/{END_POINT_VERSION}/fill_history",
    },
    GrvtEndpointType.MARKET_DATA: {
        "GET_ALL_INSTRUMENTS": f"full/{END_POINT_VERSION}/all_instruments",
        "GET_INSTRUMENTS": f"full/{END_POINT_VERSION}/instruments",
        "GET_INSTRUMENT": f"full/{END_POINT_VERSION}/instrument",
        "GET_TICKER": f"full/{END_POINT_VERSION}/ticker",
        "GET_MINI_TICKER": f"full/{END_POINT_VERSION}/mini",
        "GET_ORDER_BOOK": f"full/{END_POINT_VERSION}/book",
        "GET_TRADES": f"full/{END_POINT_VERSION}/trade",
        "GET_TRADE_HISTORY": f"full/{END_POINT_VERSION}/trade_history",
        "GET_FUNDING": f"full/{END_POINT_VERSION}/funding",
        "GET_CANDLESTICK": f"full/{END_POINT_VERSION}/kline",
    },
}


def get_grvt_endpoint(environment: GrvtEnv, end_point: str) -> str | None:
    # if end_point == "GET_ALL_INSTRUMENTS":
    #     return "https://market-data.testnet.grvt.io/full/v1/instruments"
    endpoint_domains = get_grvt_endpoint_domains(environment.value)
    for endpoints_type, endpoints in GRVT_ENDPOINTS.items():
        if end_point in endpoints:
            return f"{endpoint_domains[endpoints_type]}/{endpoints[end_point]}"
    return None


def get_all_grvt_endpoints(environment: GrvtEnv) -> dict[str, str]:
    endpoint_domains = get_grvt_endpoint_domains(environment.value)
    endpoints = {}
    for endpoints_type, endpoints_map in GRVT_ENDPOINTS.items():
        for endpoint, path in endpoints_map.items():
            endpoints[endpoint] = f"{endpoint_domains[endpoints_type]}/{path}"
    return endpoints


CHAIN_IDS = {
    GrvtEnv.DEV.value: 327,
    GrvtEnv.TESTNET.value: 326,
}

########################################################
