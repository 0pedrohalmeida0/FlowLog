"""Sistema de licença do FlowLog Licença.

Modelo de licenciamento (v1.5):
    - **Trial**: 30 dias a partir do primeiro start. Sem chave necessária.
      Relatórios gerados com marca d'água "FLOWLOG TRIAL".
    - **Licença ativada**: chave de 25 caracteres (formato XXXXX-XXXXX-XXXXX-XXXXX-XXXXX)
      validada contra uma assinatura HMAC-SHA256. Sem expiração (vitalícia)
      ou anual (com data de expiração embutida na chave).
    - **Persistência**: arquivo JSON em `%APPDATA%/FlowLog/license.json`
      (Windows) ou `~/.config/flowlog/license.json` (Linux/macOS).

Geração de chaves:
    O vendor gera chaves usando `gerar_chave(validade_dias=None)`. A chave é
    derivada de (secret_key + product_id + data) via HMAC, codificada em
    base32 (5 grupos de 5 chars separados por hífen). Cada chave é única
    e pode ser verificada sem acesso ao banco de dados do vendor.

Aviso de segurança:
    Este é um esquema de licenciamento "honest system" — assume que o
    cliente não vai fazer reverse engineering do binário empacotado.
    Para um esquema anti-pirataria robusto, use proteções de HW/VM.
"""

import base64
import hashlib
import hmac
import json
import os
import platform
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# Config
# ============================================================

# Segredo mestra do vendor. Em produção, isso é embutido no binário
# compilado com PyInstaller --key. Em dev, fica aqui.
# 32 bytes aleatórios gerados uma vez; trocar em caso de vazamento.
_VENDOR_SECRET = b"flowlog-vendor-secret-v1-DO-NOT-SHARE-PUBLICLY"

# Versão do schema de licença (para invalidação retroativa)
_LICENSE_VERSION = 1

# Trial: 30 dias a partir do primeiro start
TRIAL_DAYS = 30

# Watermark que aparece em relatórios durante o trial
TRIAL_WATERMARK = "FLOWLOG TRIAL"


# ============================================================
# Persistência
# ============================================================


