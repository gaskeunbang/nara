use candid::{CandidType, Deserialize};
use ic_cdk::api::management_canister::http_request::{
    CanisterHttpRequestArgument, HttpHeader, HttpMethod, HttpResponse, TransformArgs,
};
use ic_cdk::{init, query, update};
use serde_json::Value;
use std::cell::RefCell;
use std::collections::HashMap;
use tract_core::prelude::*;
use tract_onnx::prelude::*;

// Custom getrandom implementation for Internet Computer
use getrandom::{register_custom_getrandom, Error};

fn ic_getrandom(buf: &mut [u8]) -> Result<(), Error> {
    let time_nanos = ic_cdk::api::time();
    let mut seed = time_nanos;
    
    for byte in buf.iter_mut() {
        seed = seed.wrapping_mul(1103515245).wrapping_add(12345);
        *byte = (seed >> 16) as u8;
    }
    
    Ok(())
}

register_custom_getrandom!(ic_getrandom);

const ROBUST_SCALER_CENTER: [f32; 39] = [
    500.00000000, 24.19257430, 0.00000000, 0.00515026, 20179.19890299, 162744.12817500, 337709.28023401, 2401005.98743850, 3145731.78229690, 3258444.22596370, 0.50024835, 0.02059043, 0.02052335, 0.00678044, 367.77563522, 93.00000000, 25.32089750, 0.00171007, 50000.00000000, 1.00000000, 1.05798670, 1.00000000, 1.20121428, 1.00000000, 2.57271125, 3.50543741, 0.00000292, 0.00237095, 22609327.25630069, 0.00003816, 0.02060263, -0.00000422, 0.12792705, 0.45440979, 6.21660610, 9.91245714, 11.99994063, 12.72994365, 5.91018806
];

const ROBUST_SCALER_SCALE: [f32; 39] = [
    900.00000000, 181.14663028, 1.00000000, 0.02407081, 88727.34312907, 460085.39398830, 867319.63701405, 5151612.05388445, 5098592.13800559, 4975251.98320015, 0.22377573, 0.06201440, 0.05585687, 0.04269268, 3837.51080000, 83.00000000, 856.31712125, 0.00750546, 90000.00000000, 1.00000000, 1.42745344, 1.00000000, 0.04421943, 0.20000000, 12.56589233, 41.17319779, 0.00006255, 0.01179423, 307327339.09537828, 0.00014891, 0.04130368, 0.00010596, 0.38392016, 0.22559865, 2.29363426, 3.23171595, 2.18702399, 2.08042306, 5.35361217
];

// ============================================================================
// CONSTANTS FOR EMBEDDED MODELS
// ============================================================================

const MODEL_BYTES: &[u8] = include_bytes!("../assets/model.onnx");
const FEATURE_NAMES_JSON: &str = include_str!("../assets/features.json");
const MODEL_TYPE: &str = "lightgbm_embedded";

