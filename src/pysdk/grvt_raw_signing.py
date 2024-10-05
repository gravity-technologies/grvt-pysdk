from enum import Enum

from eth_account import Account
from eth_account.messages import encode_typed_data

from .grvt_raw_base import GrvtApiConfig, GrvtEnv
from .grvt_raw_types import Instrument, Order, TimeInForce

#########################
# INSTRUMENT CONVERSION #
#########################


PRICE_MULTIPLIER = 1_000_000_000


class SignTimeInForce(Enum):
    GOOD_TILL_TIME = 1
    ALL_OR_NONE = 2
    IMMEDIATE_OR_CANCEL = 3
    FILL_OR_KILL = 4


TIME_IN_FORCE_TO_SIGN_TIME_IN_FORCE = {
    TimeInForce.GOOD_TILL_TIME: SignTimeInForce.GOOD_TILL_TIME,
    TimeInForce.ALL_OR_NONE: SignTimeInForce.ALL_OR_NONE,
    TimeInForce.IMMEDIATE_OR_CANCEL: SignTimeInForce.IMMEDIATE_OR_CANCEL,
    TimeInForce.FILL_OR_KILL: SignTimeInForce.FILL_OR_KILL,
}


#####################
# EIP-712 chain IDs #
#####################
CHAIN_IDS = {
    GrvtEnv.DEV: 327,
    GrvtEnv.TESTNET: 326,
}


def get_EIP712_domain_data(env: GrvtEnv) -> dict[str, str | int]:
    return {
        "name": "GRVT Exchange",
        "version": "0",
        "chainId": CHAIN_IDS[env],
    }


EIP712_ORDER_MESSAGE_TYPE = {
    "Order": [
        {"name": "subAccountID", "type": "uint64"},
        {"name": "isMarket", "type": "bool"},
        {"name": "timeInForce", "type": "uint8"},
        {"name": "postOnly", "type": "bool"},
        {"name": "reduceOnly", "type": "bool"},
        {"name": "legs", "type": "OrderLeg[]"},
        {"name": "nonce", "type": "uint32"},
        {"name": "expiration", "type": "int64"},
    ],
    "OrderLeg": [
        {"name": "assetID", "type": "uint256"},
        {"name": "contractSize", "type": "uint64"},
        {"name": "limitPrice", "type": "uint64"},
        {"name": "isBuyingContract", "type": "bool"},
    ],
}


def sign_order(
    order: Order,
    config: GrvtApiConfig,
    account: Account,
    instruments: dict[str, Instrument],
) -> Order:
    if config.private_key is None:
        raise ValueError("Private key is not set")

    legs = []
    for leg in order.legs:
        instrument = instruments[leg.instrument]
        size_multiplier = 10**instrument.base_decimals
        legs.append(
            {
                "assetID": instrument.instrument_hash,
                "contractSize": int(float(leg.size) * size_multiplier),
                "limitPrice": int(float(leg.limit_price) * PRICE_MULTIPLIER),
                "isBuyingContract": leg.is_buying_asset,
            }
        )
    message_data = {
        "subAccountID": order.sub_account_id,
        "isMarket": order.is_market or False,
        "timeInForce": TIME_IN_FORCE_TO_SIGN_TIME_IN_FORCE[order.time_in_force].value,
        "postOnly": order.post_only or False,
        "reduceOnly": order.reduce_only or False,
        "legs": legs,
        "nonce": order.signature.nonce,
        "expiration": order.signature.expiration,
    }
    domain_data = get_EIP712_domain_data(config.env)
    signature = encode_typed_data(domain_data, EIP712_ORDER_MESSAGE_TYPE, message_data)
    signed_message = account.sign_message(signature)
    order.signature.r = "0x" + hex(signed_message.r)[2:].zfill(64)
    order.signature.s = "0x" + hex(signed_message.s)[2:].zfill(64)
    order.signature.v = signed_message.v
    order.signature.signer = str(account.address)
    return order
