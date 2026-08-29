#!/usr/bin/env python3
import os, sys, argparse, hashlib, zipfile, json, shutil, subprocess

def encode_varint(val):
    res = bytearray()
    while True:
        b = val & 0x7F
        val >>= 7
        if val:
            res.append(b | 0x80)
        else:
            res.append(b)
            break
    return bytes(res)

def encode_field(field_num, wire_type, data):
    key = (field_num << 3) | wire_type
    return encode_varint(key) + data

def encode_varint_field(field_num, val):
    return encode_field(field_num, 0, encode_varint(val))

def encode_bytes_field(field_num, data):
    return encode_field(field_num, 2, encode_varint(len(data))+data)

def generate_ota_pure_python(bin_path, key_path, output_zip_path, sd_req=0x8C, hw_version=0):
    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import ec, utils
    except ImportError:
        print("'cryptography' python module is required.")
        return False

    with open(bin_path, "rb") as f:
        app_bin = f.read()

    with open(key_path, "rb") as f:
        priv_key = serialization.load_pem_private_key(f.read(), password=None)

    app_hash = hashlib.sha256(app_bin).digest()[::-1]
    hash_msg = encode_varint_field(1, 3) + encode_bytes_field(2, app_hash)

    init_cmd = (
        encode_varint_field(1, 0xFFFFFFFF) +
        encode_varint_field(2, hw_version) +
        encode_bytes_field(3, encode_varint(sd_req)) +
        encode_varint_field(4, 0) +
        encode_varint_field(5, 0) +
        encode_varint_field(6, 0) +
        encode_varint_field(7, len(app_bin)) +
        encode_bytes_field(8, hash_msg) +
        encode_varint_field(9, 1) +
        encode_bytes_field(10, bytes([0x08, 0x01, 0x12, 0x00]))
    )

    cmd_msg = encode_varint_field(1, 1) + encode_bytes_field(2, init_cmd)

    der_sig = priv_key.sign(init_cmd, ec.ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(der_sig)

    r_bytes = r.to_bytes(32, byteorder='little')
    s_bytes = s.to_bytes(32, byteorder='little')
    signature = r_bytes + s_bytes

    signed_cmd = (
        encode_bytes_field(1, cmd_msg) +
        encode_varint_field(2, 0) +
        encode_bytes_field(3, signature)
    )

    packet = encode_bytes_field(2, signed_cmd)

    bin_basename = os.path.basename(bin_path)
    dat_basename = os.path.splitext(bin_basename)[0] + '.dat'

    manifest_data = {
        'manifest': {
            'application': {
                'bin_file': bin_basename,
                'dat_file': dat_basename
            }
        }
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps(manifest_data, indent=4))
        zf.writestr(dat_basename, packet)
        zf.writestr(bin_basename, app_bin)

    print(f"Successfully generated OTA package: {output_zip_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Generate Nordic Secure DFU OTA package for Caravelle BLE')
    parser.add_argument('bin_file', help='Path to compiled zmk.bin file')
    parser.add_argument('-o', '--output', help='Output .zip path', default=None)
    parser.add_argument('-k', '--key', help='Path to private_key.pem', default=None)
    parser.add_argument('--sd-req', help='SoftDevice req ID (hex)', default='0x8C')
    parser.add_argument('--hw-version', help='Hardware version', type=int, default=0)

    args = parser.parse_args()

    if not os.path.isfile(args.bin_file):
        print('Error: Input binary %s not found.' % args.bin_file)
        sys.exit(1)

    default_key = os.path.join(os.path.dirname(__file__), '..', 'config', 'keys', 'private_key.pem')
    key_path = args.key or default_key
    if not os.path.isfile(key_path):
        print('Error: Private key %s not found.' % key_path)
        sys.exit(1)


    out_zip = args.output
    if not out_zip:
        base = os.path.splitext(args.bin_file)[0]
        out_zip = '%s_ota.zip' % base

    sd_req_val = int(args.sd_req, 16) if args.sd_req.startswith('0x') else int(args.sd_req)

    nrfutil_cmd = shutil.which('nrfutil')
    if nrfutil_cmd:
        cmd = [
            nrfutil_cmd, 'pkg', 'generate',
            '--hw-version', str(args.hw_version),
            '--sd-req', hex(sd_req_val),
            '--debug-mode',
            '--key-file', key_path,
            '--application', args.bin_file,
            out_zip
        ]
        res = subprocess.run(cmd)
        if res.returncode == 0:
            print('Successfully generated OTA package via nrfutil: %s' % out_zip)
            sys.exit(0)

    success = generate_ota_pure_python(args.bin_file, key_path, out_zip, sd_req=sd_req_val, hw_version=args.hw_version)
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
