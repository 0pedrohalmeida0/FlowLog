"""Testes do csv_export e csv_import: sanitização contra CSV Injection."""

import os
import tempfile
from unittest.mock import MagicMock

from csv_export import _csv_safe, exportar_inventario


class TestCsvSafe:
    """CR-08 / AL-03: _csv_safe neutraliza fórmula no Excel/Sheets."""

    def test_csv_safe_igualdade_string_normal(self):
        assert _csv_safe("Notebook") == "Notebook"
        assert _csv_safe("Mouse sem fio") == "Mouse sem fio"

    def test_csv_safe_prefixa_formula_igual(self):
        assert _csv_safe("=cmd|'/c calc'!A1") == "'=cmd|'/c calc'!A1"

    def test_csv_safe_prefixa_mais(self):
        assert _csv_safe("+1234567890") == "'+1234567890"

    def test_csv_safe_prefixa_menos(self):
        assert _csv_safe("-2+5+cmd|'/c calc'!A1") == "'-2+5+cmd|'/c calc'!A1"

    def test_csv_safe_prefixa_arroba(self):
        assert _csv_safe("@SUM(1+1)") == "'@SUM(1+1)"

    def test_csv_safe_prefixa_tab_cr(self):
        assert _csv_safe("\tinjection") == "'\tinjection"
        assert _csv_safe("\rinjection") == "'\rinjection"

    def test_csv_safe_none_vira_string_vazia(self):
        assert _csv_safe(None) == ""

    def test_csv_safe_string_vazia(self):
        assert _csv_safe("") == ""


class TestExportInventario:
    """CR-08: exportar_inventario sanitiza nome e fornecedor."""

    def test_export_sanitiza_nome_e_fornecedor(self):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "=cmd|'/c calc'!A1", 5, 10.50, "@evil"),
            (2, "Mouse sem fio", 3, 25.00, "ACME"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "out.csv")
            import builtins

            original = builtins.input
            builtins.input = lambda _: caminho
            try:
                exportar_inventario(mock_cursor)
            finally:
                builtins.input = original
            with open(caminho, encoding="utf-8-sig") as f:
                conteudo = f.read()
            # O nome malicioso foi prefixado com apóstrofo
            assert "'=cmd|'/c calc'!A1" in conteudo
            # Fornecedor malicioso também
            assert "'@evil" in conteudo
            # E o normal passou intacto
            assert "Mouse sem fio" in conteudo
            assert "ACME" in conteudo
