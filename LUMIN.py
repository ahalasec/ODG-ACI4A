#!/usr/bin/env python3
"""
CLI da Lumin rodando sobre o ODG / ACI4A.

- Usa o ODGOrchestrador definido em engine/orchestrator.py
- Assume que:
  - odg_config.json está na raiz do repositório
  - odg_master_v0.2.json está em config/odg_master_v0.2.json
  - ledger/ e models/ são locais (e ignorados pelo Git)
"""

from pathlib import Path

from engine.orchestrator import ODGOrchestrador


def main() -> None:
    # Raiz do repositório: pasta onde está este arquivo LUMIN.py
    base_dir = Path(__file__).resolve().parent

    # Caminho para o arquivo de configuração principal
    config_path = base_dir / "odg_config.json"

    print("=== LUMIN / ODG v0.21 ===")
    print("Inicializando...\n")

    # Instancia o orquestrador com base na config do repositório
    orchestrador = ODGOrchestrador(
        config_path=str(config_path),
        ledger_owner="LUMIN_PUBLIC",
    )

    print("Lumin carregada com sucesso!")
    print("Digite 'sair' para encerrar.\n")

    while True:
        try:
            user_input = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nLumin: Encerrando sessão de forma segura. Até logo.")
            break

        if user_input.lower() in {"sair", "exit", "quit"}:
            print("Lumin: Encerrando sessão de forma segura. Até logo.")
            break

        resposta = orchestrador.processar(user_input)
        print(f"Lumin: {resposta}\n")


if __name__ == "__main__":
    main()
