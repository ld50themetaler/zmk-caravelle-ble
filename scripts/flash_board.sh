#!/bin/bash
set -e

SIDE=$1
if [ "$SIDE" != "left" ] && [ "$SIDE" != "right" ]; then
    echo "Usage: $0 [left|right]"
    exit 1
fi

HEX_FILE="/home/ld50/zmk-caravelle-ble/firmware/caravelle_${SIDE}_full_bundle.hex"
if [ ! -f "$HEX_FILE" ]; then
    echo "Error: Bundle HEX file not found: $HEX_FILE"
    exit 1
fi

echo "========================================================="
echo " Flashing Caravelle BLE [${SIDE^^}] with Full Bundle HEX"
echo " Target: SoftDevice S132 + Secure DFU Bootloader + ZMK"
echo " File  : $HEX_FILE"
echo "========================================================="

openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c "init; reset init; halt; nrf5 mass_erase; program $HEX_FILE verify reset; exit"


echo ""
echo "========================================================="
echo " [SUCCESS] Caravelle BLE [${SIDE^^}] Flashing Complete!"
echo " The board has been reset and is now running ZMK."
echo " It is also ready for future wireless BLE OTA updates."
echo "========================================================="
