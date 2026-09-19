from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"
ENV_PATH = PROJECT_ROOT / ".env"


@dataclass
class Credentials:
    username: str
    password: str


@dataclass
class Settings:
    cnpj_emissor: str
    razao_social_emissor: str
    url_login: str
    url_emissao: str
    codigo_servico_padrao: str
    descricao_padrao: str
    headless: bool
    chrome_profile_path: Optional[str]


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
        url_login=plataforma.get("url_login") or url_emissao,
        url_emissao=url_emissao,
        codigo_servico_padrao=servico.get("codigo_servico", ""),
        descricao_padrao=servico.get("descricao_padrao", ""),
        headless=bool(navegador.get("headless", False)),
        chrome_profile_path=navegador.get("chrome_profile_path") or None,
    )


def load_credentials() -> Credentials:
    load_dotenv(ENV_PATH)
    username = os.getenv("GOVBR_USERNAME", "")
    password = os.getenv("GOVBR_PASSWORD", "")
    if not username or not password:
        raise ValueError(
            "GOVBR_USERNAME/GOVBR_PASSWORD não encontrados. Copie .env.example "
            "para .env e preencha (esse arquivo nunca deve ser commitado)."
        )
    return Credentials(username=username, password=password)
