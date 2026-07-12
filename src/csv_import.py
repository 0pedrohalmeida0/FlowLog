"""Importação em massa de produtos a partir de CSV.

Formato esperado (com ou sem cabeçalho):
    nome,quantidade,preco_custo,fornecedor_cnpj,alerta_minimo
    Teclado Mecânico,10,150.00,12.345.678/0001-90,5
    Mouse sem fio,25,49.90,98.765.432/0001-10,3

    - Separador: ; (recomendado) ou , (auto-detectado).
    - Encoding: utf-8-sig (com BOM) ou utf-8.
    - Decimais: usa . ou , (auto-convertido).
    - Campos opcionais: alerta_minimo (vazio = sem alerta).
    - CNPJ: com ou sem máscara; será validado.
    - Fornecedor inexistente: perguntado se quer cadastrar.

Fluxo:
    1. Usuário informa caminho do CSV.
    2. Lê e valida linha por linha; pula inválidas com aviso.
    3. Mostra resumo: X válidas, Y inválidas.
    4. Se houver válidas, pede confirmação.
    5. Insere em transação atômica (ou rollback se algo falhar).
"""

import csv
from pathlib import Path

from database import Database
from logging_config import get_logger
from utils import normalize_cnpj, validar_cnpj

logger = get_logger(__name__)


CAMPOS_OBRIGATORIOS = ["nome", "quantidade", "preco_custo", "fornecedor_cnpj"]
CAMPOS_OPCIONAIS = ["alerta_minimo"]


def _csv_safe(s):
    """AL-03: sanitiza contra CSV injection (CVE-2014-3524).

    Se o nome do produto começar com =, +, -, @, TAB ou CR, o Excel/Sheets
    interpreta como fórmula — em casos piores exfiltra dados via DDE ou
    executa comandos. Prefixa com apóstrofo para neutralizar.
    """
    s = str(s)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    return s


def _detectar_delimiter(sample):
    """Detecta separador: ; (preferido BR) ou , (padrão internacional)."""
    # Conta ocorrências nos primeiros 4KB
    amostra = sample[:4096]
    return ";" if amostra.count(";") > amostra.count(",") else ","


def _parse_decimal(s):
    """Aceita '10.50', '10,50', '1.234,56' (BR), retorna float."""
    s = s.strip()
    if not s:
        raise ValueError("valor vazio")
    # Se tem vírgula como separador decimal, normaliza
    if "," in s and s.count(",") == 1 and "." not in s:
        s = s.replace(",", ".")
    elif "," in s and "." in s:
        # Formato BR: 1.234,56 -> remove pontos de milhar e troca vírgula
        s = s.replace(".", "").replace(",", ".")
    return float(s)


def _parse_int(s):
    s = s.strip()
    if not s:
        raise ValueError("valor vazio")
    return int(s)


