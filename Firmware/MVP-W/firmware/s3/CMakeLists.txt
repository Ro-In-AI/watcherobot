cmake_minimum_required(VERSION 3.16)

# Add Watcher-Firmware components path
set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../Watcher-Firmware/components"
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(MVP-W-S3)

# Create SPIFFS partition image from spiffs/ directory
spiffs_create_partition_image(storage spiffs FLASH_IN_PROJECT)
