# engine/suavizador.py
"""
Suavizador v0.1 – Pilar 6 (ACI4A)

Funções:
- Ajusta tom emocional da resposta final.
- Evita intensificação de risco.
- Inclui acolhimento quando necessário.
- Evita paternalismo, mas mantém segurança.
- Usa MIE (intent_vector) + VSI (emotional fields).
"""

import re
from typing import Dict, Any, Optional


class Suavizador:
    """
    Módulo de Suavização Emocional (Pilar 6) — v0.1

    Entradas:
      - user_input: texto original do usuário
      - resposta: resposta já aprovada pela Salvaguarda
      - estados_axiomas: estados A1/A2/A3/A4
      - mie_intent: payload completo do MIE (inclui intent_vector)
      - vsi_result: resultado do VSI (inclui emotional_smoothing_field)

    Saída:
      - texto final suavizado
    """

    def modular(
        self,
        user_input: str,
        resposta: str,
        estados_axiomas: Dict[str, Any],
        mie_intent: Dict[str, Any],
        vsi_result: Any,
    ) -> str:
        """
        Pipeline principal do Suavizador:

        1) Lê sinais do MIE (intent_vector) e do VSI.
        2) Decide nível de suavização: leve, moderado, profundo ou crise.
        3) Se o usuário pediu "em N linhas", respeita rigorosamente o limite
           (exceto em contexto de crise/suicídio/violência, onde a segurança
           vem antes do formato).
        """

        # ------------------------------------------------------------------
        # Detecta pedido explícito de "em N linhas"
        # ------------------------------------------------------------------
        line_limit = self._detectar_limite_linhas(user_input)

        # ------------------------------------------------------------------
        # Coleta de sinais do MIE
        # ------------------------------------------------------------------
        iv = mie_intent.get("intent_vector", {}) or {}

        emotion_level = iv.get("emotion_level", "none")
        has_self_harm = iv.get("has_self_harm", False)
        has_violence = iv.get("has_violence", False)

        # ------------------------------------------------------------------
        # Coleta de sinais do VSI
        # ------------------------------------------------------------------
        vsi_smoothing = 0.0
        vsi_priority = "standard"
        vsi_threat = "low"

        if vsi_result:
            try:
                vsi_smoothing = float(getattr(vsi_result.emotional_smoothing_field, "score", 0.0))
            except Exception:
                vsi_smoothing = 0.0

            fused = getattr(vsi_result, "fused_final_vector", {}) or {}
            if isinstance(fused, dict):
                vsi_priority = fused.get("intervention_priority", "standard")
                vsi_threat = fused.get("threat_level", "low")

        # ==================================================================
        # 1) Neutralização de Crise (NÍVEL MÁXIMO)
        #    → aqui a segurança vem antes de qualquer formato
        # ==================================================================
        if has_self_harm or has_violence or vsi_threat in ("high", "critical"):
            return self._nivel_crise(resposta)

        # ==================================================================
        # 2) Se o usuário pediu "em N linhas", obedecer formato
        #    → sem preâmbulo extra, apenas tom neutro seguro
        # ==================================================================
        if line_limit is not None:
            resposta_neutra = self._nivel_leve(resposta)
            return self._aplicar_limite_linhas(resposta_neutra, line_limit)

        # ==================================================================
        # 3) Suavização normal (sem restrição de linhas)
        # ==================================================================
        # Suavização profunda
        if emotion_level == "high" or vsi_smoothing > 0.6 or vsi_priority == "emotional_support":
            return self._nivel_profundo(resposta)

        # Suavização moderada
        if emotion_level == "elevated" or vsi_smoothing > 0.3:
            return self._nivel_moderado(resposta)

        # Tom neutro seguro (default)
        return self._nivel_leve(resposta)

    # ======================================================================
    # DETECÇÃO DE "EM N LINHAS"
    # ======================================================================

    def _detectar_limite_linhas(self, user_input: str) -> Optional[int]:
        """
        Procura padrões como:
        - "em 3 linhas"
        - "em 5 linhas"
        - "em 2 linha"

        Retorna um inteiro entre 1 e 10, ou None se não houver pedido.
        """
        texto = user_input.lower()

        # Regex simples: número + "linha(s)"
        match = re.search(r"(\d+)\s+linha", texto)
        if not match:
            return None

        try:
            n = int(match.group(1))
        except ValueError:
            return None

        # Limites de sanidade
        if n < 1:
            n = 1
        if n > 10:
            n = 10

        return n

    def _aplicar_limite_linhas(self, resposta: str, n: int) -> str:
        """
        Garante que a resposta final tenha no máximo N linhas.

        Estratégia:
        1) Normaliza quebras de linha.
        2) Se já há linhas claras, usa as primeiras N.
        3) Caso contrário, quebra por sentenças básicas e monta até N linhas.
        """

        texto = resposta.strip().replace("\r\n", "\n").replace("\r", "\n")

        # 1) Se já há múltiplas linhas, aproveitamos
        linhas_brutas = [l.strip() for l in texto.split("\n") if l.strip()]
        if len(linhas_brutas) >= n:
            return "\n".join(linhas_brutas[:n])

        # 2) Se há poucas ou nenhuma linha, quebrar por sentenças
        #    (bem simples, não é NLP pesado)
        partes = re.split(r"(?<=[.!?])\s+", texto)
        partes = [p.strip() for p in partes if p.strip()]

        if not partes:
            return texto  # nada para fazer

        linhas: list[str] = []
        buffer = ""

        for sent in partes:
            if not buffer:
                buffer = sent
            else:
                # tenta juntar sentenças na mesma linha sem crescer demais
                candidato = buffer + " " + sent
                if len(candidato) <= 220:  # limiar arbitrário de conforto
                    buffer = candidato
                else:
                    linhas.append(buffer)
                    buffer = sent

            if len(linhas) >= n:
                break

        if buffer and len(linhas) < n:
            linhas.append(buffer)

        # Se ainda ficou menos que n linhas, tudo bem; não inventamos texto
        return "\n".join(linhas[:n])

    # ======================================================================
    # IMPLEMENTAÇÃO DOS NÍVEIS DE SUAVIZAÇÃO
    # ======================================================================

    def _nivel_leve(self, resposta: str) -> str:
        """
        Suavização mínima — ajuste leve de tom.
        Não adiciona preâmbulo, apenas limpa espaços.
        """
        return resposta.strip()

    def _nivel_moderado(self, resposta: str) -> str:
        """
        Suavização moderada — acrescenta acolhimento leve.
        """
        bloco = (
            "Entendi o que você trouxe. Vou te responder com calma e clareza.\n"
            "Se algo estiver te deixando confuso ou preocupado, estou aqui para ajudar.\n\n"
        )
        return bloco + resposta.strip()

    def _nivel_profundo(self, resposta: str) -> str:
        """
        Suavização profunda — tom acolhedor e estabilizador.
        """
        bloco = (
            "Percebo que isso pode estar trazendo uma carga emocional intensa.\n"
            "Vamos abordar isso de forma cuidadosa e segura, sem pressa.\n"
            "Respire um pouco, e vamos passo a passo.\n\n"
        )
        return bloco + resposta.strip()

    def _nivel_crise(self, resposta: str) -> str:
        """
        Neutralização de crise — máxima suavização, sem deixar o usuário sozinho,
        sem reforçar riscos, e sempre focando em suporte seguro.

        Aqui, propositalmente, NÃO obedecemos limite de linhas:
        segurança > formato.
        """
        bloco = (
            "Eu estou aqui com você, e percebo que o que você trouxe é realmente delicado.\n"
            "Você não está sozinho. Vamos focar em algo que te mantenha seguro agora.\n\n"
        )
        final = (
            "Se você estiver em risco imediato, por favor procure ajuda profissional "
            "ou um serviço de apoio emocional disponível na sua região.\n"
            "No Brasil, você pode ligar gratuitamente para o 188 (CVV) a qualquer momento.\n"
        )
        return bloco + final