def _license_dir() -> Path:
    """Retorna o diretório de configuração do FlowLog por plataforma."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "FlowLog"
    # Linux/macOS: XDG_CONFIG_HOME ou ~/.config
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "flowlog"


def _license_path() -> Path:
    return _license_dir() / "license.json"


# ============================================================
# Modelo de dados
# ============================================================


class EstadoLicenca:
    """Estado da licença local: trial ou ativada.

    Attributes:
        modo: 'trial', 'activated' ou 'expired'.
        instalada_em: data/hora do primeiro start (criação).
        expira_em: data/hora de expiração do trial (None se licença vitalícia).
        chave: chave de ativação (None durante trial).
        ativa_em: data/hora de ativação (None durante trial).
        cliente_hash: hash do nome do cliente (privacidade — nome não é persistido).
    """

    def __init__(
        self,
        modo: str,
        instalada_em: datetime,
        expira_em: datetime | None = None,
        chave: str | None = None,
        ativa_em: datetime | None = None,
        cliente_hash: str | None = None,
    ) -> None:
        self.modo = modo
        self.instalada_em = instalada_em
        self.expira_em = expira_em
        self.chave = chave
        self.ativa_em = ativa_em
        self.cliente_hash = cliente_hash

    def to_dict(self) -> dict:
        return {
            "modo": self.modo,
            "instalada_em": self.instalada_em.isoformat(),
            "expira_em": self.expira_em.isoformat() if self.expira_em else None,
            "chave": self.chave,
            "ativa_em": self.ativa_em.isoformat() if self.ativa_em else None,
            "cliente_hash": self.cliente_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EstadoLicenca":
        return cls(
            modo=d["modo"],
            instalada_em=datetime.fromisoformat(d["instalada_em"]),
            expira_em=datetime.fromisoformat(d["expira_em"]) if d.get("expira_em") else None,
            chave=d.get("chave"),
            ativa_em=datetime.fromisoformat(d["ativa_em"]) if d.get("ativa_em") else None,
            cliente_hash=d.get("cliente_hash"),
        )

    def em_trial(self) -> bool:
        """True se está em período de trial (não expirado)."""
        if self.modo != "trial":
            return False
        if self.expira_em is None:
            return False
        return datetime.now() < self.expira_em

    def trial_expirado(self) -> bool:
        """True se trial venceu."""
        if self.modo == "activated":
            return False
        if self.expira_em is None:
            return False
        return datetime.now() >= self.expira_em

    def dias_restantes_trial(self) -> int:
        """Dias restantes de trial (0 se expirado ou ativado)."""
        if self.modo == "activated" or self.expira_em is None:
            return 0
        delta = self.expira_em - datetime.now()
        return max(0, int(delta.total_seconds() // 86400) + 1)

    def __repr__(self) -> str:
        if self.modo == "activated":
            return f"<EstadoLicenca ATIVADA (cliente_hash={self.cliente_hash})>"
        dias = self.dias_restantes_trial()
        return f"<EstadoLicenca TRIAL ({dias} dias restantes)>"


# ============================================================
# Persistência do estado
# ============================================================


def carregar_estado() -> EstadoLicenca | None:
    """Carrega o estado da licença do disco. None se não existe."""
    path = _license_path()
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return EstadoLicenca.from_dict(json.load(f))
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("Arquivo de licença corrompido: %s", e)
        return None


def salvar_estado(estado: EstadoLicenca) -> None:
    """Persiste o estado da licença em disco. Cria diretório se necessário."""
    path = _license_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Permissão 0o600 (só owner lê/escreve) — defesa contra outros users
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(estado.to_dict(), f, indent=2)
    except Exception:
        os.close(fd)
        raise


def inicializar_trial() -> EstadoLicenca:
    """Cria e persiste um estado de trial começando agora.

    Idempotente: se já existe estado válido, retorna o existente.
    """
    existente = carregar_estado()
    if existente is not None:
        return existente

    agora = datetime.now()
    estado = EstadoLicenca(
        modo="trial",
        instalada_em=agora,
        expira_em=agora + timedelta(days=TRIAL_DAYS),
    )
    salvar_estado(estado)
    logger.info("Trial de %d dias iniciado (expira em %s)", TRIAL_DAYS, estado.expira_em)
    return estado


# ============================================================
# Geração e validação de chaves (lado vendor)
# ============================================================


def _b32(data: bytes) -> str:
    """Base32 sem padding (mais legível em chaves)."""
    return base64.b32encode(data).decode("ascii").rstrip("=")


def _b64url(data: bytes) -> str:
    """Base64 URL-safe sem padding (RFC 4648 §5)."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _hmac_chave(payload: bytes) -> str:
    """Gera o HMAC de um payload binário usando o segredo vendor."""
    return hmac.new(_VENDOR_SECRET, payload, hashlib.sha256).hexdigest()


def _pack_payload(product_id: str, cliente: str, validade_dias: int | None) -> bytes:
    """Empacota o payload em 15 bytes (formato binário fixo).

    Layout:
        [0]      product_id (1 byte: 1=flowlog-v1, 2=flowlog-cloud)
        [1:3]    emitida_em (2 bytes, dias desde 2026-01-01)
        [3:5]    expira_em (2 bytes, dias desde emissão; 0=vitalícia)
        [5:9]    cliente_hash (4 bytes, primeiros 4 do SHA-256 do nome)
        [9:11]   nonce (2 bytes aleatórios pra unicidade)
        [11:15]  reservado (4 bytes zero, expansão futura)
    """
    import struct

    # Product ID: 1 byte (1 = flowlog-v1)
    prod_byte = 1 if product_id == "flowlog-v1" else 2

    # Datas: dias desde 2026-01-01
    epoch = datetime(2026, 1, 1)
    emitida = (datetime.now() - epoch).days
    if emitida < 0 or emitida > 65535:
        raise ValueError("Data de emissão fora do range suportado (2026-01-01 a 2205+).")
    expira = 0
    if validade_dias is not None:
        if validade_dias < 0 or validade_dias > 65535:
            raise ValueError("Validade fora do range (0-65535 dias).")
        expira = validade_dias

    # Hash do cliente: primeiros 4 bytes do SHA-256
    cliente_hash = hashlib.sha256(cliente.encode("utf-8")).digest()[:4]

    # Nonce
    nonce = secrets.token_bytes(2)

    return struct.pack(">BHH4s2s4x", prod_byte, emitida, expira, cliente_hash, nonce)


