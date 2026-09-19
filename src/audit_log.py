from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "nfse_emissoes.jsonl"


def _append(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_attempt(dados_nota: dict) -> str:
    """Grava a intenção de emissão ANTES de qualquer clique final, para que o
    registro exista mesmo que o processo trave logo em seguida. Nunca passe
    credenciais em dados_nota — só campos da própria nota."""
    run_id = str(uuid.uuid4())
    _append({
        "run_id": run_id,
        "evento": "tentativa",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dados_nota": dados_nota,
    })
    return run_id


def log_result(run_id: str, status: str, detalhe: str = "", protocolo: Optional[str] = None) -> None:
    _append({
        "run_id": run_id,
        "evento": "resultado",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "detalhe": detalhe,
        "protocolo": protocolo,
    })
