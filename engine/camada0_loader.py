import json
import os
from typing import Any, Dict, Optional

from engine.ledger_ops import load_for_session, load_civilizational_snapshot


def _log(msg: str) -> None:
    """Log centralizado da Camada 0."""
    print(f"[CAMADA 0] {msg}")


# ===============================================================
# PILAR 5 — Ledger Simbólico Civilizatório (conectado)
# ===============================================================
def _load_civilizational_stats(base_dir: str) -> Dict[str, Any]:
    """
    Carrega estatísticas agregadas do Ledger Civilizatório.

    Usa engine.ledger_ops.load_civilizational_snapshot(base_dir).

    Estrutura esperada:
    {
        "available": True/False,
        "meta": {...},
        "stats": {
            "global_self_harm_risk": "low|medium|high",
            "misinformation_pressure": "low|medium|high",
            "a1_risk_ratio": float,
            "a2_uncertainty_ratio": float,
            "entries_total": int,
            ...
        }
    }
    """
    try:
        snapshot = load_civilizational_snapshot(base_dir)
        if not isinstance(snapshot, dict):
            return {
                "available": False,
                "meta": {
                    "source": "load_civilizational_snapshot",
                    "note": "Snapshot retornou formato inesperado.",
                },
                "stats": {},
            }
        return snapshot
    except Exception as e:
        _log(f"AVISO: falha ao carregar snapshot civilizatório: {e}")
        return {
            "available": False,
            "meta": {
                "source": "load_civilizational_snapshot",
                "note": f"Exceção ao carregar snapshot: {e}",
            },
            "stats": {},
        }


