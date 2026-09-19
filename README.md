# NFS-e Automation (MEI)

Automação da emissão de NFS-e no **nfse.gov.br** (Emissor Nacional). Projeto
separado do repositório do jogo GP Manager de propósito — este repo é
**público** no GitHub (dados de CNPJ são públicos), mas `config/settings.yaml`
e `logs/` continuam de fora (`.gitignore`), já que ali entram valores e
histórico reais de notas.

Site publicado (usa o [`formulario.html`](formulario.html) como referência
pra preencher manualmente, sem automação nenhuma):
https://mateusfalkowski.github.io/nfse-automacao/formulario.html

## Script Python/Selenium (em andamento)

O script **nunca faz login** — ele se conecta numa janela de Chrome que você
já abriu e logou manualmente, via `--remote-debugging-port`. Assim a senha
nunca passa pelo código.

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config\settings.example.yaml config\settings.yaml
```

Preencha `config\settings.yaml` (CNPJ pra rótulo do log; a URL de emissão e
os valores fixos já vêm certos por padrão).

### Uso

1. Abra o Chrome manualmente com depuração remota habilitada:
   ```bash
   chrome.exe --remote-debugging-port=9222
   ```
2. Faça login normalmente em nfse.gov.br nessa janela.
3. Rode o script:
   ```bash
   python -m src.cli              # dry-run: preenche e tira screenshot, NÃO emite
   python -m src.cli --auto       # emite de verdade
   python -m src.cli --auto --yes # sem confirmação no terminal (uso avançado)
   ```

### Estado dos seletores (`src/nfse_bot.py`)

Todas as 4 etapas mapeadas e implementadas, testado ao vivo até a tela final
sem clicar em emitir (2026-09-18, nota de teste pro Cosmos, R$1,00):

- ✅ Etapa 1 — **Pessoas**: IBS/CBS, competência, tomador (CNPJ com busca
  automática de nome/endereço), botão avançar.
- ✅ Etapa 2 — **Serviço**: município (combobox com busca), código de
  tributação (combobox com busca), descrição, e "Informações para Obra"
  (usa o endereço do tomador — só aparece pra códigos de construção/reforma
  como o 07.05.01).
- ✅ Etapa 3 — **Valores**: valor do serviço; ISSQN e Tributação Federal já
  vêm travados certos pro Simples Nacional. Precisa escolher "Não informar
  nenhum valor estimado" nos Tributos aproximados (campo obrigatório).
- ✅ Etapa 4 — **Nota**: botão final é `btnProsseguir` ("Emitir NFS-e") — só
  clicado se `dry_run=False`.

Achados importantes:
- Interações via JavaScript puro (sem passar por um clique/tecla de verdade)
  **não** disparam a busca de CNPJ nem a revelação de alguns campos — use
  sempre `.click()`/`.send_keys()` do Selenium (like the code already does),
  nunca `execute_script` pra simular clique.
- "Item da NBS" aparece com * mas não bloqueia o avançar em branco.
- Combobox de Município/Código de Tributação são select2 (busca com clique
  + digitação + clique na opção) — ver `_select2_escolher()`.

Ainda não testado: rodar isso de fato via Selenium (só testei manualmente no
navegador embutido do Claude). O nome dos métodos/seletores deve estar
certo, mas vale conferir no primeiro run real.

Todo run grava duas linhas em `logs/nfse_emissoes.jsonl` (antes e depois de
cada tentativa), pra ter rastro mesmo se o processo falhar no meio.

## Modo alternativo: preenchimento ao vivo com o Claude

Antes de escrever o script, o fluxo era: você loga, faz captcha e clica em
"Emitir"; o Claude preenche os campos ao vivo pelo navegador embutido do app,
na conversa. Ainda funciona como plano B se o script travar em algo.

### Dois emitentes

O CNPJ emitente é definido por **quem está logado**, não é campo do
formulário: Mateus (61.827.278/0001-21, próprio) ou Marcio Edson Falkowski
(43.070.496/0001-82). Confirme em "Meus dados" na home do portal antes de
preencher qualquer nota.

### O que já é fixo (confirmado em 6 notas reais emitidas)

- Código de tributação nacional: **07.05.01** (reparação/conservação/reforma
  de edifícios e congêneres)
- ISSQN: Operação Tributável, Não Retido
- IBS/CBS: sempre em branco/zerado, inclusive na nota mais recente — responder
  "Não" mantém o padrão histórico (constatação empírica, não é parecer
  tributário)

### Pegadinhas do site

- Ele salva **rascunhos automaticamente** ao começar uma nota nova — confira
  a lista de rascunhos antes de abrir uma nota do zero, pra não duplicar.
- Link direto pra "Visualizar" uma nota antiga abre em branco; precisa
  navegar clicando pela interface.
- Uma aba nova no navegador (embutido ou via debugger-address) não herda a
  sessão logada — reaproveite a mesma janela, ou vai pedir login de novo.

## Pontos de atenção

- **Captcha**: não ajudo a contornar captcha/bot-detection — se aparecer em
  algum ponto do fluxo, essa etapa continua manual de qualquer forma.
- **Irreversibilidade**: depois de emitida, a NFS-e normalmente não pode ser
  cancelada livremente. Por isso o script tem dry-run como padrão (só emite
  de verdade com `--auto`), e no modo ao vivo o clique final é sempre seu.
