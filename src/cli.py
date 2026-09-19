from __future__ import annotations

import argparse
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


def confirmar(dados: dict) -> bool:
    print("\n=== Confira os dados antes de prosseguir ===")
    for chave, valor in dados.items():
        print(f"  {chave}: {valor}")
    resposta = input("\nConfirma o envio destes dados? [s/N]: ").strip().lower()
    return resposta == "s"


def main() -> int:
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