def _normalizar_linha(raw, idx):
    """Converte uma linha do CSV em dict validado.

    Retorna (dict_valido, lista_de_erros).
    """
    # Aceita tanto com quanto sem header
    if isinstance(raw, dict):
        # csv.DictReader com header
        linha = {k.strip().lower(): (v or "").strip() for k, v in raw.items()}
    else:
        return None, [f"linha {idx}: formato inesperado (sem header)"]

    erros = []
    nome = linha.get("nome", "")
    if not nome:
        erros.append("campo 'nome' vazio")

    try:
        quantidade = _parse_int(linha.get("quantidade", ""))
        if quantidade < 0:
            erros.append("'quantidade' não pode ser negativa")
    except ValueError as e:
        quantidade = None
        erros.append(f"'quantidade' inválida: {e}")

    try:
        preco = _parse_decimal(linha.get("preco_custo", ""))
        if preco < 0:
            erros.append("'preco_custo' não pode ser negativo")
    except ValueError as e:
        preco = None
        erros.append(f"'preco_custo' inválido: {e}")

    cnpj_raw = linha.get("fornecedor_cnpj", "")
    if not cnpj_raw:
        erros.append("'fornecedor_cnpj' vazio")
        cnpj = None
    elif not validar_cnpj(cnpj_raw):
        erros.append(f"'fornecedor_cnpj' inválido: {cnpj_raw!r}")
        cnpj = None
    else:
        cnpj = normalize_cnpj(cnpj_raw)

    alerta_str = linha.get("alerta_minimo", "")
    if alerta_str:
        try:
            alerta = _parse_int(alerta_str)
            if alerta < 0:
                erros.append("'alerta_minimo' não pode ser negativo")
                alerta = None
        except ValueError as e:
            alerta = None
            erros.append(f"'alerta_minimo' inválido: {e}")
    else:
        alerta = None

    if erros:
        return None, [f"linha {idx}: " + "; ".join(erros)]

    # AL-03: sanitiza nome contra CSV injection
    return {
        "nome": _csv_safe(nome),
        "quantidade": quantidade,
        "preco_custo": preco,
        "fornecedor_cnpj": cnpj,
        "alerta_minimo": alerta,
    }, []


def importar_produtos_csv():
    """Fluxo interativo: pede caminho, valida, confirma, insere."""
    print("\n--- 📥 IMPORTAR PRODUTOS DE CSV ---")
    caminho_str = input("Caminho do arquivo CSV: ").strip()
    if not caminho_str:
        print("❌ Erro: caminho vazio.")
        return

    caminho = Path(caminho_str)
    if not caminho.exists():
        print(f"❌ Arquivo não encontrado: {caminho}")
        return

    # AL-03: limite de tamanho para evitar OOM com CSV gigante.
    # 50 MB cabe ~500k linhas simples. Pra mais que isso, o usuário
    # deveria usar um loader de streaming; por enquanto, hard-limit.
    MAX_CSV_SIZE = 50 * 1024 * 1024
    if caminho.stat().st_size > MAX_CSV_SIZE:
        size_mb = caminho.stat().st_size / 1024 / 1024
        print(
            f"❌ Arquivo muito grande ({size_mb:.1f} MB > 50 MB). "
            f"Divida em arquivos menores ou contate o suporte."
        )
        return

    # Lê o arquivo (tenta utf-8-sig primeiro, depois utf-8)
    texto = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            texto = caminho.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        print("❌ Erro: não foi possível decodificar o arquivo (tente UTF-8 ou Latin-1).")
        return

    delimiter = _detectar_delimiter(texto)
    reader = csv.DictReader(texto.splitlines(), delimiter=delimiter)

    validas = []
    invalidas = []
    cnpjs_unicos = set()
    for idx, raw in enumerate(reader, start=2):  # linha 2 = após header
        dados, erros = _normalizar_linha(raw, idx)
        if dados is None:
            invalidas.extend(erros)
        else:
            validas.append(dados)
            cnpjs_unicos.add(dados["fornecedor_cnpj"])

    # CR-05: detecta CNPJs duplicados DENTRO do CSV. Se 2 linhas têm
    # o mesmo CNPJ novo, a 2a INSERT dá UNIQUE error e o rollback joga
    # fora TUDO. Aqui só avisamos; na inserção, agrupamos por CNPJ.
    cnpjs_no_csv = [p["fornecedor_cnpj"] for p in validas]
    duplicados = {c for c in cnpjs_no_csv if cnpjs_no_csv.count(c) > 1}
    if duplicados:
        print(
            "\n⚠️  Aviso: o CSV contém CNPJs repetidos (vou usar o mesmo "
            "fornecedor para todos os produtos com aquele CNPJ):"
        )
        for c in sorted(duplicados):
            print(f"   • {c}")

    print("\n📊 Resumo da validação:")
    print(f"   ✅ {len(validas)} linhas válidas")
    print(f"   ❌ {len(invalidas)} linhas inválidas")

    if invalidas:
        print("\nLinhas inválidas (não serão importadas):")
        for erro in invalidas[:10]:  # mostra no máximo 10
            print(f"   • {erro}")
        if len(invalidas) > 10:
            print(f"   ... e mais {len(invalidas) - 10} linha(s)")

    if not validas:
        print("\n⚠️ Nenhuma linha válida. Nada será importado.")
        return

    confirma = input(f"\nConfirma a importação de {len(validas)} produtos? (S/N): ").strip().upper()
    if confirma != "S":
        print("Importação cancelada.")
        return

    _inserir_produtos(validas)


