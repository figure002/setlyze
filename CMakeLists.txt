cmake_minimum_required (VERSION 2.6)
project (setlyze)

# The version number.
set (setlyze_VERSION_MAJOR 1)
set (setlyze_VERSION_MINOR 0)
set (setlyze_VERSION_PATCH 0)

# Pass some of the CMake settings to the post install script.
configure_file (
  "${PROJECT_SOURCE_DIR}/cmake/debian/postinst.in"
  "${PROJECT_BINARY_DIR}/cmake/debian/postinst"
  )

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

