# engine/fsm_axiomas.py

from typing import Any, Dict, List, Optional


class FSMAxiomas:
    """
    FSM simbólica dos axiomas no contexto ACI4A.

    Responsabilidades:
    - Manter o estado atual de cada axioma (A1, A2, ...).
    - Processar eventos vindos do MIE + vetores semânticos de intenção.
    - Permitir reidratação a partir do ledger (memória de sessão).
    - Expor snapshot serializável para ser gravado no ledger.
    - Aplicar moduladores civilizatórios (Pilar 2: axiomas evolutivos).

    Conceitos principais:

    - self.estados:
        Mapa simples de estados atuais dos axiomas, ex:
        {"A1": "A1_SAFE_FLOW", "A2": "A2_BASELINE"}

    - self.moduladores:
        Parâmetros dinâmicos por axioma, ex:
        {
            "A1": {"rigidez": 1.0, "sensibilidade": 1.0},
            "A2": {"rigidez": 1.0, "sensibilidade": 1.0},
        }

        - rigidez: quão rápido o axioma sobe para RISK.
        - sensibilidade: quão fácil o axioma entra em estados de alerta/uncertainty.
    """

    def __init__(self, axiomas_dict: Optional[Dict[str, Any]] = None) -> None:
        self.axiomas: Dict[str, Any] = axiomas_dict or {}
        self.estados: Dict[str, str] = {}
        self.moduladores: Dict[str, Dict[str, float]] = {}

        # Inicializa a FSM com axiomas, se já foram passados
        if self.axiomas:
            self.load_axiomas(self.axiomas)
        else:
            # Defaults de segurança caso ainda não haja axiomas carregados
            self.estados.setdefault("A1", "A1_SAFE_FLOW")
            self.estados.setdefault("A2", "A2_BASELINE")

        # Inicializa moduladores padrão
        self._ensure_default_moduladores()

    # ------------------------------------------------------------------
    # 0.1 — Loader da FSM dos Axiomas
    # ------------------------------------------------------------------
    def load_axiomas(self, axiomas_dict: Dict[str, Any]) -> None:
        """
        Carrega/atualiza a definição dos axiomas e inicializa estados.
        """
        self.axiomas = axiomas_dict or {}
        self.estados = {}

        for ax_nome, ax_def in self.axiomas.items():
            # Pulamos chaves que não são definições de axioma (ex. "descricao")
            if not isinstance(ax_def, dict):
                continue

            fsm = ax_def.get("fsm", {})
            initial_state = fsm.get("initial_state")
            if initial_state:
                self.estados[ax_nome] = initial_state

        # Defaults de segurança caso algo não venha definido
        self.estados.setdefault("A1", "A1_SAFE_FLOW")
        self.estados.setdefault("A2", "A2_BASELINE")

        # Garantir moduladores padrão após recarregar axiomas
        self._ensure_default_moduladores()

    # ------------------------------------------------------------------
    # Moduladores evolutivos (Pilar 2)
    # ------------------------------------------------------------------
    def _ensure_default_moduladores(self) -> None:
        """
        Garante que existam moduladores padrão para os axiomas críticos (A1, A2).
        """
        self.moduladores.setdefault("A1", {"rigidez": 1.0, "sensibilidade": 1.0})
        self.moduladores.setdefault("A2", {"rigidez": 1.0, "sensibilidade": 1.0})

    def apply_civilizational_modulators(
        self,
        civilizational_stats: Dict[str, Any],
        session_memory: Dict[str, Any],
        prognostico_inicial: Dict[str, Any],
    ) -> None:
        """
        Ajusta parâmetros de rigidez/sensibilidade dos axiomas
        com base em sinais civilizatórios e prognóstico.

        Versão inicial (seed):
        - Exemplo de lógica:
            - Se o risco civilizatório de self-harm estiver alto,
              aumenta a rigidez de A1 (mais agressivo ao subir para RISK).
            - Se a pressão de desinformação estiver alta,
              aumenta a sensibilidade de A2 (fica mais alerta).

        Essa função pode evoluir com:
        - estatísticas reais do ledger civilizatório,
        - aprendizado de longo prazo,
        - curvas não-lineares, etc.
        """
        stats = civilizational_stats.get("stats", {}) or {}

        # Garante que os moduladores existam
        self._ensure_default_moduladores()

        # ------------------------------
        # Exemplo: ajustar A1 (preservação da vida)
        # ------------------------------
        a1_mod = self.moduladores.get("A1", {})
        rigidez_a1 = a1_mod.get("rigidez", 1.0)

        global_selfharm = stats.get("global_self_harm_risk", "low")
        predicted_selfharm = prognostico_inicial.get("predicted_self_harm_risk", "low")

        # Se o risco global ou previsto for elevado -> aumenta rigidez de A1
        if global_selfharm in ("medium", "high") or predicted_selfharm in ("medium", "high"):
            rigidez_a1 = max(rigidez_a1, 1.2)
        else:
            # fallback suave para o default
            rigidez_a1 = min(rigidez_a1, 1.0)

        a1_mod["rigidez"] = rigidez_a1
        self.moduladores["A1"] = a1_mod

        # ------------------------------
        # Exemplo: ajustar A2 (verdade / não-delírio)
        # ------------------------------
        a2_mod = self.moduladores.get("A2", {})
        sens_a2 = a2_mod.get("sensibilidade", 1.0)

        misinformation_pressure = stats.get("misinformation_pressure", "low")
        if misinformation_pressure in ("medium", "high"):
            sens_a2 = max(sens_a2, 1.2)
        else:
            sens_a2 = min(sens_a2, 1.0)

        a2_mod["sensibilidade"] = sens_a2
        self.moduladores["A2"] = a2_mod

        # No futuro, poderíamos imprimir logs detalhados aqui,
        # ou registrar esses ajustes no ledger.

    # ------------------------------------------------------------------
    # 0.4 — Validação Prévia
    # ------------------------------------------------------------------
    def validate(self) -> None:
        """
        Checa consistência básica dos axiomas carregados e dos moduladores.

        - Garante A1 e A2 com estados iniciais.
        - Garante moduladores para A1 e A2.
        - Futuro: valida coerência de transições declaradas em self.axiomas.
        """
        if "A1" not in self.estados:
            print("[FSM_AXIOMAS] AVISO: A1 sem estado inicial. Aplicando default A1_SAFE_FLOW.")
            self.estados["A1"] = "A1_SAFE_FLOW"

        if "A2" not in self.estados:
            print("[FSM_AXIOMAS] AVISO: A2 sem estado inicial. Aplicando default A2_BASELINE.")
            self.estados["A2"] = "A2_BASELINE"

        self._ensure_default_moduladores()

    # ------------------------------------------------------------------
    # Reidratação a partir do ledger (memória simbólica)
    # ------------------------------------------------------------------
    def init_from_memory(self, session_memory: Dict[str, Any]) -> None:
        """
        Reidrata a FSM a partir da memória de sessão vinda do ledger.

        Espera (se existir) algo como:
            session_memory["fsm_states"] = { "A1": "...", "A2": "...", ... }
            session_memory["fsm_modulators"] = {
                "A1": {"rigidez": ..., "sensibilidade": ...},
                "A2": {...}
            }

        Se não existir, não faz nada.
        """
        if not session_memory:
            return

        fsm_states = session_memory.get("fsm_states")
        if isinstance(fsm_states, dict):
            for ax_nome, state in fsm_states.items():
                self.estados[ax_nome] = state

        fsm_mods = session_memory.get("fsm_modulators")
        if isinstance(fsm_mods, dict):
            # Atualiza moduladores conhecidos, sem perder defaults
            for ax_nome, mods in fsm_mods.items():
                if not isinstance(mods, dict):
                    continue
                base = self.moduladores.get(ax_nome, {"rigidez": 1.0, "sensibilidade": 1.0})
                base.update(mods)
                self.moduladores[ax_nome] = base

        # Garante defaults mínimos
        self._ensure_default_moduladores()

    # ------------------------------------------------------------------
    # Snapshot para salvar no ledger
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """
        Devolve um dicionário com o estado atual dos axiomas e moduladores,
        pronto para ser gravado no ledger.

        Ex:
            {
                "fsm_states": { "A1": "A1_SAFE_FLOW", "A2": "A2_BASELINE", ... },
                "fsm_modulators": {
                    "A1": {"rigidez": 1.2, "sensibilidade": 1.0},
                    "A2": {"rigidez": 1.0, "sensibilidade": 1.2},
                }
            }
        """
        return {
            "fsm_states": dict(self.estados),
            "fsm_modulators": {
                ax: dict(mods) for ax, mods in self.moduladores.items()
            },
        }

    # ------------------------------------------------------------------
    # Núcleo: processamento de eventos
    # ------------------------------------------------------------------
    def process_events(self, eventos: Optional[List[str]], contexto: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Recebe lista de eventos do MIE + módulos de intenção vetorial
        e ajusta os estados dos axiomas.

        Eventos podem incluir:
        - self_harm_flag, chemistry_flag, violence_flag
        - ambiguity_high, no_risk
        - risk_manipulacao, risk_fracionado
        - meta_query_flag
        - intent_selfharm_latent, intent_chemistry_latent, intent_extreme_scenario

        Retorna um novo dicionário de estados.
        """

        if eventos is None:
            eventos = []

        # Normaliza para garantir que são strings
        eventos = [str(e) for e in eventos]

        new_states = dict(self.estados)

        # Lê moduladores atuais
        a1_mod = self.moduladores.get("A1", {"rigidez": 1.0, "sensibilidade": 1.0})
        a2_mod = self.moduladores.get("A2", {"rigidez": 1.0, "sensibilidade": 1.0})

        rigidez_a1 = a1_mod.get("rigidez", 1.0)
        sens_a2 = a2_mod.get("sensibilidade", 1.0)

        # ------------------------------------------------------
        # A1 - preservação da vida (explícita + vetorial)
        # ------------------------------------------------------
        eventos_risco_duro = [
            "self_harm_flag", "chemistry_flag", "violence_flag",
            "intent_selfharm_latent", "intent_chemistry_latent", "intent_extreme_scenario",
        ]

        eventos_risco_suave = [
            "risk_manipulacao", "risk_fracionado",
        ]

        if any(e in eventos for e in eventos_risco_duro):
            # rigidez alta → cai direto em RISK
            if rigidez_a1 >= 1.0:
                new_states["A1"] = "A1_RISK"
            else:
                # Em um cenário hipoteticamente mais brando,
                # poderíamos cair em QUERY, mas mantemos conservador.
                new_states["A1"] = "A1_QUERY"

        elif any(e in eventos for e in eventos_risco_suave) and new_states.get("A1") == "A1_SAFE_FLOW":
            new_states["A1"] = "A1_QUERY"

        elif "ambiguity_high" in eventos and new_states.get("A1") == "A1_SAFE_FLOW":
            new_states["A1"] = "A1_QUERY"

        elif "no_risk" in eventos and new_states.get("A1") in ["A1_QUERY", "A1_RISK"]:
            new_states["A1"] = "A1_SAFE_FLOW"

        # ------------------------------------------------------
        # A2 - verdade / não-delírio / meta-consciência
        # ------------------------------------------------------
        # Alta sensibilidade → mais propenso a cair em UNCERTAINTY
        if "meta_query_flag" in eventos or "ambiguity_high" in eventos:
            # Se sensibilidade for maior que 1, podemos no futuro
            # elevar para estados mais fortes (ex: DELIRIUM_RISK).
            new_states["A2"] = "A2_UNCERTAINTY"

        elif "no_risk" in eventos and new_states.get("A2") != "A2_BASELINE":
            new_states["A2"] = "A2_BASELINE"

        self.estados = new_states
        return new_states
