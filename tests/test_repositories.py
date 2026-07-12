"""Smoke + mock tests dos repositories.

Estratégia: mockar o Database e capturar o que é passado para
`cursor.execute(sql, params)`. Verifica que o SQL gerado tem o nome
da tabela certa, contém as colunas esperadas, e os parâmetros são
os mesmos do input.

Cobertura real dos repos (com MySQL ao vivo) fica pra v1.3+ quando
montarmos a suite de integração.
"""

from unittest.mock import MagicMock

from repositories.fornecedor_repository import FornecedorRepository
from repositories.historico_repository import HistoricoRepository
from repositories.log_edicoes_repository import LogEdicoesRepository
from repositories.produto_repository import ProdutoRepository
from repositories.usuario_repository import UsuarioRepository

# ============================================================
# Helpers
# ============================================================


def _mock_db_com_cursor():
    """Retorna (mock_db, mock_cursor) configurados.

    O mock_db.connect() devolve uma conexão que tem .cursor(),
    e o cursor.fetchone/fetchall devolvem os resultados configurados.
    """
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_db = MagicMock()
    mock_db.connect.return_value = mock_conn
    return mock_db, mock_conn, mock_cursor


def _captura_execute(mock_cursor):
    """Retorna (sql_str, params_tuple) da última chamada execute()."""
    assert mock_cursor.execute.called, "cursor.execute() não foi chamado"
    args, kwargs = mock_cursor.execute.call_args
    sql = args[0]
    params = args[1] if len(args) > 1 else kwargs.get("params", ())
    return sql, params


# ============================================================
# ProdutoRepository
# ============================================================


