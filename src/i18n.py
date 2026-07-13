"""Internacionalização (i18n) do FlowLog Licença.

Implementação leve, sem dependência de gettext (não precisa de .po/.mo files).

Idiomas suportados:
    - pt_BR (default)
    - en

Uso:
    from i18n import t
    print(t("menu.bem_vindo"))
    # pt_BR: "Bem-vindo ao FlowLog"
    # en:    "Welcome to FlowLog"

Configuração via env var:
    FLOWLOG_LANG=en  # força inglês
    FLOWLOG_LANG=pt_BR  # força português
    # sem env var: detecta do sistema (LANG/LC_ALL)
"""

import os

# Catálogo de strings. Para adicionar: chame `t("nova.chave")` no código
# e adicione nos dois idiomas aqui. (Migração pra gettext quando i18n virar
# problema grande; por enquanto, este dict serve.)
_STRINGS = {
    "pt_BR": {
        "menu.bem_vindo": "Bem-vindo ao FlowLog",
        "menu.titulo": "FLOWLOG - GESTÃO DE ESTOQUE",
        "menu.sair": "Sair",
        "menu.opcao_invalida": "⚠️ Opção inválida! Tente novamente.",
        "login.titulo": "LOGIN",
        "login.usuario": "Usuário",
        "login.senha": "Senha",
        "login.bloqueado": "Conta bloqueada por excesso de tentativas.",
        "login.invalido": "Usuário ou senha incorretos.",
        "trial.titulo": "FLOWLOG TRIAL",
        "trial.dias_restantes": "{dias} dia(s) restante(s)",
        "licenca.ativada": "Licença ativada para: {cliente}",
        "licenca.invalida": "Chave de ativação inválida, expirada ou de outro produto.",
        "erro.generico": "❌ Erro inesperado: {mensagem}",
        "sucesso.operacao": "✅ Operação concluída com sucesso.",
    },
    "en": {
        "menu.bem_vindo": "Welcome to FlowLog",
        "menu.titulo": "FLOWLOG - INVENTORY MANAGEMENT",
        "menu.sair": "Exit",
        "menu.opcao_invalida": "⚠️ Invalid option! Try again.",
        "login.titulo": "LOGIN",
        "login.usuario": "Username",
        "login.senha": "Password",
        "login.bloqueado": "Account locked due to too many failed attempts.",
        "login.invalido": "Invalid username or password.",
        "trial.titulo": "FLOWLOG TRIAL",
        "trial.dias_restantes": "{dias} day(s) remaining",
        "licenca.ativada": "License activated for: {cliente}",
        "licenca.invalida": "Invalid, expired, or wrong product activation key.",
        "erro.generico": "❌ Unexpected error: {mensagem}",
        "sucesso.operacao": "✅ Operation completed successfully.",
    },
}

DEFAULT_LANG = "pt_BR"


def _detectar_lang() -> str:
    """Detecta o idioma do sistema. pt_BR se não conseguir."""
    # 1. Env var FLOWLOG_LANG tem prioridade
    custom = os.environ.get("FLOWLOG_LANG", "").strip()
    if custom and custom in _STRINGS:
        return custom

    # 2. LANG/LC_ALL do sistema
    lang_env = os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
    lang = lang_env.split(".")[0].lower()  # "en_US.UTF-8" -> "en_us"
    # Tenta match exato ("en_us" não tá no dict, mas "en" está)
    if lang in _STRINGS:
        return lang
    # Match pelo prefixo: "en" casa "en" e "en_us"
    prefix = lang.split("_")[0]
    if prefix in _STRINGS:
        return prefix

    return DEFAULT_LANG


_LANG = _detectar_lang()


def set_lang(lang: str) -> None:
    """Força um idioma (útil pra testes)."""
    global _LANG
    if lang in _STRINGS:
        _LANG = lang


def get_lang() -> str:
    """Retorna o idioma atual."""
    return _LANG


def t(chave: str, **kwargs) -> str:
    """Traduz uma chave. Se não encontrar, retorna a própria chave.

    Args:
        chave: identificador da string (ex: "menu.bem_vindo").
        **kwargs: substituições no texto (ex: t("trial.dias_restantes", dias=23)).

    Returns:
        String traduzida com substituições aplicadas.
    """
    texto = _STRINGS.get(_LANG, {}).get(chave)
    if texto is None:
        # Fallback pro default se a chave não existe no idioma atual
        texto = _STRINGS.get(DEFAULT_LANG, {}).get(chave, chave)
    if kwargs:
        try:
            texto = texto.format(**kwargs)
        except (KeyError, IndexError):
            # Se faltar alguma chave de format, retorna o template
            pass
    return texto


def idiomas_disponiveis() -> list[str]:
    """Lista os idiomas disponíveis."""
    return list(_STRINGS.keys())
