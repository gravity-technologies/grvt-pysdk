# GRVT SDK

## Introduction

**GRVT SDK** is a Python-based library that provides easy access to trade-realted APIs of grvt.io

--
> :warning: **Warning**
GRVT SDK is in Beta version and will undergo significant changes until stable production version.

## Dependencies

- Python 3.9 and above
- Libraries: see `requirements.txt`

## Setup and Configuration

1. **Install the required libraries**:

    ```bash
    % pip install -r requirements.txt
    ```

2. **Set up environment variables**:

    ```bash
        export GRVT_PRIVATE_KEY="<Secret Private Key of your APi Key>"
        export GRVT_API_KEY="<API Key>"
        export GRVT_TRADING_ACCOUNT_ID=<Trading account ID>
        export GRVT_ENV="testnet"
        export GRVT_END_POINT_VERSION="v1"
        export GRVT_WS_STREAM_VERSION="v1"
    ```

## How to Run Tests of SDK

1. **Test sync calls to Rest APIs**:

    ```bash
    % python3 test_grvt_cctx.py
    ```

    A. See if there are wany `WARNING` or `ERROR` messages in the output.
    B. Check the following lines at the end of the run :

    ```bash
    ... INFO - validate_return_values: short_name='CREATE_ORDER', endpoint='https://trades.dev.gravitymarkets.io/full/v1/create_order', not called
    ... INFO - validate_return_values: short_name='CANCEL_ALL_ORDERS', endpoint='https://trades.dev.gravitymarkets.io/full/v1/cancel_all_orders', check_result='OK'
    ... INFO - validate_return_values: short_name='CANCEL_ORDER', endpoint='https://trades.dev.gravitymarkets.io/full/v1/cancel_order', not called
    ...
    ```

    Verify that all endpoints should `check_result='OK'`

2. **Test async calls to Rest APIs**:

    ```bash
    % python3 test_grvt_cctx_pro.py
    ```

    A. See if there are wany `WARNING` or `ERROR` messages in the output.
    B. Check the following lines at the end of the run :

    ```bash
    ... INFO - validate_return_values: short_name='CREATE_ORDER', endpoint='https://trades.dev.gravitymarkets.io/full/v1/create_order', not called
    ... INFO - validate_return_values: short_name='CANCEL_ALL_ORDERS', endpoint='https://trades.dev.gravitymarkets.io/full/v1/cancel_all_orders', check_result='OK'
    ... INFO - validate_return_values: short_name='CANCEL_ORDER', endpoint='https://trades.dev.gravitymarkets.io/full/v1/cancel_order', not called
    ...
    ```

    Verify that all endpoints should `check_result='OK'`

3. **Test Web Sockets**:

    ```bash
    % python3 test_grvt_cctx_ws.py
    ```

    A. See if there are wany `WARNING` or `ERROR` messages in the output.
    B. Check the following lines at the end of the run :

    ```bash
    ... INFO - Last message: stream='v1.book.d' message={'stream': 'v1.book.d', 'selector': 'BTC_USDT_Perp@500-10-1', 'sequence_number': '3', 'feed': {...}}
    ... INFO - Last message: stream='v1.trade' message={'stream': 'v1.trade', 'selector': 'v1.trade-full-BTC_USDT_Perp-100', 'sequence_number': '1', 'feed': {...}}
    ... INFO - Last message: stream='v1.candle' message={}
    ... INFO - Last message: stream='v1.position' message={'stream': 'v1.position', 'selector': 'v1.position-full-4005936244055728-BTC_USDT_Perp-a', 'sequence_number': '0', 'feed': {...}}
    ...
    ```

    Verify that all streams that you expect to have messages for do have messages.

## SDK Design - TBD
