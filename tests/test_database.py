"""Testes do database.py: pool MySQL + sanitização de erros (CR-06)."""

from database import Database


class TestSanitizeError:
    """CR-06: erros do driver MySQL não devem logar senha ou host."""

    def test_sanitize_remove_password(self):
        msg = Database._sanitize_error(
            Exception("Access denied (using password: YES, password=SenhaSecreta123)")
        )
        assert "SenhaSecreta123" not in msg
        assert "password=***" in msg

    def test_sanitize_remove_user(self):
        msg = Database._sanitize_error(Exception("Failed for user=admin@host"))
        assert "user=admin" not in msg
        assert "user=***" in msg

    def test_sanitize_remove_host(self):
        msg = Database._sanitize_error(Exception("Can't connect to host=192.168.1.1"))
        assert "192.168.1.1" not in msg
        assert "host=***" in msg

    def test_sanitize_mantem_mensagem_basica(self):
        msg = Database._sanitize_error(Exception("OperationalError: 1045"))
        assert "1045" in msg
        assert "OperationalError" in msg

    def test_sanitize_texto_sem_parametros_sensiveis(self):
        msg = Database._sanitize_error(Exception("Some random error"))
        assert msg == "Some random error"

    def test_sanitize_case_insensitive(self):
        msg = Database._sanitize_error(Exception("PASSWORD=TopSecret; USER=root"))
        assert "TopSecret" not in msg
        assert "root" not in msg
