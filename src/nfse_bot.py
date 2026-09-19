from __future__ import annotations

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from .config import Settings

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "logs" / "screenshots"


class NFSeBot:
    def __init__(self, settings: Settings, headless: bool = False):
        self.settings = settings
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        if settings.chrome_profile_path:
            options.add_argument(f"--user-data-dir={settings.chrome_profile_path}")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def login(self, username: str, password: str) -> None:
        self.driver.get(self.settings.url_login)
        # TODO: os seletores abaixo são placeholders. Preencher depois de
        # inspecionar a página real de login (Chrome DevTools > Elements).
        # Exemplo:
        #   from selenium.webdriver.common.by import By
        #   from selenium.webdriver.support import expected_conditions as EC
        #   campo_usuario = self.wait.until(
        #       EC.presence_of_element_located((By.ID, "SELETOR_USUARIO"))
        #   )
        #   campo_usuario.send_keys(username)
        #   self.driver.find_element(By.ID, "SELETOR_SENHA").send_keys(password)
        #   self.driver.find_element(By.ID, "SELETOR_BOTAO_ENTRAR").click()
        raise NotImplementedError(
            "Seletores de login ainda não configurados (veja os TODOs em login())."
        )

    def fill_form(self, dados_nota: dict) -> None:
        self.driver.get(self.settings.url_emissao)
        # TODO: mapear cada campo do formulário real, algo como:
        #   from selenium.webdriver.common.by import By
        #   self.driver.find_element(By.ID, "SELETOR_CNPJ_TOMADOR").send_keys(
        #       dados_nota["tomador_cnpj_cpf"]
        #   )
        #   self.driver.find_element(By.ID, "SELETOR_VALOR").send_keys(dados_nota["valor"])
        #   ...
        raise NotImplementedError(
            "Seletores do formulário ainda não configurados (veja os TODOs em fill_form())."
        )

    def screenshot(self, nome: str) -> str:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOTS_DIR / f"{nome}.png"
        self.driver.save_screenshot(str(path))
        return str(path)

    def submit(self, dry_run: bool) -> dict:
        if dry_run:
            screenshot_path = self.screenshot("dry_run_preview")
            return {"status": "dry_run", "screenshot": screenshot_path}

        # TODO: seletor real do botão final de emissão.
        #   from selenium.webdriver.common.by import By
        #   self.driver.find_element(By.ID, "SELETOR_BOTAO_EMITIR").click()
        raise NotImplementedError(
            "Seletor do botão de emissão ainda não configurado (veja o TODO em submit())."
        )

    def close(self) -> None:
        self.driver.quit()
