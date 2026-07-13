# -*- mode: python ; coding: utf-8 -*-
# ============================================================
# FlowLog — PyInstaller spec (v1.5 Licença)
# ============================================================
# Gera um executável standalone Windows com tudo embutido.
# Uso: pyinstaller flowlog.spec
# Output: dist/FlowLog.exe
# ============================================================

import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(SPECPATH).resolve()
SRC = PROJECT_ROOT / "src"
ASSETS = PROJECT_ROOT / "assets"


# Hidden imports do mysql-connector (não detectados automaticamente)
HIDDEN_IMPORTS = [
    "mysql.connector",
    "mysql.connector.pooling",
    "mysql.connector.connection",
    "mysql.connector.cursor",
    "mysql.connector.errors",
    "mysql.connector.utils",
    "bcrypt",
    "dotenv",
    # Módulos próprios importados dinamicamente
    "src.licenca",
    "src.setup_wizard",
    "src.auto_update",
    "src.i18n",
    "src.main",
    "src.auth",
    "src.session",
    "src.database",
    "src.utils",
    "src.exceptions",
    "src.repositories.base",
    "src.repositories.produto_repository",
    "src.repositories.fornecedor_repository",
    "src.repositories.historico_repository",
    "src.repositories.log_edicoes_repository",
    "src.repositories.usuario_repository",
    "src.services.auth_service",
    "src.services.estoque_service",
    "src.services.fornecedor_service",
    "src.services.historico_service",
    "src.services.produto_service",
    "src.services.usuario_service",
    "src.backup",
    "src.cadastrar_usuario",
    "src.cadastro_interativo",
    "src.configurar_alerta",
    "src.csv_export",
    "src.csv_import",
    "src.editar_fornecedor",
    "src.editar_produto",
    "src.entrada",
    "src.excluir_fornecedor",
    "src.gerenciar_fornecedor",
    "src.listar_produtos",
    "src.logging_config",
    "src.login",
    "src.relatorio_curva",
    "src.saida_estoque",
    "src.ver_historico",
]

# Dados a incluir (não-Python)
DATAS = [
    (str(SCHEMA := PROJECT_ROOT / "schema.sql"), "schema.sql"),
    (str(PROJECT_ROOT / ".env.example"), ".env.example"),
    (str(PROJECT_ROOT / "CHANGELOG.md"), "CHANGELOG.md"),
    (str(PROJECT_ROOT / "README.md"), "README.md"),
]

# Binários
BINARIES = []

# Ícone (se existir)
icon_path = ASSETS / "icon.ico"
icon = str(icon_path) if icon_path.exists() else None


a = Analysis(
    [str(SRC / "__main__.py")],
    pathex=[str(SRC), str(PROJECT_ROOT)],
    binaries=BINARIES,
    datas=DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir módulos grandes não usados pra enxugar o .exe
        "tkinter",
        "test",
        "unittest",
        "pydoc",
        "doctest",
        "argparse",  # usado, mas exclui o resto da stdlib não usada
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="FlowLog",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # comprime o binário (precisa do UPX instalado)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI app — True
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)
