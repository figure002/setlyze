cmake_minimum_required (VERSION 2.6)
project (setlyze-core)

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
install (FILES ../icons/setlyze-16.png DESTINATION share/icons/hicolor/16x16/apps RENAME setlyze.png)
install (FILES ../icons/setlyze-22.png DESTINATION share/icons/hicolor/22x22/apps RENAME setlyze.png)
install (FILES ../icons/setlyze-32.png DESTINATION share/icons/hicolor/32x32/apps RENAME setlyze.png)
install (FILES ../icons/setlyze-48.png DESTINATION share/icons/hicolor/48x48/apps RENAME setlyze.png)
install (FILES ../icons/setlyze-128.png DESTINATION share/icons/hicolor/128x128/apps RENAME setlyze.png)
install (FILES ../icons/setlyze-48.svg DESTINATION share/icons/hicolor/scalable/apps RENAME setlyze.svg)
install (FILES ../icons/setlyze.desktop DESTINATION share/applications)

# Add the install targets for the test data.
#install (DIRECTORY ../test-data DESTINATION share/setlyze)
