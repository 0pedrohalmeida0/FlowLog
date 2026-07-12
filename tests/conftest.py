"""Fixtures compartilhadas pelos testes.

Por que existe: pytest descobre os testes a partir de `testpaths = ["tests"]`
(configurado em pyproject.toml). Para que `import utils` funcione nos testes,
adicionamos `src/` ao sys.path. Também isolamos a sessão do módulo
(que é state global) entre testes com `autouse=True`.
"""

import sys
from pathlib import Path

# Garante que `import utils`, `import session`, etc. funcionam
# sem precisar instalar o pacote.
SRC = Path(__file__).parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import pytest  # noqa: E402

import session  # noqa: E402  (após sys.path)


@pytest.fixture(autouse=True)
def _limpar_sessao():
    """Cada teste começa com sessão vazia, independente do anterior."""
    session.logout()
    yield
    session.logout()
