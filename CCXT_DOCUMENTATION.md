# GRVT CCXT Documentation

This documentation covers all the CCXT (CryptoCurrency eXchange Trading Library) related files in the GRVT Python SDK. The CCXT integration provides a standardized interface for interacting with the GRVT trading platform.

## Overview

The GRVT CCXT module provides both synchronous and asynchronous interfaces for trading operations, market data access, and WebSocket connectivity. It follows CCXT conventions while adding GRVT-specific functionality.

## File Structure

### Core Implementation Files

#### 1. `grvt_ccxt_base.py`

**Purpose**: Abstract base class providing common functionality for GRVT CCXT implementations.

**Key Features**:

- Common initialization and configuration
- Order validation and payload generation
- Account authentication checks
- Symbol validation
- Environment configuration management
- Return value tracking for testing

**Main Classes**:

- `GrvtCcxtBase`: Base class with shared functionality

**Key Methods**:

- `__init__()`: Initialize with environment, logger, and parameters
- `describe()`: Returns description of class methods
- `get_trading_account_id()`: Get trading account ID
- `_check_order_arguments()`: Validate order parameters
- `_check_account_auth()`: Verify account authentication
- `_get_payload_*()`: Various payload generation methods for different operations

#### 2. `grvt_ccxt.py`

**Purpose**: Synchronous CCXT implementation for REST API interactions.

**Key Features**:

- Synchronous REST API calls
- Order management (create, cancel, fetch)
- Market data retrieval
- Account information access
- Position management

**Main Classes**:

- `GrvtCcxt`: Main synchronous trading class

**Usage Example**:

```python
from grvt_api import GrvtCcxt
from grvt_env import GrvtEnv

grvt = GrvtCcxt(env=GrvtEnv.TESTNET)
markets = grvt.fetch_markets()
```

#### 3. `grvt_ccxt_pro.py`

**Purpose**: Asynchronous CCXT implementation for REST API interactions.

**Key Features**:

- Asynchronous REST API calls using aiohttp
- Concurrent operations support
- Same functionality as sync version but with async/await pattern
- Better performance for high-frequency operations

**Main Classes**:

- `GrvtCcxtPro`: Main asynchronous trading class

**Usage Example**:

```python
from grvt_api_pro import GrvtCcxtPro
from grvt_env import GrvtEnv

grvt = GrvtCcxtPro(env=GrvtEnv.TESTNET)
markets = await grvt.fetch_markets()
```

#### 4. `grvt_ccxt_ws.py`

**Purpose**: WebSocket implementation extending the async CCXT functionality.

**Key Features**:

- Real-time market data streaming
- Order updates via WebSocket
- Multiple stream support
- Connection management and reconnection logic
- Event-driven architecture

**Main Classes**:

- `GrvtCcxtWS`: WebSocket-enabled trading class extending `GrvtCcxtPro`

**WebSocket Streams**:

- Market data streams
- Trading data streams
- Order book updates
- Trade executions

### Supporting Files

#### 5. `grvt_ccxt_types.py`

**Purpose**: Type definitions and constants for GRVT CCXT operations.

**Key Components**:

- `Num`: Numeric type alias (None | str | float | int | Decimal)
- `Amount`: Amount type alias (Decimal | int | float | str)
- `GrvtOrderSide`: Literal type for order sides ("buy", "sell")
- `GrvtOrderType`: Literal type for order types ("limit", "market")
- `CandlestickInterval`: Enum for candlestick intervals
- `GrvtInvalidOrder`: Exception for invalid orders
- Constants for multipliers and conversions

#### 6. `grvt_ccxt_utils.py`

**Purpose**: Utility functions and classes for GRVT operations.

**Key Components**:

- `TimeInForce`: Enum for order time-in-force options
- `GrvtOrder`: Order data structure
- `GrvtSignature`: Signature handling
- Cookie management functions
- Order payload generation
- Cryptographic signing utilities
- Symbol parsing functions

**Important Functions**:

- `get_cookie_with_expiration()`: Sync cookie retrieval
- `get_cookie_with_expiration_async()`: Async cookie retrieval
- `get_order_payload()`: Generate order payload
- `get_grvt_order()`: Create GRVT order object
- `sign_derisk_mm_ratio_request()`: Sign de-risk requests

#### 7. `grvt_ccxt_env.py`

**Purpose**: Environment configuration and endpoint management.

**Key Components**:

- `GrvtEnv`: Environment enumeration (PROD, TESTNET, STAGING, DEV)
- `GrvtEndpointType`: REST endpoint types (EDGE, TRADE_DATA, MARKET_DATA)
- `GrvtWSEndpointType`: WebSocket endpoint types
- Endpoint URL generation functions
- Chain ID mappings

**Key Functions**:

- `get_grvt_endpoint()`: Get REST endpoint URL
- `get_grvt_ws_endpoint()`: Get WebSocket endpoint URL
- `get_all_grvt_endpoints()`: Get all available endpoints

#### 8. `grvt_ccxt_test_utils.py`

**Purpose**: Testing utilities and validation functions.

**Key Features**:

