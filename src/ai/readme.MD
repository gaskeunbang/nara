# AI Trade Cost Predictor - Internet Computer Canister

A sophisticated on-chain AI system that predicts cryptocurrency trade execution costs across multiple exchanges using real-time market microstructure analysis.

## Overview

This canister deploys a production-grade LightGBM model directly on the Internet Computer, performing real-time slippage prediction and multi-exchange cost optimization. The system processes 39 complex market features and provides actionable trading insights through decentralized inference.

## Project Structure

```
D:\AAL\Coding\piton\ChainPrice\nara\src\ai\
├── src/
│   └── lib.rs                 # Main canister implementation
├── assets/
│   ├── model.onnx            # Pre-trained LightGBM model (ONNX format)
│   └── features.json         # Feature mapping configuration
├── Cargo.toml                # Rust dependencies
└── trade_predictor.did       # Candid interface definition
```

## Core Technology

**AI Model**: High-performance LightGBM with 39-dimensional feature space  
**Inference Engine**: Tract ONNX runtime optimized for WebAssembly  
**Data Processing**: Real-time market microstructure feature engineering  
**Scaling**: Embedded RobustScaler parameters for deterministic preprocessing  
**Supported Exchanges**: Binance, Kraken, Coinbase, OKX

## API Endpoints

### Primary Endpoint

#### `predict_trade_cost` (update)
Analyzes trade execution costs across all supported exchanges.

**Request Payload:**
```rust
TradeRequest {
    symbol: String,      // e.g., "BTC/USDT", "ETH-USD"
    amount: f64,         // Trade quantity
    side: String,        // "buy" or "sell"
    amount_usd: Option<f64>  // Optional USD value
}
```

**Usage Example:**
```bash
dfx canister call ai_canister predict_trade_cost '(record {
    symbol = "BTC/USDT";
    amount = 0.5;
    side = "buy";
    amount_usd = opt 25000.0
})'
```

**Response:**
```candid
PredictionResponse {
    best_venue: String,           // Optimal exchange
    potential_savings: f64,       // Cost difference vs worst venue
    quotes: Vec<ExchangeQuote>,   // Per-exchange analysis
    model_info: ModelInfo,        // AI model metadata
    timestamp: u64
}
```

**Exchange Quote Structure:**
```candid
ExchangeQuote {
    exchange: String,             // Exchange name
    symbol: String,               // Trading pair
    quote_price: f64,            // Current market price
    predicted_slippage: f64,     // AI-predicted slippage %
    total_cost: f64,             // Complete execution cost
    fees: HashMap<String, f64>,  // Breakdown of all fees
    recommendation_score: f64     // Venue ranking score
}
```

### Diagnostic Endpoints

#### `health_check` (query)
System status and component health verification.

#### `get_model_info` (query)
AI model specifications and metadata.

#### `get_supported_exchanges` (query)
List of integrated exchange APIs.

#### `debug_model_status` (query)
Detailed internal diagnostics for troubleshooting.

#### `test_feature_calculation` (query)
Validates feature engineering pipeline with test data.

## Key Features

### 🧠 Advanced AI Pipeline
- **39-feature market microstructure analysis**
- **Real-time order book depth calculation**
- **Dynamic volatility and imbalance metrics**
- **Engineered interaction features**

### ⚡ High-Performance Inference
- **Embedded model weights** (no external dependencies)
- **Optimized tensor operations** via Tract engine
- **Hardcoded preprocessing parameters** for deterministic scaling
- **Sub-second prediction latency**

### 🔄 Multi-Exchange Integration
- **Simultaneous data fetching** from 4 major exchanges
- **Exchange-specific API parsing** (REST endpoints)
- **Unified cost comparison** and ranking
- **Fee structure optimization**

### 🛡️ Production Reliability
- **Comprehensive error handling** for network failures
- **Input validation and sanitization**
- **Bounded prediction outputs** (0.01% - 10% slippage)
- **Graceful degradation** on partial exchange failures

## Deployment

1. **Build the canister:**
   ```bash
   dfx build ai_canister
   ```

2. **Deploy locally:**
   ```bash
   dfx deploy ai_canister
   ```

3. **Verify deployment:**
   ```bash
   dfx canister call ai_canister health_check
   ```

## Model Performance

The embedded LightGBM model processes market microstructure through:

- **Order book imbalance analysis**
- **Price impact estimation**
- **Liquidity depth profiling**  
- **Cross-exchange arbitrage detection**
- **Temporal volatility patterns**

Feature engineering includes logarithmic transformations, interaction terms, and normalized depth ratios optimized for cryptocurrency market dynamics.

## Technical Implementation

### WebAssembly Optimization
The canister uses custom `getrandom` implementation for Internet Computer compatibility and employs efficient tensor operations through the Tract inference framework.

### Data Pipeline
1. **Market Data Ingestion** → HTTP outcalls to exchange APIs
2. **Feature Engineering** → 39-dimensional feature vector creation
3. **Preprocessing** → RobustScaler normalization
4. **Model Inference** → ONNX graph execution
5. **Cost Calculation** → Fee-adjusted total cost estimation

### Error Handling
Robust error management covers network timeouts, malformed responses, model failures, and partial exchange outages while maintaining service availability.

---

*This system represents a sophisticated integration of machine learning, blockchain infrastructure, and financial market analysis - delivering institutional-grade trade optimization through decentralized AI.*