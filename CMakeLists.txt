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

# Pass some of the CMake settings to the setlyze script.
configure_file (
  "${PROJECT_SOURCE_DIR}/scripts/setlyze.in"
  "${PROJECT_BINARY_DIR}/scripts/setlyze"
)

# Add the install targets.
install (FILES setlyze.pyw DESTINATION share/setlyze)
install (DIRECTORY setlyze DESTINATION share/setlyze)
install (DIRECTORY appdirs DESTINATION share/setlyze)
install (PROGRAMS ${PROJECT_BINARY_DIR}/scripts/setlyze DESTINATION bin)

# Add the install targets for the application icons.
install (FILES graphics/icons/setlyze-16.png DESTINATION share/icons/hicolor/16x16/apps RENAME setlyze.png)
install (FILES graphics/icons/setlyze-22.png DESTINATION share/icons/hicolor/22x22/apps RENAME setlyze.png)
install (FILES graphics/icons/setlyze-32.png DESTINATION share/icons/hicolor/32x32/apps RENAME setlyze.png)
install (FILES graphics/icons/setlyze-48.png DESTINATION share/icons/hicolor/48x48/apps RENAME setlyze.png)
install (FILES graphics/icons/setlyze-128.png DESTINATION share/icons/hicolor/128x128/apps RENAME setlyze.png)
install (FILES graphics/icons/setlyze-48.svg DESTINATION share/icons/hicolor/scalable/apps RENAME setlyze.svg)
install (FILES graphics/icons/setlyze.desktop DESTINATION share/applications)

# Add the install targets for the test data.
#install (DIRECTORY test-data DESTINATION share/setlyze)

# Uninstall target.
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/cmake_uninstall.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
    IMMEDIATE @ONLY
)

add_custom_target(uninstall
    COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake
)
