# engine/vsi.py

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class VectorScore:
    """
    Representa uma dimensão vetorial interpretável.

    score:    valor normalizado em [-1.0, 1.0]
    confidence: confiança heurística da leitura [0.0, 1.0]
    components: subcomponentes que contribuíram para o score
    interpretation: leitura textual humana da dimensão
    """
    score: float
    confidence: float
    components: Dict[str, float]
    interpretation: str


@dataclass
class VSIResult:
    """
    Resultado completo do VSI v0.1.

    intent_vector:
        Vetor numérico compacto com as dimensões principais (12 eixos).
    semantic_intent_field:
        Map com VectorScore detalhando cada dimensão semântico-intencional.
    axiomatic_coherence_field:
        Vetores relacionados à A2 (coerência/realidade) e afins.
    prognostic_ethical_field:
        Vetores de risco/prognóstico ético (Pilar 1 + 4).
    emotional_smoothing_field:
        Vetor específico para uso na suavização (Pilar 6).
    fused_final_vector:
        Agregados globais: classificação, risco, recomendações, etc.
    """
    intent_vector: Dict[str, float]
    semantic_intent_field: Dict[str, VectorScore]
    axiomatic_coherence_field: Dict[str, VectorScore]
    prognostic_ethical_field: Dict[str, VectorScore]
    emotional_smoothing_field: VectorScore
    fused_final_vector: Dict[str, Any]


