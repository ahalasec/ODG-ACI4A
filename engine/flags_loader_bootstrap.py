# engine/flags_loader_bootstrap.py

import os
from typing import Optional, Callable, Dict, Any

from .mie_guardiao import FlagLoader, MIEGuardiao


def create_flags_loader(base_dir: Optional[str] = None) -> FlagLoader:
    """
    Cria e carrega um FlagLoader com todos os arquivos flags_*.json.

    :param base_dir:
        Diretório onde estão os arquivos de flags.
        Se None, assume engine/mie_flags (pasta padrão dentro do projeto).
    """
    if base_dir is None:
        # Diretório padrão: engine/mie_flags (relativo a este arquivo)
        current_dir = os.path.dirname(__file__)
        base_dir = os.path.join(current_dir, "mie_flags")

    pattern = os.path.join(base_dir, "flags_*.json")

    loader = FlagLoader()
    loader.load_from_glob(pattern)
    return loader


def create_mie_guardiao(
    base_dir: Optional[str] = None,
    ledger_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> MIEGuardiao:
    """
    Cria um MIEGuardiao já carregado com todas as flags JSON.

    :param base_dir:
        Diretório das flags (ver create_flags_loader).
    :param ledger_callback:
        Função opcional para receber o payload estruturado de análise
        e integrá-lo ao Ledger Civilizatório.
    """
    loader = create_flags_loader(base_dir=base_dir)
    mie = MIEGuardiao(flags_loader=loader, ledger_callback=ledger_callback)
    return mie


# Opcional: pequeno teste manual (pode remover em produção)
if __name__ == "__main__":
    def _debug_ledger(payload: Dict[str, Any]) -> None:
        print("=== MIE RESULT (DEBUG) ===")
        print("Texto:", payload.get("full_text"))
        print("Lexical events:", payload.get("lexical_events"))
        print("Flags dinâmicas:", [f["id"] for f in payload.get("dynamic_flags", [])])
        print("Intent vector:", payload.get("intent_vector"))

    mie = create_mie_guardiao(ledger_callback=_debug_ledger)
    res = mie.analisar_estruturado("Estou desesperado, não aguento mais", "")
    # Apenas pra ver no terminal
