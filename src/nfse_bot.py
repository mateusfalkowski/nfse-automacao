from __future__ import annotations

import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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
        # driver.get() bloqueia até o carregamento terminar, então os campos
        # já existem quando o método retorna (ao contrário de clicar num
        # link do dashboard, que não espera a navegação acontecer).
        self.driver.get(self.settings.url_emissao)
        self.wait.until(EC.presence_of_element_located((By.ID, "PreencherInfoIBSCBS")))

    def _clicar(self, elemento) -> None:
        """Rola até o elemento e dá uma folga antes de clicar. Preencher um
        campo costuma expandir/mover outras seções da tela logo em seguida
        (ex: endereço do tomador aparecendo após a busca por CNPJ), o que faz
        um clique imediato cair em cima do elemento errado."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", elemento)
        time.sleep(0.5)
        elemento.click()

    def _set_radio(self, name: str, valor: str) -> None:
        # O <input> em si é escondido pelo estilo custom do rádio (fica dentro
        # de <label><input>Texto<span class="cr">...</span></label>, sem
        # atributo for) — o Selenium recusa clicar nele direto ("element not
        # interactable"). Clica no <label> pai, que é o que está visível.
        # Alguns desses radios (ex: Compras Governamentais) começam
        # desabilitados até outra parte da tela terminar de carregar — espera
        # ficar habilitado antes de clicar, senão dá o mesmo erro.
        input_el = self.driver.find_element(By.CSS_SELECTOR, f'input[name="{name}"][value="{valor}"]')
        self.wait.until(lambda d: not input_el.get_attribute("disabled"))
        self._clicar(input_el.find_element(By.XPATH, ".."))

    def _click_radio_by_label(self, texto: str) -> None:
        """Clica no <label> que contenha esse texto (não no <input>, que
        costuma estar escondido por trás do estilo custom do rádio)."""
        self._clicar(self.driver.find_element(By.XPATH, f'//label[contains(normalize-space(.), "{texto}")]'))

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

    def _valor_br(self, valor: str) -> str:
        """O site espera vírgula decimal (1500,00). Se vier com ponto (o
        formato sugerido no prompt do cli.py, tipo 1500.00), converte."""
        return valor if "," in valor else valor.replace(".", ",")

    def _somente_digitos(self, texto: str) -> str:
        return "".join(c for c in texto if c.isdigit())

    def _fechar_confirm_se_houver(self) -> None:
        """Alguns CNPJs/CEPs disparam um popup de confirmação (jconfirm) —
        ex: dados cadastrais desatualizados/inconsistentes na Receita. Aceita
        se aparecer; se não aparecer em 2s, segue em frente normalmente."""
        try:
            WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".jconfirm-buttons button"))
            ).click()
        except TimeoutException:
            pass

    def _avancar(self) -> None:
        self._clicar(self.driver.find_element(By.XPATH, '//*[self::button or self::a][contains(., "Avançar")]'))

    def preencher_pessoas(self, dados: dict) -> None:
        """Etapa 1 (Pessoas)."""
        # IBS/CBS precisa ser respondido ANTES: é o que libera o campo de competência.
        self._set_radio("PreencherInfoIBSCBS", "1" if self.settings.ibs_cbs == "Sim" else "0")

        # Importante: tem que ser pelo calendário mesmo, não digitando no
        # campo de texto. Digitar direto deixa o campo com o valor certo
        # visualmente, mas os dados do emitente (nome, Simples Nacional,
        # município) nunca carregam — só populam quando a data é escolhida
        # pelo próprio widget (achado testando, confirmado pelo usuário).
        # Só funciona pro mês/ano já exibido no calendário (isto é, "hoje";
        # não implementa navegar pra outro mês).
        self.driver.find_element(By.ID, "btn_DataCompetencia").click()
        dia = dados["competencia"].split("-")[0].lstrip("0")
        self.wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                f'//td[contains(@class,"day") and not(contains(@class,"old")) '
                f'and not(contains(@class,"new")) and normalize-space(text())="{dia}"]',
            ))
        ).click()
        time.sleep(0.5)  # deixa o popup do calendário terminar de fechar

        # TipoEmitente já vem em "1" (Prestador/Fornecedor) por padrão.

        # "Compras governamentais" não tem asterisco de obrigatório na tela
        # (diferente de quase tudo em volta) e o input fica desabilitado até
        # o tomador ser identificado — não precisa (e não dá pra) mexer nele
        # pro caso normal (tomador não é órgão público).

        self.driver.find_element(By.ID, "Tomador_Inscricao").send_keys(dados["tomador_cnpj_cpf"])
        self.driver.find_element(By.ID, "btn_Tomador_Inscricao_pesquisar").click()
        # Espera curta: se o CNPJ não for encontrado (CPF de pessoa física,
        # CNPJ novo etc.) o campo nunca preenche sozinho, e não queremos travar
        # nos 20s do wait padrão nem abortar a execução por causa disso.
        try:
            WebDriverWait(self.driver, 4).until(
                lambda d: d.find_element(By.ID, "Tomador_Nome").get_attribute("value")
            )
        except TimeoutException:
            pass
        self._fechar_confirm_se_houver()
        if not self.driver.find_element(By.ID, "Tomador_Nome").get_attribute("value"):
            self.driver.find_element(By.ID, "Tomador_Nome").send_keys(dados["tomador_nome"])

        # TODO: pra alguns tomadores (ex: Condomínio Brasília) o CEP que vem
        # da busca por CNPJ está desatualizado na Receita Federal. Tentei
        # sobrescrever aqui, mas o campo `Tomador_EnderecoNacional_CEP` usa
        # uma máscara "00.000-000" (com ponto) diferente do padrão brasileiro
        # "00000-000", e buscar CEP nesse formato sempre retorna "CEP
        # inválido" no site — parece bug/particularidade do formulário deles
        # nesse campo específico. Por enquanto, corrija esses casos
        # manualmente na tela depois que o script preencher o resto.

        self._avancar()

    def preencher_servico(self, dados: dict) -> None:
        """Etapa 2 (Serviço). Precisa da etapa Pessoas já concluída."""
        self._select2_escolher("LocalPrestacao_CodigoMunicipioPrestacao", MUNICIPIO.split("/")[0], MUNICIPIO)
        self._select2_escolher(
            "ServicoPrestado_CodigoTributacaoNacional", dados["codigo_servico"], dados["codigo_servico"]
        )
        # "O serviço é um caso de imunidade/exportação/não incidência?" — Não.
        self._set_radio("ServicoPrestado.HaExportacaoImunidadeNaoIncidencia", "0")

        # Item da NBS (*): parece obrigatório na tela mas NÃO bloqueia o
        # Avançar deixado em branco — confirmado testando ao vivo. Não
        # preencher.

        self.driver.find_element(By.ID, "ServicoPrestado_Descricao").send_keys(dados["descricao"])

        # "Informações para Obra" só aparece pra códigos de tributação de
        # construção/reforma (caso do 07.05.01). Usamos o endereço do
        # tomador como endereço da obra (é o prédio onde o serviço é feito).
        if dados.get("tomador_endereco_cep"):
            self._set_radio("Obra.TipoInformacao", "3")  # "Endereço no Brasil"
            self.driver.find_element(By.ID, "Obra_CEP").send_keys(self._somente_digitos(dados["tomador_endereco_cep"]))
            self.driver.find_element(By.ID, "btn_Obra_CEP").click()
            self.wait.until(lambda d: d.find_element(By.ID, "Obra_Bairro").get_attribute("value"))
            if dados.get("tomador_endereco_numero"):
                self.driver.find_element(By.ID, "Obra_Numero").send_keys(dados["tomador_endereco_numero"])

        self._avancar()

    def preencher_valores(self, dados: dict) -> None:
        """Etapa 3 (Valores/Tributação). ISSQN e Tributação Federal já vêm
        travados e corretos pro Simples Nacional — só falta o valor e a
        declaração de tributos aproximados."""
        self.driver.find_element(By.ID, "Valores_ValorServico").send_keys(self._valor_br(dados["valor"]))
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
