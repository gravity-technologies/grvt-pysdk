import logging
import os
import random
import time

from pysdk import grvt_raw_types
from pysdk.grvt_raw_base import GrvtApiConfig
from pysdk.grvt_raw_env import GrvtEnv
from pysdk.grvt_raw_signing import sign_order
from pysdk.grvt_raw_sync import GrvtRawSync


def get_config() -> GrvtApiConfig:
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    conf = GrvtApiConfig(
        env=GrvtEnv(os.getenv("GRVT_ENV", "testnet")),
        trading_account_id=os.getenv("GRVT_SUB_ACCOUNT_ID"),
        private_key=os.getenv("GRVT_PRIVATE_KEY"),
        api_key=os.getenv("GRVT_API_KEY"),
        logger=logger,
    )
    logger.debug(conf)
    return conf


def get_test_order(
    api: GrvtRawSync, instruments: dict[str, grvt_raw_types.Instrument]
) -> grvt_raw_types.Order | None:
    # Skip test if configs are not set
    if (
        api.config.trading_account_id is None
        or api.config.private_key is None
        or api.config.api_key is None
    ):
        return None

    order = grvt_raw_types.Order(
        sub_account_id=str(api.config.trading_account_id),
        time_in_force=grvt_raw_types.TimeInForce.GOOD_TILL_TIME,
        legs=[
            grvt_raw_types.OrderLeg(
                instrument="BTC_USDT_Perp",
                size="1.2",  # 1.2 BTC
                limit_price="64170.7",  # 80,000 USDT
                is_buying_asset=True,
            )
        ],
        signature=grvt_raw_types.Signature(
            signer="",  # Populated by sign_order
            r="",  # Populated by sign_order
            s="",  # Populated by sign_order
            v=0,  # Populated by sign_order
            expiration=str(time.time_ns() + 20 * 24 * 60 * 60 * 1_000_000_000),  # 20 days
            nonce=random.randint(0, 2**32 - 1),
        ),
        metadata=grvt_raw_types.OrderMetadata(
            client_order_id=str(random.randint(0, 2**32 - 1)),
        ),
    )
    return sign_order(order, api.config, api.account, instruments)
