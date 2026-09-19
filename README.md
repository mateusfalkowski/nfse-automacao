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

Mapeados inspecionando o HTML real do assistente de emissão (2026-09-18):

- ✅ Etapa 1 — **Pessoas**: IBS/CBS, competência, tomador (CNPJ/nome), botão
  avançar. Detalhe: `PreencherInfoIBSCBS` precisa ser respondido antes do
  campo de competência ficar habilitado; o checkbox de endereço do tomador
  parece ter estilo customizado (não confirmado se `.click()` do Selenium
  funciona nele).
- ⬜ Etapa 2 — **Serviço**: não inspecionada ainda.
- ⬜ Etapa 3 — **Valores**: não inspecionada ainda.
- ⬜ Etapa 4 — **Nota** (botão final de emitir): não inspecionada ainda.

Pra completar as etapas que faltam: com o Chrome já conectado e a etapa
Pessoas preenchida, inspecionar a próxima tela do mesmo jeito (JS no console:
`Array.from(document.querySelectorAll('input,select,textarea,button')).map(...)`
pra listar id/name/type de cada campo).

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
