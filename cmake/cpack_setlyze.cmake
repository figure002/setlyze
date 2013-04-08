# CPack setlyze config

set (CPACK_GENERATORS "TGZ")
set (CPACK_SOURCE_GENERATORS "TGZ")
set (CPACK_STRIP_FILES ON)
set (CPACK_SOURCE_IGNORE_FILES ".git;.gitignore;build;doctrees;win32;.*.pyc;.*.pywc")

set (CPACK_DEBIAN_PACKAGE_NAME "setlyze")
set (CPACK_PACKAGE_DESCRIPTION_SUMMARY "Species settlement analyzer\n A tool for analyzing the settlement of species on SETL plates.")
set (CPACK_DEBIAN_PACKAGE_MAINTAINER "Serrano Pereira <serrano.pereira@gmail.com>")
set (CPACK_PACKAGE_CONTACT "serrano.pereira@gmail.com")
set (CPACK_DEBIAN_PACKAGE_DEPENDS "python (>=2.7), python (<3.0), python-gtk2, python-cairo, python-gobject, python-rpy, python-setuptools, r-base-core")

set (CPACK_DEBIAN_PACKAGE_SECTION "Science")
set (CPACK_DEBIAN_PACKAGE_VERSION ${CPACK_PACKAGE_VERSION})

set (CPACK_BINARY_RPM OFF)
set (CPACK_BINARY_DEB ON)
set (CPACK_BINARY_Z OFF)
set (CPACK_BINARY_TGZ OFF)

set (CPACK_SOURCE_TGZ ON)
set (CPACK_SOURCE_Z OFF)
set (CPACK_SOURCE_TZ OFF)
set (CPACK_SOURCE_TBZ2 OFF)

set (CPACK_PACKAGE_VERSION_MAJOR ${setlyze_VERSION_MAJOR})
set (CPACK_PACKAGE_VERSION_MINOR ${setlyze_VERSION_MINOR})
set (CPACK_PACKAGE_VERSION_PATCH ${setlyze_VERSION_PATCH})

include (CPack)

