; ================================================================
; Inno Setup Script — Sistema de Estimulação BCI
; Autor: Igor Sforzin
; ================================================================
; Para compilar: abrir esse arquivo no Inno Setup Compiler
; Download Inno Setup: https://jrsoftware.org/isinfo.php
; ================================================================

#define AppName      "Sistema de Estimulação BCI"
#define AppVersion   "1.0"
#define AppPublisher "Igor Sforzin"
#define AppDir       "SistemaEstimulacao"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppDir}
DefaultGroupName={#AppName}
OutputDir=dist
OutputBaseFilename=SistemaEstimulacao_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=assets\icon.ico

; Mostra progresso bonito
ShowLanguageDialog=no
LanguageDetectionMethod=none

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
; ── Arquivos do sistema ──────────────────────────────────────
Source: "interface_nano.py";   DestDir: "{app}"; Flags: ignoreversion
Source: "signal_gen_nano.py";  DestDir: "{app}"; Flags: ignoreversion
Source: "main.c";              DestDir: "{app}"; Flags: ignoreversion
Source: "bootstrap.py";        DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*";            DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

; ── Dependências (coloque os instaladores na pasta deps\) ────
Source: "deps\python-installer.exe";  DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall
Source: "deps\xc8-installer.exe";     DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall

; ── avrdude bundled (copie a pasta avrdude\8.0.0-arduino1\ para deps\avrdude\) ──
Source: "deps\avrdude\*"; DestDir: "{app}\avrdude"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Atalho na área de trabalho
Name: "{autodesktop}\{#AppName}"; Filename: "{cmd}"; Parameters: "/c pythonw ""{app}\bootstrap.py"""; WorkingDir: "{app}"; IconFilename: "{app}\assets\icon.ico"; Comment: "Sistema de Estimulação BCI"

; Atalho no menu iniciar
Name: "{group}\{#AppName}"; Filename: "{cmd}"; Parameters: "/c pythonw ""{app}\bootstrap.py"""; WorkingDir: "{app}"; IconFilename: "{app}\assets\icon.ico"

; Atalho para desinstalar
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"

[Run]
; ── 1. Instala Python (silencioso, adiciona ao PATH) ─────────
Filename: "{tmp}\python-installer.exe"; Parameters: "/passive InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1"; StatusMsg: "Instalando Python..."; Flags: waituntilterminated

; ── 2. Instala XC8 (silencioso) ──────────────────────────────
Filename: "{tmp}\xc8-installer.exe"; Parameters: "/quiet"; StatusMsg: "Instalando XC8 Compiler..."; Flags: waituntilterminated

; ── 3. Instala libs Python ───────────────────────────────────
Filename: "{cmd}"; Parameters: "/c python -m pip install numpy pyserial --quiet"; StatusMsg: "Instalando bibliotecas Python..."; Flags: waituntilterminated runhidden

; ── 4. Abre o sistema ao final (opcional) ────────────────────
Filename: "{cmd}"; Parameters: "/c pythonw ""{app}\bootstrap.py"""; WorkingDir: "{app}"; Description: "Abrir o Sistema de Estimulação agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\build"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files;          Name: "{app}\pipeline_config.txt"
Type: files;          Name: "{app}\sinal_base.h"
