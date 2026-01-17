#!/usr/bin/env python3
"""
===============================================================================
GRVT ORDER SIGNER - STANDALONE SCRIPT
===============================================================================

A standalone Python script for signing GRVT orders with zero dependencies to the GRVT SDK.
Users can input their environment, private key, and order payload to get the signature.

===============================================================================
HOW ORDER SIGNING WORKS - STEP BY STEP
===============================================================================

1. PREPARE ORDER DATA
   - User provides order details (size, price, instrument, etc.)
   - Script fetches instrument metadata (hash, decimals) from API or file

2. BUILD EIP-712 MESSAGE DATA
   - Convert user order to contract format (handle decimals, types)
   - Map instrument names to contract asset IDs
   - Convert prices/sizes to contract units (avoid floating point errors)

3. CREATE EIP-712 DOMAIN DATA
   - Identify the contract ("GRVT Exchange")
   - Specify chain ID (prevents cross-chain signature replay)
   - Set contract version

4. GENERATE EIP-712 SIGNABLE MESSAGE
   - Combine domain + types + message data
   - Create structured hash using EIP-712 standard
   - This is what actually gets signed (not raw JSON)

5. CRYPTOGRAPHIC SIGNING
   - Use private key to sign the EIP-712 message
   - Extract r, s, v signature components
   - Get signer's Ethereum address

6. CREATE COMPLETE ORDER PAYLOAD
   - Combine original order data with signature
   - Ready for API submission to GRVT

===============================================================================
KEY FUNCTIONS TO UNDERSTAND SIGNING:
===============================================================================

- build_order_message_data(): Converts user order to contract format
- get_eip712_domain_data(): Creates contract identification data
- sign_order(): Main signing function (calls all above)
- encode_typed_data(): EIP-712 message encoding (from eth-account)

===============================================================================
USAGE:
    python grvt_order_signer.py

DEPENDENCIES:
    pip install eth-account requests

AUTHOR: GRVT
"""

import json
import time
import requests
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Union

from eth_account import Account
from eth_account.messages import encode_typed_data


class GrvtEnv(Enum):
    """GRVT Environment enumeration."""
    DEV = "dev"
    STAGING = "staging"
    TESTNET = "testnet"
    PROD = "prod"


class TimeInForce(Enum):
    """Time in Force enumeration."""
    GOOD_TILL_TIME = "GOOD_TILL_TIME"
    ALL_OR_NONE = "ALL_OR_NONE"
    IMMEDIATE_OR_CANCEL = "IMMEDIATE_OR_CANCEL"
    FILL_OR_KILL = "FILL_OR_KILL"


class SignTimeInForce(Enum):
    """Sign Time in Force enumeration (numeric values for signing)."""
    GOOD_TILL_TIME = 1
    ALL_OR_NONE = 2
    IMMEDIATE_OR_CANCEL = 3
    FILL_OR_KILL = 4


# ================================================================================
# ENVIRONMENT CONFIGURATIONS
# ================================================================================
# Chain IDs for each environment - used in EIP-712 domain data
CHAIN_IDS = {
    GrvtEnv.DEV: 327,        # Development environment chain ID
    GrvtEnv.STAGING: 327,    # Staging environment chain ID  
    GrvtEnv.TESTNET: 326,    # Testnet environment chain ID
    GrvtEnv.PROD: 325,       # Production environment chain ID
}

# API endpoints for fetching instruments data
INSTRUMENTS_API_ENDPOINTS = {
    GrvtEnv.DEV: "https://market-data.dev.gravitymarkets.io/full/v1/all_instruments",
    GrvtEnv.STAGING: "https://market-data.staging.gravitymarkets.io/full/v1/all_instruments",
    GrvtEnv.TESTNET: "https://market-data.testnet.grvt.io/full/v1/all_instruments",
    GrvtEnv.PROD: "https://market-data.grvt.io/full/v1/all_instruments",
}

