import logging
import pytest
from eth_account import Account

from pysdk.grvt_raw_signing import sign_order
from pysdk.grvt_raw_base import GrvtApiConfig
from pysdk.grvt_raw_env import GrvtEnv
from pysdk.grvt_raw_types import Currency, Kind, Order, OrderMetadata, OrderLeg, Signature, Instrument, TimeInForce, InstrumentSettlementPeriod


def test_sign_order_table():
    # Setup logger
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    private_key = "f7934647276a6e1fa0af3f4467b4b8ddaf45d25a7368fa1a295eef49a446819d"
    sub_account_id = "8289849667772468"
    expiry = 1730800479321350000
    nonce = 828700936

    test_cases = [
        {
            "name": "test decimal precision 1, 3 decimals",
            "order": Order(
                metadata=OrderMetadata(
                    client_order_id="1", create_time="1730800479321350000"),
                sub_account_id=sub_account_id,
                time_in_force=TimeInForce.GOOD_TILL_TIME,
                post_only=False,
                is_market=False,
                reduce_only=False,
                legs=[
                    OrderLeg(
                        instrument="BTC_USDT_Perp",
                        size="1.013",
                        limit_price="68900.5",
                        is_buying_asset=False
                    )
                ],
                signature=Signature(
                    signer='',
                    r='',
                    s='',
                    v=0,
                    expiration=expiry,
                    nonce=nonce
                )
            ),
            "want_r": "0xb00512d986a718b15136a8ba23de1c1ec84bbdb9958629cbbe4909bae620bb04",
            "want_s": "0x79f706de61c68cc14d7734594b5d8689df2b2a7b25951f9a3f61d799f4327ffc",
            "want_v": 28,
            "want_error": None
        },
        {
            "name": "test decimal precision 2, 9 decimals",
            "order": Order(
                metadata=OrderMetadata(
                    client_order_id="1", create_time="1730800479321350000"),
                sub_account_id=sub_account_id,
                time_in_force=TimeInForce.GOOD_TILL_TIME,
                post_only=False,
                is_market=False,
                reduce_only=False,
                legs=[
                    OrderLeg(
                        instrument="BTC_USDT_Perp",
                        size="1.123123123",
                        limit_price="68900.777123479",
                        is_buying_asset=False
                    )
                ],
                signature=Signature(
                    signer='',
                    r='',
                    s='',
                    v=0,
                    expiration=expiry,
                    nonce=nonce
                )
            ),
            "want_r": "0x365ec79d299c8bcd5f2acff89faf741a90ca02a4b8a6b1b1a5d4f3d16130f9f0",
            "want_s": "0x465129bca7855f008ea5bc22fe3ee630e4a8e3b9b99c1745631deef29957048a",
            "want_v": 28,
            "want_error": None
        },
        {
            "name": "test decimal precision 3, round down",
            "order": Order(
                metadata=OrderMetadata(
                    client_order_id="1", create_time="1730800479321350000"),
                sub_account_id=sub_account_id,
                time_in_force=TimeInForce.GOOD_TILL_TIME,
                post_only=False,
                is_market=False,
                reduce_only=False,
                legs=[
                    OrderLeg(
                        instrument="BTC_USDT_Perp",
                        size="1.1231231234",
                        limit_price="68900.7771234794",
                        is_buying_asset=False
                    )
                ],
                signature=Signature(
                    signer='',
                    r='',
                    s='',
                    v=0,
                    expiration=expiry,
                    nonce=nonce
                )
            ),
            "want_r": "0x365ec79d299c8bcd5f2acff89faf741a90ca02a4b8a6b1b1a5d4f3d16130f9f0",
            "want_s": "0x465129bca7855f008ea5bc22fe3ee630e4a8e3b9b99c1745631deef29957048a",
            "want_v": 28,
            "want_error": None
        },
        {
            "name": "test decimal precision 4, round down",
            "order": Order(
                metadata=OrderMetadata(
                    client_order_id="1", create_time="1730800479321350000"),
                sub_account_id=sub_account_id,
                time_in_force=TimeInForce.GOOD_TILL_TIME,
                post_only=False,
                is_market=False,
                reduce_only=False,
                legs=[
                    OrderLeg(
                        instrument="BTC_USDT_Perp",
                        size="1.1231231239",
                        limit_price="68900.7771234799",
                        is_buying_asset=False
                    )
                ],
                signature=Signature(
                    signer='',
                    r='',
                    s='',
                    v=0,
                    expiration=expiry,
                    nonce=nonce
                )
            ),
            "want_r": "0x365ec79d299c8bcd5f2acff89faf741a90ca02a4b8a6b1b1a5d4f3d16130f9f0",
            "want_s": "0x465129bca7855f008ea5bc22fe3ee630e4a8e3b9b99c1745631deef29957048a",
            "want_v": 28,
            "want_error": None
        },
        # {
        #     "name": "no private key",
        #     "order": Order(),
        #     "want_error": ValueError("Private key is not set")
        # },
        # {
        #     "name": "decimal precision test",
        #     "order": Order(
        #         sub_account_id="123",
        #         time_in_force=TimeInForce.GOOD_TILL_TIME,
        #         legs=[
        #             OrderLeg(
        #                 instrument="BTC_USDT_Perp",
        #                 size="1.013",
        #                 limit_price="64170.7",
        #                 is_buying_asset=True
        #             )
        #         ],
        #         signature=Signature(
        #             expiration=expiry,
        #             nonce=nonce
        #         )
        #     ),
        #     "want_error": None
        # }
    ]

    account = Account.from_key(private_key)

    instruments = {
        "BTC_USDT_Perp": Instrument(
            instrument="BTC_USDT_Perp",
            instrument_hash="0x030501",
            base=Currency.BTC,
            quote=Currency.USDT,
            kind=Kind.PERPETUAL,
            venues=[],
            settlement_period=InstrumentSettlementPeriod.DAILY,
            tick_size="0.00000001",
            min_size="0.00000001",
            create_time="123",
            base_decimals=9,
            quote_decimals=9,
            max_position_size="1000000",
        )
    }

    for tc in test_cases:
        config = GrvtApiConfig(
            env=GrvtEnv.TESTNET,
            private_key=private_key,
            trading_account_id=sub_account_id,
            api_key="not-needed",
            logger=logger
        )

        signed_order = sign_order(tc["order"], config, account, instruments)
        print(signed_order)

        # Verify signature fields are populated
        assert signed_order.signature.signer == str(account.address)

        # Compare r, s, v values with expected values
        if "want_r" in tc:
            assert signed_order.signature.r == tc[
                "want_r"], f"Test '{tc['name']}' failed: r value mismatch"
        if "want_s" in tc:
            assert signed_order.signature.s == tc[
                "want_s"], f"Test '{tc['name']}' failed: s value mismatch"
        if "want_v" in tc:
            assert signed_order.signature.v == tc[
                "want_v"], f"Test '{tc['name']}' failed: v value mismatch"
