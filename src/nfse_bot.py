from __future__ import annotations

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import Settings

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "logs" / "screenshots"


class NFSeBot:
    """Conecta numa janela do Chrome já aberta e logada (veja README:
    rodar Chrome com --remote-debugging-port). O login nunca é feito por
    aqui — é sempre manual, na sua própria sessão."""

    def __init__(self, settings: Settings):
        self.settings = settings
        options = Options()
        options.debugger_address = settings.debugger_address
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def abrir_nova_nfse(self) -> None:
        self.driver.get(self.settings.url_emissao)

    def _set_radio(self, name: str, valor: str) -> None:
        self.driver.find_element(By.CSS_SELECTOR, f'input[name="{name}"][value="{valor}"]').click()

    def preencher_pessoas(self, dados: dict) -> None:
        """Etapa 1 (Pessoas) do assistente de emissão. Seletores confirmados
        inspecionando o HTML real em 2026-09-18 (conta Mateus)."""
        # IBS/CBS precisa ser respondido ANTES: é o que libera o campo de competência.
        self._set_radio("PreencherInfoIBSCBS", "1" if self.settings.ibs_cbs == "Sim" else "0")

        competencia = self.driver.find_element(By.ID, "DataCompetencia")
        competencia.clear()
        competencia.send_keys(dados["competencia"])  # formato DD-MM-AAAA

        # TipoEmitente já vem em "1" (Prestador/Fornecedor) por padrão — não mexe
        # a menos que o caso de uso mude.

        self.driver.find_element(By.ID, "Tomador_Inscricao").send_keys(dados["tomador_cnpj_cpf"])
        self.driver.find_element(By.ID, "Tomador_Nome").send_keys(dados["tomador_nome"])

        if dados.get("tomador_endereco"):
            # TODO: Tomador_InformarEndereco parece ser um checkbox com estilo
            # customizado — um .click() direto no <input> não bastou num teste
            # rápido via JS. Testar aqui com Selenium de verdade (deve simular
            # clique de mouse real e funcionar), e ajustar se não marcar.
            self.driver.find_element(By.ID, "Tomador_InformarEndereco").click()
            # TODO: mapear os campos de endereço (CEP/Logradouro/Numero/Bairro/
            # Município) — só dá pra confirmar os IDs com o checkbox já marcado.

        self.driver.find_element(By.ID, "btnAvancar").click()

    def preencher_servico(self, dados: dict) -> None:
        # TODO: etapa 2 (Serviço) ainda não inspecionada. Precisa abrir o
        # assistente com preencher_pessoas() já concluído e repetir o mesmo
        # processo de inspeção (ver README) pra pegar os seletores reais de
        # código de serviço, descrição e ISSQN.
        raise NotImplementedError("Seletores da etapa Serviço ainda não mapeados.")

    def preencher_valores(self, dados: dict) -> None:
        # TODO: etapa 3 (Valores) ainda não inspecionada.
        raise NotImplementedError("Seletores da etapa Valores ainda não mapeados.")

    def screenshot(self, nome: str) -> str:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOTS_DIR / f"{nome}.png"
        self.driver.save_screenshot(str(path))
        return str(path)

    def submit(self, dry_run: bool) -> dict:
        if dry_run:
            screenshot_path = self.screenshot("dry_run_preview")
            return {"status": "dry_run", "screenshot": screenshot_path}

        # TODO: etapa 4 (Nota) — seletor real do botão final de emissão.
        raise NotImplementedError(
            "Seletor do botão de emissão ainda não configurado (etapa Nota)."
        )

    def close(self) -> None:
        self.driver.quit()
