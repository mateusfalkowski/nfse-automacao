from __future__ import annotations

import argparse
import re
import sys
from datetime import date

from . import audit_log, config
from .nfse_bot import NFSeBot


def prompt(campo: str, default: str = "") -> str:
    sufixo = f" [{default}]" if default else ""
    valor = input(f"{campo}{sufixo}: ").strip()
    return valor or default


def coletar_dados_nota(settings: config.Settings) -> dict:
    hoje = date.today()
    competencia_padrao = hoje.strftime("%d-%m-%Y")

    print("\n=== Dados da nota (Enter aceita o valor padrão entre colchetes) ===")
    return {
        "tomador_cnpj_cpf": prompt("CNPJ/CPF do tomador"),
        "tomador_nome": prompt("Nome/Razão social do tomador"),
        # Nome/endereço do tomador normalmente vêm da busca por CNPJ no site;
        # CEP/número aqui são só pra "Informações para Obra" (etapa Serviço),
        # que usa o endereço onde o serviço foi prestado — deixe em branco se
        # não se aplicar ao código de serviço usado.
        "tomador_endereco_cep": prompt("CEP do local do serviço (obra, opcional)"),
        "tomador_endereco_numero": prompt("Número do local do serviço (opcional)"),
        "valor": prompt("Valor do serviço (ex: 1500.00)"),
        "descricao": prompt("Descrição do serviço", settings.descricao_padrao),
        "competencia": prompt("Competência (DD-MM-AAAA)", competencia_padrao),
        "codigo_servico": prompt("Código do serviço", settings.codigo_servico_padrao),
    }


def ler_bloco_colado() -> str:
    print(
        "\nCole abaixo o resumo recebido (do formulario.html/WhatsApp) e "
        "termine com uma linha só com '---':"
    )
    linhas: list[str] = []
    while True:
        try:
            linha = input()
        except EOFError:
            break
        if linha.strip() == "---":
            break
        linhas.append(linha)
    return "\n".join(linhas)


def parse_resumo(texto: str, settings: config.Settings) -> dict:
    """Extrai os campos do texto que o formulario.html gera (label: valor,
    uma por linha). Formato esperado do "Endereço do tomador":
    "Logradouro, Numero, Bairro, Cidade/UF, CEP 00.000-000"."""
    campos = {}
    for linha in texto.splitlines():
        if ":" in linha:
            chave, _, valor = linha.partition(":")
            campos[chave.strip()] = valor.strip()

    endereco = campos.get("Endereço do tomador", "")
    partes = [p.strip() for p in endereco.split(",")]
    numero = partes[1] if len(partes) > 1 else ""
    cep_match = re.search(r"CEP\s*([\d.\-]+)", endereco)
    cep = cep_match.group(1) if cep_match else ""

    hoje = date.today()
    comp_match = re.match(r"(\d{2})/(\d{4})", campos.get("Competência", ""))
    if comp_match:
        competencia = f"{hoje.day:02d}-{comp_match.group(1)}-{comp_match.group(2)}"
    else:
        competencia = hoje.strftime("%d-%m-%Y")

    return {
        "tomador_cnpj_cpf": campos.get("CNPJ/CPF do tomador", ""),
        "tomador_nome": campos.get("Nome do tomador", ""),
        "tomador_endereco_cep": cep,
        "tomador_endereco_numero": numero,
        "valor": campos.get("Valor total do serviço", "").replace("R$", "").strip(),
        "descricao": campos.get("Descrição do serviço", settings.descricao_padrao),
        "competencia": competencia,
        "codigo_servico": campos.get("Código de tributação", settings.codigo_servico_padrao),
    }


def confirmar(dados: dict) -> bool:
    print("\n=== Confira os dados antes de prosseguir ===")
    for chave, valor in dados.items():
        print(f"  {chave}: {valor}")
    resposta = input("\nConfirma o envio destes dados? [s/N]: ").strip().lower()
    return resposta == "s"


def main() -> int:
    # No Windows o stdin/stdout às vezes vem em cp1252 em vez de UTF-8
    # (depende do terminal/como o script é chamado), o que corrompe
    # acentuação digitada (ex: "inspeção" virando "inspeÃ§Ã£o") — e isso vai
    # pro campo de descrição da nota de verdade, não é só cosmético. Força
    # UTF-8 pra não depender da configuração de quem roda.
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Automação de emissão de NFS-e (MEI)")
    parser.add_argument(
        "--auto",
        action="store_true",
        help=(
            "Desativa o dry-run e clica de fato no botão de emitir. Só use "
            "depois de validar várias execuções em dry-run."
        ),
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Pula a confirmação no terminal (use com cuidado, ex. em execução agendada).",
    )
    args = parser.parse_args()

    settings = config.load_settings()

    print("\n[1] Colar resumo recebido (WhatsApp/formulário)  [2] Preencher campo a campo")
    escolha = input("Escolha [1]: ").strip() or "1"
    if escolha == "1":
        dados_nota = parse_resumo(ler_bloco_colado(), settings)
    else:
        dados_nota = coletar_dados_nota(settings)

    if not args.yes and not confirmar(dados_nota):
        print("Cancelado pelo usuário.")
        return 1

    run_id = audit_log.log_attempt(dados_nota)
    bot = NFSeBot(settings)
    try:
        bot.abrir_nova_nfse()
        bot.preencher_pessoas(dados_nota)
        bot.preencher_servico(dados_nota)
        bot.preencher_valores(dados_nota)
        resultado = bot.submit(dry_run=not args.auto)
        audit_log.log_result(
            run_id, status=resultado.get("status", "desconhecido"), detalhe=str(resultado)
        )
        print(f"\nConcluído: {resultado}")
        return 0
    except Exception as exc:
        audit_log.log_result(run_id, status="erro", detalhe=str(exc))
        print(f"\nErro durante a automação: {exc}", file=sys.stderr)
        return 1
    finally:
        bot.close()


if __name__ == "__main__":
    raise SystemExit(main())
