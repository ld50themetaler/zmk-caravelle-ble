#!/bin/bash
# Post-build wrapper for ZMK: generates signed DFU packages after build completes
# Inspired by QMK's nrfutil integration, adapted for ZMK with ECDSA P256 signing
#
# Usage:
#   bash post_build.sh [firmware_dir]
#
# Environment Variables:
#   NRFUTIL      - Path to nrf-util binary (default: nrfutil)
#   KEY_FILE     - Path to EC private key for ECDSA signing

FIRMWARE_DIR="${1:-./firmware}"
NRFUTIL="${NRFUTIL:-nrfutil}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If NRFUTIL not in PATH, try common locations
if ! command -v "$NRFUTIL" &> /dev/null 2>&1; then
    # Try workspace root
    if [[ -f "/zmk-workspace/nrfutil" ]]; then
        NRFUTIL="/zmk-workspace/nrfutil"
    elif [[ -f "$(pwd)/nrfutil" ]]; then
        NRFUTIL="$(pwd)/nrfutil"
    fi
fi

# Default key file location
if [[ -z "$KEY_FILE" ]]; then
    if [[ -f "/zmk-workspace/caravelle_bootloader/private_key.pem" ]]; then
        KEY_FILE="/zmk-workspace/caravelle_bootloader/private_key.pem"
    elif [[ -f "$SCRIPT_DIR/../../caravelle_bootloader/private_key.pem" ]]; then
        KEY_FILE="$SCRIPT_DIR/../../caravelle_bootloader/private_key.pem"
    fi
fi

if [[ ! -d "$FIRMWARE_DIR" ]]; then
    echo "[ERROR] Firmware directory not found: $FIRMWARE_DIR"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "Post-Build: Generating Signed DFU packages"
echo "════════════════════════════════════════════════════════"
echo "NRFUTIL: $NRFUTIL"
echo "KEY_FILE: ${KEY_FILE:-(unsigned mode)}"
echo ""

found_count=0
success_count=0

# Check if nrfutil is available
if ! command -v "$NRFUTIL" &> /dev/null; then
    echo "[ERROR] nrfutil not found at: $NRFUTIL"
    echo "Install from: https://www.nordicsemi.com/Products/Development-tools/nrf-util"
    exit 1
fi

for bin_file in "$FIRMWARE_DIR"/*.bin; do
    if [[ -f "$bin_file" ]]; then
        ((found_count++))
        base_name=$(basename "$bin_file" .bin)
        zip_file="$FIRMWARE_DIR/${base_name}.zip"
        
        echo "[DFU] Processing: $(basename "$bin_file")"
        
        # Build and execute nrfutil command
        # CRC検証のみ（ブートローダー設定v1対応）
        if "$NRFUTIL" nrf5sdk-tools pkg generate \
            --debug-mode \
            --hw-version 0 \
            --sd-req 0x78 \
            --application "$bin_file" \
            --application-version 0xFFFFFFFF \
            --app-boot-validation VALIDATE_GENERATED_CRC \
            --key-file "$KEY_FILE" \
            "$zip_file" 2>&1 | grep -v "WARNING"; then
            ((success_count++))
            echo "[✓] Created (ECDSA+CRC): $(basename "$zip_file")"
            echo ""
        else
            echo "[✗] Failed: $(basename "$bin_file")"
            echo ""
        fi
    fi
done

if [[ $found_count -eq 0 ]]; then
    echo "[WARNING] No .bin files found in $FIRMWARE_DIR"
    exit 1
fi

echo "════════════════════════════════════════════════════════"
echo "✓ DFU packages generated: $success_count / $found_count"
echo ""
echo "Files ready for NRF Toolbox:"
ls -lh "$FIRMWARE_DIR"/*.zip 2>/dev/null || echo "(none)"
echo ""
echo "Next: Use NRF Toolbox (iOS/Android) → DFU tab → Select file"
echo "════════════════════════════════════════════════════════"
echo ""