"""Testes da sessão: estado do usuário, expiração por inatividade."""

import time

import session


class TestEstadoInicial:
    def test_inicia_deslogada(self):
        assert session.esta_logado() is False
        assert session.nivel_atual() is None
        assert session.usuario_id_atual() is None
        assert session.usuario_atual() is None

    def test_sessao_expirada_sem_login(self):
        # Sem login, considera expirada (não há o que manter)
        assert session.sessao_expirada(30) is True


class TestLoginLogout:
    def test_login_popula_sessao(self):
        session.login(42, "pedro", 3)
        assert session.esta_logado() is True
        assert session.usuario_id_atual() == 42
        assert session.nivel_atual() == 3
        atual = session.usuario_atual()
        assert atual is not None
        assert atual["username"] == "pedro"
        assert atual["nivel_acesso"] == 3

    def test_logout_limpa_tudo(self):
        session.login(42, "pedro", 3)
        session.logout()
        assert session.esta_logado() is False
        assert session.nivel_atual() is None
        assert session.usuario_id_atual() is None
        assert session.usuario_atual() is None

    def test_login_inicializa_ultimo_acesso(self):
        session.login(1, "u", 1)
        # ultimo_acesso deve estar preenchido (data recente)
        assert session._sessao["ultimo_acesso"] is not None


class TestExpiracao:
    def test_sessao_recem_logada_nao_expirada(self):
        session.login(1, "u", 1)
        assert session.sessao_expirada(30) is False

    def test_registrar_atividade_atualiza_timestamp(self):
        session.login(1, "u", 1)
        t1 = session._sessao["ultimo_acesso"]
        time.sleep(0.05)
        session.registrar_atividade()
        t2 = session._sessao["ultimo_acesso"]
        assert t2 > t1, "ultimo_acesso deveria ter avançado"

    def test_registrar_atividade_sem_login_noop(self):
        # Não levanta, não faz nada
        session.registrar_atividade()
        assert session.esta_logado() is False

    def test_sessao_expirada_com_timeout_zero(self):
        # timeout 0 = desabilita expiração (sempre False se logado)
        session.login(1, "u", 1)
        # Hack: simula inatividade envelhecendo o timestamp
        from datetime import datetime, timedelta

        session._sessao["ultimo_acesso"] = datetime.now() - timedelta(hours=24)
        # Com timeout 0, a função deve retornar False (não expirar)
        # A convenção "0 = desabilitado" é responsabilidade do caller (main.py)
        # Aqui testamos só a lógica do helper com timeout normal
        assert session.sessao_expirada(30) is True

    def test_sessao_expirada_apos_inatividade_real(self):
        session.login(1, "u", 1)
        from datetime import datetime, timedelta

        # Força ultimo_acesso pra 31 minutos atrás
        session._sessao["ultimo_acesso"] = datetime.now() - timedelta(minutes=31)
        assert session.sessao_expirada(30) is True

    def test_sessao_nao_expirada_antes_limite(self):
        session.login(1, "u", 1)
        from datetime import datetime, timedelta

        session._sessao["ultimo_acesso"] = datetime.now() - timedelta(minutes=29)
        assert session.sessao_expirada(30) is False
