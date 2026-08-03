[Setup]
AppName=SI Filings Pro
AppVersion=1.0.0
AppPublisher=Sharp Intell Technologies
AppPublisherURL=https://leadsharp.in/sifilings
AppSupportURL=https://leadsharp.in/sifilings/support
AppUpdatesURL=https://leadsharp.in/sifilings/updates
DefaultDirName={autopf}\SI Filings Pro
DefaultGroupName=SI Filings Pro
AllowNoIcons=yes
LicenseFile=
OutputBaseFilename=SI_Filings_Pro_Setup_v1.0.0
SetupIconFile=C:\RIYAS\Sharp INtell\SI Filings\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "C:\RIYAS\Sharp INtell\SI Filings\dist\SI_Filings_Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SI Filings Pro"; Filename: "{app}\SI_Filings_Pro.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\Uninstall SI Filings Pro"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SI Filings Pro"; Filename: "{app}\SI_Filings_Pro.exe"; Tasks: desktopicon; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\SI_Filings_Pro.exe"; Description: "{cm:LaunchProgram,SI Filings Pro}"; Flags: nowait postinstall skipifsilent
