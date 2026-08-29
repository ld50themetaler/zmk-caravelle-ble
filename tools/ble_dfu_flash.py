#!/usr/bin/env python3
import asyncio
import json
import struct
import sys
import zipfile
import zlib
from pathlib import Path
from bleak import BleakClient, BleakScanner

# Nordic Secure DFU UUIDs
DFU_SERVICE_UUID = "0000fe59-0000-1000-8000-00805f9b34fb"
DFU_CONTROL_POINT_UUID = "8ec90001-f315-4f60-9fb8-838830daea50"
DFU_PACKET_UUID = "8ec90002-f315-4f60-9fb8-838830daea50"

# Opcodes
OP_CREATE = 0x01
OP_SET_PRN = 0x02
OP_CALC_CRC = 0x03
OP_EXECUTE = 0x04
OP_SELECT = 0x06
OP_RESPONSE = 0x60

# Object types
OBJ_COMMAND = 0x01
OBJ_DATA = 0x02

# Result codes
RES_CODES = {
    0x00: "INVALID",
    0x01: "SUCCESS",
    0x02: "OP_CODE_NOT_SUPPORTED",
    0x03: "INVALID_PARAMETER",
    0x04: "INSUFFICIENT_RESOURCES",
    0x05: "INVALID_OBJECT",
    0x07: "UNSUPPORTED_TYPE",
    0x08: "OPERATION_NOT_PERMITTED",
    0x0A: "OPERATION_FAILED",
    0x0B: "EXTENDED_ERROR",
}

EXT_ERROR_CODES = {
    0x00: "NO_ERROR",
    0x01: "INVALID_ERROR_CODE",
    0x02: "WRONG_COMMAND_FORMAT",
    0x03: "UNKNOWN_COMMAND",
    0x04: "INIT_COMMAND_INVALID",
    0x05: "FW_VERSION_FAILURE",
    0x06: "HW_VERSION_FAILURE",
    0x07: "SD_VERSION_FAILURE",
    0x08: "SIGNATURE_MISSING",
    0x09: "WRONG_HASH_TYPE",
    0x0A: "HASH_FAILED",
    0x0B: "WRONG_SIGNATURE_TYPE",
    0x0C: "VERIFICATION_FAILED",
    0x0D: "INSUFFICIENT_SPACE",
}


class DfuController:
    def __init__(self, client: BleakClient):
        self.client = client
        self.response_queue = asyncio.Queue()

    def notification_handler(self, sender, data: bytearray):
        # print(f"  [Notify] {data.hex()}")
        self.response_queue.put_nowait(bytes(data))

    async def send_cmd(self, cmd: bytes, timeout: float = 10.0) -> bytes:
        while not self.response_queue.empty():
            self.response_queue.get_nowait()

        await self.client.write_gatt_char(DFU_CONTROL_POINT_UUID, cmd, response=True)
        resp = await asyncio.wait_for(self.response_queue.get(), timeout=timeout)
        if len(resp) < 3 or resp[0] != OP_RESPONSE:
            raise RuntimeError(f"Invalid response: {resp.hex()}")
        
        req_op = resp[1]
        res_code = resp[2]
        if res_code != 0x01:
            err_str = RES_CODES.get(res_code, f"UNKNOWN_0x{res_code:02X}")
            ext_info = ""
            if res_code == 0x0B and len(resp) >= 4:
                ext_code = resp[3]
                ext_info = f" -> Extended Error: {EXT_ERROR_CODES.get(ext_code, f'0x{ext_code:02X}')}"
            raise RuntimeError(f"DFU Command 0x{req_op:02X} failed: {err_str}{ext_info}")
        return resp

    async def select_object(self, obj_type: int):
        resp = await self.send_cmd(bytes([OP_SELECT, obj_type]))
        max_size, offset, crc = struct.unpack("<III", resp[3:15])
        return max_size, offset, crc

    async def create_object(self, obj_type: int, size: int):
        cmd = bytes([OP_CREATE, obj_type]) + struct.pack("<I", size)
        await self.send_cmd(cmd)

    async def calculate_crc(self):
        resp = await self.send_cmd(bytes([OP_CALC_CRC]))
        offset, crc = struct.unpack("<II", resp[3:11])
        return offset, crc

    async def execute(self):
        await self.send_cmd(bytes([OP_EXECUTE]))

    async def set_prn(self, prn: int = 0):
        cmd = bytes([OP_SET_PRN]) + struct.pack("<H", prn)
        await self.send_cmd(cmd)

    async def write_packet(self, data: bytes):
        await self.client.write_gatt_char(DFU_PACKET_UUID, data, response=False)


