# engine/ledger_ops.py

import os
import json
from datetime import datetime
from typing import Any, Dict, Optional, List, Callable


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class LedgerManager:
    """
    Gerencia o Ledger do ODG / ACI4A.

    v0.2 – objetivos:
    - Manter compatibilidade com o uso atual via Orchestrator v2.0:
        • __init__(base_dir, owner="Lumin")
        • registrar_interacao(user_msg=..., draft=..., resposta_final=..., ...)
        • load_for_session(base_dir) (funções utilitárias abaixo)
    - Integrar com o MIE Guardião v2.0:
        • callback para receber payload estruturado do MIE
        • armazenar 'intent_vector' + flags dinâmicas por interação

    Estrutura básica do arquivo odg_ledger_index.json:

    {
      "version": "aci4a_ledger_v0.1",
      "owner": "Lumin",
      "created_at": "...",
      "updated_at": "...",
      "total_interactions": 0,
      "interactions": [
        {
          "ts": "...",
          "user_msg": "...",
          "draft": "...",
          "final": "...",
          "fsm_states": [...],
          "fsm_snapshot": {...},
          "eventos": [...],
          "prognostico": {...},
          "civilizational_context": {...},
          "mie": {
            "lexical_events": [...],
            "dynamic_flags": [...],
            "intent_vector": {...}
          }
        },
        ...
      ]
    }

    Rotação, agregações civilizatórias e análises mais complexas
    ficam para versões futuras (v0.2+).
    """

    def __init__(self, base_dir: str, owner: str = "Lumin"):
        self.base_dir = base_dir
        self.owner = owner

        # Diretório onde o ledger é mantido
        self.ledger_dir = os.path.join(self.base_dir, "ledger")
        os.makedirs(self.ledger_dir, exist_ok=True)

        # Caminho do arquivo principal do ledger
        self.index_path = os.path.join(self.ledger_dir, "odg_ledger_index.json")

        # Payload mais recente vindo do MIE (via callback)
        self._last_mie_payload: Optional[Dict[str, Any]] = None

        # Garante que o arquivo exista (ou seja criado do zero)
        self._ensure_index_file()

    # ------------------------------------------------------------------
    # Integração com o MIE Guardião (callback)
    # ------------------------------------------------------------------
    def mie_callback(self, payload: Dict[str, Any]) -> None:
        """
        Callback para ser passado ao MIEGuardiao.

        Exemplo de uso:

            ledger = LedgerManager(base_dir)
            mie = MIEGuardiao(
                flags_loader=...,
                ledger_callback=ledger.mie_callback,
            )

        O payload possui campos:
        - user_text, draft_text, full_text
        - lexical_events
        - dynamic_flags
        - intent_vector
        """
        self._last_mie_payload = payload

    def get_mie_callback(self) -> Callable[[Dict[str, Any]], None]:
        """
        Alternativa caso se prefira obter a função em vez de referenciá-la
        diretamente. Útil para injeção em factories.
        """
        return self.mie_callback

    # ------------------------------------------------------------------
    # Registro de interação (usado pelo Orquestrador v2.0)
    # ------------------------------------------------------------------
    def registrar_interacao(
        self,
        user_msg: str,
        draft: str,
        resposta_final: str,
        estados_axiomas: Optional[List[str]] = None,
        fsm_snapshot: Optional[Dict[str, Any]] = None,
        eventos: Optional[List[str]] = None,
        prognostico: Optional[Dict[str, Any]] = None,
        civilizational_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Registra uma interação completa no ledger.

        Assinatura compatível com Orchestrator v2.0:

            self.ledger.registrar_interacao(
                user_msg=user_input,
                draft=draft,
                resposta_final=resposta_final,
                estados_axiomas=new_states,
                fsm_snapshot=fsm_snapshot,
                eventos=eventos_total,
                prognostico=prognostico_turno,
                civilizational_context=self.civilizational_stats,
            )

        Integra, se disponível, o último payload recebido do MIE via
        self.mie_callback().
        """
        data = self._load_index()

        # Garantia extra em cima do _load_index (robustez)
        if "interactions" not in data or not isinstance(data["interactions"], list):
            data["interactions"] = []
        if "total_interactions" not in data or not isinstance(data["total_interactions"], int):
            data["total_interactions"] = len(data["interactions"])

        interaction: Dict[str, Any] = {
            "ts": _now_iso(),
            "user_msg": user_msg,
            "draft": draft,
            "final": resposta_final,
            "fsm_states": estados_axiomas or [],
            "fsm_snapshot": fsm_snapshot or {},
            "eventos": eventos or [],
            "prognostico": prognostico or {},
            "civilizational_context": civilizational_context or {},
        }

        # Se o MIE tiver observado algo nesta janela, agregamos
        if self._last_mie_payload is not None:
            mie_payload = self._last_mie_payload
            self._last_mie_payload = None  # consome o snapshot

            interaction["mie"] = {
                "lexical_events": mie_payload.get("lexical_events", []),
                "dynamic_flags": mie_payload.get("dynamic_flags", []),
                "intent_vector": mie_payload.get("intent_vector", {}),
            }

        data["interactions"].append(interaction)
        data["total_interactions"] = data.get("total_interactions", 0) + 1
        data["updated_at"] = _now_iso()

        self._save_index(data)

    # ------------------------------------------------------------------
    # API de consulta simples (para futuras camadas)
    # ------------------------------------------------------------------
    def get_all_interactions(self) -> List[Dict[str, Any]]:
        """Retorna a lista de interações armazenadas."""
        data = self._load_index()
        return data.get("interactions", [])

    def get_last_interaction(self) -> Optional[Dict[str, Any]]:
        """Retorna a última interação registrada, se existir."""
        interactions = self.get_all_interactions()
        if not interactions:
            return None
        return interactions[-1]

    # ------------------------------------------------------------------
    # Infra de arquivo JSON
    # ------------------------------------------------------------------
    def _ensure_index_file(self) -> None:
        """
        Garante que o arquivo principal exista com estrutura mínima.
        Não sobrescreve se já existir.
        """
        if not os.path.exists(self.index_path):
            initial = {
                "version": "aci4a_ledger_v0.1",
                "owner": self.owner,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "total_interactions": 0,
                "interactions": [],
            }
            self._save_index(initial)

    def _load_index(self) -> Dict[str, Any]:
        """
        Carrega o índice do ledger e faz MIGRAÇÃO leve caso o formato
        seja antigo ou esteja incompleto.
        """
        if not os.path.exists(self.index_path):
            self._ensure_index_file()

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            # Em caso de corrupção, recomeça (v0.1 simples)
            return {
                "version": "aci4a_ledger_v0.1",
                "owner": self.owner,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "total_interactions": 0,
                "interactions": [],
            }

        # Se por algum motivo não for dict, reseta
        if not isinstance(data, dict):
            data = {}

        # MIGRAÇÃO / NORMALIZAÇÃO
        if "version" not in data:
            data["version"] = "aci4a_ledger_v0.1"
        if "owner" not in data:
            data["owner"] = self.owner
        if "created_at" not in data:
            data["created_at"] = _now_iso()
        if "updated_at" not in data:
            data["updated_at"] = _now_iso()
        if "interactions" not in data or not isinstance(data.get("interactions"), list):
            # Ledger antigo sem campo interactions → cria lista vazia
            data["interactions"] = []
        if "total_interactions" not in data or not isinstance(data.get("total_interactions"), int):
            data["total_interactions"] = len(data["interactions"])

        return data

    def _save_index(self, data: Dict[str, Any]) -> None:
        os.makedirs(self.ledger_dir, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------
# Funções utilitárias para a Camada 0 / boot
# ----------------------------------------------------------------------
def read_ledger_index_data(base_dir: str) -> Optional[Dict[str, Any]]:
    """
    Lê diretamente o odg_ledger_index.json se existir.

    Usado como base para carregar memória simbólica de sessão.
    """
    ledger_dir = os.path.join(base_dir, "ledger")
    index_path = os.path.join(ledger_dir, "odg_ledger_index.json")

    if not os.path.exists(index_path):
        return None

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Pequena normalização para consumo pela camada 0
        if not isinstance(data, dict):
            return None
        if "interactions" not in data or not isinstance(data["interactions"], list):
            data["interactions"] = []
        return data
    except Exception:
        return None


def load_for_session(base_dir: str) -> Optional[Dict[str, Any]]:
    """
    API simples chamada pela camada0_loader.camada0_boot.

    v0.1:
    - apenas lê o ledger index e devolve, se existir.
    - versões futuras podem filtrar por janela temporal, sessão, etc.
    """
    return read_ledger_index_data(base_dir)


def load_civilizational_snapshot(base_dir: str) -> Dict[str, Any]:
    """
    Stub v0.1 para integração com a Camada 0.

    Futuro (v0.2+):
    - varrer múltiplos ledgers,
    - agregar estatísticas globais,
    - calcular riscos civilizatórios.

    Hoje:
    - retorna snapshot mínimo dizendo que não há dados agregados.
    """
    return {
        "available": False,
        "meta": {
            "source": "ledger_ops.load_civilizational_snapshot",
            "note": "Snapshot civilizatório ainda não implementado (v0.1).",
            "base_dir": base_dir,
        },
        "stats": {},
    }
