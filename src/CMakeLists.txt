cmake_minimum_required (VERSION 2.6)
project (setlyze-core)

# Set the install prefix.
set (CMAKE_INSTALL_PREFIX /usr)

# Pass some of the CMake settings to the setlyze script.
configure_file (
  "${PROJECT_SOURCE_DIR}/scripts/setlyze.in"
  "${PROJECT_BINARY_DIR}/scripts/setlyze"
  )

# Add the install targets.
install (FILES setlyze.pyw DESTINATION share/setlyze)
install (DIRECTORY setlyze DESTINATION share/setlyze)
install (PROGRAMS ${PROJECT_BINARY_DIR}/scripts/setlyze DESTINATION bin)

# Add the install targets for the application icons.
#install (FILES ../icons/setlyze-48.svg DESTINATION share/icons/hicolor/scalable/apps RENAME setlyze.svg)

# Add the install targets for the test data.
#install (DIRECTORY ../test-data DESTINATION share/setlyze)
