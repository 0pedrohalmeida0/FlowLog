"""Testes dos services (lógica de negócio) com mocks de repository.

Os services são testáveis em isolamento: recebem repositories no
construtor, então passamos mocks e verificamos o comportamento sem
precisar de MySQL real.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

import session
from exceptions import (
    AuthenticationError,
    CNPJInvalidoError,
    ContaBloqueadaError,
    EstoqueInsuficienteError,
    NotFoundError,
    ValidationError,
)
from services.auth_service import AuthService
from services.estoque_service import EstoqueService
from services.fornecedor_service import FornecedorService
from services.produto_service import ProdutoService

# ============================================================
# AuthService
# ============================================================


class TestAuthService:
    def setup_method(self):
        session.logout()
        self.mock_users = MagicMock()
        self.svc = AuthService(user_repo=self.mock_users)

    def test_usuario_vazio_levanta_validation_error(self):
        with pytest.raises(ValidationError):
            self.svc.autenticar("", "senha")
        with pytest.raises(ValidationError):
            self.svc.autenticar("user", "")

    def test_usuario_nao_existente_mensagem_generica(self):
        """Mensagem genérica para evitar user enumeration."""
        self.mock_users.buscar_para_auth.return_value = None
        with pytest.raises(AuthenticationError) as exc_info:
            self.svc.autenticar("ghost", "qualquer")
        # A mensagem NÃO deve dizer "usuário não existe"
        assert "não" not in exc_info.value.message.lower() or "incorretos" in exc_info.value.message

    def test_senha_correta_retorna_nivel(self):
        self.mock_users.buscar_para_auth.return_value = {
            "id": 1,
            "username": "u",
            "nivel_acesso": 2,
            "senha": b"$2b$12$validhash",
            "tentativas_falhas": 0,
            "bloqueado_ate": None,
        }
        with patch("services.auth_service.verificar_senha", return_value=True):
            nivel = self.svc.autenticar("u", "senha_certa")
        assert nivel == 2
        self.mock_users.resetar_tentativas.assert_called_once_with(1)

    def test_senha_errada_incrementa_tentativas_e_levanta_auth_error(self):
        self.mock_users.buscar_para_auth.return_value = {
            "id": 1,
            "username": "u",
            "nivel_acesso": 1,
            "senha": b"$2b$12$hash",
            "tentativas_falhas": 0,
            "bloqueado_ate": None,
        }
        with patch("services.auth_service.verificar_senha", return_value=False):
            with pytest.raises(AuthenticationError):
                self.svc.autenticar("u", "errada")
        self.mock_users.registrar_falha_login.assert_called_once()
        args = self.mock_users.registrar_falha_login.call_args
        assert args[0][0] == 1  # user_id
        assert args[0][1] == 1  # tentativas = 0 + 1

    def test_senha_errada_atinge_limite_bloqueia(self):
        self.mock_users.buscar_para_auth.return_value = {
            "id": 1,
            "username": "u",
            "nivel_acesso": 1,
            "senha": b"$2b$12$hash",
            "tentativas_falhas": 4,
            "bloqueado_ate": None,
        }
        with patch("services.auth_service.verificar_senha", return_value=False):
            with pytest.raises(ContaBloqueadaError):
                self.svc.autenticar("u", "errada")
        # tentativas = 4 + 1 = 5 (== max_attempts)
        args = self.mock_users.registrar_falha_login.call_args
        assert args[0][1] == 5

    def test_conta_bloqueada_nao_consulta_senha(self):
        futuro = datetime.now() + timedelta(minutes=10)
        self.mock_users.buscar_para_auth.return_value = {
            "id": 1,
            "username": "u",
            "nivel_acesso": 1,
            "senha": b"$2b$12$hash",
            "tentativas_falhas": 5,
            "bloqueado_ate": futuro,
        }
        with pytest.raises(ContaBloqueadaError):
            self.svc.autenticar("u", "qualquer")
        # Verificar que reset NÃO foi chamado (não houve sucesso)
        self.mock_users.resetar_tentativas.assert_not_called()


# ============================================================
# EstoqueService
# ============================================================


def _setup_transacao_mock(mock_produtos, transacao_return):
    """Configura o mock de transaction() pra devolver (conn, cur) no __enter__."""
    mock_cur = MagicMock()
    mock_conn = MagicMock()
    mock_produtos.transaction.return_value.__enter__.return_value = (mock_conn, mock_cur)
    return mock_conn, mock_cur


class TestEstoqueService:
    def setup_method(self):
        session.logout()
        session.login(99, "operador_teste", 2)  # garante usuário logado
        self.mock_prod = MagicMock()
        self.mock_hist = MagicMock()
        self.svc = EstoqueService(
            produto_repo=self.mock_prod,
            historico_repo=self.mock_hist,
        )

    def teardown_method(self):
        session.logout()

    def test_quantidade_zero_levanta_validation_error(self):
        with pytest.raises(ValidationError):
            self.svc.registrar_entrada(1, 0)
        with pytest.raises(ValidationError):
            self.svc.registrar_saida(1, 0)
        with pytest.raises(ValidationError):
            self.svc.registrar_entrada(1, -5)

    def test_quantidade_nao_int_levanta_validation_error(self):
        with pytest.raises(ValidationError):
            self.svc.registrar_entrada(1, "dez")
        with pytest.raises(ValidationError):
            self.svc.registrar_saida(1, 1.5)  # float, não int

    def test_produto_inexistente_levanta_not_found(self):
        _, mock_cur = _setup_transacao_mock(self.mock_prod, None)
        mock_cur.fetchone.return_value = None
        with pytest.raises(NotFoundError):
            self.svc.registrar_entrada(999, 5)

    def test_entrada_aumenta_saldo_e_grava_log(self):
        _, mock_cur = _setup_transacao_mock(self.mock_prod, None)
        # SELECT devolve (nome, qtd_atual)
        mock_cur.fetchone.side_effect = [
            ("Teclado", 10),  # SELECT nome, quantidade
        ]
        resultado = self.svc.registrar_entrada(1, 5)
        assert resultado["qtd_anterior"] == 10
        assert resultado["qtd_nova"] == 15
        # UPDATE chamado com (15, 1)
        update_call = mock_cur.execute.call_args_list[1]
        assert "UPDATE produtos" in update_call[0][0]
        assert update_call[0][1] == (15, 1)
        # historico.inserir chamado com (cur, 1, 'ENTRADA', 5, 99)
        self.mock_hist.inserir.assert_called_once()
        args = self.mock_hist.inserir.call_args
        assert args[0][1] == 1
        assert args[0][2] == "ENTRADA"
        assert args[0][3] == 5
        assert args[0][4] == 99  # usuario_id

    def test_saida_estoque_insuficiente_levanta_excecao(self):
        _, mock_cur = _setup_transacao_mock(self.mock_prod, None)
        mock_cur.fetchone.return_value = ("Mouse", 3)
        with pytest.raises(EstoqueInsuficienteError) as exc_info:
            self.svc.registrar_saida(1, 10)
        # Mensagem inclui o saldo atual
        assert "3" in exc_info.value.message

    def test_saida_com_saldo_suficiente_diminui(self):
        _, mock_cur = _setup_transacao_mock(self.mock_prod, None)
        mock_cur.fetchone.return_value = ("Mouse", 10)
        resultado = self.svc.registrar_saida(1, 3)
        assert resultado["qtd_anterior"] == 10
        assert resultado["qtd_nova"] == 7
        self.mock_hist.inserir.assert_called_once()
        args = self.mock_hist.inserir.call_args
        assert args[0][2] == "SAIDA"


# ============================================================
# ProdutoService
# ============================================================


class TestProdutoService:
    def setup_method(self):
        session.logout()
        self.mock_prod = MagicMock()
        self.mock_forn = MagicMock()
        self.mock_log = MagicMock()
        self.svc = ProdutoService(
            produto_repo=self.mock_prod,
            fornecedor_repo=self.mock_forn,
            log_edicoes_repo=self.mock_log,
        )

    def teardown_method(self):
        session.logout()

    # ---- cadastrar ----

    def test_cadastrar_com_dados_validos(self):
        self.mock_forn.buscar_por_cnpj.return_value = None
        self.mock_forn.criar.return_value = 7
        self.mock_prod.criar.return_value = 42
        novo_id = self.svc.cadastrar(
            nome="Notebook",
            quantidade=10,
            preco_custo=2500.0,
            fornecedor_cnpj="11.222.333/0001-81",
            alerta_minimo=3,
        )
        assert novo_id == 42
        # fornecedor criado com cnpj normalizado
        self.mock_forn.criar.assert_called_once()
        cnpj_arg = self.mock_forn.criar.call_args.kwargs["cnpj"]
        assert cnpj_arg == "11222333000181"  # sem máscara
        # produto criado com fornecedor_id
        self.mock_prod.criar.assert_called_once()
        prod_args = self.mock_prod.criar.call_args
        assert prod_args.kwargs["fornecedor_id"] == 7

    def test_cadastrar_cnpj_invalido_levanta_cnpj_error(self):
        with pytest.raises(CNPJInvalidoError):
            self.svc.cadastrar(
                nome="X",
                quantidade=1,
                preco_custo=1.0,
                fornecedor_cnpj="00000000000000",  # sequencia repetida
            )
        # Nenhum insert aconteceu
        self.mock_forn.criar.assert_not_called()
        self.mock_prod.criar.assert_not_called()

    def test_cadastrar_nome_vazio_levanta_validation(self):
        with pytest.raises(ValidationError):
            self.svc.cadastrar(
                nome="   ",
                quantidade=1,
                preco_custo=1.0,
                fornecedor_cnpj="11.222.333/0001-81",
            )

    def test_cadastrar_quantidade_negativa_levanta_validation(self):
        with pytest.raises(ValidationError):
            self.svc.cadastrar(
                nome="X",
                quantidade=-1,
                preco_custo=1.0,
                fornecedor_cnpj="11.222.333/0001-81",
            )

    def test_cadastrar_reusa_fornecedor_existente(self):
        self.mock_forn.buscar_por_cnpj.return_value = {"id": 99, "razao_social": "ACME"}
        self.mock_prod.criar.return_value = 1
        self.svc.cadastrar(
            nome="X",
            quantidade=1,
            preco_custo=1.0,
            fornecedor_cnpj="11.222.333/0001-81",
        )
        self.mock_forn.criar.assert_not_called()
        # produto inserido com fornecedor_id=99
        assert self.mock_prod.criar.call_args.kwargs["fornecedor_id"] == 99

    # ---- editar ----

    def test_editar_rejeita_quantidade(self):
        with pytest.raises(ValidationError) as exc_info:
            self.svc.editar(1, {"quantidade": 50})
        assert "quantidade" in exc_info.value.message.lower()

    def test_editar_rejeita_campo_invalido(self):
        with pytest.raises(ValidationError) as exc_info:
            self.svc.editar(1, {"campo_inexistente": "x"})
        assert "campo_inexistente" in exc_info.value.message

    def test_editar_produto_inexistente_levanta_not_found(self):
        self.mock_prod.buscar_por_id.return_value = None
        with pytest.raises(NotFoundError):
            self.svc.editar(999, {"nome": "X"})

    def test_editar_nome_vazio_levanta_validation(self):
        with pytest.raises(ValidationError):
            self.svc.editar(1, {"nome": "   "})

    def test_editar_preco_negativo_levanta_validation(self):
        self.mock_prod.buscar_por_id.return_value = {
            "id": 1,
            "nome": "X",
            "quantidade": 1,
            "preco_custo": 10.0,
            "fornecedor_id": 1,
            "alerta_minimo": 1,
        }
        with pytest.raises(ValidationError):
            self.svc.editar(1, {"preco_custo": -5.0})

    def test_editar_alerta_minimo_negativo_levanta_validation(self):
        self.mock_prod.buscar_por_id.return_value = {
            "id": 1,
            "nome": "X",
            "quantidade": 1,
            "preco_custo": 10.0,
            "fornecedor_id": 1,
            "alerta_minimo": 1,
        }
        with pytest.raises(ValidationError):
            self.svc.editar(1, {"alerta_minimo": -1})

    def test_editar_campos_vazios_levanta_validation(self):
        with pytest.raises(ValidationError):
            self.svc.editar(1, {})

    def test_editar_com_sucesso_grava_snapshot(self):
        # Produto atual
        self.mock_prod.buscar_por_id.return_value = {
            "id": 1,
            "nome": "Velho",
            "quantidade": 5,
            "preco_custo": 10.0,
            "fornecedor_id": 1,
            "alerta_minimo": 1,
        }
        # Configurar transação
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": 1,
            "nome": "Novo",
            "quantidade": 5,
            "preco_custo": 10.0,
            "fornecedor_id": 1,
            "alerta_minimo": 1,
        }
        mock_cur.rowcount = 1
        self.mock_prod.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cur)

        resultado = self.svc.editar(1, {"nome": "Novo"})

        assert resultado["snapshot_antes"]["nome"] == "Velho"
        assert resultado["snapshot_depois"]["nome"] == "Novo"
        # log_edicoes.registrar foi chamado
        self.mock_log.registrar.assert_called_once()

    def test_editar_usa_select_for_update_cr04(self):
        """CR-04: editar deve usar SELECT ... FOR UPDATE dentro da
        transação para evitar lost-update em concorrência."""
        self.mock_prod.buscar_por_id.return_value = {
            "id": 1,
            "nome": "Velho",
            "quantidade": 5,
            "preco_custo": 10.0,
            "fornecedor_id": 1,
            "alerta_minimo": 1,
        }
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": 1,
            "nome": "Novo",
            "quantidade": 5,
            "preco_custo": 10.0,
            "fornecedor_id": 1,
            "alerta_minimo": 1,
        }
        mock_cur.rowcount = 1
        self.mock_prod.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cur)

        self.svc.editar(1, {"nome": "Novo"})

        # CR-04: o lock foi feito durante a transação
        self.mock_prod.buscar_por_id_locked.assert_called_once()

    def test_editar_rowcount_zero_levanta_not_found(self):
        """Se o produto foi deletado entre o SELECT e o UPDATE, rowcount=0."""
        self.mock_prod.buscar_por_id.return_value = {
            "id": 1,
            "nome": "X",
            "quantidade": 1,
            "preco_custo": 10.0,
            "fornecedor_id": 1,
            "alerta_minimo": 1,
        }
        mock_cur = MagicMock()
        mock_cur.rowcount = 0
        self.mock_prod.transaction.return_value.__enter__.return_value = (MagicMock(), mock_cur)
        with pytest.raises(NotFoundError):
            self.svc.editar(1, {"nome": "Y"})

    def test_buscar_e_listar_todos_fachada_publica_me01(self):
        """ME-01: métodos públicos do service substituem acesso a
        atributos privados pelos feature modules."""
        self.mock_prod.buscar_por_id.return_value = {"id": 7, "nome": "X"}
        self.mock_prod.listar_todos.return_value = [{"id": 1}, {"id": 2}]
        self.mock_prod.listar_abaixo_do_minimo.return_value = [
            {"nome": "A", "quantidade": 0, "alerta_minimo": 1, "fornecedor": "F"}
        ]
        assert self.svc.buscar(7)["id"] == 7
        assert len(self.svc.listar_todos()) == 2
        assert self.svc.listar_abaixo_do_minimo()[0]["nome"] == "A"


# ============================================================
# FornecedorService
# ============================================================


class TestFornecedorService:
    def setup_method(self):
        self.mock_repo = MagicMock()
        self.svc = FornecedorService(repo=self.mock_repo)

    def test_cadastrar_com_dados_validos(self):
        self.mock_repo.buscar_por_cnpj.return_value = None
        self.mock_repo.criar.return_value = 5
        novo_id = self.svc.cadastrar("ACME LTDA", "11.222.333/0001-81")
        assert novo_id == 5
        # CNPJ passado normalizado
        self.mock_repo.criar.assert_called_once()
        cnpj_arg = self.mock_repo.criar.call_args[0][1]
        assert cnpj_arg == "11222333000181"

    def test_cadastrar_cnpj_invalido_levanta_cnpj_error(self):
        with pytest.raises(CNPJInvalidoError):
            self.svc.cadastrar("X", "00000000000000")

    def test_cadastrar_duplicado_levanta_validation(self):
        self.mock_repo.buscar_por_cnpj.return_value = {"id": 1, "razao_social": "Já existe"}
        with pytest.raises(ValidationError):
            self.svc.cadastrar("X", "11.222.333/0001-81")

    def test_editar_razao_social_id_inexistente_levanta_not_found(self):
        self.mock_repo.atualizar_razao_social.return_value = 0
        with pytest.raises(NotFoundError):
            self.svc.editar_razao_social(999, "Nova")

    def test_editar_razao_social_vazia_levanta_validation(self):
        with pytest.raises(ValidationError):
            self.svc.editar_razao_social(1, "   ")

    def test_excluir_id_inexistente_levanta_not_found(self):
        self.mock_repo.excluir.return_value = 0
        with pytest.raises(NotFoundError):
            self.svc.excluir(999)

    def test_excluir_com_sucesso(self):
        self.mock_repo.excluir.return_value = 1
        self.svc.excluir(1)  # não deve levantar
