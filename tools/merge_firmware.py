#!/usr/bin/env python3
import os, sys, argparse
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

def main():
    parser = argparse.ArgumentParser(description="Merge SoftDevice + Bootloader + ZMK App into a single full bundle HEX for Caravelle BLE")
    parser.add_argument("--sd", dest="sd_path", default=os.environ.get("SOFTDEVICE_HEX"), help="Path to SoftDevice S132 v3.0 HEX")
    parser.add_argument("--bl", dest="bl_path", default=os.environ.get("BOOTLOADER_HEX"), help="Path to Secure DFU Bootloader HEX")
    parser.add_argument("--app", dest="app_path", help="Path to ZMK application HEX")
    parser.add_argument("-o", "--out", dest="out_path", help="Output merged HEX path")
    parser.add_argument("--batch", action="store_true", help="Merge both left and right from artifacts/ into firmware/")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if args.batch:
        if not args.sd_path or not os.path.isfile(args.sd_path):
            print("Error: --sd or SOFTDEVICE_HEX environment variable must point to a valid SoftDevice HEX.")
            sys.exit(1)
        if not args.bl_path or not os.path.isfile(args.bl_path):
            print("Error: --bl or BOOTLOADER_HEX environment variable must point to a valid Bootloader HEX.")
            sys.exit(1)

        left_app = os.path.join(base_dir, "artifacts/caravelle_left_central.hex")
        right_app = os.path.join(base_dir, "artifacts/caravelle_right_peripheral.hex")
        out_dir = os.path.join(base_dir, "firmware")

        if not os.path.isfile(left_app) or not os.path.isfile(right_app):
            print(f"Error: Artifacts not found. Please run scripts/build_local.sh first.")
            sys.exit(1)

        print("=== Merging Left Bundle ===")
        merge_bundle(args.sd_path, args.bl_path, left_app, os.path.join(out_dir, "caravelle_left_full_bundle.hex"))
        print("\n=== Merging Right Bundle ===")
        merge_bundle(args.sd_path, args.bl_path, right_app, os.path.join(out_dir, "caravelle_right_full_bundle.hex"))
        return

    if not args.sd_path or not args.bl_path or not args.app_path or not args.out_path:
        parser.print_help()
        print("\nNote: You can also run with --batch if SOFTDEVICE_HEX and BOOTLOADER_HEX are set.")
        sys.exit(1)

    merge_bundle(args.sd_path, args.bl_path, args.app_path, args.out_path)

if __name__ == "__main__":
    main()