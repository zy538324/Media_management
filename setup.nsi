!include "MUI2.nsh"

Name "Media Management Setup"
OutFile "setup.exe"
InstallDir "$PROGRAMFILES\MediaManagement"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
  SetOutPath $INSTDIR
  File /r "B:\Code\Media_management Code\*"

  # Run the batch script
  nsExec::ExecToLog '"$INSTDIR\setup.bat"'
SectionEnd