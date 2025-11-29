# engine/salvaguarda.py

from typing import Dict, Any, Optional


class Salvaguarda:
    """
    Camada de Autonomia de Salvaguarda
    - Recebe estados dos axiomas (FSM)
    - Opcionalmente recebe sinais do MIE Guardião (intent_vector)
    - Decide se vai permitir, modificar, bloquear ou redirecionar a resposta

    Integração com pilares ACI4A:
    - Pilar 3 (Autonomia Negativa):
        • bloqueia/resstringe quando o usuário delega demais ou está em risco.
    - Pilar 6 (Suavização psicológica):
        • modula a resposta em casos de emoção elevada/alta.
    - Pilar 1 (Prognóstico, via Ledger):
        • as decisões aqui alimentam o ledger com o tipo de intervenção aplicada.
    """

    def __init__(self) -> None:
        # Thresholds simples para v0.2
        self.high_risk_severities = {"high", "critical"}
        self.medium_risk_severities = {"medium"}

    # ------------------------------------------------------------------
    # Classificação de risco a partir do intent_vector do MIE
    # ------------------------------------------------------------------
    def _classificar_risco_mie(self, mie_intent: Dict[str, Any]) -> str:
        """
        Recebe um intent_vector (parte do payload estruturado do MIE):

        mie_intent = {
            "has_self_harm": bool,
            "has_violence": bool,
            "has_chemistry": bool,
            "has_dependency": bool,
            "has_overtrust": bool,
            "has_meta_query": bool,
            "emotion_level": "none"|"elevated"|"high",
            "max_severity": "none"|"low"|"medium"|"high"|"critical",
            "categories": {...},
            "severities": {...}
        }

        Retorna: "none" | "low" | "medium" | "high" | "critical"
        """

        if not mie_intent:
            return "none"

        has_self_harm = mie_intent.get("has_self_harm", False)
        has_violence = mie_intent.get("has_violence", False)
        has_chemistry = mie_intent.get("has_chemistry", False)
        has_dependency = mie_intent.get("has_dependency", False)
        has_overtrust = mie_intent.get("has_overtrust", False)
        emotion_level = mie_intent.get("emotion_level", "none") or "none"
        max_severity = mie_intent.get("max_severity", "none") or "none"

        # 1) Risco crítico: self-harm ou violência com alta emoção/severidade
        if has_self_harm:
            if emotion_level == "high" or max_severity in self.high_risk_severities:
                return "critical"
            return "high"

        if has_violence and (emotion_level == "high" or max_severity in self.high_risk_severities):
            return "high"

        # 2) Risco químico + severidade alta
        if has_chemistry and max_severity in self.high_risk_severities:
            return "high"

        # 3) Dependência/overtrust + emoção elevada
        if (has_dependency or has_overtrust) and emotion_level in ("elevated", "high"):
            return "medium"

        # 4) Severidade média isolada
        if max_severity in self.medium_risk_severities:
            return "medium"

        # 5) Emoção elevada isolada
        if emotion_level == "elevated":
            return "low"

        return "none"

    # ------------------------------------------------------------------
    # Decisão principal
    # ------------------------------------------------------------------
    def decidir(
        self,
        estados_axiomas: Dict[str, str],
        draft: str,
        mie_intent: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        estados_axiomas: dict com algo como {"A1": "A1_SAFE_FLOW", "A2": "A2_BASELINE"}
        draft: resposta preliminar do modelo
        mie_intent: intent_vector ou payload estruturado do MIE (opcional)

        Retorna: 'allow' | 'modify' | 'block' | 'redirect'

        Compatível com versão anterior:
        - se mie_intent não for passado, a lógica se reduz ao comportamento antigo.
        """

        estado_a1 = estados_axiomas.get("A1", "")
        estado_a2 = estados_axiomas.get("A2", "")

        # Se vier payload completo, extraímos só o intent_vector
        if mie_intent and "intent_vector" in mie_intent:
            mie_intent = mie_intent.get("intent_vector") or mie_intent

        risk_mie = self._classificar_risco_mie(mie_intent or {})

        # ============================================================
        # 1) Regras duras de A1 (Prognóstico ético / risco imediato)
        # ============================================================
        # Se A1 está em risco ou override -> bloco total
        if estado_a1 in ["A1_RISK", "A1_OVERRIDE"]:
            return "block"

        # Risco crítico vindo do MIE também força bloqueio
        if risk_mie == "critical":
            return "block"

        # ============================================================
        # 2) Regras intermediárias de A1 (consulta / dúvida)
        # ============================================================
        # Se A1 está em QUERY -> resposta permitida mas com modulação
        if estado_a1 == "A1_QUERY":
            return "modify"

        # Risco alto do MIE sugere modificação cuidadosa
        if risk_mie == "high":
            return "modify"

        # ============================================================
        # 3) Coerência / estabilidade (A2)
        # ============================================================
        # Estados de incerteza, contradição ou delírio sugerem modulação
        if estado_a2 in ["A2_UNCERTAINTY", "A2_CONTRADICTION", "A2_DELIRIUM_RISK"]:
            return "modify"

        # Risco médio do MIE também indica modificação
        if risk_mie == "medium":
            return "modify"

        # ============================================================
        # 4) Casos de baixo risco / suavização leve
        # ============================================================
        # Risco baixo: podemos manter allow, mas o suavizador (Pilar 6)
        # pode ajustar o tom mais à frente. Aqui não mexemos no fluxo.
        # risk_mie == "low" cai no comportamento padrão.

        # Caso padrão
        return "allow"

    # ------------------------------------------------------------------
    # Aplicação da decisão ao draft
    # ------------------------------------------------------------------
    def aplicar(self, decision: str, draft: str) -> str:
        """
        Aplica a decisão à resposta draft.
        """

        if decision == "block":
            return (
                "Não posso responder isso de forma direta. "
                "Vamos focar em algo que te proteja ou te ajude a buscar suporte seguro."
            )

        if decision == "modify":
            return "Vou responder de forma cuidadosa e segura: " + (draft or "")

        if decision == "redirect":
            return "Prefiro redirecionar essa conversa para algo que não te exponha a risco."

        # allow
        return draft or ""