class VSIEngine:
    """
    VSI v0.1 – Vetores Semânticos de Intenção (Pilar 4 – ACI4A)

    Função:
      - Recebe o payload estruturado do MIEGuardiao (mie_guardiao.py)
      - Converte sinais simbólicos em um vetor numérico de intenção
      - Gera campos interpretáveis para:
          • Axiomas (A1, A2, A3, A4)
          • Salvaguarda
          • Suavizador
          • Ledger / Prognóstico

    Uso típico:

        mie_res = mie.analisar_estruturado(user_msg, draft)
        vsi = VSIEngine()
        vsi_res = vsi.from_mie_payload(mie_res)

    v0.1 é heurístico e simples de propósito. Versões futuras podem:
      - incorporar histórico (diachronic),
      - pesos aprendidos,
      - leitura mais fina de coerência.
    """

    def __init__(self) -> None:
        # Ordem de severidade usada para converter max_severity em escala numérica.
        self._severity_order = ["none", "low", "medium", "high", "critical"]
        self._severity_map = {
            "none": 0.0,
            "low": 0.25,
            "medium": 0.5,
            "high": 0.75,
            "critical": 1.0,
        }

        # Mapeamento emocional simples
        self._emotion_map = {
            "none": 0.0,
            "elevated": 0.6,
            "high": 1.0,
        }

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------
    def from_mie_payload(self, mie_payload: Dict[str, Any]) -> VSIResult:
        """
        Constrói o VSIResult a partir do payload do MIEGuardiao.

        Espera algo como:

        mie_payload = {
          "user_text": str,
          "draft_text": str,
          "full_text": str,
          "lexical_events": [...],
          "dynamic_flags": [...],
          "intent_vector": {
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
        }
        """

        intent = mie_payload.get("intent_vector", {}) or {}
        lexical_events = mie_payload.get("lexical_events", []) or []
        full_text = mie_payload.get("full_text", "") or ""

        # 1) Construir dimensões semânticas principais (12 eixos)
        semantic_intent_field = self._build_semantic_field(intent, lexical_events, full_text)

        # 2) Campo de coerência axiomática (v0.1 – simples, focado em A2)
        axiomatic_coherence_field = self._build_axiomatic_field(semantic_intent_field)

        # 3) Campo de prognóstico ético / risco
        prognostic_ethical_field = self._build_prognostic_field(semantic_intent_field, intent)

        # 4) Campo de suavização emocional (Pilar 6)
        emotional_smoothing_field = self._build_emotional_smoothing(semantic_intent_field)

        # 5) Vetor numérico compacto (intent_vector final)
        intent_vector = self._build_numeric_vector(semantic_intent_field)

        # 6) Vetor final fusionado / classificação global
        fused_final_vector = self._build_fused(intent_vector, semantic_intent_field, prognostic_ethical_field)

        return VSIResult(
            intent_vector=intent_vector,
            semantic_intent_field=semantic_intent_field,
            axiomatic_coherence_field=axiomatic_coherence_field,
            prognostic_ethical_field=prognostic_ethical_field,
            emotional_smoothing_field=emotional_smoothing_field,
            fused_final_vector=fused_final_vector,
        )

    # ------------------------------------------------------------------
    # 1) Campo semântico-intencional (12 dimensões)
    # ------------------------------------------------------------------
    def _build_semantic_field(
        self,
        intent: Dict[str, Any],
        lexical_events: Any,
        full_text: str,
    ) -> Dict[str, VectorScore]:
        has_self_harm = bool(intent.get("has_self_harm", False))
        has_violence = bool(intent.get("has_violence", False))
        has_chemistry = bool(intent.get("has_chemistry", False))
        has_dependency = bool(intent.get("has_dependency", False))
        has_overtrust = bool(intent.get("has_overtrust", False))
        has_meta_query = bool(intent.get("has_meta_query", False))

        emotion_level = intent.get("emotion_level", "none") or "none"
        max_severity = intent.get("max_severity", "none") or "none"

        # Helper para converter severidade
        sev_val = self._severity_map.get(max_severity, 0.0)
        emo_val = self._emotion_map.get(emotion_level, 0.0)

        # 1. Agency – complementar à dependência / overtrust, com leve boost em meta_query
        dep_raw = 1.0 if (has_dependency or has_overtrust) else 0.0
        agency_score = max(-1.0, min(1.0, 0.3 + (0.3 if has_meta_query else 0.0) - 0.6 * dep_raw))
        agency = VectorScore(
            score=agency_score,
            confidence=0.7,
            components={
                "dependency_penalty": -0.6 * dep_raw,
                "meta_query_boost": 0.3 if has_meta_query else 0.0,
                "base": 0.3,
            },
            interpretation=(
                "Alta agência / impulso de ação."
                if agency_score > 0.5 else
                "Agência moderada."
                if agency_score > 0.0 else
                "Baixa agência, possível passividade ou delegação excessiva."
            ),
        )

        # 2. Dependency – derivado dos sinais de dependência + overtrust
        dep_score = 1.0 if (has_dependency or has_overtrust) else 0.0
        dep_score = max(-1.0, min(1.0, dep_score))
        dependency = VectorScore(
            score=dep_score,
            confidence=0.8 if (has_dependency or has_overtrust) else 0.4,
            components={
                "has_dependency": 1.0 if has_dependency else 0.0,
                "has_overtrust": 1.0 if has_overtrust else 0.0,
            },
            interpretation=(
                "Dependência forte do sistema / delegação de decisão."
                if dep_score > 0.7 else
                "Alguma tendência a delegar ao sistema."
                if dep_score > 0.0 else
                "Autonomia preservada, sem delegação crítica explícita."
            ),
        )

        # 3. Instrumentality – uso do sistema para fins concretos
        # v0.1: heurística simples – se não há dependência extrema, assume instrumentalidade moderada.
        instr_base = 0.6 if not has_dependency else 0.3
        instrumentality = VectorScore(
            score=instr_base,
            confidence=0.5,
            components={
                "inverse_dependency": 1.0 - dep_score,
            },
            interpretation=(
                "Alto uso instrumental do sistema para objetivos claros."
                if instr_base > 0.5 else
                "Uso mais exploratório ou assistido do sistema."
            ),
        )

        # 4. Risk Drive – aproximação de risco (self-harm, violência, química)
        risk_signals = sum([
            1.0 if has_self_harm else 0.0,
            1.0 if has_violence else 0.0,
            1.0 if has_chemistry else 0.0,
        ])
        risk_score = min(1.0, 0.4 * risk_signals + 0.4 * sev_val)
        risk_drive = VectorScore(
            score=risk_score,
            confidence=0.8 if risk_signals > 0 else 0.4,
            components={
                "self_harm": 1.0 if has_self_harm else 0.0,
                "violence": 1.0 if has_violence else 0.0,
                "chemistry": 1.0 if has_chemistry else 0.0,
                "severity": sev_val,
            },
            interpretation=(
                "Direção de risco elevada."
                if risk_score > 0.6 else
                "Alguns sinais de risco presentes."
                if risk_score > 0.2 else
                "Sem direção de risco relevante detectada."
            ),
        )

        # 5. Emotional Load – intensidade emocional
        emo_score = emo_val
        emotional_load = VectorScore(
            score=emo_score,
            confidence=0.9,
            components={
                "emotion_level": emo_val,
            },
            interpretation=(
                "Emoção intensa / estado emocional alto."
                if emo_score > 0.7 else
                "Emoção moderada / alguma carga emocional."
                if emo_score > 0.2 else
                "Baixa carga emocional aparente."
            ),
        )

        # 6. Emotional Direction – v0.1: neutro, pois não temos polaridade textual ainda
        emo_dir_score = 0.0
        emotional_direction = VectorScore(
            score=emo_dir_score,
            confidence=0.3,
            components={},
            interpretation="Direção emocional (positiva/negativa) não avaliada em v0.1.",
        )

        # 7. Ambiguity – usa evento de ambiguidade alta + tamanho da mensagem
        text_len = len(full_text.split())
        has_ambiguity_event = "ambiguity_high" in lexical_events
        amb_base = 0.7 if has_ambiguity_event else 0.0
        if text_len <= 3:
            amb_base = max(amb_base, 0.6)

        ambiguity = VectorScore(
            score=amb_base,
            confidence=0.7 if has_ambiguity_event else 0.5,
            components={
                "short_text": 1.0 if text_len <= 3 else 0.0,
                "ambiguity_event": 1.0 if has_ambiguity_event else 0.0,
            },
            interpretation=(
                "Alta ambiguidade / pouca informação explícita."
                if amb_base > 0.6 else
                "Ambiguidade moderada ou pontual."
                if amb_base > 0.0 else
                "Baixa ambiguidade aparente."
            ),
        )

        # 8. Self-Harm Latent – aqui usamos diretamente has_self_harm
        sh_score = 0.9 if has_self_harm else 0.0
        selfharm_latent = VectorScore(
            score=sh_score,
            confidence=0.95 if has_self_harm else 0.3,
            components={
                "self_harm_flag": 1.0 if has_self_harm else 0.0,
            },
            interpretation=(
                "Sinais fortes de auto-risco / autoagressão."
                if sh_score > 0.8 else
                "Sem sinais explícitos de auto-risco."
            ),
        )

        # 9. Violence Latent – idem para violência
        vio_score = 0.8 if has_violence else 0.0
        violence_latent = VectorScore(
            score=vio_score,
            confidence=0.9 if has_violence else 0.3,
            components={
                "violence_flag": 1.0 if has_violence else 0.0,
            },
            interpretation=(
                "Sinais fortes de intenção violenta."
                if vio_score > 0.7 else
                "Sem sinais claros de violência literal."
            ),
        )

        # 10. Coherence – v0.1: assume coerência razoável se não há ambiguidade alta
        coh_score = 0.8 if amb_base < 0.3 else 0.5
        coherence = VectorScore(
            score=coh_score,
            confidence=0.6,
            components={
                "inverse_ambiguity": 1.0 - amb_base,
            },
            interpretation=(
                "Coerência discursiva boa."
                if coh_score > 0.7 else
                "Coerência moderada, com possíveis lacunas."
            ),
        )

        # 11. Future Orientation – v0.1 neutro (sem análise frasal ainda)
        future_orientation = VectorScore(
            score=0.0,
            confidence=0.2,
            components={},
            interpretation="Orientação temporal (futuro) não avaliada em v0.1.",
        )

        # 12. Manipulation Attempts – v0.1 neutro
        manipulation_attempts = VectorScore(
            score=0.0,
            confidence=0.2,
            components={},
            interpretation="Tentativas de manipulação discursiva não avaliadas em v0.1.",
        )

        return {
            "agency": agency,
            "dependency": dependency,
            "instrumentality": instrumentality,
            "risk_drive": risk_drive,
            "emotional_load": emotional_load,
            "emotional_direction": emotional_direction,
            "ambiguity": ambiguity,
            "self_harm_latent": selfharm_latent,
            "violence_latent": violence_latent,
            "coherence": coherence,
            "future_orientation": future_orientation,
            "manipulation_attempts": manipulation_attempts,
        }

    # ------------------------------------------------------------------
    # 2) Campo axiomático (A2 focado, v0.1)
    # ------------------------------------------------------------------
    def _build_axiomatic_field(self, semantic_field: Dict[str, VectorScore]) -> Dict[str, VectorScore]:
        """
        v0.1: apenas A2 (validação de realidade/coerência) derivado da coerência.
        Em versões futuras, podemos incluir A1, A3, A4 com vetores próprios.
        """
        coherence = semantic_field["coherence"].score
        ambiguity = semantic_field["ambiguity"].score

        base = max(-1.0, min(1.0, coherence - 0.3 * ambiguity))

        a2 = VectorScore(
            score=base,
            confidence=0.7,
            components={
                "coherence": coherence,
                "ambiguity_penalty": -0.3 * ambiguity,
            },
            interpretation=(
                "Alta aderência à realidade e coerência narrativa."
                if base > 0.6 else
                "Coerência razoável, com alguma incerteza."
                if base > 0.2 else
                "Possível fragilidade na coerência / interpretação da realidade."
            ),
        )

        return {
            "A2_reality_validation": a2,
        }

    # ------------------------------------------------------------------
    # 3) Campo de prognóstico ético
    # ------------------------------------------------------------------
    def _build_prognostic_field(
        self,
        semantic_field: Dict[str, VectorScore],
        intent: Dict[str, Any],
    ) -> Dict[str, VectorScore]:
        sev_val = self._severity_map.get(intent.get("max_severity", "none") or "none", 0.0)

        # Ethical prognosis – combina risco + coerência
        risk = semantic_field["risk_drive"].score
        coherence = semantic_field["coherence"].score

        # Score simples: risco baixo + coerência alta -> bom prognóstico
        ethical_score = max(-1.0, min(1.0, coherence - risk - 0.2 * sev_val))

        ethical_prognosis = VectorScore(
            score=ethical_score,
            confidence=0.7,
            components={
                "coherence": coherence,
                "risk_drive": -risk,
                "severity_penalty": -0.2 * sev_val,
            },
            interpretation=(
                "Prognóstico ético positivo / estável."
                if ethical_score > 0.4 else
                "Prognóstico ético moderado, requer atenção."
                if ethical_score > 0.0 else
                "Prognóstico ético delicado, monitoramento recomendado."
            ),
        )

        # Truth coherence – próxima de A2, mas focada em verdade/consistência
        a2 = self._build_axiomatic_field(semantic_field)["A2_reality_validation"]
        truth_score = max(-1.0, min(1.0, 0.7 * a2.score + 0.3 * coherence))

        truth = VectorScore(
            score=truth_score,
            confidence=0.8,
            components={
                "a2": a2.score,
                "coherence": coherence,
            },
            interpretation=(
                "Alta coerência com a realidade e consistência narrativa."
                if truth_score > 0.6 else
                "Coerência aceitável, com margem de incerteza."
                if truth_score > 0.2 else
                "Risco de distorção, confusão ou interpretações frágeis."
            ),
        )

        # Negative autonomy – combina dependency + overtrust implícitos
        dep = semantic_field["dependency"].score
        manip = semantic_field["manipulation_attempts"].score

        auto_score = max(-1.0, min(1.0, -(0.7 * dep + 0.3 * manip)))
        negative_autonomy = VectorScore(
            score=auto_score,
            confidence=0.7,
            components={
                "dependency": -0.7 * dep,
                "manipulation": -0.3 * manip,
            },
            interpretation=(
                "Autonomia preservada / boa integridade decisória."
                if auto_score > 0.4 else
                "Autonomia razoável, com leves riscos de influência."
                if auto_score > 0.0 else
                "Risco de comprometimento de autonomia / delegação excessiva."
            ),
        )

        return {
            "ethical_prognosis_index": ethical_prognosis,
            "truth_coherence_indicators": truth,
            "negative_autonomy_detectors": negative_autonomy,
        }

    # ------------------------------------------------------------------
    # 4) Campo de suavização emocional (Pilar 6)
    # ------------------------------------------------------------------
    def _build_emotional_smoothing(self, semantic_field: Dict[str, VectorScore]) -> VectorScore:
        emo = abs(semantic_field["emotional_load"].score)
        coherence = semantic_field["coherence"].score

        # Suavização maior quando:
        # - volatilidade emocional é alta (emo alto)
        # - coerência é baixa (precisa de cuidado)
        # Aqui o score representa "quanto suavizar"
        smoothing_score = max(0.0, min(1.0, 0.6 * emo + 0.4 * (1.0 - coherence)))

        return VectorScore(
            score=smoothing_score,
            confidence=0.8,
            components={
                "emotional_volatility": emo,
                "inverse_coherence": 1.0 - coherence,
            },
            interpretation=(
                "Necessidade alta de suavização emocional na resposta."
                if smoothing_score > 0.6 else
                "Necessidade moderada de suavização."
                if smoothing_score > 0.3 else
                "Pouca necessidade adicional de suavização."
            ),
        )

    # ------------------------------------------------------------------
    # 5) Vetor numérico compacto
    # ------------------------------------------------------------------
    def _build_numeric_vector(self, semantic_field: Dict[str, VectorScore]) -> Dict[str, float]:
        """
        Extrai apenas os scores numéricos das 12 dimensões principais.
        """
        return {
            name: vs.score
            for name, vs in semantic_field.items()
        }

    # ------------------------------------------------------------------
    # 6) Vetor final fusionado / classificação global
    # ------------------------------------------------------------------
    def _build_fused(
        self,
        intent_vector: Dict[str, float],
        semantic_field: Dict[str, VectorScore],
        prognostic_field: Dict[str, VectorScore],
    ) -> Dict[str, Any]:
        # Scores auxiliares
        risk = semantic_field["risk_drive"].score
        self_harm = semantic_field["self_harm_latent"].score
        violence = semantic_field["violence_latent"].score
        dep = semantic_field["dependency"].score
        agency = semantic_field["agency"].score
        ethical = prognostic_field["ethical_prognosis_index"].score

        # Risco global (bem simples v0.1)
        global_risk = max(self_harm, violence, risk)

        # Autonomia global
        autonomy_index = max(-1.0, min(1.0, agency - dep))

        # Classificação principal
        if self_harm >= 0.8:
            classification = "High Self-Risk"
        elif violence >= 0.7:
            classification = "Violence Risk"
        elif ethical > 0.4 and autonomy_index > 0.3:
            classification = "Ethical Autonomous Agent"
        elif dep > 0.7:
            classification = "High Dependency / Overtrust"
        else:
            classification = "Neutral / Standard Intent"

        # Nível de ameaça
        if global_risk >= 0.8:
            threat_level = "critical"
        elif global_risk >= 0.5:
            threat_level = "high"
        elif global_risk >= 0.2:
            threat_level = "moderate"
        else:
            threat_level = "low"

        # Prioridade de intervenção (texto alto nível)
        if threat_level in ("critical", "high"):
            intervention_priority = "protective"
        elif dep > 0.7:
            intervention_priority = "autonomy_support"
        elif semantic_field["emotional_load"].score > 0.6:
            intervention_priority = "emotional_support"
        else:
            intervention_priority = "standard"

        # Recomendações simples
        recommendations = []
        if self_harm >= 0.8:
            recommendations.append("Ativar protocolos de proteção e suporte imediato.")
        if violence >= 0.7:
            recommendations.append("Evitar qualquer instrução que amplifique dano a terceiros.")
        if dep > 0.7:
            recommendations.append("Reforçar autonomia, evitar decidir pelo usuário.")
        if semantic_field["emotional_load"].score > 0.6:
            recommendations.append("Responder com tom acolhedor e cuidadoso.")
        if not recommendations:
            recommendations.append("Fluxo padrão com monitoramento simbólico.")

        return {
            "global_risk_score": global_risk,
            "autonomy_index": autonomy_index,
            "ethical_prognosis_score": ethical,
            "threat_level": threat_level,
            "primary_intent_classification": classification,
            "intervention_priority": intervention_priority,
            "recommended_approach": recommendations,
        }
