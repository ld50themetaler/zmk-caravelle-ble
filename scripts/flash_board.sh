#!/bin/bash
set -e

SIDE=$1
if [ "$SIDE" != "left" ] && [ "$SIDE" != "right" ]; then
    echo "Usage: $0 [left|right]"
    exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEX_FILE="${HEX_FILE:-$REPO_DIR/firmware/caravelle_${SIDE}_full_bundle.hex}"

if [ ! -f "$HEX_FILE" ]; then
    # Fallback to artifacts if available
    ALT_HEX="$REPO_DIR/artifacts/caravelle_${SIDE}_central.hex"
    if [ "$SIDE" = "right" ]; then
        ALT_HEX="$REPO_DIR/artifacts/caravelle_${SIDE}_peripheral.hex"
    fi
    if [ -f "$ALT_HEX" ]; then
        HEX_FILE="$ALT_HEX"
    else
        echo "Error: HEX file not found: $HEX_FILE"
        echo "Please build the firmware first or place the bundle HEX in $REPO_DIR/firmware/"
        exit 1
    fi
fi

echo "========================================================="
echo " Flashing Caravelle BLE [${SIDE^^}] via ST-Link / OpenOCD"
echo " Target HEX: $HEX_FILE"
echo "========================================================="

openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c "init; reset init; halt; nrf5 mass_erase; program $HEX_FILE verify reset; exit"

echo ""
echo "========================================================="
echo " [SUCCESS] Caravelle BLE [${SIDE^^}] Flashing Complete!"
echo " The board has been reset and is now running ZMK."
echo "========================================================="