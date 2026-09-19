from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"


@dataclass
class Settings:
    cnpj_emissor: str
    razao_social_emissor: str
    url_emissao: str
    codigo_servico_padrao: str
    descricao_padrao: str
    ibs_cbs: str
    debugger_address: str


def load_settings() -> Settings:
    if not SETTINGS_PATH.exists():
        raise FileNotFoundError(
            f"{SETTINGS_PATH} não encontrado. Copie config/settings.example.yaml "
            "para config/settings.yaml e preencha com seus dados."
        )

    raw = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8")) or {}
    emissor = raw.get("emissor", {}) or {}
    plataforma = raw.get("plataforma", {}) or {}
    servico = raw.get("servico_padrao", {}) or {}
    navegador = raw.get("navegador", {}) or {}

    url_emissao = plataforma.get("url_emissao") or ""
    if not url_emissao:
        raise ValueError(
            "plataforma.url_emissao está vazio em settings.yaml. Preencha com o "
            "link exato da página de emissão antes de rodar o script."
        )

    return Settings(
        cnpj_emissor=emissor.get("cnpj", ""),
        razao_social_emissor=emissor.get("razao_social", ""),
        url_emissao=url_emissao,
        codigo_servico_padrao=servico.get("codigo_servico", ""),
        descricao_padrao=servico.get("descricao_padrao", ""),
        ibs_cbs=servico.get("ibs_cbs", "Não"),
        debugger_address=navegador.get("debugger_address", "127.0.0.1:9222"),
    )
