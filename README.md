# NFS-e Automation (MEI)

Automação da emissão de NFS-e no **nfse.gov.br** (Emissor Nacional). Projeto
separado do repositório do jogo GP Manager de propósito — este repo é
**público** no GitHub (dados de CNPJ são públicos), mas `config/settings.yaml`
e `logs/` continuam de fora (`.gitignore`), já que ali entram valores e
histórico reais de notas.

Site publicado: https://mateusfalkowski.github.io/nfse-automacao/formulario.html

### Fluxo pra quem não mexe com o script (ex: pai/mãe)

1. Preenche o [`formulario.html`](formulario.html) no celular/PC.
2. Clica em **"Enviar por WhatsApp"** — abre o WhatsApp com o resumo pronto
   pra mandar pra quem for rodar o script.
3. Quem recebe roda `python -m src.cli`, escolhe a opção **"Colar resumo"**,
   cola a mensagem do WhatsApp e termina com uma linha `---`. O script separa
   os campos sozinho — não precisa digitar nada de novo.

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
3. Rode o script (ele pergunta se você quer colar o resumo do WhatsApp/
   formulário ou preencher campo a campo):
   ```bash
   python -m src.cli              # dry-run: preenche e tira screenshot, NÃO emite
   python -m src.cli --auto       # emite de verdade
   python -m src.cli --auto --yes # sem confirmação no terminal (uso avançado)
   ```

Rodando assim, direto no terminal, não usa Claude nem gasta tokens — é só
Python/Selenium na sua máquina.

### Estado dos seletores (`src/nfse_bot.py`)

**Confirmado rodando `python -m src.cli` de verdade** (não só manualmente): as
4 etapas passam sem erro e o dry-run chega até a tela real de
`DPS/EmitirNFSe` (2026-09-19, nota de teste pro Cosmos, R$1,00).

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
  clicado se `dry_run=False`. **Nunca testado de verdade** (só chegou na
  tela via dry-run) — a primeira vez com `--auto` merece atenção redobrada.

Achados importantes (todos custaram várias rodadas de debug pra descobrir):
- **A competência tem que ser escolhida no calendário de verdade, nunca
  digitada no campo de texto** — digitar deixa o valor certo visualmente,
  mas os dados do emitente (nome, Simples Nacional, município) nunca
  carregam, e o formulário inteiro fica travado sem erro nenhum visível.
- Rádios têm o `<input>` escondido atrás de um estilo customizado — clicar
  precisa ser no `<label>` pai, nunca no input (`element not interactable`).
- "Compras Governamentais" não tem asterisco de obrigatório e fica
  desabilitado até o tomador ser identificado — não precisa mexer nele.
- "Item da NBS" aparece com * mas não bloqueia o avançar em branco.
- Preencher um campo costuma reposicionar coisas na tela (ex: endereço do
  tomador aparecendo depois da busca de CNPJ) — todo clique passa por
  `_clicar()`, que rola até o elemento e espera um instante antes de clicar,
  senão o clique cai em cima de outra coisa.
- Combobox de Município/Código de Tributação são select2 (busca com clique
  + digitação + clique na opção) — ver `_select2_escolher()`.
- Interações via JavaScript puro (`execute_script` simulando clique) não
  disparam vários desses comportamentos — só clique/tecla de verdade do
  Selenium funciona (é basicamente a mesma lição da competência, mas vale
  lembrar antes de "otimizar" qualquer clique daqui.

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