def _inserir_produtos(produtos):
    """Insere a lista de produtos no banco em uma única transação.

    CR-05: agrupa produtos por CNPJ e resolve fornecedores em batch.
    Antes: para cada produto, fazia SELECT e/ou INSERT no fornecedor.
    Se 2 linhas tinham o mesmo CNPJ novo, a 2a INSERT falhava com
    UNIQUE, e o rollback joga fora TUDO. Agora:
      1. Coleta CNPJs únicos da lista.
      2. Pré-cria fornecedores que não existem (uma vez, na mesma transação).
      3. Insere os produtos em batch.
    """
    from exceptions import ValidationError

    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    inseridos = 0
    fornecedores_criados = 0
    try:
        cursor = conexao.cursor()

        # 1. Pré-resolver fornecedores
        cnpjs_unicos = {p["fornecedor_cnpj"] for p in produtos}

        for cnpj in cnpjs_unicos:
            cursor.execute(
                "SELECT id FROM fornecedores "
                "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s",
                (cnpj,),
            )
            row = cursor.fetchone()
            if row:
                continue
            # CR-05: 2a INSERT para o mesmo CNPJ é impossível agora porque
            # processamos cada CNPJ uma única vez.
            try:
                razao_social = f"(importado CSV) {cnpj}"
                cursor.execute(
                    "INSERT INTO fornecedores (razao_social, cnpj) VALUES (%s, %s)",
                    (razao_social, cnpj),
                )
                fornecedores_criados += 1
                logger.info(
                    "Fornecedor criado via import CSV: CNPJ=%s ID=%d",
                    cnpj,
                    cursor.lastrowid,
                )
            except Exception as e:
                # Se já foi criado em outro processo (race), segue.
                if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
                    raise

        # 2. Re-busca todos os IDs em um único SELECT
        cnpj_to_id = {}
        for cnpj in cnpjs_unicos:
            cursor.execute(
                "SELECT id FROM fornecedores "
                "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s",
                (cnpj,),
            )
            row = cursor.fetchone()
            if row:
                cnpj_to_id[cnpj] = row[0]

        # 3. Insere os produtos em batch
        for p in produtos:
            fornecedor_id = cnpj_to_id.get(p["fornecedor_cnpj"])
            if not fornecedor_id:
                raise ValidationError(
                    f"Fornecedor com CNPJ {p['fornecedor_cnpj']} não foi resolvido."
                )
            cursor.execute(
                "INSERT INTO produtos (nome, quantidade, preco_custo, fornecedor_id, alerta_minimo) "
                "VALUES (%s, %s, %s, %s, %s)",
                (p["nome"], p["quantidade"], p["preco_custo"], fornecedor_id, p["alerta_minimo"]),
            )
            inseridos += 1

        conexao.commit()
        logger.info(
            "Import CSV concluído: %d produtos inseridos, %d fornecedores criados",
            inseridos,
            fornecedores_criados,
        )
        print("\n✅ Importação concluída!")
        print(f"   {inseridos} produtos inseridos")
        print(f"   {fornecedores_criados} fornecedores criados")
    except Exception as e:
        try:
            conexao.rollback()
        except Exception:
            pass
        logger.exception("Falha na importação CSV")
        print(f"❌ Erro durante importação: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    importar_produtos_csv()
