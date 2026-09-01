#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_DIR="/home/ld50/zmk-workspace"
OUT_DIR="$REPO_DIR/artifacts"

mkdir -p "$OUT_DIR"

echo "========================================================="
echo " Fast Local Build for Caravelle BLE (with Docker)"
echo " Source: $REPO_DIR"
echo " Output: $OUT_DIR"
echo "========================================================="

# 1. Build Left (Central)
echo ""
echo ">>> [1/4] Building Left (Central)..."
docker run --rm \
  -v "$WORKSPACE_DIR":/workspace \
  -v "$REPO_DIR":/workspace/config/zmk-caravelle-ble \
  -w /workspace \
  zmkfirmware/zmk-build-arm:stable \
  bash -c "west zephyr-export >/dev/null 2>&1 && \
           west build -s zmk/app -d .build/caravelle_left -b caravelle -- \
             -DZMK_CONFIG=/workspace/config/zmk-caravelle-ble/config \
             -DSHIELD=caravelle_left \
             -DCONFIG_ZMK_SPLIT=y \
             -DCONFIG_ZMK_SPLIT_ROLE_CENTRAL=y \
             -DZMK_EXTRA_MODULES='/workspace/modules/zmk-feature-non-lipo-battery-management;/workspace/modules/prospector-zmk-module'"

cp "$WORKSPACE_DIR/.build/caravelle_left/zephyr/zmk.hex" "$OUT_DIR/caravelle_left_central.hex"
cp "$WORKSPACE_DIR/.build/caravelle_left/zephyr/zmk.bin" "$OUT_DIR/caravelle_left_central.bin"

# 2. Build Right (Peripheral)
echo ""
echo ">>> [2/4] Building Right (Peripheral)..."
docker run --rm \
  -v "$WORKSPACE_DIR":/workspace \
  -v "$REPO_DIR":/workspace/config/zmk-caravelle-ble \
  -w /workspace \
  zmkfirmware/zmk-build-arm:stable \
  bash -c "west zephyr-export >/dev/null 2>&1 && \
           west build -s zmk/app -d .build/caravelle_right -b caravelle -- \
             -DZMK_CONFIG=/workspace/config/zmk-caravelle-ble/config \
             -DSHIELD=caravelle_right \
             -DCONFIG_ZMK_SPLIT=y \
             -DCONFIG_ZMK_SPLIT_ROLE_CENTRAL=n \
             -DZMK_EXTRA_MODULES='/workspace/modules/zmk-feature-non-lipo-battery-management;/workspace/modules/prospector-zmk-module'"

cp "$WORKSPACE_DIR/.build/caravelle_right/zephyr/zmk.hex" "$OUT_DIR/caravelle_right_peripheral.hex"
cp "$WORKSPACE_DIR/.build/caravelle_right/zephyr/zmk.bin" "$OUT_DIR/caravelle_right_peripheral.bin"

# 3. Generate OTA Packages
echo ""
echo ">>> [3/4] Generating Nordic Secure DFU OTA Packages..."
python3 "$REPO_DIR/tools/generate_ota.py" \
  --bin "$OUT_DIR/caravelle_left_central.bin" \
  --key "$REPO_DIR/config/keys/private_key.pem" \
  --app-version 1 \
  --hw-version 52 \
  --sd-req 0x00B6 \
  --out "$OUT_DIR/caravelle_left_central_ota.zip"

python3 "$REPO_DIR/tools/generate_ota.py" \
  --bin "$OUT_DIR/caravelle_right_peripheral.bin" \
  --key "$REPO_DIR/config/keys/private_key.pem" \
  --app-version 1 \
  --hw-version 52 \
  --sd-req 0x00B6 \
  --out "$OUT_DIR/caravelle_right_peripheral_ota.zip"

echo ""
echo "========================================================="
echo " [SUCCESS] Local Build & OTA Package Generation Complete!"
echo " Output files in $OUT_DIR:"
ls -lh "$OUT_DIR"
echo "========================================================="