# ===============================================================
# PILAR 1 — Prognóstico Ético Multiturno (seed)
# ===============================================================
def _compute_initial_prognosis(
    session_memory: Dict[str, Any],
    civilizational_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prognóstico inicial de risco para a sessão.
    Ainda extremamente conservador (versão seed),
    mas preparado para expansão futura (análise de múltiplos turnos).
    """
    prognosis = {
        "predicted_self_harm_risk": "low",
        "predicted_chemistry_risk": "low",
        "predicted_violence_risk": "low",
        "predicted_emotional_instability": "low",
        "has_previous_session": bool(session_memory),
    }

    # Exemplo de uso futuro de stats civilizatórios:
    stats = civilizational_stats.get("stats") or {}
    global_selfharm = stats.get("global_self_harm_risk")
    if global_selfharm in ("medium", "high"):
        prognosis["predicted_self_harm_risk"] = global_selfharm

    misinformation_pressure = stats.get("misinformation_pressure")
    if misinformation_pressure in ("medium", "high"):
        # Em versões futuras, isso pode modular predicted_violence_risk
        # ou risco de delírio.
        pass

    # Futuro: aprendizado baseado em histórico da sessão:
    # ex: session_memory.get("last_entry"), analisar padrões, etc.

    return prognosis


# ===============================================================
# CAMADA 0 — BOOT ÉTICO COMPLETO (ACI4A)
# ===============================================================
def camada0_boot(
    fsm_obj: Optional[Any] = None,
    base_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    CAMADA 0 — BOOT ÉTICO / FSM / LEDGER / CONTEXTO CIVILIZATÓRIO (ACI4A)

    Responsabilidades:
    - Carregar axiomas (odg_master_v0.2.json)
    - Instanciar FSM
    - Carregar ledger de sessão (memória individual)
    - Carregar snapshot civilizatório agregado (Pilar 5)
    - Calcular prognóstico inicial (Pilar 1)
    - Reidratar FSM com memória de sessão
    - Validar axiomas
    - Aplicar moduladores evolutivos (Pilar 2)
    - Retornar fsm + memória + prognóstico + stats
    """

    errors = []

    # -----------------------------------------------------------
    # 0.0 — Determinar diretório base
    # -----------------------------------------------------------
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))

    base_dir = os.path.abspath(base_dir)
    _log(f"Base dir resolvido: {base_dir}")

    # -----------------------------------------------------------
    # 0.1 — Instanciar FSM se necessário
    # -----------------------------------------------------------
    if fsm_obj is None:
        try:
            from engine.fsm_axiomas import FSMAxiomas
            fsm_obj = FSMAxiomas()
            _log("FSMAxiomas instanciada automaticamente.")
        except Exception as e:
            msg = f"ERRO: Não foi possível instanciar FSMAxiomas: {e}"
            _log(msg)
            return {
                "fsm": None,
                "session_memory": {},
                "civilizational_stats": {},
                "prognostico_inicial": {},
                "ok": False,
                "errors": [msg],
            }

    # -----------------------------------------------------------
    # 0.2 — Localizar arquivo de axiomas
    # -----------------------------------------------------------
    master_path = os.path.join(base_dir, "odg_master_v0.2.json")

    if not os.path.exists(master_path):
        msg = "ERRO: odg_master_v0.2.json não encontrado."
        _log(msg)
        return {
            "fsm": fsm_obj,
            "session_memory": {},
            "civilizational_stats": {},
            "prognostico_inicial": {},
            "ok": False,
            "errors": [msg],
        }

    _log(f"Axiomas localizados em: {master_path}")

    # -----------------------------------------------------------
    # 0.3 — Carregar axiomas
    # -----------------------------------------------------------
    try:
        with open(master_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        msg = f"ERRO ao carregar master JSON: {e}"
        _log(msg)
        return {
            "fsm": fsm_obj,
            "session_memory": {},
            "civilizational_stats": {},
            "prognostico_inicial": {},
            "ok": False,
            "errors": [msg],
        }

    if "axiomas" not in data:
        msg = "ERRO: JSON não contém 'axiomas'."
        _log(msg)
        return {
            "fsm": fsm_obj,
            "session_memory": {},
            "civilizational_stats": {},
            "prognostico_inicial": {},
            "ok": False,
            "errors": [msg],
        }

    axiomas_dict = data["axiomas"]

    try:
        fsm_obj.load_axiomas(axiomas_dict)
        _log("Axiomas carregados na FSM.")
    except Exception as e:
        msg = f"ERRO ao carregar axiomas na FSM: {e}"
        _log(msg)
        return {
            "fsm": fsm_obj,
            "session_memory": {},
            "civilizational_stats": {},
            "prognostico_inicial": {},
            "ok": False,
            "errors": [msg],
        }

    # -----------------------------------------------------------
    # 0.3 — Carregar memória de sessão (ledger individual)
    # -----------------------------------------------------------
    try:
        session_memory = load_for_session(base_dir)
    except Exception as e:
        msg = f"ERRO ao carregar ledger da sessão: {e}"
        _log(msg)
        session_memory = None

    if session_memory:
        _log("Memória de sessão carregada.")
    else:
        _log("Nenhuma memória prévia encontrada — primeiro boot.")
        session_memory = {}

    # -----------------------------------------------------------
    # 0.4 — Carregar estatísticas civilizatórias (Ledger Civilizatório)
    # -----------------------------------------------------------
    civilizational_stats = _load_civilizational_stats(base_dir)
    if civilizational_stats.get("available"):
        _log("Estatísticas civilizatórias carregadas a partir do ledger.")
    else:
        _log("Estatísticas civilizatórias indisponíveis ou vazias.")

    # -----------------------------------------------------------
    # Prognóstico inicial (Pilar 1)
    # -----------------------------------------------------------
    prognostico_inicial = _compute_initial_prognosis(
        session_memory=session_memory,
        civilizational_stats=civilizational_stats,
    )
    _log("Prognóstico ético inicial calculado.")

    # -----------------------------------------------------------
    # Reidratar FSM + validar axiomas
    # -----------------------------------------------------------
    if hasattr(fsm_obj, "init_from_memory"):
        try:
            fsm_obj.init_from_memory(session_memory)
            _log("FSM reidratada a partir do ledger.")
        except Exception as e:
            msg = f"AVISO: falha ao reidratar FSM: {e}"
            _log(msg)
            errors.append(msg)

    if hasattr(fsm_obj, "validate"):
        try:
            fsm_obj.validate()
            _log("FSM validada com sucesso.")
        except Exception as e:
            msg = f"AVISO: falha na validação da FSM: {e}"
            _log(msg)
            errors.append(msg)

    # -----------------------------------------------------------
    # PILAR 2 — Aplicar moduladores evolutivos (se existir método)
    # -----------------------------------------------------------
    if hasattr(fsm_obj, "apply_civilizational_modulators"):
        try:
            fsm_obj.apply_civilizational_modulators(
                civilizational_stats=civilizational_stats,
                session_memory=session_memory,
                prognostico_inicial=prognostico_inicial,
            )
            _log("Moduladores evolutivos aplicados.")
        except Exception as e:
            msg = f"AVISO: falha ao aplicar moduladores evolutivos: {e}"
            _log(msg)
            errors.append(msg)

    ok = len([e for e in errors if e.startswith("ERRO")]) == 0

    if ok:
        _log("Boot ético ACI4A finalizado com sucesso.")
    else:
        _log("Boot ético ACI4A concluído com AVISOS/ERROS.")

    return {
        "fsm": fsm_obj,
        "session_memory": session_memory,
        "civilizational_stats": civilizational_stats,
        "prognostico_inicial": prognostico_inicial,
        "ok": ok,
        "errors": errors,
    }
