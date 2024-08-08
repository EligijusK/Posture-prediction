;NSIS Modern User Interface
;Basic Example Script
;Written by Joost Verburg

;--------------------------------
;Include Modern UI

!include "MUI2.nsh"
!include LogicLib.nsh

;--------------------------------
;General

;Name and file
Unicode True

!define ACT_ICON "ico.ico"
!define LNK_ARGS ""
OutFile "SitYEA Install.exe"
Name "SitYEA"

;Default installation folder
InstallDir "$LOCALAPPDATA\SitYEA"

;Get installation folder from registry if available
InstallDirRegKey HKCU "Software\SitYEA" ""

;Request application privileges for Windows Vista
RequestExecutionLevel user

Icon "bin\${ACT_ICON}"

;--------------------------------
;Interface Settings

!define MUI_ABORTWARNING

;--------------------------------
;Pages

;   !insertmacro MUI_PAGE_LICENSE "${NSISDIR}\Docs\Modern UI\License.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

!define REALSENSE_SDK_VER "2.45.0.3212"
; !define DEBUG_MODE

Section "Application" SecMain
    SectionIn RO ;Make it read-only
    
    SetOutPath "$INSTDIR"

    ;Store installation folder
    WriteRegStr HKCU "Software\SitYEA" "" $INSTDIR
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SitYEA" "DisplayName" "SitYEA"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SitYEA" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    File "bin\ico.ico"

    ; !ifndef DEBUG_MODE
    ;     File /nonfatal /a /r /x ".access" "build\"
    ; !endif

    FileOpen $9 .access w ;Opens a Empty File and fills it
    FileWrite $9 "{\"passwordAccess\": \"20210309\"}"
    FileClose $9 ;Closes the filled file
    
    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Start Menu Shortcuts" SecShortcutsStartMenu
    SetShellVarContext current
    CreateDirectory "$SMPROGRAMS\SitYEA"
    CreateShortCut "$SMPROGRAMS\SitYEA\SitYEA.lnk" "$INSTDIR\SitYEA.exe" "-- ${LNK_ARGS}" "$INSTDIR\${ACT_ICON}" 0
    CreateShortCut "$SMPROGRAMS\SitYEA\SitYEA - Small.lnk" "$INSTDIR\SitYEA.exe" "-- --width=720 ${LNK_ARGS}" "$INSTDIR\${ACT_ICON}" 0
    ; CreateShortCut "$SMPROGRAMS\SitYEA\SitYEA Recorder.lnk" "$INSTDIR\recorder.exe"
    CreateShortCut "$SMPROGRAMS\SitYEA\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Desktop Shortcut" SecShortcut
    SetShellVarContext current
    CreateShortCut "$DESKTOP\SitYEA.lnk" "$INSTDIR\SitYEA.exe" "-- ${LNK_ARGS}" "$INSTDIR\${ACT_ICON}" 0
SectionEnd

; !ifndef DEBUG_MODE
;     Section "Realsense SDK ${REALSENSE_SDK_VER}" SecRealsense
;         SetOutPath "$INSTDIR"
;         File "dist\Intel.RealSense.SDK-WIN10-${REALSENSE_SDK_VER}.exe"
;         ExecWait "Intel.RealSense.SDK-WIN10-${REALSENSE_SDK_VER}.exe"
;     SectionEnd

;     Section "Visual Studio C++" SecRedist
;         SetOutPath "$INSTDIR"
;         File "dist\VC_redist.x64.exe"
;         ExecWait "VC_redist.x64.exe"
;     SectionEnd
; !endif


Section /o "Desktop Shortcut (Small Resolution)" SecShortcutSmall
    SetShellVarContext current
    CreateShortCut "$DESKTOP\SitYEA - Small.lnk" "$INSTDIR\SitYEA.exe" "-- --width=720 ${LNK_ARGS}" "$INSTDIR\${ACT_ICON}" 0
SectionEnd


; Section /o "Desktop Shortcut For Debug Recorder" SecShortcutRecorder
;     SetShellVarContext current
;     CreateShortCut "$DESKTOP\SitYEA Recorder.lnk" "$INSTDIR\recorder.exe"
; SectionEnd

;--------------------------------
;Descriptions

    ;Language strings
    LangString DESC_SecMain ${LANG_ENGLISH} "Main Application."
    LangString DESC_SecShortcut ${LANG_ENGLISH} "Create desktop shortcut."
    LangString DESC_SecShortcutsStartMenu ${LANG_ENGLISH} "Create start menu shortcuts."
    LangString DESC_SecShortcutSmall ${LANG_ENGLISH} "Create desktop shortcut for small screens."
    LangString DESC_SecShortcutRecorder ${LANG_ENGLISH} "Create recorder desktop shortcut."
    !ifndef DEBUG_MODE
        LangString DESC_SecRealsense ${LANG_ENGLISH} "Install Realsense SDK ${REALSENSE_SDK_VER}."
        LangString DESC_SecRedist ${LANG_ENGLISH} "Install Visual Studio C++ 2015-2019 redistributable."
    !endif

    ;Assign language strings to sections
    !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
        !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
        !insertmacro MUI_DESCRIPTION_TEXT ${SecShortcut} $(DESC_SecShortcut)
        !insertmacro MUI_DESCRIPTION_TEXT ${SecShortcutsStartMenu} $(DESC_SecShortcutsStartMenu)
        !insertmacro MUI_DESCRIPTION_TEXT ${SecShortcutSmall} $(DESC_SecShortcutSmall)
        !insertmacro MUI_DESCRIPTION_TEXT ${SecShortcutRecorder} $(DESC_SecShortcutRecorder)
        !ifndef DEBUG_MODE
            !insertmacro MUI_DESCRIPTION_TEXT ${SecRealsense} $(DESC_SecRealsense)
            !insertmacro MUI_DESCRIPTION_TEXT ${SecRedist} $(DESC_SecRedist)
        !endif
    !insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"
    Delete "$INSTDIR\Uninstall.exe"

    Delete "$DESKTOP\SitYEA.lnk"
    Delete "$DESKTOP\SitYEA - Small.lnk"
    ; Delete "$DESKTOP\SitYEA Recorder.lnk"

    RMDir /r "$SMPROGRAMS\SitYEA"
    RMDir /r "$INSTDIR"

    DeleteRegKey /ifempty HKCU "Software\SitYEA"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SitYEA"
SectionEnd