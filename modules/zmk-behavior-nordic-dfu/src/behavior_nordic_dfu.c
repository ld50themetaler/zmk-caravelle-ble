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

static int on_keymap_binding_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
    LOG_INF("Entering Nordic DFU Mode! Erasing settings page at 0x%08x...", NRF_DFU_SETTINGS_PAGE_ADDR);
    
    // Erase the DFU settings page. 
    // When settings page is erased, Nordic Secure DFU bootloader detects
    // !nrf_dfu_app_is_valid() and unconditionally starts Bluetooth DFU mode (DfuTarg).
    nrfx_nvmc_page_erase(NRF_DFU_SETTINGS_PAGE_ADDR);

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
