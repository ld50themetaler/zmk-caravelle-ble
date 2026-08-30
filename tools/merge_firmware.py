#!/usr/bin/env python3
import os, sys
import intelhex

def merge_bundle(sd_path, bl_path, app_path, out_path):
    ih = intelhex.IntelHex()
    
    sd = intelhex.IntelHex(sd_path)
    sd.start_addr = None
    
    bl = intelhex.IntelHex(bl_path)
    bl.start_addr = None
    
    app = intelhex.IntelHex(app_path)
    app.start_addr = None
    
    ih.merge(sd, overlap='error')
    ih.merge(bl, overlap='error')
    ih.merge(app, overlap='error')
    
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    ih.write_hex_file(out_path)
    print(f"Generated bundle: {out_path} ({os.path.getsize(out_path)} bytes)")
    print("Segments:", [(hex(s), hex(e)) for s, e in ih.segments()])

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sd_path = "/home/ld50/ble/nRF5_SDK_12.3.0_d7731ad/components/softdevice/s132/hex/s132_nrf52_3.0.0_softdevice.hex"
    bl_path = "/home/ld50/ble_caravelle_ble/qmk_firmware/caravelle_ble-bootloader.hex"
    
    left_app = os.path.join(base_dir, "build/left/zephyr/zmk.hex")
    right_app = os.path.join(base_dir, "build/right/zephyr/zmk.hex")
    out_dir = os.path.join(base_dir, "firmware")
    
    print("=== Merging Left Bundle ===")
    merge_bundle(sd_path, bl_path, left_app, os.path.join(out_dir, "caravelle_left_full_bundle.hex"))
    
    print("\n=== Merging Right Bundle ===")
    merge_bundle(sd_path, bl_path, right_app, os.path.join(out_dir, "caravelle_right_full_bundle.hex"))
