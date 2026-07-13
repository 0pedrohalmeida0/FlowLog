"""Testes do i18n: tradução, detecção de idioma, fallbacks."""

import i18n


class TestTraducao:
    def test_traducao_pt_br(self):
        i18n.set_lang("pt_BR")
        assert i18n.t("menu.bem_vindo") == "Bem-vindo ao FlowLog"

    def test_traducao_en(self):
        i18n.set_lang("en")
        assert i18n.t("menu.bem_vindo") == "Welcome to FlowLog"

    def test_fallback_quando_chave_nao_existe(self):
        i18n.set_lang("pt_BR")
        # Chave inexistente retorna ela mesma
        assert i18n.t("chave.que.nao.existe") == "chave.que.nao.existe"

    def test_format_com_kwargs(self):
        i18n.set_lang("pt_BR")
        resultado = i18n.t("trial.dias_restantes", dias=23)
        assert "23" in resultado

    def test_format_com_kwargs_faltando(self):
        i18n.set_lang("pt_BR")
        # Se faltar kwarg, retorna o template (sem crash)
        resultado = i18n.t("trial.dias_restantes")
        assert "dia" in resultado

    def test_idiomas_disponiveis(self):
        idiomas = i18n.idiomas_disponiveis()
        assert "pt_BR" in idiomas
        assert "en" in idiomas


class TestDeteccaoIdioma:
    def test_env_var_custom(self, monkeypatch):
        monkeypatch.setenv("FLOWLOG_LANG", "en")
        # Recarrega o módulo pra pegar o env var
        import importlib

        importlib.reload(i18n)
        assert i18n.get_lang() == "en"

    def test_default_quando_sem_env_var(self, monkeypatch):
        monkeypatch.delenv("FLOWLOG_LANG", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        import importlib

        importlib.reload(i18n)
        # Default = pt_BR
        assert i18n.get_lang() in ("pt_BR", "en")

    def test_idioma_invalido_vira_default(self, monkeypatch):
        monkeypatch.setenv("FLOWLOG_LANG", "klingon")
        import importlib

        importlib.reload(i18n)
        assert i18n.get_lang() == "pt_BR"
