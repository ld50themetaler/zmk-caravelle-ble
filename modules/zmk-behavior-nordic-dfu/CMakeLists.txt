# CMakeLists.txt for zmk-behavior-nordic-dfu
target_sources_ifdef(CONFIG_ZMK_BEHAVIOR_NORDIC_DFU app PRIVATE src/behavior_nordic_dfu.c)
target_include_directories_ifdef(CONFIG_ZMK_BEHAVIOR_NORDIC_DFU app PUBLIC include)
