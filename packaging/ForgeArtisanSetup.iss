; Inno Setup Script for ForgeArtisan
; Compiles into a single standalone ForgeArtisanSetup.exe with PATH modification task

#define MyAppName "ForgeArtisan"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ForgeArtisan Open Source"
#define MyAppURL "https://github.com/meta-models/forge-artisan"
#define MyAppExeName "forge-artisan.exe"

[Setup]
AppId={{8B2F36A7-69B2-4A73-98D1-C998B3C182A4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=ForgeArtisan-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addtopath"; Description: "Add ForgeArtisan to system PATH environment variable (recommended)"; GroupDescription: "System Integration:"; Flags: checkedonce
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "dist,build,.venv,workspace\runs\*"

[Icons]
Name: "{group}\ForgeArtisan Studio"; Filename: "{cmd}"; Parameters: "/k ""{app}\forge-artisan.bat"" ui"; WorkingDir: "{app}"
Name: "{autodesktop}\ForgeArtisan Studio"; Filename: "{cmd}"; Parameters: "/k ""{app}\forge-artisan.bat"" ui"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
; Add to User PATH if task is checked
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + UpperCase(Param) + ';', ';' + UpperCase(OrigPath) + ';') = 0;
end;

[Run]
Filename: "{app}\forge-artisan.bat"; Parameters: "status"; Description: "Verify Engine Connection"; Flags: nowait postinstall skipifsilent
