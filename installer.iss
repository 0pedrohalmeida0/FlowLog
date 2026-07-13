; ============================================================
; FlowLog — Inno Setup Script (v1.5 Licença)
; ============================================================
; Gera um instalador Windows .exe com wizard completo.
; Pré-requisito: Inno Setup 6.x (https://jrsoftware.org/isdl.php)
; Compilação: iscc installer.iss
; Output: Output/FlowLog_Setup_v1.5.0.exe
; ============================================================

#define MyAppName "FlowLog"
#define MyAppDisplayName "FlowLog - Gestão de Estoque"
#define MyAppVersion "1.5.0"
#define MyAppPublisher "Pedro Almeida"
#define MyAppURL "https://github.com/0pedrohalmeida0/FlowLog"
#define MyAppExeName "FlowLog.exe"
#define MyAppCopyright "© 2026 Pedro Almeida"

[Setup]
; ID único do app (gere novo se for fork)
AppId={{B5E8F9D2-1C3A-4E7B-9F8D-2A6C4E8B1D3F}
AppName={#MyAppName}
AppDisplayName={#MyAppDisplayName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
AppCopyright={#MyAppCopyright}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.md
InfoBeforeFile=docs\venda\INSTALL.md
OutputDir=Output
OutputBaseFilename=FlowLog_Setup_v{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; Windows 7 SP1 ou superior
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppDisplayName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDisplayName}
VersionInfoCopyright={#MyAppCopyright}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtopath"; Description: "Adicionar FlowLog ao PATH (para usar 'flowlog' no terminal)"; GroupDescription: "Opções avançadas:"

[Files]
; Binário principal
Source: "dist\FlowLog\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Schema do banco (para o setup wizard)
Source: "schema.sql"; DestDir: "{app}"; Flags: ignoreversion
; Documentação
Source: "docs\venda\*.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\logs"
Name: "{app}\backups"

[Icons]
Name: "{group}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppDisplayName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppDisplayName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpa dados de configuração do usuário
Type: filesandordirs; Name: "{userappdata}\FlowLog"

[Code]
// Hook: roda antes da instalação para verificar pré-requisitos
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // Verifica se MySQL está instalado (heurística simples)
  if not RegKeyExists(HKLM, 'SOFTWARE\MySQL AB\MySQL Server') and
     not RegKeyExists(HKLM, 'SOFTWARE\Wow6432Node\MySQL AB\MySQL Server') and
     not RegKeyExists(HKLM, 'SOFTWARE\MariaDB') then
  begin
    if MsgBox(
      'MySQL não foi detectado neste computador.' + #13#10 +
      'O FlowLog precisa de um MySQL rodando para funcionar.' + #13#10#13#10 +
      'Você pode:' + #13#10 +
      '  - Instalar MySQL agora: https://dev.mysql.com/downloads/installer/' + #13#10 +
      '  - Continuar mesmo assim e configurar depois' + #13#10#13#10 +
      'Continuar a instalação?',
      mbConfirmation, MB_YESNO
    ) = IDNO then
      Result := False;
  end;
end;
