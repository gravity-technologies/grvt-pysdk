# Changelog

## Version [0.1.29] - 2025-06-30

### Changes in 0.1.29

- Added new currencies: `HYPE, UNI, MOODENG, LAUNCHCOIN` in the **raw** code
- Improvements and type fixes in `fetch_funding_rate_history()` methods of GrvtCcxt and GrvtCcxtPro.

## Version [0.1.28] - 2025-06-02

### Changes in 0.1.28

- Renamed currency name `AI_16_Z` into `AI16Z` in the **raw** code to match the exchange currency name.

## Version [0.1.27] - 2025-05-19

### Changes in 0.1.27

- `GrvtCcxt` and `GrvtCcxtPro` classes:
  
  - renamed method `fetch_balances()` to `fetch_balance()` as defined in ccxt.

## Version [0.1.26] - 2025-05-15

### Added in 0.1.26

- `GrvtCcxt` and `GrvtCcxtPro` classes:
  
  - new method `describe()` - returns a list of public method names
  - new method `fetch_balances()` - returns dict with balances in ccxt format.
  - constructor parameter `order_book_ccxt_format: bool = False` . If = True then order book snapshots from `fetch_order_book()` are in ccxt format.

### Fixed in 0.1.26

- Issues with typing and lynting errors

## Version [0.1.25] - 2025-04-25

### Fixed in 0.1.25

- Issues with typing and lynting errors
- Fixed bug in test_grvt_ccxt.py