// ============================================================================
// TYPES & STRUCTS
// ============================================================================

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct TradeRequest {
    pub symbol: String,
    pub amount: f64,
    pub side: String,
    pub amount_usd: Option<f64>,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct ExchangeQuote {
    pub exchange: String,
    pub symbol: String,
    pub quote_price: f64,
    pub predicted_slippage: f64,
    pub total_cost: f64,
    pub fees: HashMap<String, f64>,
    pub recommendation_score: f64,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct PredictionResponse {
    pub best_venue: String,
    pub potential_savings: f64,
    pub quotes: Vec<ExchangeQuote>,
    pub model_info: ModelInfo,
    pub timestamp: u64,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct ModelInfo {
    pub model_type: String,
    pub feature_count: u32,
    pub inference_engine: String,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct MarketData {
    pub bids: Vec<(f64, f64)>,
    pub asks: Vec<(f64, f64)>,
    pub trades: Vec<TradeData>,
    pub timestamp: u64,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct TradeData {
    pub price: f64,
    pub amount: f64,
    pub timestamp: u64,
}

#[derive(CandidType, Deserialize, Debug)]
pub enum ApiError {
    InvalidRequest(String),
    ModelNotLoaded,
    PredictionFailed(String),
    NetworkError(String),
    ExchangeError(String),
}

// ============================================================================
// GLOBAL STATE
// ============================================================================

thread_local! {
    static STATE: RefCell<AppState> = RefCell::new(AppState::default());
}

#[derive(Default)]
struct AppState {
    model: Option<SimplePlan<TypedFact, Box<dyn TypedOp>, Graph<TypedFact, Box<dyn TypedOp>>>>,
    feature_names: Vec<String>,
    model_type: String,
    exchange_fees: HashMap<String, ExchangeFees>,
    initialization_status: String,
}

#[derive(Clone)]
struct ExchangeFees {
    #[allow(dead_code)]
    maker: f64,
    taker: f64,
}

impl AppState {
    fn new() -> Self {
        let mut exchange_fees = HashMap::new();
        // All 4 exchanges matching your Python validation
        exchange_fees.insert("binance".to_string(), ExchangeFees { maker: 0.001, taker: 0.001 });
        exchange_fees.insert("kraken".to_string(), ExchangeFees { maker: 0.0016, taker: 0.0026 });
        exchange_fees.insert("coinbase".to_string(), ExchangeFees { maker: 0.005, taker: 0.005 });
        exchange_fees.insert("okx".to_string(), ExchangeFees { maker: 0.0008, taker: 0.001 });

        Self {
            model: None,
            feature_names: Vec::new(),
            model_type: "none".to_string(),
            exchange_fees,
            initialization_status: "starting".to_string(),
        }
    }
}

// ============================================================================
// IMPROVED MODEL MANAGEMENT
// ============================================================================

fn load_onnx_model_safe(model_data: &[u8], model_name: &str) -> TractResult<SimplePlan<TypedFact, Box<dyn TypedOp>, Graph<TypedFact, Box<dyn TypedOp>>>> {
    ic_cdk::println!("Loading {} model, size: {} bytes", model_name, model_data.len());
    
    if model_data.is_empty() {
        return Err(TractError::msg("Model data is empty"));
    }

    let mut cursor = std::io::Cursor::new(model_data);
    
    // More robust model loading with error handling
    let model = tract_onnx::onnx()
        .model_for_read(&mut cursor)?
        .with_input_fact(0, InferenceFact::dt_shape(f32::datum_type(), tvec![1, 39]))?
        .into_optimized()?
        .into_runnable()?;
    
    ic_cdk::println!("Successfully loaded {} model", model_name);
    Ok(model)
}

#[init]
fn init() {
    ic_cdk::println!("Starting canister initialization...");
    let mut app_state = AppState::new();

    // Load feature names first
    match serde_json::from_str::<Vec<String>>(FEATURE_NAMES_JSON) {
        Ok(names) => {
            app_state.feature_names = names;
            ic_cdk::println!("✅ Loaded {} feature names", app_state.feature_names.len());
        },
        Err(e) => {
            ic_cdk::println!("❌ Failed to parse feature names: {}", e);
            app_state.initialization_status = format!("feature_error: {}", e);
        }
    }

    // Load main model with better error handling
    match load_onnx_model_safe(MODEL_BYTES, "main") {
        Ok(model) => {
            app_state.model = Some(model);
            ic_cdk::println!("✅ Successfully loaded main model");
        },
        Err(e) => {
            ic_cdk::println!("❌ Failed to load main model: {}", e);
            app_state.initialization_status = format!("model_error: {}", e);
        }
    }

    app_state.model_type = MODEL_TYPE.to_string();

    // Set final status - removed scaler check since we're using hardcoded scaling
    if app_state.model.is_some() && !app_state.feature_names.is_empty() {
        app_state.initialization_status = "fully_loaded".to_string();
        ic_cdk::println!("✅ All components loaded successfully");
    } else {
        if app_state.initialization_status.starts_with("starting") {
            app_state.initialization_status = "partial_load".to_string();
        }
        ic_cdk::println!("⚠️ Initialization completed with issues");
    }

    STATE.with(|state| {
        *state.borrow_mut() = app_state;
    });

    ic_cdk::println!("🏁 Canister initialization completed");
}

#[query]
fn get_model_info() -> ModelInfo {
    STATE.with(|state| {
        let state = state.borrow();
        ModelInfo {
            model_type: state.model_type.clone(),
            feature_count: state.feature_names.len() as u32,
            inference_engine: "Tract ONNX".to_string(),
        }
    })
}

// ============================================================================
// FEATURE CALCULATION - ENSURE 39 FEATURES
// ============================================================================

fn calculate_features(market_data: &MarketData, trade_request: &TradeRequest) -> Result<Vec<f64>, ApiError> {
    let bids = &market_data.bids;
    let asks = &market_data.asks;
    
    if bids.is_empty() || asks.is_empty() {
        return Err(ApiError::InvalidRequest("Empty order book".to_string()));
    }

    let best_bid = bids[0].0;
    let best_ask = asks[0].0;
    let mid_price = (best_bid + best_ask) / 2.0;
    let trade_side = if trade_request.side.to_lowercase() == "buy" { 1.0 } else { 0.0 };
    
    let order_size_usd = trade_request.amount_usd
        .unwrap_or(trade_request.amount * mid_price);

    // Core features
    let spread = best_ask - best_bid;
    let spread_percentage = (spread / mid_price) * 100.0;
    
    // Market depth calculations
    let market_depth_level_1 = bids[0].1 * best_bid + asks[0].1 * best_ask;
    
    let market_depth_level_5 = bids.iter().take(5).map(|(p, v)| p * v).sum::<f64>()
        + asks.iter().take(5).map(|(p, v)| p * v).sum::<f64>();
    
    let market_depth_level_10 = bids.iter().take(10).map(|(p, v)| p * v).sum::<f64>()
        + asks.iter().take(10).map(|(p, v)| p * v).sum::<f64>();
    
    // Order book imbalance
    let total_bids: f64 = bids.iter().take(10).map(|(_, v)| v).sum();
    let total_asks: f64 = asks.iter().take(10).map(|(_, v)| v).sum();
    let total_volume = total_bids + total_asks;
    let order_book_imbalance = if total_volume > 0.0 { total_bids / total_volume } else { 0.5 };

    // Price slopes
    let ask_price_slope = if asks.len() >= 5 {
        (asks[4].0 - asks[0].0) / asks[0].0 * 100.0
    } else { 0.0 };
    
    let bid_price_slope = if bids.len() >= 5 {
        (bids[0].0 - bids[4].0) / bids[0].0 * 100.0
    } else { 0.0 };

    // Trade volatility
    let trade_volatility_1m = if market_data.trades.len() > 1 {
        let prices: Vec<f64> = market_data.trades.iter().map(|t| t.price).collect();
        let max_price = prices.iter().cloned().fold(0.0f64, f64::max);
        let min_price = prices.iter().cloned().fold(f64::INFINITY, f64::min);
        max_price - min_price
    } else { 0.0 };

    let trade_volume_1m = market_data.trades.iter().map(|t| t.amount).sum::<f64>();

    // Advanced features
    let depth_utilization = if market_depth_level_10 > 0.0 {
        order_size_usd / market_depth_level_10
    } else { 0.0 };

    let relative_order_size = depth_utilization;
    let bid_ask_ratio = bids.len() as f64 / asks.len().max(1) as f64;
    
    let bid_depth_5 = bids.iter().take(5).map(|(p, v)| p * v).sum::<f64>();
    let ask_depth_5 = asks.iter().take(5).map(|(p, v)| p * v).sum::<f64>();
    let order_book_depth_ratio = if ask_depth_5 > 0.0 { bid_depth_5 / ask_depth_5 } else { 1.0 };

    // Engineered features
    let size_spread_interaction = order_size_usd * spread_percentage;
    let size_volatility_interaction = order_size_usd * trade_volatility_1m;
    let depth_utilization_squared = depth_utilization * depth_utilization;
    let imbalance_spread = order_book_imbalance * spread_percentage;
    let depth_spread_ratio = market_depth_level_5 / (spread_percentage + 1e-8);
    let volatility_spread = trade_volatility_1m * spread_percentage;

    // Create feature vector - EXACTLY 39 features to match your model
    let features = vec![
        order_size_usd,                    // 1
        trade_request.amount,              // 2
        trade_side,                        // 3
        spread_percentage,                 // 4
        market_depth_level_1,             // 5
        market_depth_level_5,             // 6
        market_depth_level_10,            // 7
        market_depth_level_5,             // 8 (duplicate for compatibility)
        order_book_imbalance,             // 9
        ask_price_slope,                  // 10
        bid_price_slope,                  // 11
        trade_volatility_1m,              // 12
        trade_volume_1m,                  // 13
        mid_price,                        // 14
        relative_order_size,              // 15
        bid_ask_ratio,                    // 16
        order_book_depth_ratio,           // 17
        depth_utilization,                // 18
        size_spread_interaction,          // 19
        size_volatility_interaction,      // 20
        depth_utilization_squared,        // 21
        imbalance_spread,                 // 22
        depth_spread_ratio,               // 23
        volatility_spread,                // 24
        (ask_price_slope + bid_price_slope) / 2.0, // 25
        ask_price_slope - bid_price_slope, // 26
        market_depth_level_1 / (market_depth_level_5 + 1e-8), // 27
        market_depth_level_5 / (market_depth_level_10 + 1e-8), // 28
        (order_size_usd + 1.0).ln(),      // 29
        (market_depth_level_1 + 1.0).ln(), // 30
        (market_depth_level_5 + 1.0).ln(), // 31
        (market_depth_level_10 + 1.0).ln(), // 32
        (trade_volume_1m + 1.0).ln(),     // 33
        // Additional features to reach 39
        best_bid,                         // 34
        best_ask,                         // 35
        spread,                           // 36
        total_bids,                       // 37
        total_asks,                       // 38
        (mid_price + 1.0).ln(),          // 39
    ];

    // Verify we have exactly 39 features
    if features.len() != 39 {
        ic_cdk::println!("⚠️ Feature count mismatch: expected 39, got {}", features.len());
    }

    Ok(features)
}

// ============================================================================
// IMPROVED ONNX PREDICTION WITH HARDCODED SCALING
// ============================================================================

fn apply_scaling(features: Vec<f32>) -> Vec<f32> {
    features.into_iter().enumerate().map(|(i, val)| {
        // Handle cases where scale might be zero to avoid division by zero
        if ROBUST_SCALER_SCALE[i].abs() > 1e-9 {
            (val - ROBUST_SCALER_CENTER[i]) / ROBUST_SCALER_SCALE[i]
        } else {
            val - ROBUST_SCALER_CENTER[i]
        }
    }).collect()
}

fn predict_slippage(features: Vec<f64>) -> Result<f64, ApiError> {
    STATE.with(|state| {
        let state = state.borrow();
        
        let model = state.model.as_ref()
            .ok_or(ApiError::ModelNotLoaded)?;

        ic_cdk::println!("Making prediction with {} features", features.len());

        // Ensure we have exactly 39 features
        if features.len() != 39 {
            return Err(ApiError::PredictionFailed(
                format!("Expected 39 features, got {}", features.len())
            ));
        }

        // Convert features to f32 and handle potential NaN/Inf values
        let features_f32: Vec<f32> = features.iter().map(|&x| {
            if x.is_finite() { x as f32 } else { 0.0f32 }
        }).collect();

        // Apply hardcoded scaling
        let scaled_features = apply_scaling(features_f32);
        
        // Create input tensor with proper shape
        let input_tensor = tract_core::ndarray::Array2::from_shape_vec(
            (1, 39),
            scaled_features
        ).map_err(|e| ApiError::PredictionFailed(format!("Tensor creation failed: {}", e)))?;

        let tensor_input = input_tensor.into_dyn().into_tensor().into();

        // Make prediction directly with scaled features
        let prediction_result = model
            .run(tvec![tensor_input])
            .map_err(|e| ApiError::PredictionFailed(format!("Prediction failed: {}", e)))?;

        // Extract prediction value
        let prediction = prediction_result[0]
            .to_array_view::<f32>()
            .map_err(|e| ApiError::PredictionFailed(format!("Output extraction failed: {}", e)))?
            .iter()
            .next()
            .copied()
            .unwrap_or(0.01) as f64;

        // Bound prediction to reasonable range
        let bounded_prediction = prediction.max(0.0001).min(0.1);
        
        ic_cdk::println!("Prediction: {:.4}%", bounded_prediction * 100.0);
        Ok(bounded_prediction)
    })
}

// ============================================================================
// EXPANDED MARKET DATA FETCHING (4 EXCHANGES)
// ============================================================================

#[update]
async fn fetch_market_data(exchange: String, symbol: String) -> Result<MarketData, ApiError> {
    let url = build_market_data_url(&exchange, &symbol)?;
    
    let request = CanisterHttpRequestArgument {
        url,
        method: HttpMethod::GET,
        body: None,
        max_response_bytes: Some(1000000),
        transform: Some(ic_cdk::api::management_canister::http_request::TransformContext {
            function: ic_cdk::api::management_canister::http_request::TransformFunc(
                candid::Func {
                    principal: ic_cdk::api::id(),
                    method: "transform_response".to_string(),
                },
            ),
            context: vec![],
        }),
        headers: vec![
            HttpHeader {
                name: "User-Agent".to_string(),
                value: "Trade-Cost-Predictor/1.0".to_string(),
            },
        ],
    };

    match ic_cdk::api::management_canister::http_request::http_request(request, 25_000_000_000).await {
        Ok((response,)) => {
            parse_market_data_response(&exchange, &response.body)
        }
        Err(e) => Err(ApiError::NetworkError(format!("HTTP request failed: {:?}", e))),
    }
}

fn build_market_data_url(exchange: &str, symbol: &str) -> Result<String, ApiError> {
    let url = match exchange.to_lowercase().as_str() {
        "binance" => {
            let formatted_symbol = symbol.replace("/", "");
            format!("https://api.binance.com/api/v3/depth?symbol={}&limit=20", formatted_symbol)
        },
        "kraken" => {
            let formatted_symbol = symbol.replace("/", "");
            format!("https://api.kraken.com/0/public/Depth?pair={}&count=20", formatted_symbol)
        },
        "coinbase" => {
            format!("https://api.exchange.coinbase.com/products/{}/book?level=2", symbol)
        },
        "okx" => {
            let formatted_symbol = symbol.replace("/", "-");
            format!("https://www.okx.com/api/v5/market/books?instId={}&sz=20", formatted_symbol)
        },
        _ => return Err(ApiError::ExchangeError(format!("Unsupported exchange: {}", exchange))),
    };
    
    Ok(url)
}

fn parse_market_data_response(exchange: &str, body: &[u8]) -> Result<MarketData, ApiError> {
    let json_str = String::from_utf8(body.to_vec())
        .map_err(|e| ApiError::NetworkError(format!("Invalid UTF-8: {}", e)))?;
    
    let json: Value = serde_json::from_str(&json_str)
        .map_err(|e| ApiError::NetworkError(format!("Invalid JSON: {}", e)))?;

    match exchange.to_lowercase().as_str() {
        "binance" => parse_binance_response(&json),
        "kraken" => parse_kraken_response(&json),
        "coinbase" => parse_coinbase_response(&json),
        "okx" => parse_okx_response(&json),
        _ => Err(ApiError::ExchangeError("Unsupported exchange".to_string())),
    }
}

fn parse_binance_response(json: &Value) -> Result<MarketData, ApiError> {
    let bids = json["bids"]
        .as_array()
        .ok_or(ApiError::NetworkError("No bids data".to_string()))?
        .iter()
        .take(20)
        .filter_map(|bid| {
            let price = bid[0].as_str()?.parse().ok()?;
            let volume = bid[1].as_str()?.parse().ok()?;
            Some((price, volume))
        })
        .collect();

    let asks = json["asks"]
        .as_array()
        .ok_or(ApiError::NetworkError("No asks data".to_string()))?
        .iter()
        .take(20)
        .filter_map(|ask| {
            let price = ask[0].as_str()?.parse().ok()?;
            let volume = ask[1].as_str()?.parse().ok()?;
            Some((price, volume))
        })
        .collect();

    Ok(MarketData {
        bids,
        asks,
        trades: vec![],
        timestamp: ic_cdk::api::time(),
    })
}

fn parse_kraken_response(json: &Value) -> Result<MarketData, ApiError> {
    let result = json["result"]
        .as_object()
        .ok_or(ApiError::NetworkError("No result data".to_string()))?;
    
    let pair_data = result
        .values()
        .next()
        .ok_or(ApiError::NetworkError("No pair data".to_string()))?;

    let bids = pair_data["bids"]
        .as_array()
        .ok_or(ApiError::NetworkError("No bids data".to_string()))?
        .iter()
        .take(20)
        .filter_map(|bid| {
            let price = bid[0].as_str()?.parse().ok()?;
            let volume = bid[1].as_str()?.parse().ok()?;
            Some((price, volume))
        })
        .collect();

    let asks = pair_data["asks"]
        .as_array()
        .ok_or(ApiError::NetworkError("No asks data".to_string()))?
        .iter()
        .take(20)
        .filter_map(|ask| {
            let price = ask[0].as_str()?.parse().ok()?;
            let volume = ask[1].as_str()?.parse().ok()?;
            Some((price, volume))
        })
        .collect();

    Ok(MarketData {
        bids,
        asks,
        trades: vec![],
        timestamp: ic_cdk::api::time(),
    })
}

fn parse_coinbase_response(json: &Value) -> Result<MarketData, ApiError> {
    let bids = json["bids"]
        .as_array()
        .ok_or(ApiError::NetworkError("No bids data".to_string()))?
        .iter()
        .take(20)
        .filter_map(|bid| {
            let price = bid[0].as_str()?.parse().ok()?;
            let volume = bid[1].as_str()?.parse().ok()?;
            Some((price, volume))
        })
        .collect();

    let asks = json["asks"]
        .as_array()
        .ok_or(ApiError::NetworkError("No asks data".to_string()))?
        .iter()
        .take(20)
        .filter_map(|ask| {
            let price = ask[0].as_str()?.parse().ok()?;
            let volume = ask[1].as_str()?.parse().ok()?;
            Some((price, volume))
        })
        .collect();

    Ok(MarketData {
        bids,
        asks,
        trades: vec![],
        timestamp: ic_cdk::api::time(),
    })
}

fn parse_okx_response(json: &Value) -> Result<MarketData, ApiError> {
    let data = json["data"]
        .as_array()
        .and_then(|arr| arr.get(0))
        .ok_or(ApiError::NetworkError("No data".to_string()))?;

    let bids = data["bids"]
        .as_array()
        .ok_or(ApiError::NetworkError("No bids data".to_string()))?
        .iter()
        .take(20)
        .filter_map(|bid| {
            let price = bid[0].as_str()?.parse().ok()?;
            let volume = bid[1].as_str()?.parse().ok()?;
            Some((price, volume))
        })
        .collect();

    let asks = data["asks"]
        .as_array()
        .ok_or(ApiError::NetworkError("No asks data".to_string()))?
        .iter()
        .take(20)
        .filter_map(|ask| {
            let price = ask[0].as_str()?.parse().ok()?;
            let volume = ask[1].as_str()?.parse().ok()?;
            Some((price, volume))
        })
        .collect();

    Ok(MarketData {
        bids,
        asks,
        trades: vec![],
        timestamp: ic_cdk::api::time(),
    })
}

#[query]
fn transform_response(args: TransformArgs) -> HttpResponse {
    HttpResponse {
        status: args.response.status.clone(),
        body: args.response.body.clone(),
        headers: vec![],
    }
}

// ============================================================================
// MAIN PREDICTION API - UPDATED FOR 4 EXCHANGES
// ============================================================================

#[update]
async fn predict_trade_cost(request: TradeRequest) -> Result<PredictionResponse, ApiError> {
    // Check if model is loaded (removed scaler check since we use hardcoded scaling)
    let model_loaded = STATE.with(|state| {
        let state = state.borrow();
        state.model.is_some()
    });

    if !model_loaded {
        return Err(ApiError::ModelNotLoaded);
    }

    let exchanges = vec!["binance", "kraken", "coinbase", "okx"];
    let mut quotes = Vec::new();
    let mut successful_exchanges = 0;

    for exchange in exchanges {
        match process_exchange_quote(exchange, &request).await {
            Ok(quote) => {
                quotes.push(quote);
                successful_exchanges += 1;
            },
            Err(e) => {
                ic_cdk::println!("Failed to get quote from {}: {:?}", exchange, e);
                continue;
            }
        }
    }

    ic_cdk::println!("Got quotes from {}/{} exchanges", successful_exchanges, 4);

    if quotes.is_empty() {
        return Err(ApiError::ExchangeError("No quotes available from any exchange".to_string()));
    }

    quotes.sort_by(|a, b| a.total_cost.partial_cmp(&b.total_cost).unwrap_or(std::cmp::Ordering::Equal));

    let best_venue = quotes[0].exchange.clone();
    let potential_savings = if quotes.len() > 1 {
        quotes.last().unwrap().total_cost - quotes[0].total_cost
    } else {
        0.0
    };

    let model_info = get_model_info();

    Ok(PredictionResponse {
        best_venue,
        potential_savings,
        quotes,
        model_info,
        timestamp: ic_cdk::api::time(),
    })
}

async fn process_exchange_quote(exchange: &str, request: &TradeRequest) -> Result<ExchangeQuote, ApiError> {
    ic_cdk::println!("Processing quote for {} on {}", request.symbol, exchange);
    
    let market_data = fetch_market_data(exchange.to_string(), request.symbol.clone()).await?;
    
    // Check if we got valid market data
    if market_data.bids.is_empty() || market_data.asks.is_empty() {
        return Err(ApiError::ExchangeError(format!("No market data from {}", exchange)));
    }

    let features = calculate_features(&market_data, request)?;
    ic_cdk::println!("Calculated {} features for {}", features.len(), exchange);
    
    let predicted_slippage = predict_slippage(features)?;
    
    let quote_price = if request.side.to_lowercase() == "buy" {
        market_data.asks.get(0)
            .ok_or(ApiError::ExchangeError("No asks available".to_string()))?
            .0
    } else {
        market_data.bids.get(0)
            .ok_or(ApiError::ExchangeError("No bids available".to_string()))?
            .0
    };

    let (total_cost, fees) = calculate_total_cost(
        quote_price,
        predicted_slippage,
        exchange,
        &request.side,
        request.amount,
    )?;

    let recommendation_score = 1.0 / (total_cost + 1e-8);

    ic_cdk::println!("Quote from {}: price={:.2}, slippage={:.4}%, cost={:.2}", 
                     exchange, quote_price, predicted_slippage * 100.0, total_cost);

    Ok(ExchangeQuote {
        exchange: exchange.to_string(),
        symbol: request.symbol.clone(),
        quote_price,
        predicted_slippage,
        total_cost,
        fees,
        recommendation_score,
    })
}

fn calculate_total_cost(
    quote_price: f64,
    predicted_slippage: f64,
    exchange: &str,
    trade_side: &str,
    amount: f64,
) -> Result<(f64, HashMap<String, f64>), ApiError> {
    let exchange_fees = STATE.with(|state| {
        state.borrow().exchange_fees.get(exchange).cloned()
    }).ok_or(ApiError::ExchangeError(format!("Exchange {} not supported", exchange)))?;

    let trading_fee = exchange_fees.taker;
    
    let actual_price = if trade_side.to_lowercase() == "buy" {
        quote_price * (1.0 + predicted_slippage)
    } else {
        quote_price * (1.0 - predicted_slippage)
    };

    let gross_cost = amount * actual_price;
    let fee_cost = gross_cost * trading_fee;
    let total_cost = gross_cost + fee_cost;

    let mut fees = HashMap::new();
    fees.insert("trading_fee".to_string(), fee_cost);
    fees.insert("slippage_cost".to_string(), amount * (actual_price - quote_price).abs());
    fees.insert("total_fees".to_string(), fee_cost);

    Ok((total_cost, fees))
}

// ============================================================================
// ENHANCED HEALTH CHECK & UTILITY ENDPOINTS
// ============================================================================

#[query]
fn health_check() -> HashMap<String, String> {
    let mut status = HashMap::new();
    
    STATE.with(|state| {
        let state = state.borrow();
        status.insert("status".to_string(), "healthy".to_string());
        status.insert("model_loaded".to_string(), state.model.is_some().to_string());
        status.insert("scaling_method".to_string(), "hardcoded_robust_scaler".to_string());
        status.insert("model_type".to_string(), state.model_type.clone());
        status.insert("feature_count".to_string(), state.feature_names.len().to_string());
        status.insert("supported_exchanges".to_string(), "binance,kraken,coinbase,okx".to_string());
        status.insert("initialization_status".to_string(), state.initialization_status.clone());
        
        // Add detailed status for debugging
        if state.model.is_none() {
            status.insert("model_error".to_string(), "Model failed to load - check ONNX compatibility".to_string());
        }
        if state.feature_names.is_empty() {
            status.insert("features_error".to_string(), "Feature names failed to load".to_string());
        }
    });

    status
}

#[query]
fn get_supported_exchanges() -> Vec<String> {
    vec![
        "binance".to_string(), 
        "kraken".to_string(), 
        "coinbase".to_string(), 
        "okx".to_string()
    ]
}

// Debug endpoint to check what's happening with model loading
#[query]
fn debug_model_status() -> HashMap<String, String> {
    let mut debug_info = HashMap::new();
    
    STATE.with(|state| {
        let state = state.borrow();
        debug_info.insert("model_bytes_size".to_string(), MODEL_BYTES.len().to_string());
        debug_info.insert("scaling_method".to_string(), "hardcoded_arrays".to_string());
        debug_info.insert("scaler_center_length".to_string(), ROBUST_SCALER_CENTER.len().to_string());
        debug_info.insert("scaler_scale_length".to_string(), ROBUST_SCALER_SCALE.len().to_string());
        debug_info.insert("feature_names_count".to_string(), state.feature_names.len().to_string());
        debug_info.insert("model_loaded".to_string(), state.model.is_some().to_string());
        debug_info.insert("initialization_status".to_string(), state.initialization_status.clone());
        
        // Check if embedded assets are actually there
        debug_info.insert("feature_json_length".to_string(), FEATURE_NAMES_JSON.len().to_string());
        debug_info.insert("model_type_constant".to_string(), MODEL_TYPE.to_string());
    });

    debug_info
}

// Test endpoint for manual feature calculation
#[query]
fn test_feature_calculation() -> Result<Vec<f64>, ApiError> {
    // Create dummy market data for testing
    let test_market_data = MarketData {
        bids: vec![
            (100.0, 1.0), (99.5, 2.0), (99.0, 1.5), (98.5, 0.8), (98.0, 2.2)
        ],
        asks: vec![
            (100.5, 1.2), (101.0, 1.8), (101.5, 1.0), (102.0, 0.9), (102.5, 1.5)
        ],
        trades: vec![],
        timestamp: ic_cdk::api::time(),
    };

    let test_request = TradeRequest {
        symbol: "BTC/USDT".to_string(),
        amount: 1.0,
        side: "buy".to_string(),
        amount_usd: Some(100.0),
    };

    calculate_features(&test_market_data, &test_request)
}

// Export candid interface
ic_cdk::export_candid!();