def _unpack_payload(data: bytes) -> dict:
    """Desempacota os 15 bytes do payload."""
    import struct

    if len(data) != 15:
        return None
    # Formato: B (1) + H (2) + H (2) + 4s (4) + 2s (2) = 11 bytes
    # Os 4 bytes de padding no pack são ignorados no unpack
    prod_byte, emitida, expira, cliente_hash, nonce = struct.unpack(">BHH4s2s4x", data)

    epoch = datetime(2026, 1, 1)
    emitida_dt = epoch + timedelta(days=emitida)

    product_id = "flowlog-v1" if prod_byte == 1 else "flowlog-cloud"

    expira_dt = None
    if expira > 0:
        expira_dt = emitida_dt + timedelta(days=expira)

    return {
        "product_id": product_id,
        "cliente_hash": cliente_hash.hex(),
        "emitida_em": emitida_dt,
        "expira_em": expira_dt,
    }


def gerar_chave(
    validade_dias: int | None = None,
    cliente: str = "",
    product_id: str = "flowlog-v1",
) -> str:
    """Gera uma chave de ativação (lado vendor).

    Args:
        validade_dias: None para vitalícia, ou número de dias.
        cliente: nome do cliente (aparece em "Licenciado a: <cliente>").
        product_id: identificador do produto (default 'flowlog-v1').

    Returns:
        Chave no formato XXXXX-XXXXX-XXXXX-XXXXX (20 chars + 4 hífens = 24 chars).

    Layout (15 bytes payload + 5 chars sig):
        [0]      product_id
        [1:3]    emitida_em (dias desde 2026-01-01)
        [3:5]    expira_em (dias desde emissão; 0=vitalícia)
        [5:9]    hash do nome do cliente
        [9:11]   nonce
        [11:15]  reservado

    Exemplo:
        >>> gerar_chave(validade_dias=365, cliente="XPTO")
        'K7F3D-2H8M1-P9R4S-V6T8W'
    """
    payload = _pack_payload(product_id, cliente, validade_dias)

    # Codifica payload em base64 url-safe (15 bytes = 20 chars)
    payload_b64 = _b64url(payload)  # exatamente 20 chars

    # Assinatura HMAC: primeiros 5 chars hex (20 bits de integridade)
    sig = _hmac_chave(payload)[:5]

    # Chave: payload (20) + sig (5) = 25 chars = 5 grupos de 5
    # NÃO fazemos .upper() no payload_b64 (corromperia os dados) — só na sig
    bruto = payload_b64 + sig.upper()
    grupos = [bruto[i : i + 5] for i in range(0, 25, 5)]
    return "-".join(grupos)


def _parse_chave(chave: str) -> dict | None:
    """Decodifica a chave em payload + assinatura. None se malformada."""
    # Remove hífens e valida tamanho (NÃO faz upper — corromperia o base64)
    bruto = chave.replace("-", "").strip()
    if len(bruto) != 25:
        return None
    # base64 url-safe usa _ além de A-Z a-z 0-9
    if not all(c.isalnum() or c == "_" for c in bruto):
        return None

    # Os últimos 5 chars são a assinatura (uppercase hex); o resto é o payload
    # em base64 url-safe (mixed case).
    sig_fornecida_upper = bruto[-5:].upper()
    payload_b64 = bruto[:-5]

    # Decodifica base64 url-safe
    try:
        # Adiciona padding que tiramos
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
    except (ValueError, UnicodeDecodeError):
        return None

    if len(payload_bytes) != 15:
        return None

    # Valida assinatura (constante-time)
    sig_esperada = _hmac_chave(payload_bytes)[:5].upper()
    if not hmac.compare_digest(sig_fornecida_upper, sig_esperada):
        return None

    # Desempacota o payload
    return _unpack_payload(payload_bytes)


