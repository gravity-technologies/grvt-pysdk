import logging
import random
import time
from pprint import pprint

from pysdk.grvt_raw_base import GrvtError, GrvtApiConfig
from pysdk.grvt_raw_signing import sign_transfer
from pysdk.grvt_raw_sync import GrvtRawSync
from pysdk.grvt_raw_types import Currency, Signature, Transfer, ApiTransferRequest

from test_raw_utils import get_config


# Setup logger
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    config = get_config()
    api = GrvtRawSync(config)
    funding_account_address = input("From account address: ")
    if not funding_account_address:
        raise ValueError("From account address is required")
    _transfer = Transfer(
        from_account_id=funding_account_address,
        from_sub_account_id=(input("From sub account ID: ") or "0"),
        to_account_id=(input("To address: ") or funding_account_address),
        to_sub_account_id=(input("To sub account ID: ") or "0"),
        currency=Currency.USDT,
        num_tokens=(input("Transfer amount (USDT - default 1): ") or "1"),
        signature=Signature(
            signer="",
            r="",
            s="",
            v=0,
            expiration=str(time.time_ns() + 20 * 24 * 60 * 60 * 1_000_000_000),  # 20 days
            nonce=random.randint(0, 2**32 - 1),
        ),
    )
    
    pprint(_transfer)

    transfer = sign_transfer(
        _transfer,
        api.config,
        api.account,
    )

    pprint(transfer)

    resp = api.transfer_v1(
        ApiTransferRequest(
            transfer.from_account_id,
            transfer.from_sub_account_id,
            transfer.to_account_id,
            transfer.to_sub_account_id,
            transfer.currency,
            transfer.num_tokens,
            transfer.signature,
        )
    )

    pprint(resp)

    if isinstance(resp, GrvtError):
        raise ValueError(f"Received error: {resp}")
    if resp.result is None:
        raise ValueError("Expected order to be non-null")


if __name__ == "__main__":
    main()
