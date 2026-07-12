"""Smoke tests da hierarquia de exceções do FlowLog."""

import pytest

import exceptions


class TestHierarquia:
    """Toda exceção específica deve herdar de FlowLogError."""

    @pytest.mark.parametrize(
        "cls",
        [
            exceptions.ValidationError,
            exceptions.NotFoundError,
            exceptions.BusinessRuleError,
            exceptions.AuthenticationError,
            exceptions.AuthorizationError,
            exceptions.DatabaseError,
            exceptions.InfrastructureError,
            exceptions.EstoqueInsuficienteError,
            exceptions.ContaBloqueadaError,
            exceptions.CNPJInvalidoError,
        ],
    )
    def test_herda_de_flowlog_error(self, cls):
        assert issubclass(cls, exceptions.FlowLogError)

    def test_estoque_insuficiente_herda_de_business_rule(self):
        assert issubclass(exceptions.EstoqueInsuficienteError, exceptions.BusinessRuleError)

    def test_conta_bloqueada_herda_de_authentication(self):
        assert issubclass(exceptions.ContaBloqueadaError, exceptions.AuthenticationError)

    def test_cnpj_invalido_herda_de_validation(self):
        assert issubclass(exceptions.CNPJInvalidoError, exceptions.ValidationError)


class TestMensagens:
    """Exceções devem carregar mensagem acessível via str()."""

    def test_message_padrao(self):
        with pytest.raises(exceptions.NotFoundError) as exc_info:
            raise exceptions.NotFoundError("produto não achado")
        assert "produto não achado" in str(exc_info.value)
        assert exc_info.value.message == "produto não achado"

    def test_message_vazia(self):
        with pytest.raises(exceptions.FlowLogError) as exc_info:
            raise exceptions.FlowLogError()
        assert exc_info.value.message == ""

    def test_catch_all_flowlog_error(self):
        """Quem captura FlowLogError pega todas as específicas."""
        with pytest.raises(exceptions.FlowLogError):
            raise exceptions.EstoqueInsuficienteError("x")
        with pytest.raises(exceptions.FlowLogError):
            raise exceptions.CNPJInvalidoError("x")
