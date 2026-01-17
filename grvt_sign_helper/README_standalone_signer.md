# GRVT Order Signer - Standalone Script

A standalone Python script for signing GRVT orders with zero dependencies to the GRVT SDK. This script allows users to sign orders by providing their environment, private key, and order payload.

## Features

- ✅ Zero dependencies to the GRVT SDK repository
- ✅ Support for all GRVT environments (dev, staging, testnet, production)
- ✅ EIP-712 compliant order signing
- ✅ Interactive command-line interface
- ✅ Detailed output showing payload to sign and signature components
- ✅ A step by step on how to implement order siginng in python (check out `grvt_order_signer.py`)

## Installation

1. Install the required dependency:

```bash
pip install -r requirements_standalone.txt
```

## Usage

### Quick Start with Example Files

1. Install dependencies:

```bash
pip install -r requirements_standalone.txt
```

2. Run the script and use the example files:

```bash
python grvt_order_signer.py
```

3. When prompted:
   - Select environment (e.g., 3 for testnet)
   - Enter your private key
   - Choose option 1 for order data (use default create_order_data.json)
   - Choose option 1 for instruments data (fetch from API) - this will get the latest instruments automatically

### Manual Usage

Run the script:

```bash
python grvt_order_signer.py
```

The script will prompt you for:

1. **Environment**: Choose from dev, staging, testnet, or production
2. **Private Key**: Your wallet's private key in hex format
3. **Order Data**: JSON payload containing order details (can use default file, load from custom file, or enter manually)
4. **Instruments Data**: JSON payload containing instrument metadata (can be fetched from API, loaded from file, or entered manually)

## Input Methods

The script supports multiple input methods:

### Order Data Input:

1. **Default File**: Use the included `create_order_data.json` file (recommended for quick start)
2. **Custom JSON File**: Load data from a custom JSON file
3. **Manual Input**: Enter JSON data directly in the terminal

### Instruments Data Input:

1. **API Fetch**: Fetch latest instruments from GRVT API (recommended)
2. **JSON File Input**: Load data from a JSON file
3. **Manual Input**: Enter JSON data directly in the terminal

### Example Files

The repository includes example files to help you get started:

- `create_order_data.json` - Sample order data with the correct schema
- `example_instruments.json` - Sample instruments data

## Example

### Order Data Format

```json
{
  "order": {
    "sub_account_id": "YOUR_GRVT_SUBACCOUNT_ID",
    "is_market": false,
    "time_in_force": "GOOD_TILL_TIME",
    "post_only": false,
    "reduce_only": false,
    "legs": [
      {
        "instrument": "BTC_USDT_Perp",
        "size": "1.5",
        "limit_price": "115038.01",
        "is_buying_asset": true
      }
    ],
    "signature": {
      "expiration": "1697788800000000000",
      "nonce": 1234567890
    },
    "metadata": {
      "client_order_id": "23042"
    }
  }
}
```

### Instruments Data Format

```json
{
  "BTC_USDT_Perp": {
    "instrument_hash": "0x030501",
    "base_decimals": 9
  }
}
```

## Output

The script will display:

- **Signer**: The wallet address that signed the order
- **R, S, V**: Signature components
- **Payload to Sign**: The complete EIP-712 payload that was signed
- **Complete Signature**: The final signature object
- **Complete Order Payload**: The complete order with signature included, ready for API submission

### Complete Order Payload

The complete order payload includes all the original order data plus the signature components (r, s, v, signer). This payload is ready to be submitted directly to the GRVT API. The structure looks like:

```json
{
  "order": {
    "sub_account_id": "YOUR_GRVT_SUBACCOUNT_ID",
    "is_market": false,
    "time_in_force": "GOOD_TILL_TIME",
    "post_only": false,
    "reduce_only": false,
    "legs": [...],
    "signature": {
      "r": "0x...",
      "s": "0x...",
      "v": 27,
      "expiration": "1697788800000000000",
      "nonce": 1234567890,
      "signer": "0x..."
    },
    "metadata": {
      "client_order_id": "23042"
    }
  }
}
```

## Supported Environments

| Environment | Chain ID | API Endpoint                                                            | Description             |
| ----------- | -------- | ----------------------------------------------------------------------- | ----------------------- |
| dev         | 327      | `https://market-data.dev.gravitymarkets.io/full/v1/all_instruments`     | Development environment |
| staging     | 327      | `https://market-data.staging.gravitymarkets.io/full/v1/all_instruments` | Staging environment     |
| testnet     | 326      | `https://market-data.testnet.grvt.io/full/v1/all_instruments`           | Testnet environment     |
| prod        | 325      | `https://market-data.grvt.io/full/v1/all_instruments`                   | Production environment  |

### API Integration

The script can automatically fetch the latest instruments data from GRVT's market data API. This ensures you always have the most up-to-date instrument information including:

- Instrument hashes
- Base decimals
- All available trading pairs

When you choose to fetch from API, the script will:

1. Make a POST request to the appropriate endpoint for your selected environment
2. Parse the response to extract instrument metadata
3. Optionally save the fetched data to a local JSON file for future use

## Time in Force Options

- `GOOD_TILL_TIME`: Good till time (default)
- `ALL_OR_NONE`: All or none
- `IMMEDIATE_OR_CANCEL`: Immediate or cancel
- `FILL_OR_KILL`: Fill or kill

## Security Notes

- ⚠️ **Never share your private key with anyone**
- ⚠️ **Use testnet environment for testing**
- ⚠️ **Verify all order details before signing**
- ⚠️ **Keep your private key secure and backed up**

## Error Handling

The script includes comprehensive error handling for:

- Invalid environment selection
- Malformed JSON input
- Missing instrument data
- Invalid time in force values
- Private key format issues

## Dependencies

- `eth-account`: For EIP-712 message signing
- `requests`: For HTTP API calls to fetch instruments
- `decimal`: For precise decimal arithmetic (built-in)
- `json`: For JSON parsing (built-in)
- `time`: For timestamp utilities (built-in)

## License

This script is provided as-is for educational and development purposes. Please refer to the main GRVT SDK license for usage terms.
