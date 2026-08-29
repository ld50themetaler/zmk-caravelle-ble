#!/bin/bash
set -e

CONFIG_DIR="/home/ld50/zmk-caravelle-ble/config"
WORKSPACE_DIR="/home/ld50/zmk-workspace"
OUT_DIR="/home/ld50/zmk-caravelle-ble/build"
ARTIFACTS_DIR="$OUT_DIR/artifacts"

mkdir -p "$OUT_DIR"
mkdir -p "$ARTIFACTS_DIR"

echo "[1/3] Building ZMK firmware via Docker container..."
docker run --rm \
  -v "$CONFIG_DIR":/zmk-config:ro \
  -v "$WORKSPACE_DIR":/workspace \
  -v "$OUT_DIR":/output \
  -w /workspace \
  zmkfirmware/zmk-build-arm:stable bash -c '
  set -e
  west zephyr-export

  echo "=== Building Caravelle LEFT ==="
  west build -s zmk/app -d /output/left -b caravelle --pristine -- -DZMK_CONFIG=/zmk-config -DSHIELD=caravelle_left -DZMK_EXTRA_MODULES="/workspace/modules/zmk-feature-non-lipo-battery-management;/workspace/modules/prospector-zmk-module"

  echo "=== Building Caravelle RIGHT ==="
  west build -s zmk/app -d /output/right -b caravelle --pristine -- -DZMK_CONFIG=/zmk-config -DSHIELD=caravelle_right -DZMK_EXTRA_MODULES="/workspace/modules/zmk-feature-non-lipo-battery-management;/workspace/modules/prospector-zmk-module"
'


echo "[2/3] Collecting build artifacts..."
cp "$OUT_DIR/left/zephyr/zmk.bin" "$ARTIFACTS_DIR/caravelle_ble_left.bin"
if [ -f "$OUT_DIR/left/zephyr/zmk.hex" ]; then
  cp "$OUT_DIR/left/zephyr/zmk.hex" "$ARTIFACTS_DIR/caravelle_ble_left.hex"
fi

cp "$OUT_DIR/right/zephyr/zmk.bin" "$ARTIFACTS_DIR/caravelle_ble_right.bin"
if [ -f "$OUT_DIR/right/zephyr/zmk.hex" ]; then
  cp "$OUT_DIR/right/zephyr/zmk.hex" "$ARTIFACTS_DIR/caravelle_ble_right.hex"
fi

echo "[3/3] Generating Nordic Secure DFU OTA packages..."
python3 /home/ld50/zmk-caravelle-ble/tools/generate_ota.py \
  "$ARTIFACTS_DIR/caravelle_ble_left.bin" \
  -o "$ARTIFACTS_DIR/caravelle_ble_left_ota.zip"

python3 /home/ld50/zmk-caravelle-ble/tools/generate_ota.py \
  "$ARTIFACTS_DIR/caravelle_ble_right.bin" \
  -o "$ARTIFACTS_DIR/caravelle_ble_right_ota.zip"

echo ""
echo "======================================================="
echo "Build Successful! Artifacts are available in:"
echo "$ARTIFACTS_DIR"
ls -lh "$ARTIFACTS_DIR"
echo "======================================================="