def validar_chave(chave: str) -> dict | None:
    """Valida uma chave de ativação.

    Returns:
        Dict com metadados (cliente, emitida_em, expira_em) se válida.
        None se inválida, expirada ou produto errado.
    """
    info = _parse_chave(chave)
    if info is None:
        return None
    if info["product_id"] != "flowlog-v1":
        return None
    if info["expira_em"] is not None and info["expira_em"] < datetime.now():
        return None
    return info


def ativar_licenca(chave: str) -> EstadoLicenca:
    """Ativa uma chave e persiste o novo estado.

    Raises:
        ValueError: chave inválida, expirada ou produto errado.
    """
    info = validar_chave(chave)
    if info is None:
        raise ValueError(
            "Chave de ativação inválida, expirada ou de outro produto. "
            "Verifique com o vendor (contato@flowlog.app)."
        )

    estado_atual = carregar_estado() or inicializar_trial()
    novo = EstadoLicenca(
        modo="activated",
        instalada_em=estado_atual.instalada_em,
        expira_em=info["expira_em"],
        chave=chave,
        ativa_em=datetime.now(),
        cliente_hash=info["cliente_hash"],
    )
    salvar_estado(novo)
    logger.info("Licença ativada (cliente_hash=%s)", info["cliente_hash"])
    return novo


# ============================================================
# Status runtime
# ============================================================


def status_licenca() -> EstadoLicenca:
    """Retorna o estado atual. Se não existir, inicia trial automaticamente.

    Função de conveniência: garante que sempre tem um estado válido.
    """
    estado = carregar_estado()
    if estado is None:
        estado = inicializar_trial()
    return estado


def aplicar_watermark(texto: str) -> str:
    """Adiciona marca d'água de trial em textos de relatório.

    Adiciona "[FLOWLOG TRIAL — 23 dias restantes]" no início do texto.
    Se licença já ativada, retorna o texto intacto.
    """
    estado = status_licenca()
    if estado.modo == "activated":
        return texto
    if estado.trial_expirado():
        return texto  # O caller deve ter bloqueado antes
    dias = estado.dias_restantes_trial()
    watermark = f"\n*** [FLOWLOG TRIAL — {dias} dia(s) restante(s)] ***\n"
    return watermark + texto


# ============================================================
# CLI de teste / admin
# ============================================================


def main():  # pragma: no cover
    """CLI: 'python -m src.licenca status|ativar|gerar'."""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python -m src.licenca [status|ativar|gerar]")
        return

    cmd = sys.argv[1]
    if cmd == "status":
        estado = status_licenca()
        print(estado)
        print(f"  Modo:          {estado.modo}")
        print(f"  Instalada em:  {estado.instalada_em}")
        print(f"  Expira em:     {estado.expira_em}")
        if estado.cliente:
            print(f"  Cliente:       {estado.cliente}")
        if estado.em_trial():
            print(f"  Dias restantes: {estado.dias_restantes_trial()}")
    elif cmd == "ativar":
        chave = input("Cole a chave de ativação: ").strip()
        try:
            novo = ativar_licenca(chave)
            print(f"✅ Licença ativada para: {novo.cliente}")
        except ValueError as e:
            print(f"❌ {e}")
    elif cmd == "gerar":
        # Comando do VENDOR — só pra gerar chaves no console
        dias = input("Validade em dias (vazio = vitalícia): ").strip()
        dias = int(dias) if dias else None
        cliente = input("Nome do cliente: ").strip()
        print(f"Chave: {gerar_chave(validade_dias=dias, cliente=cliente)}")
    else:
        print(f"Comando desconhecido: {cmd}")


if __name__ == "__main__":
    main()