# Time in Force mapping
TIME_IN_FORCE_TO_SIGN_TIME_IN_FORCE = {
    TimeInForce.GOOD_TILL_TIME: SignTimeInForce.GOOD_TILL_TIME,
    TimeInForce.ALL_OR_NONE: SignTimeInForce.ALL_OR_NONE,
    TimeInForce.IMMEDIATE_OR_CANCEL: SignTimeInForce.IMMEDIATE_OR_CANCEL,
    TimeInForce.FILL_OR_KILL: SignTimeInForce.FILL_OR_KILL,
}

# ================================================================================
# EIP-712 TYPE DEFINITIONS - CRITICAL FOR SIGNATURE VERIFICATION
# ================================================================================
# These type definitions MUST match exactly what the smart contract expects.
# Any changes to these types will break signature verification.
EIP712_ORDER_MESSAGE_TYPE = {
    "Order": [
        {"name": "subAccountID", "type": "uint64"},      # Subaccount identifier
        {"name": "isMarket", "type": "bool"},            # Market vs limit order
        {"name": "timeInForce", "type": "uint8"},        # Order execution type
        {"name": "postOnly", "type": "bool"},            # Maker-only flag
        {"name": "reduceOnly", "type": "bool"},          # Position reduction only
        {"name": "legs", "type": "OrderLeg[]"},          # Order legs array
        {"name": "nonce", "type": "uint32"},             # Unique order nonce
        {"name": "expiration", "type": "int64"},         # Order expiration timestamp
    ],
    "OrderLeg": [
        {"name": "assetID", "type": "uint256"},          # Asset identifier hash
        {"name": "contractSize", "type": "uint64"},      # Size in contract units
        {"name": "limitPrice", "type": "uint64"},        # Price in contract units
        {"name": "isBuyingContract", "type": "bool"},    # Buy/sell direction
    ],
}

# ================================================================================
# SIGNING CONSTANTS
# ================================================================================
# Price multiplier for converting decimal prices to contract units
# All prices are stored as integers in the contract (1e9 = 1.0 price)
PRICE_MULTIPLIER = 1_000_000_000


def get_eip712_domain_data(env: GrvtEnv, chain_id: int = None) -> Dict[str, Union[str, int]]:
    """
    ================================================================================
    EIP-712 DOMAIN DATA - CONTRACT IDENTIFICATION
    ================================================================================
    Domain data identifies the specific contract and chain for signature verification.
    This ensures signatures are only valid for the intended contract and environment.
    """
    return {
        "name": "GRVT Exchange",                    # Contract name identifier
        "version": "0",                            # Contract version
        "chainId": chain_id or CHAIN_IDS[env],     # Blockchain chain ID (prevents cross-chain replay)
    }


