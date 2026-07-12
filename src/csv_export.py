"""Exportação de relatórios do FlowLog para CSV.

Formato gerado:
    - Encoding: utf-8-sig (BOM) — abre corretamente no Excel BR.
    - Separador: ; (padrão brasileiro, evita conflito com vírgula em números).
    - Decimais: , (padrão brasileiro).
    - Quebras de linha: \\r\\n (Excel-friendly).

Cada export recebe um cursor MySQL já com o SELECT executado e itera
sobre `fetchall()`. O caller controla o SQL.
"""

import csv
from datetime import datetime
from pathlib import Path

from logging_config import get_logger

# BA-02: imports no topo do módulo (em vez de dentro da função).
# Resolve a noqa:PLC0415 e elimina ciclos de import.
from relatorio_curva import _SQL_CURVA_ABC

logger = get_logger(__name__)


# CR-08: paridade com AL-03 (csv_import._csv_safe). O import sanitiza
# nomes, mas um produto cadastrado direto pela interface pode ter nome
# começando com =, +, -, @. Quando exportado pra CSV, o Excel/Sheets
# interpreta como fórmula e pode executar. Sanitizamos também no export.
def _csv_safe(s):
    """CR-08: neutraliza CSV injection (CVE-2014-3524) no export.

    Se o valor começar com =, +, -, @, TAB ou CR, prefixa com `'`
    para que o Excel/Sheets não interprete como fórmula.
    """
    s = str(s) if s is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    return s


# Defaults BR: utf-8-sig + ; + , + \r\n
_CSV_DEFAULTS = {
    "encoding": "utf-8-sig",
    "delimiter": ";",
    "lineterminator": "\r\n",
}


def _default_filename(prefix):
    """Gera um nome de arquivo timestamped dentro do cwd."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"flowlog_{prefix}_{ts}.csv"


def _ask_path(prefix):
    """Pergunta o caminho ao usuário, com default no cwd."""
    default = _default_filename(prefix)
    caminho = input(f"Caminho do arquivo CSV (Enter para '{default}'): ").strip()
    if not caminho:
        caminho = default
    return Path(caminho)


def _escrever_csv(caminho, headers, rows):
    """Escreve headers + rows em CSV no padrão BR."""
    with open(caminho, "w", newline="", encoding=_CSV_DEFAULTS["encoding"]) as f:
        writer = csv.writer(
            f,
            delimiter=_CSV_DEFAULTS["delimiter"],
            lineterminator=_CSV_DEFAULTS["lineterminator"],
        )
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


# ============================================================
# Inventário
# ============================================================


def exportar_inventario(cursor):
    """Exporta a lista de produtos para CSV.

    `cursor` deve ter executado o SELECT de produtos (com ou sem JOIN).
    Espera colunas: id, nome, quantidade, preco_custo, fornecedor_nome.
    """
    headers = ["ID", "Nome", "Quantidade", "Preço de Custo (R$)", "Fornecedor"]
    cursor.execute("""
        SELECT p.id, p.nome, p.quantidade, p.preco_custo,
               COALESCE(f.razao_social, '(sem fornecedor)') AS fornecedor
        FROM produtos p
        LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        ORDER BY p.id
        """)
    rows = []
    for pid, nome, qtd, preco, fornecedor in cursor.fetchall():
        # Formata decimal no padrão BR
        preco_str = f"{float(preco):.2f}".replace(".", ",")
        # CR-08: sanitiza campos de texto contra CSV injection
        rows.append([pid, _csv_safe(nome), qtd, preco_str, _csv_safe(fornecedor)])

    caminho = _ask_path("inventario")
    _escrever_csv(caminho, headers, rows)
    logger.info("Inventário exportado: %d linhas em %s", len(rows), caminho)
    print(f"✅ {len(rows)} produtos exportados para: {caminho}")


# ============================================================
# Histórico de movimentações
# ============================================================


def exportar_historico(cursor, tipo_filtro=None):
    """Exporta o histórico de movimentações.

    `tipo_filtro` (opcional): 'ENTRADA', 'SAIDA' ou None para todos.
    """
    headers = ["ID", "Data", "Tipo", "Produto", "Quantidade", "Usuário"]
    sql = """
        SELECT h.id, h.data_movimentacao, h.tipo, p.nome, h.quantidade,
               COALESCE(u.username, '(sistema)') AS usuario
        FROM historico_movimentacoes h
        JOIN produtos p ON h.produto_id = p.id
        LEFT JOIN usuarios u ON h.usuario_id = u.id
    """
    params = ()
    if tipo_filtro:
        sql += " WHERE UPPER(h.tipo) = %s"
        params = (tipo_filtro,)
    sql += " ORDER BY h.data_movimentacao DESC"

    cursor.execute(sql, params)
    rows = []
    for hid, data, tipo, produto, qtd, usuario in cursor.fetchall():
        # CR-08: sanitiza campos de texto
        rows.append(
            [
                hid,
                data.strftime("%Y-%m-%d %H:%M:%S"),
                tipo,
                _csv_safe(produto),
                qtd,
                _csv_safe(usuario),
            ]
        )

    sufixo = tipo_filtro.lower() if tipo_filtro else "completo"
    caminho = _ask_path(f"historico_{sufixo}")
    _escrever_csv(caminho, headers, rows)
    logger.info("Histórico exportado: %d linhas em %s", len(rows), caminho)
    print(f"✅ {len(rows)} movimentações exportadas para: {caminho}")


# ============================================================
# Curva ABC
# ============================================================


def exportar_curva_abc(cursor):
    """Exporta o resultado da Curva ABC.

    Espera que o `cursor` já executou a query da Curva ABC
    (vide relatorio_curva._SQL_CURVA_ABC) e está posicionado antes
    do fetchall. Aqui refazemos a query para manter a função independente.
    """
    headers = ["Classe", "Produto", "Saídas", "% Individual", "% Acumulado"]
    cursor.execute(_SQL_CURVA_ABC)
    rows = []
    for nome, total, pct, pct_acum, classe in cursor.fetchall():
        # CR-08: sanitiza o nome contra CSV injection
        rows.append(
            [
                classe,
                _csv_safe(nome),
                total,
                f"{float(pct):.2f}".replace(".", ","),
                f"{float(pct_acum):.2f}".replace(".", ","),
            ]
        )

    caminho = _ask_path("curva_abc")
    _escrever_csv(caminho, headers, rows)
    logger.info("Curva ABC exportada: %d linhas em %s", len(rows), caminho)
    print(f"✅ {len(rows)} produtos da Curva ABC exportados para: {caminho}")