- Return value validation
- Endpoint testing utilities
- Default validation checks
- Test result tracking

**Main Functions**:

- `validate_return_values()`: Validate API return values
- `default_check()`: Default validation for responses

#### 9. `grvt_ccxt_logging_selector.py`

**Purpose**: Logging configuration and management.

**Key Features**:

- Environment-based logging configuration
- File vs console logging selection
- Timestamp-based log file naming
- Configurable log levels

## Architecture

### Class Hierarchy

```text
GrvtCcxtBase (Abstract Base Class)
├── GrvtCcxt (Synchronous REST)
└── GrvtCcxtPro (Asynchronous REST)
    └── GrvtCcxtWS (WebSocket Extension)
```

### Environment Support

- **PROD**: Production environment
- **TESTNET**: Testing environment
- **STAGING**: Staging environment  
- **DEV**: Development environment

### Authentication

The CCXT implementation supports:

- Private key-based signing
- API key authentication
- Cookie-based session management
- EIP-712 typed data signing

### Order Types

- **Limit Orders**: Orders with specified price
- **Market Orders**: Orders executed at current market price
- **Time-in-Force Options**: GOOD_TILL_TIME, FILL_OR_KILL, IMMEDIATE_OR_CANCEL, ALL_OR_NOTHING

## Usage Patterns

### Synchronous Trading

```python
from pysdk import GrvtCcxt, GrvtEnv

# Initialize
grvt = GrvtCcxt(
    env=GrvtEnv.TESTNET,
    parameters={
        'trading_account_id': 'your_account_id',
        'private_key': 'your_private_key'
    }
)

# Fetch markets
markets = grvt.fetch_markets()

# Create order
order = grvt.create_order('BTC/USD', 'limit', 'buy', 1.0, 50000)

# Cancel order
grvt.cancel_order(order['id'])
```

### Asynchronous Trading

```python
import asyncio
from pysdk import GrvtCcxtPro, GrvtEnv

async def main():
    grvt = GrvtCcxtPro(
        env=GrvtEnv.TESTNET,
        parameters={
            'trading_account_id': 'your_account_id',
            'private_key': 'your_private_key'
        }
    )
    
    markets = await grvt.fetch_markets()
    order = await grvt.create_order('BTC/USD', 'limit', 'buy', 1.0, 50000)
    
asyncio.run(main())
```

### WebSocket Streaming

```python
import asyncio
from pysdk import GrvtCcxtWS, GrvtEnv

async def handle_message(message):
    print(f"Received: {message}")

async def main():
    grvt = GrvtCcxtWS(env=GrvtEnv.TESTNET)
    await grvt.watch_trades('BTC/USD', handle_message)
    
asyncio.run(main())
```

## Error Handling

### Custom Exceptions

- `GrvtInvalidOrder`: Raised for invalid order parameters
- Standard HTTP errors for API failures
- WebSocket connection errors for stream issues

### Validation

- Order parameter validation
- Symbol format validation
- Account authentication checks
- Amount and price validations

## Testing

### Test Files

- `test_ccxt.py`: General CCXT functionality tests
- `test_grvt_ccxt.py`: Synchronous CCXT tests
- `test_grvt_ccxt_pro.py`: Asynchronous CCXT tests
- `test_grvt_ccxt_ws.py`: WebSocket functionality tests
- `test_grvt_ccxt_vault.py`: Vault-related tests
- `test_grvt_ccxt_vault_pro.py`: Async vault tests

### Testing Utilities

The `grvt_ccxt_test_utils.py` file provides utilities for:

- Validating API responses
- Checking endpoint coverage
- Tracking test results
- Default validation functions

## Configuration

### Environment Variables

- `GRVT_END_POINT_VERSION`: API version (default: "v1")
- `LOG_FILE`: Enable file logging ("TRUE"/"FALSE")
- `LOGGING_LEVEL`: Log level (default: "INFO")
- `GRVT_ENV`: Environment name

### Parameters Dictionary

Common parameters include:

- `trading_account_id`: Account identifier
- `private_key`: Private key for signing
- `api_key`: API key for authentication
- `order_book_ccxt_format`: Order book format preference

## Best Practices

1. **Environment Selection**: Always specify the correct environment (TESTNET for testing, PROD for live trading)
2. **Error Handling**: Implement proper try-catch blocks for network and API errors
3. **Rate Limiting**: Be aware of API rate limits and implement appropriate delays
4. **Security**: Keep private keys secure and never log them
5. **Testing**: Use TESTNET environment for development and testing
6. **Async Usage**: Prefer async implementation for better performance in high-frequency scenarios
7. **WebSocket Management**: Properly handle WebSocket connections and implement reconnection logic

## Security Considerations

- Private keys are used for order signing and should be kept secure
- All communications use HTTPS/WSS protocols
- EIP-712 standard is used for typed data signing
- Session cookies have expiration times and are refreshed automatically
- API endpoints are environment-specific to prevent accidental cross-environment operations

This documentation provides a comprehensive overview of the GRVT CCXT implementation and should serve as a reference for developers working with the SDK.