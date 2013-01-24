cmake_minimum_required (VERSION 2.6)
project (setlyze)

# The version number.
set (setlyze_VERSION_MAJOR 0)
set (setlyze_VERSION_MINOR 2)
set (setlyze_VERSION_PATCH 0)

# Settings for creating the setlyze packages.
include (cmake/cpack_setlyze.cmake)

# Add a subdirectory to the build.
add_subdirectory (src)

# Uninstall target.
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/cmake_uninstall.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
    IMMEDIATE @ONLY)

add_custom_target(uninstall
    COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake)

