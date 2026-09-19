from __future__ import annotations

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import Settings

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "logs" / "screenshots"
MUNICIPIO = "Curitiba/PR"


class NFSeBot:
    """Conecta numa janela do Chrome já aberta e logada (veja README:
    rodar Chrome com --remote-debugging-port). O login nunca é feito por
    aqui — é sempre manual, na sua própria sessão.

    Seletores confirmados por inspeção ao vivo em 2026-09-18 (conta Mateus,
    CNPJ 61.827.278/0001-21), preenchendo uma nota de teste (Cosmos, R$1,00)
    até a etapa final sem clicar em "Emitir NFS-e"."""

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

    def _click_radio_by_label(self, texto: str) -> None:
        """Clica no radio associado a um <label> que contenha esse texto.
        Mais robusto que adivinhar o value numérico de cada opção."""
        label = self.driver.find_element(By.XPATH, f'//label[contains(normalize-space(.), "{texto}")]')
        try:
            label.find_element(By.TAG_NAME, "input").click()
        except Exception:
            self.driver.find_element(By.ID, label.get_attribute("for")).click()

    def _select2_escolher(self, select_id: str, busca: str, contem_texto: str) -> None:
        """Abre um combobox select2 (busca com AJAX/filtro local), digita e
        clica na opção cujo texto contenha `contem_texto`."""
        self.driver.find_element(By.CSS_SELECTOR, f"#{select_id} + span").click()
        campo_busca = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input.select2-search__field"))
        )
        campo_busca.send_keys(busca)
        opcao = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f'//li[contains(@class,"select2-results__option") and contains(., "{contem_texto}")]')
            )
        )
        opcao.click()

    def _avancar(self) -> None:
        self.driver.find_element(By.XPATH, '//*[self::button or self::a][contains(., "Avançar")]').click()

    def preencher_pessoas(self, dados: dict) -> None:
        """Etapa 1 (Pessoas)."""
        # IBS/CBS precisa ser respondido ANTES: é o que libera o campo de competência.
        self._set_radio("PreencherInfoIBSCBS", "1" if self.settings.ibs_cbs == "Sim" else "0")

        competencia = self.driver.find_element(By.ID, "DataCompetencia")
        competencia.clear()
        competencia.send_keys(dados["competencia"])  # formato DD-MM-AAAA

        # TipoEmitente já vem em "1" (Prestador/Fornecedor) por padrão.

        # Compras governamentais: default "Não" (caso normal, tomador não é governo).
        self._click_radio_by_label("Não")

        self.driver.find_element(By.ID, "Tomador_Inscricao").send_keys(dados["tomador_cnpj_cpf"])
        self.driver.find_element(By.ID, "btn_Tomador_Inscricao_pesquisar").click()
        self.wait.until(lambda d: d.find_element(By.ID, "Tomador_Nome").get_attribute("value"))
        # A busca por CNPJ preenche Nome e Endereço automaticamente. Só usa
        # tomador_nome/tomador_endereco de `dados` se a busca não achar nada
        # (ex.: CPF de pessoa física, ou CNPJ novo ainda não cadastrado).
        if not self.driver.find_element(By.ID, "Tomador_Nome").get_attribute("value"):
            self.driver.find_element(By.ID, "Tomador_Nome").send_keys(dados["tomador_nome"])

        self._avancar()

    def preencher_servico(self, dados: dict) -> None:
        """Etapa 2 (Serviço). Precisa da etapa Pessoas já concluída."""
        self._select2_escolher("LocalPrestacao_CodigoMunicipioPrestacao", MUNICIPIO.split("/")[0], MUNICIPIO)
        self._select2_escolher(
            "ServicoPrestado_CodigoTributacaoNacional", dados["codigo_servico"], dados["codigo_servico"]
        )
        # "O serviço é um caso de imunidade/exportação/não incidência?" — Não.
        self._click_radio_by_label("Não")

        # Item da NBS (*): parece obrigatório na tela mas NÃO bloqueia o
        # Avançar deixado em branco — confirmado testando ao vivo. Não
        # preencher.

        self.driver.find_element(By.ID, "ServicoPrestado_Descricao").send_keys(dados["descricao"])

        # "Informações para Obra" só aparece pra códigos de tributação de
        # construção/reforma (caso do 07.05.01). Usamos o endereço do
        # tomador como endereço da obra (é o prédio onde o serviço é feito).
        if dados.get("tomador_endereco_cep"):
            self._click_radio_by_label("Endereço no Brasil")  # value="3"
            self.driver.find_element(By.ID, "Obra_CEP").send_keys(dados["tomador_endereco_cep"])
            self.driver.find_element(By.ID, "btn_Obra_CEP").click()
            self.wait.until(lambda d: d.find_element(By.ID, "Obra_Bairro").get_attribute("value"))
            if dados.get("tomador_endereco_numero"):
                self.driver.find_element(By.ID, "Obra_Numero").send_keys(dados["tomador_endereco_numero"])

        self._avancar()

    def preencher_valores(self, dados: dict) -> None:
        """Etapa 3 (Valores/Tributação). ISSQN e Tributação Federal já vêm
        travados e corretos pro Simples Nacional — só falta o valor e a
        declaração de tributos aproximados."""
        self.driver.find_element(By.ID, "Valores_ValorServico").send_keys(dados["valor"])
        self._click_radio_by_label("Não informar nenhum valor estimado")
        self._avancar()

    def screenshot(self, nome: str) -> str:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOTS_DIR / f"{nome}.png"
        self.driver.save_screenshot(str(path))
        return str(path)

    def submit(self, dry_run: bool) -> dict:
        if dry_run:
            screenshot_path = self.screenshot("dry_run_preview")
            return {"status": "dry_run", "screenshot": screenshot_path}

        self.driver.find_element(By.ID, "btnProsseguir").click()  # "Emitir NFS-e"
        return {"status": "emitido"}

    def close(self) -> None:
        self.driver.quit()