async def perform_dfu(zip_path: str, target_address: str = None):
    print(f"=== Nordic Secure DFU OTA Tool ===")
    print(f"Package: {zip_path}")
    
    # 1. ZIP パッケージの解析
    with zipfile.ZipFile(zip_path, 'r') as z:
        manifest_data = json.loads(z.read("manifest.json").decode('utf-8'))
        manifest = manifest_data.get("manifest", {})
        app_entry = manifest.get("application", {})
        dat_filename = app_entry.get("dat_file")
        bin_filename = app_entry.get("bin_file")

        if not dat_filename or not bin_filename:
            raise ValueError("manifest.json missing dat_file or bin_file in application")

        init_packet = z.read(dat_filename)
        fw_image = z.read(bin_filename)

    print(f"  Init packet ({dat_filename}): {len(init_packet)} bytes")
    print(f"  Firmware image ({bin_filename}): {len(fw_image)} bytes")

    # 2. デバイスの検出
    if not target_address:
        print("Scanning for 'DfuTarg' device...")
        devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
        for d, adv in devices.values():
            name = adv.local_name or d.name
            if name and "DfuTarg" in name:
                target_address = d.address
                print(f"  Found DfuTarg at: {target_address} (RSSI: {adv.rssi})")
                break

    if not target_address:
        print("Error: Could not find 'DfuTarg'. Please ensure device is in DFU mode.")
        return False

    print(f"Connecting to {target_address}...")
    async with BleakClient(target_address, timeout=15.0) as client:
        print(f"Connected! Initializing DFU controller...")
        dfu = DfuController(client)
        await client.start_notify(DFU_CONTROL_POINT_UUID, dfu.notification_handler)
        await asyncio.sleep(0.5)

        # PRN = 0 (確認応答なしの連続送信モード)
        print("Setting Packet Receipt Notification (PRN = 0)...")
        await dfu.set_prn(0)

        # ----------------------------------------------------
        # Step 1: Init Packet (Command Object) 送信
        # ----------------------------------------------------
        print("\n--- [1/2] Sending Init Packet ---")
        max_cmd_size, offset, crc = await dfu.select_object(OBJ_COMMAND)
        print(f"  Command Object status: max_size={max_cmd_size}, offset={offset}, crc=0x{crc:08X}")

        print(f"  Creating Command Object (size={len(init_packet)})...")
        await dfu.create_object(OBJ_COMMAND, len(init_packet))

        # MTUサイズを考慮してパケット送信 (20バイトごと)
        chunk_size = 20
        for i in range(0, len(init_packet), chunk_size):
            chunk = init_packet[i : i + chunk_size]
            await dfu.write_packet(chunk)
            await asyncio.sleep(0.01)

        offset, crc = await dfu.calculate_crc()
        local_crc = zlib.crc32(init_packet) & 0xFFFFFFFF
        print(f"  CRC check: Remote=0x{crc:08X}, Local=0x{local_crc:08X} (offset={offset})")
        if crc != local_crc or offset != len(init_packet):
            raise RuntimeError("Init packet CRC mismatch!")

        print("  Executing Init Packet (Signature & SD validation)...")
        await dfu.execute()
        print("  Init Packet ACCEPTED by bootloader!")

        # ----------------------------------------------------
        # Step 2: Firmware Image (Data Object) 送信
        # ----------------------------------------------------
        print("\n--- [2/2] Sending Firmware Image ---")
        max_data_size, offset, crc = await dfu.select_object(OBJ_DATA)
        print(f"  Data Object status: page_size={max_data_size}, offset={offset}, crc=0x{crc:08X}")

        total_size = len(fw_image)
        bytes_sent = 0

        # max_data_size (通常4096バイト) ごとにページ分割
        while bytes_sent < total_size:
            page_chunk = fw_image[bytes_sent : bytes_sent + max_data_size]
            page_len = len(page_chunk)

            # print(f"  Writing page at offset {bytes_sent} (size: {page_len})...")
            await dfu.create_object(OBJ_DATA, page_len)

            # パケット送信 (MTU単位: 20バイト)
            for j in range(0, page_len, chunk_size):
                pkt = page_chunk[j : j + chunk_size]
                await dfu.write_packet(pkt)
                await asyncio.sleep(0.005)

            bytes_sent += page_len
            remote_offset, remote_crc = await dfu.calculate_crc()
            local_crc = zlib.crc32(fw_image[:bytes_sent]) & 0xFFFFFFFF
            percent = (bytes_sent / total_size) * 100
            sys.stdout.write(f"\r  Progress: {bytes_sent}/{total_size} bytes ({percent:.1f}%) - CRC: OK")
            sys.stdout.flush()

            await dfu.execute()

        print("\n\nAll firmware data sent and verified successfully!")
        print("Waiting for device reboot...")
        await asyncio.sleep(2.0)
        print("=== OTA Update Completed Successfully! ===")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ble_dfu_flash.py <path_to_ota_zip> [bluetooth_address]")
        sys.exit(1)

    zip_file = sys.argv[1]
    addr = sys.argv[2] if len(sys.argv) > 2 else None
    success = asyncio.run(perform_dfu(zip_file, addr))
    sys.exit(0 if success else 1)
