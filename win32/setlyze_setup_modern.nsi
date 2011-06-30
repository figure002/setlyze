; Script generated by the HM NIS Edit Script Wizard.

; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "SETLyze"
!define PRODUCT_VERSION "0.1.1"
!define PRODUCT_PUBLISHER "GiMaRIS"
!define PRODUCT_WEB_SITE "http://www.gimaris.com/"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\setlyze.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Language Selection Dialog Settings
!define MUI_LANGDLL_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_LANGDLL_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "NSIS:Language"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page
!insertmacro MUI_PAGE_LICENSE "..\COPYING"
; Components page
!insertmacro MUI_PAGE_COMPONENTS
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\setlyze.exe"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\docs\html\user_manual.html"
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "Dutch"
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "setlyze-${PRODUCT_VERSION}-bundle-win32.exe"
InstallDir "$PROGRAMFILES\GiMaRIS\SETLyze"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Section "SETLyze Core" SEC01
  SectionIn RO # Make this section read-only.
  SetOutPath "$INSTDIR"
  SetOverwrite try
  File /r "..\src\dist\*.*"
  CreateDirectory "$SMPROGRAMS\GiMaRIS\SETLyze"
  CreateShortCut "$SMPROGRAMS\GiMaRIS\SETLyze\SETLyze.lnk" "$INSTDIR\setlyze.exe"
  CreateShortCut "$DESKTOP\SETLyze.lnk" "$INSTDIR\setlyze.exe"
  CreateShortCut "$SMPROGRAMS\GiMaRIS\SETLyze\Documentation.lnk" "$INSTDIR\docs\html\index.html"
SectionEnd

Section "R 2.9.1" SEC02
  MessageBox MB_OK \
    "SETLyze requires R, a free software environment for statistical computing \
    and graphics. The installer for R 2.9.1 will now be started. You can choose \
    to abort this installer if you already have R 2.9.1 installed on your system. \
    Newer versions of R are not supported! You can safely install this version of \
    R next to other R versions on the same system."
  SetOutPath "$INSTDIR\dependencies"
  File "dependencies\R-2.9.1-win32.exe"
  ExecWait "$INSTDIR\dependencies\R-2.9.1-win32.exe"
  Delete "$INSTDIR\dependencies\R-2.9.1-win32.exe"
  RMDir "$INSTDIR\dependencies"
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME} Website.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\GiMaRIS\SETLyze\${PRODUCT_NAME} Website.lnk" "$INSTDIR\${PRODUCT_NAME} Website.url"
  CreateShortCut "$SMPROGRAMS\GiMaRIS\SETLyze\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\setlyze.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\setlyze.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "The core files for SETLyze."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} "SETLyze requires R 2.9.1, a free \
    software environment for statistical computing and graphics."
!insertmacro MUI_FUNCTION_DESCRIPTION_END


Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
!insertmacro MUI_UNGETLANGUAGE
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  RMDir /r "$SMPROGRAMS\GiMaRIS\SETLyze"
  RMDir "$SMPROGRAMS\GiMaRIS" # Remove the GiMaRIS Start Menu folder if empty.
  RMDir /r "$INSTDIR"
  RMDir "$PROGRAMFILES\GiMaRIS" # Remove the GiMaRIS Program Files folder if empty.
  Delete "$DESKTOP\SETLyze.lnk"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
