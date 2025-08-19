#!/bin/bash

echo "=== Trade Predictor Canister Diagnostics ==="
echo

# Check if files exist
echo "1. Checking asset files..."
if [ -f "src/ai/assets/model.onnx" ]; then
    model_size=$(stat -f%z "src/ai/assets/model.onnx" 2>/dev/null || stat -c%s "src/ai/assets/model.onnx" 2>/dev/null)
    echo "✓ model.onnx exists (size: $model_size bytes)"
else
    echo "✗ model.onnx NOT FOUND"
fi

if [ -f "src/ai/assets/scaler.onnx" ]; then
    scaler_size=$(stat -f%z "src/ai/assets/scaler.onnx" 2>/dev/null || stat -c%s "src/ai/assets/scaler.onnx" 2>/dev/null)
    echo "✓ scaler.onnx exists (size: $scaler_size bytes)"
else
    echo "✗ scaler.onnx NOT FOUND"
fi

if [ -f "src/ai/assets/features.json" ]; then
    echo "✓ features.json exists"
    echo "  Feature count: $(cat src/ai/assets/features.json | jq length 2>/dev/null || echo 'unknown')"
else
    echo "✗ features.json NOT FOUND"
fi

echo

# Check canister status
echo "2. Checking canister health..."
dfx canister call ai health_check

echo

echo "3. Getting debug information..."
dfx canister call ai get_debug_info

echo

echo "4. Testing fallback prediction..."
dfx canister call ai test_fallback_prediction

echo

echo "5. Testing individual exchanges..."
exchanges=("binance" "kraken")
for exchange in "${exchanges[@]}"; do
    echo "Testing $exchange..."
    dfx canister call ai test_exchange '("'$exchange'", "BTCUSDT")'
done

echo

echo "6. Attempting simple prediction..."
dfx canister call ai simple_predict '("BTC/USDT", 1.0, "buy")'

echo

echo "=== Recommendations ==="
echo "If models are not loading:"
echo "1. Check that your ONNX files are valid:"
echo "   python -c \"import onnx; print('Model valid:', onnx.checker.check_model('src/ai/assets/model.onnx'))\""
echo "   python -c \"import onnx; print('Scaler valid:', onnx.checker.check_model('src/ai/assets/scaler.onnx'))\""
echo
echo "2. Verify file sizes are reasonable (not 0 bytes or corrupted)"
echo
echo "3. Check Cargo.toml dependencies are correct for tract-onnx"
echo
echo "4. If models still fail, the canister will use fallback predictions"