def build_order_message_data(order_data: Dict[str, Any], instruments: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    ================================================================================
    STEP 1: BUILD EIP-712 ORDER MESSAGE DATA
    ================================================================================
    This function converts the user's order data into the exact format required
    for EIP-712 signing. This is the core data that will be signed.
    
    Args:
        order_data: Order data containing legs, sub_account_id, etc.
                   Can be either direct order data or wrapped in an "order" key
        instruments: Dictionary mapping instrument names to their metadata
        
    Returns:
        Dictionary containing the message data for signing
    """
    # ============================================================================
    # 1.1: Extract order data (handle both wrapped and direct formats)
    # ============================================================================
    if "order" in order_data:
        order = order_data["order"]
    else:
        order = order_data
    
    # ============================================================================
    # 1.2: Process order legs (convert to contract format)
    # ============================================================================
    legs = []
    for leg in order["legs"]:
        instrument_name = leg["instrument"]
        if instrument_name not in instruments:
            raise ValueError(f"Instrument '{instrument_name}' not found in instruments data")
        
        instrument = instruments[instrument_name]
        # Convert size to contract units using base_decimals
        size_multiplier = 10 ** instrument["base_decimals"]
        
        # ========================================================================
        # CRITICAL: Use Decimal for precision to avoid floating point errors
        # ========================================================================
        size_int = int(Decimal(leg["size"]) * Decimal(size_multiplier))
        price_int = int(Decimal(leg["limit_price"]) * Decimal(PRICE_MULTIPLIER))
        
        # Build leg in the exact format expected by the smart contract
        legs.append({
            "assetID": instrument["instrument_hash"],      # Contract asset ID
            "contractSize": size_int,                      # Size in contract units
            "limitPrice": price_int,                       # Price in contract units
            "isBuyingContract": leg["is_buying_asset"],    # Buy/sell direction
        })
    
    # ============================================================================
    # 1.3: Convert time in force to contract enum value
    # ============================================================================
    time_in_force_str = order.get("time_in_force", "GOOD_TILL_TIME")
    try:
        time_in_force = TimeInForce(time_in_force_str)
        sign_time_in_force = TIME_IN_FORCE_TO_SIGN_TIME_IN_FORCE[time_in_force]
    except (ValueError, KeyError):
        raise ValueError(f"Invalid time_in_force: {time_in_force_str}")
    
    # ============================================================================
    # 1.4: Build the final EIP-712 message data structure
    # ============================================================================
    return {
        "subAccountID": int(order["sub_account_id"]),      # Subaccount ID as integer
        "isMarket": order.get("is_market", False),         # Market order flag
        "timeInForce": sign_time_in_force.value,           # Time in force enum value
        "postOnly": order.get("post_only", False),         # Post-only flag
        "reduceOnly": order.get("reduce_only", False),     # Reduce-only flag
        "legs": legs,                                      # Processed order legs
        "nonce": order["signature"]["nonce"],              # Unique nonce
        "expiration": order["signature"]["expiration"],    # Expiration timestamp
    }


def sign_order(
    order_data: Dict[str, Any],
    instruments: Dict[str, Dict[str, Any]],
    private_key: str,
    env: GrvtEnv
) -> Dict[str, Any]:
    """
    ================================================================================
    MAIN ORDER SIGNING FUNCTION - EIP-712 SIGNATURE GENERATION
    ================================================================================
    This is the core function that performs the complete order signing process.
    It follows the EIP-712 standard for structured data signing.
    
    Args:
        order_data: Order data containing legs, signature info, etc.
        instruments: Dictionary mapping instrument names to their metadata
        private_key: Private key in hex format (with or without 0x prefix)
        env: GRVT environment
        
    Returns:
        Dictionary containing the signature components and complete order payload
    """
    # ============================================================================
    # STEP 2: PREPARE PRIVATE KEY
    # ============================================================================
    # Remove 0x prefix if present (eth-account expects raw hex)
    if private_key.startswith("0x"):
        private_key = private_key[2:]
    
    # ============================================================================
    # STEP 3: BUILD EIP-712 MESSAGE DATA
    # ============================================================================
    # Convert user order data to the exact format required for signing
    message_data = build_order_message_data(order_data, instruments)
    
    # ============================================================================
    # STEP 4: BUILD EIP-712 DOMAIN DATA
    # ============================================================================
    # Domain data identifies the contract and chain for signature verification
    domain_data = get_eip712_domain_data(env)
    
    # ============================================================================
    # STEP 5: CREATE EIP-712 SIGNABLE MESSAGE
    # ============================================================================
    # This combines domain, types, and message data into a signable hash
    # This is the actual data that gets signed (not the raw JSON)
    signable_message = encode_typed_data(domain_data, EIP712_ORDER_MESSAGE_TYPE, message_data)
    
    # ============================================================================
    # STEP 6: GENERATE CRYPTOGRAPHIC SIGNATURE
    # ============================================================================
    # Create account from private key and sign the message
    account = Account.from_key(private_key)
    signed_message = account.sign_message(signable_message)
    
    # ============================================================================
    # STEP 7: EXTRACT SIGNATURE COMPONENTS
    # ============================================================================
    # EIP-712 signatures have three components: r, s, v
    signature = {
        "r": "0x" + signed_message.r.to_bytes(32, byteorder="big").hex(),  # 32-byte r value
        "s": "0x" + signed_message.s.to_bytes(32, byteorder="big").hex(),  # 32-byte s value
        "v": signed_message.v,                                             # Recovery ID (27 or 28)
        "signer": account.address                                          # Signer's Ethereum address
    }
    
    # ============================================================================
    # STEP 8: CREATE COMPLETE ORDER PAYLOAD
    # ============================================================================
    # Combine original order data with signature for API submission
    complete_order_payload = create_complete_order_payload(order_data, signature)
    
    # ============================================================================
    # STEP 9: RETURN ALL SIGNING RESULTS
    # ============================================================================
    return {
        "signer": account.address,                    # Who signed the order
        "r": signature["r"],                         # Signature component r
        "s": signature["s"],                         # Signature component s
        "v": signature["v"],                         # Signature component v
        "payload_to_sign": {                         # The exact data that was signed
            "domain": domain_data,                   # EIP-712 domain
            "types": EIP712_ORDER_MESSAGE_TYPE,     # EIP-712 type definitions
            "message": message_data                  # The order message data
        },
        "complete_order_payload": complete_order_payload  # Ready-to-submit order
    }


def create_complete_order_payload(order_data: Dict[str, Any], signature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a complete order payload with the signature included.
    
    Args:
        order_data: Original order data (can be wrapped in "order" key or direct)
        signature: Signature components (r, s, v, signer)
        
    Returns:
        Complete order payload ready for API submission
    """
    # Handle both direct order data and wrapped order data
    if "order" in order_data:
        order = order_data["order"].copy()
    else:
        order = order_data.copy()
    
    # Update the signature in the order data
    order["signature"] = {
        "r": signature["r"],
        "s": signature["s"],
        "v": signature["v"],
        "expiration": order["signature"]["expiration"],
        "nonce": order["signature"]["nonce"],
        "signer": signature["signer"]
    }
    
    # Return the complete payload
    return {
        "order": order
    }


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {file_path}: {e}")


def fetch_instruments_from_api(env: GrvtEnv) -> Dict[str, Dict[str, Any]]:
    """
    Fetch instruments data from GRVT API.
    
    Args:
        env: GRVT environment
        
    Returns:
        Dictionary mapping instrument names to their metadata
    """
    endpoint = INSTRUMENTS_API_ENDPOINTS[env]
    payload = {"is_active": True}
    
    try:
        print(f"🔄 Fetching instruments from {env.value} environment...")
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        instruments = {}
        
        for instrument_data in data.get("result", []):
            instrument_name = instrument_data["instrument"]
            instruments[instrument_name] = {
                "instrument_hash": instrument_data["instrument_hash"],
                "base_decimals": instrument_data["base_decimals"]
            }
        
        print(f"✅ Fetched {len(instruments)} instruments from API")
        return instruments
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to fetch instruments from API: {e}")
    except (KeyError, ValueError) as e:
        raise ValueError(f"Invalid response format from API: {e}")


def save_instruments_to_file(instruments: Dict[str, Dict[str, Any]], filename: str = "instruments.json") -> None:
    """
    Save instruments data to a JSON file.
    
    Args:
        instruments: Instruments data to save
        filename: Filename to save to
    """
    try:
        with open(filename, 'w') as f:
            json.dump(instruments, f, indent=2)
        print(f"✅ Instruments data saved to {filename}")
    except Exception as e:
        raise IOError(f"Failed to save instruments to file: {e}")


def get_user_input() -> tuple[GrvtEnv, str, Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Get user input for environment, private key, order data, and instruments."""
    print("GRVT Order Signer")
    print("=" * 50)
    
    # Environment selection
    print("\nAvailable environments:")
    for i, env in enumerate(GrvtEnv, 1):
        print(f"{i}. {env.value}")
    
    while True:
        try:
            env_choice = int(input("\nSelect environment (1-4): ")) - 1
            env = list(GrvtEnv)[env_choice]
            break
        except (ValueError, IndexError):
            print("Invalid choice. Please select 1-4.")
    
    # Private key input
    print(f"\nSelected environment: {env.value}")
    private_key = input("Enter private key (hex, with or without 0x prefix): ").strip()
    
    # Order data input - allow default file, custom file, or manual input
    print("\nOrder data input options:")
    print("1. Use default create_order_data.json")
    print("2. Load from custom JSON file")
    print("3. Enter manually")
    
    order_data = None
    while order_data is None:
        choice = input("\nChoose option (1-3): ").strip()
        if choice == "1":
            try:
                order_data = load_json_file("create_order_data.json")
                print("✅ Loaded order data from create_order_data.json")
            except Exception as e:
                print(f"❌ Error loading default file: {e}")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    choice = "2"  # Fall back to custom file
        elif choice == "2":
            file_path = input("Enter path to order JSON file: ").strip()
            try:
                order_data = load_json_file(file_path)
                print(f"✅ Loaded order data from {file_path}")
            except Exception as e:
                print(f"❌ Error loading file: {e}")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    choice = "3"  # Fall back to manual input
        elif choice == "3":
            print("\nEnter order data (JSON format):")
            print("Example:")
            print(json.dumps({
                "order": {
                    "sub_account_id": "507846889459127",
                    "is_market": False,
                    "time_in_force": "GOOD_TILL_TIME",
                    "post_only": False,
                    "reduce_only": False,
                    "legs": [
                        {
                            "instrument": "BTC_USDT_Perp",
                            "size": "1.5",
                            "limit_price": "115038.01",
                            "is_buying_asset": True
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
            }, indent=2))
            
            order_data = json.loads(input("\nOrder data: "))
        else:
            print("Invalid choice. Please select 1, 2, or 3.")
    
    # Instruments data input - allow API, file, or manual input
    print("\nInstruments data input options:")
    print("1. Fetch from GRVT API (recommended)")
    print("2. Load from JSON file")
    print("3. Enter manually")
    
    instruments = None
    while instruments is None:
        choice = input("\nChoose option (1-3): ").strip()
        if choice == "1":
            try:
                instruments = fetch_instruments_from_api(env)
                # Ask if user wants to save the fetched instruments
                save_option = input("\n💾 Save fetched instruments to file? (y/n): ").strip().lower()
                if save_option == 'y':
                    filename = input("Enter filename (default: instruments.json): ").strip()
                    if not filename:
                        filename = "instruments.json"
                    save_instruments_to_file(instruments, filename)
            except Exception as e:
                print(f"❌ Error fetching from API: {e}")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    choice = "2"  # Fall back to file input
        elif choice == "2":
            file_path = input("Enter path to instruments JSON file: ").strip()
            try:
                instruments = load_json_file(file_path)
                print(f"✅ Loaded instruments data from {file_path}")
            except Exception as e:
                print(f"❌ Error loading file: {e}")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    choice = "3"  # Fall back to manual input
        elif choice == "3":
            print("\nEnter instruments data (JSON format):")
            print("Example:")
            print(json.dumps({
                "BTC_USDT_Perp": {
                    "instrument_hash": "0x030501",
                    "base_decimals": 9
                }
            }, indent=2))
            
            instruments = json.loads(input("\nInstruments data: "))
        else:
            print("Invalid choice. Please select 1, 2, or 3.")
    
    return env, private_key, order_data, instruments


def main():
    """Main function to run the order signer."""
    try:
        env, private_key, order_data, instruments = get_user_input()
        
        print("\n" + "=" * 50)
        print("SIGNING ORDER")
        print("=" * 50)
        
        # ============================================================================
        # MAIN SIGNING PROCESS - THIS IS WHERE THE MAGIC HAPPENS
        # ============================================================================
        # The sign_order() function performs the complete EIP-712 signing process:
        # 1. Converts order data to contract format
        # 2. Creates EIP-712 domain and message data
        # 3. Generates signable hash using EIP-712 standard
        # 4. Signs with private key to get r, s, v components
        # 5. Creates complete order payload ready for API submission
        signature_result = sign_order(order_data, instruments, private_key, env)
        
        # Display results
        print("\n✅ Order signed successfully!")
        print(f"\nSigner: {signature_result['signer']}")
        print(f"R: {signature_result['r']}")
        print(f"S: {signature_result['s']}")
        print(f"V: {signature_result['v']}")
        
        print("\n📋 Payload to sign:")
        print(json.dumps(signature_result['payload_to_sign'], indent=2))
        
        print("\n🔐 Complete signature:")
        print(json.dumps({
            "signer": signature_result['signer'],
            "r": signature_result['r'],
            "s": signature_result['s'],
            "v": signature_result['v']
        }, indent=2))
        
        print("\n📦 Complete order payload (ready for API submission):")
        print(json.dumps(signature_result['complete_order_payload'], indent=2))
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
