; PCI Compliance Agent Installer Script for Inno Setup
; Download Inno Setup from: https://jrsoftware.org/isinfo.php

#define MyAppName "PCI Compliance Agent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://yourcompany.com"
#define MyAppExeName "pci-agent.exe"

[Setup]
; App information
AppId={{12345678-1234-1234-1234-123456789012}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\PCI-Compliance-Agent
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installers
OutputBaseFilename=pci-agent-installer-{#MyAppVersion}
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\pci-agent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.example.yaml"; DestDir: "{app}"; DestName: "config.yaml"; Flags: ignoreversion
Source: "launcher.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion isreadme
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Dirs]
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\reports"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName} Launcher"; Filename: "{app}\launcher.bat"; WorkingDir: "{app}"; IconFilename: "{app}\pci-agent.exe"
Name: "{group}\Configuration"; Filename: "notepad.exe"; Parameters: """{app}\config.yaml"""; IconFilename: "{sys}\shell32.dll"; IconIndex: 70
Name: "{group}\Logs Folder"; Filename: "{app}\logs"
Name: "{group}\Reports Folder"; Filename: "{app}\reports"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\launcher.bat"; WorkingDir: "{app}"; IconFilename: "{app}\pci-agent.exe"; Tasks: desktopicon

[Run]
Name: "{group}\Edit Configuration"; Filename: "notepad.exe"; Parameters: """{app}\config.yaml"""; Description: "Edit configuration file"; Flags: postinstall nowait skipifsilent unchecked
Name: "{group}\Start Agent"; Filename: "{app}\launcher.bat"; WorkingDir: "{app}"; Description: "Start the PCI Compliance Agent"; Flags: postinstall nowait skipifsilent shellexec

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Create start_agent.bat helper script
    SaveStringToFile(ExpandConstant('{app}\start_agent.bat'), 
      '@echo off' + #13#10 +
      'title PCI Compliance Agent' + #13#10 +
      'color 0A' + #13#10 +
      'echo.' + #13#10 +
      'echo ========================================' + #13#10 +
      'echo   Starting PCI Compliance Agent' + #13#10 +
      'echo ========================================' + #13#10 +
      'echo.' + #13#10 +
      'echo Server URL: http://localhost:3001' + #13#10 +
      'echo Mode: WebSocket (Remote Control)' + #13#10 +
      'echo.' + #13#10 +
      'echo Press Ctrl+C to stop the agent' + #13#10 +
      'echo ========================================' + #13#10 +
      'echo.' + #13#10 +
      '"%~dp0pci-agent.exe" --websocket-mode --server-url http://localhost:3001' + #13#10 +
      'echo.' + #13#10 +
      'echo ========================================' + #13#10 +
      'echo   Agent Stopped' + #13#10 +
      'echo ========================================' + #13#10 +
      'pause', False);
  end;
end;

[UninstallDelete]
Type: files; Name: "{app}\start_agent.bat"
Type: filesandordirs; Name: "{app}\logs\*"
Type: filesandordirs; Name: "{app}\reports\*"
