"""Testes do decorator @requer_nivel e da hierarquia de RBAC."""

import auth
import session


class TestRequerNivel:
    """Decorator de RBAC: bloqueia sem sessão e sem nível suficiente."""

    def test_bloqueia_sem_sessao(self):
        @auth.requer_nivel(2)
        def handler():
            return "executou"

        # Sem login, decorator deve bloquear
        assert handler() is None

    def test_bloqueia_nivel_1_em_acao_nivel_2(self):
        session.login(1, "operador", 1)

        @auth.requer_nivel(2)
        def cadastrar_produto():
            return "executou"

        assert cadastrar_produto() is None

    def test_bloqueia_nivel_2_em_acao_nivel_3(self):
        session.login(2, "gerente", 2)

        @auth.requer_nivel(3)
        def cadastrar_usuario():
            return "executou"

        assert cadastrar_usuario() is None

    def test_permite_nivel_exato(self):
        session.login(2, "gerente", 2)

        @auth.requer_nivel(2)
        def cadastrar_produto():
            return "executou"

        assert cadastrar_produto() == "executou"

    def test_permite_nivel_maior(self):
        session.login(3, "admin", 3)

        @auth.requer_nivel(2)
        def cadastrar_produto():
            return "executou"

        assert cadastrar_produto() == "executou"

    def test_preserva_metadata_da_funcao(self):
        @auth.requer_nivel(2)
        def minha_feature():
            """Docstring preservada."""
            return 42

        # wraps preserva nome e docstring
        assert minha_feature.__name__ == "minha_feature"
        assert "Docstring preservada" in (minha_feature.__doc__ or "")

    def test_passa_argumentos_e_kwargs(self):
        session.login(3, "admin", 3)

        @auth.requer_nivel(2)
        def somar(a, b, multiplicador=1):
            return (a + b) * multiplicador

        assert somar(2, 3) == 5
        assert somar(2, 3, multiplicador=10) == 50
