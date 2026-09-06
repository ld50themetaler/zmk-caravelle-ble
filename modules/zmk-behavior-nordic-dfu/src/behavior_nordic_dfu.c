/*
 * Copyright (c) 2026 The ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 */

#define DT_DRV_COMPAT zmk_behavior_nordic_dfu

#include <zephyr/device.h>
#include <zephyr/sys/reboot.h>
#include <zephyr/logging/log.h>
#include <nrfx_nvmc.h>

#include <drivers/behavior.h>
#include <zmk/behavior.h>

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

#define NRF_DFU_SETTINGS_PAGE_ADDR 0x0007F000
#define SETTINGS_BUFFER_WORDS      88   // 352 bytes (covers full 348-byte nrf_dfu_settings_t)
#define SETTINGS_CRC_DATA_LEN      88   // bytes from offset 4 to offset 92
#define ENTER_BUTTONLESS_DFU_WORD  (88 / 4) // index 22 in uint32_t words

static uint32_t calculate_crc32(const uint8_t *p_data, uint32_t size) {
    uint32_t crc = 0xFFFFFFFF;
    for (uint32_t i = 0; i < size; i++) {
        crc ^= p_data[i];
        for (uint32_t j = 8; j > 0; j--) {
            crc = (crc >> 1) ^ (0xEDB88320U & ((crc & 1) ? 0xFFFFFFFF : 0));
        }
    }
    return ~crc;
}

static int on_keymap_binding_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
    LOG_INF("Entering Nordic DFU Mode (buttonless)! Preserving app settings...");

    // Compact buffer for dfu settings (352 bytes instead of 4KB)
    static uint32_t settings_buf[SETTINGS_BUFFER_WORDS];

    // Read current settings from flash
    memcpy(settings_buf, (const void *)NRF_DFU_SETTINGS_PAGE_ADDR, sizeof(settings_buf));

    // Set enter_buttonless_dfu = 1
    // In Nordic SDK 12.3 bootloader:
    // When enter_buttonless_dfu is 1, bootloader enters DfuTarg AND automatically
    // resets enter_buttonless_dfu back to 0.
    // Therefore, if user cancels DFU and power-cycles the board, it boots normally back to ZMK!
    settings_buf[ENTER_BUTTONLESS_DFU_WORD] = 1;

    // Recalculate CRC32 over the 88 bytes following the CRC field (offset 4..92)
    settings_buf[0] = calculate_crc32((const uint8_t *)settings_buf + 4, SETTINGS_CRC_DATA_LEN);

    // Erase 4KB settings page and write back updated settings structure
    nrfx_nvmc_page_erase(NRF_DFU_SETTINGS_PAGE_ADDR);
    nrfx_nvmc_words_write(NRF_DFU_SETTINGS_PAGE_ADDR, settings_buf, SETTINGS_BUFFER_WORDS);

    // Reboot device into bootloader
    sys_reboot(SYS_REBOOT_WARM);

    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api behavior_nordic_dfu_driver_api = {
    .binding_pressed = on_keymap_binding_pressed,
    .locality = BEHAVIOR_LOCALITY_EVENT_SOURCE,
};

#define DFU_INST(n)                                                                                \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, NULL, NULL, POST_KERNEL,                                \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &behavior_nordic_dfu_driver_api);

DT_INST_FOREACH_STATUS_OKAY(DFU_INST)

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
