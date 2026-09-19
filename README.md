# NFS-e Automation (MEI)

Automação da emissão de NFS-e no **nfse.gov.br** (Emissor Nacional). Projeto
separado do repositório do jogo GP Manager de propósito — este repo fica
**local**, sem remoto, para não misturar dados fiscais/credenciais com um
repositório público.

## Modo atual: preenchimento ao vivo

Fluxo em uso hoje (combinado 2026-09-18): você loga no nfse.gov.br e depois
faz o captcha + clica em "Emitir" — o Claude preenche os campos da nota pelo
navegador embutido do app, ao vivo, na conversa. Ninguém além de você toca em
login/captcha/emissão.

Use [`formulario.html`](formulario.html) (abre local, sem servidor) como
apoio: escolhe um cliente conhecido ou digita um novo, preenche
descrição/valor/competência, e gera um resumo pra conferir enquanto preenche
no site de verdade.

### O que já é fixo (confirmado em 6 notas reais emitidas)

- Código de tributação nacional: **07.05.01** (reparação/conservação/reforma
  de edifícios e congêneres)
- ISSQN: Operação Tributável, Não Retido
- IBS/CBS: sempre em branco/zerado, inclusive na nota mais recente — responder
  "Não" na pergunta do assistente de emissão mantém o padrão histórico
  (constatação empírica, não é parecer tributário)

### Dois emitentes

O CNPJ emitente é definido por **quem está logado**, não é campo do
formulário: Mateus (61.827.278/0001-21, próprio) ou Marcio Edson Falkowski
(43.070.496/0001-82). Confirme em "Meus dados" na home do portal antes de
preencher qualquer nota.

### Pegadinhas do site

- Ele salva **rascunhos automaticamente** ao começar uma nota nova — confira
  a lista de rascunhos antes de abrir uma nota do zero, pra não duplicar.
- Link direto pra "Visualizar" uma nota antiga abre em branco; precisa
  navegar clicando pela interface.
- Uma aba nova no navegador embutido não herda a sessão logada — reaproveite
  a mesma aba, ou vai pedir login de novo.

## Modo alternativo (pausado): script Python/Selenium

Fica pronto pra retomar quando fizer sentido rodar sem o Claude aberto —
ideia é o script conectar numa janela de Chrome que você já logou
manualmente (via `--remote-debugging-port`), sem guardar senha nenhuma.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
copy config\settings.example.yaml config\settings.yaml
```

```bash
python -m src.cli              # dry-run: preenche tudo, tira screenshot, NÃO clica em emitir
python -m src.cli --auto       # emite de verdade
python -m src.cli --auto --yes # emite sem a confirmação no terminal (uso em agendamento)
```

`src/nfse_bot.py` ainda tem os seletores do Selenium como `TODO` — faltam ser
preenchidos com base na inspeção real da página (pendente: fazer isso com uma
sessão logada aberta).

Todo run grava duas linhas em `logs/nfse_emissoes.jsonl` (antes e depois de
cada tentativa), pra ter rastro mesmo se o processo falhar no meio.

## Pontos de atenção

- **Captcha**: não ajudo a contornar captcha/bot-detection — essa etapa
  continua manual de qualquer forma, ao vivo ou via script.
- **Irreversibilidade**: depois de emitida, a NFS-e normalmente não pode ser
  cancelada livremente. Por isso o clique final é sempre seu, no modo ao vivo,
  e o script tem dry-run como padrão.
- **Senha**: se/quando o script assumir o login, a senha fica só em `.env`
  (gitignored) e nunca é gravada no log de auditoria.