class TestProdutoRepository:
    def test_buscar_por_id_gera_sql_correto(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchone.return_value = {"id": 1, "nome": "X"}

        repo = ProdutoRepository(db=mock_db)
        result = repo.buscar_por_id(42)

        sql, params = _captura_execute(mock_cursor)
        assert "FROM produtos" in sql
        assert "WHERE id = %s" in sql
        assert params == (42,)
        assert result["nome"] == "X"

    def test_buscar_por_id_retorna_none_quando_nao_existe(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchone.return_value = None

        repo = ProdutoRepository(db=mock_db)
        assert repo.buscar_por_id(999) is None

    def test_listar_abaixo_do_minimo_faz_join(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchall.return_value = []

        repo = ProdutoRepository(db=mock_db)
        repo.listar_abaixo_do_minimo()

        sql, _ = _captura_execute(mock_cursor)
        assert "FROM produtos" in sql
        assert "LEFT JOIN fornecedores" in sql
        assert "alerta_minimo IS NOT NULL" in sql
        assert "p.quantidade <= p.alerta_minimo" in sql

    def test_criar_usa_transacao_e_retorna_lastrowid(self):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 99
        mock_db.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cursor)

        repo = ProdutoRepository(db=mock_db)
        novo_id = repo.criar(
            nome="Teclado",
            quantidade=10,
            preco_custo=50.0,
            fornecedor_id=1,
            alerta_minimo=5,
        )

        assert novo_id == 99
        # Verifica que transaction() foi usado (NÃO connect())
        mock_db.transaction.assert_called_once()
        mock_db.connect.assert_not_called()
        # SQL gerado
        args, _ = mock_cursor.execute.call_args
        assert "INSERT INTO produtos" in args[0]
        assert args[1] == ("Teclado", 10, 50.0, 1, 5)

    def test_atualizar_campos_constroi_set_dinamico(self):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_db.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cursor)

        repo = ProdutoRepository(db=mock_db)
        rc = repo.atualizar_campos(7, {"nome": "Mouse", "preco_custo": 25.0})

        assert rc == 1
        args, _ = mock_cursor.execute.call_args
        sql, params = args
        assert "UPDATE produtos SET" in sql
        assert "nome = %s" in sql
        assert "preco_custo = %s" in sql
        # WHERE id = ? deve ser o último param
        assert sql.strip().endswith("WHERE id = %s")
        # Parametros: nome, preco, id (na ordem)
        assert params == ("Mouse", 25.0, 7)

    def test_atualizar_campos_ignora_id_no_dict(self):
        """Tentativa de atualizar `id` deve ser silenciosamente ignorada."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_db.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cursor)

        repo = ProdutoRepository(db=mock_db)
        repo.atualizar_campos(7, {"id": 999, "nome": "Mouse"})

        args, _ = mock_cursor.execute.call_args
        sql, params = args
        # Não deve ter "SET id = ..." (PK protegida).
        # WHERE id = %s no final é ok (é o filtro, não atribuição).
        assert "SET id = %s" not in sql
        assert "SET nome = %s" in sql
        assert params == ("Mouse", 7)

    def test_atualizar_campos_vazio_retorna_zero(self):
        mock_db = MagicMock()
        repo = ProdutoRepository(db=mock_db)
        assert repo.atualizar_campos(7, {}) == 0
        mock_db.transaction.assert_not_called()

    def test_buscar_por_id_locked_cr04(self):
        """CR-04: SELECT ... FOR UPDATE dentro de uma transação existente."""
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchone.return_value = {"id": 7}
        mock_conn = MagicMock()
        repo = ProdutoRepository(db=mock_db)

        result = repo.buscar_por_id_locked(7, mock_conn, mock_cursor)

        assert result == {"id": 7}
        args, _ = mock_cursor.execute.call_args
        sql, params = args
        assert "FOR UPDATE" in sql
        assert "WHERE id = %s" in sql
        assert params == (7,)


# ============================================================
# FornecedorRepository
# ============================================================


class TestFornecedorRepository:
    def test_buscar_por_cnpj_normalizado(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchone.return_value = {"id": 1, "razao_social": "ACME"}

        repo = FornecedorRepository(db=mock_db)
        result = repo.buscar_por_cnpj("12345678000190")

        assert result["razao_social"] == "ACME"
        sql, params = _captura_execute(mock_cursor)
        assert "FROM fornecedores" in sql
        # O SQL faz a normalização com REPLACE em ambos os lados
        assert "REPLACE" in sql
        assert params == ("12345678000190",)

    def test_criar_retorna_id(self):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 5
        mock_db.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cursor)

        repo = FornecedorRepository(db=mock_db)
        novo_id = repo.criar("Nova Empresa", "12345678000190")
        assert novo_id == 5

    def test_excluir_chama_delete(self):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_db.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cursor)

        repo = FornecedorRepository(db=mock_db)
        assert repo.excluir(7) == 1
        args, _ = mock_cursor.execute.call_args
        assert "DELETE FROM fornecedores" in args[0]
        assert args[1] == (7,)


# ============================================================
# UsuarioRepository
# ============================================================


class TestUsuarioRepository:
    def test_buscar_para_auth_inclui_senha(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchone.return_value = {"id": 1, "senha": "$2b$..."}

        repo = UsuarioRepository(db=mock_db)
        result = repo.buscar_para_auth("admin")

        assert result["senha"].startswith("$2b$")
        sql, _ = _captura_execute(mock_cursor)
        assert "FROM usuarios" in sql
        assert "senha" in sql  # está no SELECT

    def test_buscar_por_username_nao_retorna_senha(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchone.return_value = {"id": 1, "username": "admin"}

        repo = UsuarioRepository(db=mock_db)
        result = repo.buscar_por_username("admin")

        assert "senha" not in result
        sql, _ = _captura_execute(mock_cursor)
        # O SQL NÃO deve pedir a coluna senha
        assert "SELECT id, username" in sql
        # senha está em buscar_para_auth, não em buscar_por_username
        # (verifica que as duas queries são diferentes)
        assert sql.count("senha") == 0


# ============================================================
# HistoricoRepository
# ============================================================


class TestHistoricoRepository:
    def test_listar_sem_filtro(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchall.return_value = []

        repo = HistoricoRepository(db=mock_db)
        repo.listar()

        sql, _ = _captura_execute(mock_cursor)
        assert "FROM historico_movimentacoes" in sql
        assert "JOIN produtos" in sql
        assert "WHERE" not in sql  # sem filtro = sem WHERE
        assert "ORDER BY h.data_movimentacao DESC" in sql

    def test_listar_com_filtro_de_tipo(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()

        repo = HistoricoRepository(db=mock_db)
        repo.listar(tipo="ENTRADA")

        sql, params = _captura_execute(mock_cursor)
        assert "WHERE UPPER(h.tipo) = %s" in sql
        assert params == ("ENTRADA",)

    def test_inserir_usa_cursor_do_chamador(self):
        """inserir() NÃO abre conexão — recebe cursor de transação externa."""
        mock_db = MagicMock()  # não deve ser usado
        mock_cursor = MagicMock()

        repo = HistoricoRepository(db=mock_db)
        repo.inserir(mock_cursor, produto_id=1, tipo="SAIDA", quantidade=5, usuario_id=2)

        # O cursor do chamador foi usado
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "INSERT INTO historico_movimentacoes" in args[0]
        assert args[1] == (1, "SAIDA", 5, 2)
        # Nenhuma conexão foi aberta pelo repository
        mock_db.connect.assert_not_called()
        mock_db.transaction.assert_not_called()

    def test_total_saidas_por_produto_agrega_corretamente(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchall.return_value = []

        repo = HistoricoRepository(db=mock_db)
        repo.total_saidas_por_produto()

        sql, _ = _captura_execute(mock_cursor)
        assert "SUM" in sql
        assert "GROUP BY" in sql
        assert "UPPER(h.tipo) = 'SAIDA'" in sql


# ============================================================
# LogEdicoesRepository
# ============================================================


class TestLogEdicoesRepository:
    def test_registrar_serializa_snapshots_como_json(self):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cursor)

        repo = LogEdicoesRepository(db=mock_db)
        antes = {"id": 1, "nome": "Velho"}
        depois = {"id": 1, "nome": "Novo"}
        with mock_db.transaction():
            repo.registrar(
                mock_cursor,
                produto_id=1,
                usuario_id=2,
                snapshot_antes=antes,
                snapshot_depois=depois,
            )

        args, _ = mock_cursor.execute.call_args
        sql, params = args
        assert "INSERT INTO produtos_historico_edicoes" in sql
        # Os snapshots são serializados como JSON
        import json

        assert json.loads(params[2]) == antes
        assert json.loads(params[3]) == depois
        assert params[0] == 1  # produto_id
        assert params[1] == 2  # usuario_id

    def test_listar_por_produto_com_limite(self):
        mock_db, _, mock_cursor = _mock_db_com_cursor()
        mock_cursor.fetchall.return_value = []

        repo = LogEdicoesRepository(db=mock_db)
        repo.listar_por_produto(5, limite=20)

        sql, params = _captura_execute(mock_cursor)
        assert "FROM produtos_historico_edicoes" in sql
        assert "WHERE h.produto_id = %s" in sql
        assert "LIMIT %s" in sql
        assert params == (5, 20)
