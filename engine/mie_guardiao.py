# engine/mie_guardiao.py

import re
import json
import glob
from typing import List, Dict, Any, Callable, Optional


# ================================================================
# Helpers básicos
# ================================================================
def _normalize(text: str) -> str:
    """
    Normalização simples:
    - lower
    - strip
    - colapsa espaços
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _contains_any(text: str, patterns: List[str]) -> bool:
    """Verifica se algum padrão da lista aparece no texto (substring)."""
    return any(p in text for p in patterns)


# ================================================================
# Loader de flags dinâmicas (JSON)
# ================================================================
class FlagLoader:
    """
    Carrega flags definidas em arquivos JSON no formato:

    {
      "version": "aci4a_flags_v0.1",
      "range": [1, 100],
      "flags": [
        {
          "id": "SS_001_SELF_HARM_EXPL",
          "code": 1,
          "category": "saude_mental",
          "severity": "high",
          "axioms": ["A1", "A2"],
          "intent_type": "emotional",
          "event_tags": ["self_harm", "risk"],
          "patterns_any": [...],
          "regex_any": [...],
          "notes": "..."
        }
      ]
    }

    Este loader pré-normaliza padrões e compila regexes para performance.
    """

    def __init__(self) -> None:
        # Lista de flags completas (dicts)
        self.flags: List[Dict[str, Any]] = []
        # Opcional: índices por categoria/severity/intent_type
        self.by_category: Dict[str, List[Dict[str, Any]]] = {}
        self.by_severity: Dict[str, List[Dict[str, Any]]] = {}
        self.by_intent_type: Dict[str, List[Dict[str, Any]]] = {}

    # ------------------------------
    # Carregamento
    # ------------------------------
    def load_files(self, paths: List[str]) -> None:
        """
        Carrega múltiplos arquivos JSON de flags.
        paths: lista de caminhos absolutos ou relativos.
        """
        for path in paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            flags = data.get("flags", [])
            for flag in flags:
                self._prepare_flag(flag)
                self.flags.append(flag)

        self._rebuild_indexes()

    def load_from_glob(self, pattern: str = "flags_*.json") -> None:
        """
        Carrega todos os arquivos que batem com o padrão glob.
        Ex.: "flags_*.json", "data/flags_*.json"
        """
        paths = glob.glob(pattern)
        self.load_files(paths)

    # ------------------------------
    # Preparação de cada flag
    # ------------------------------
    def _prepare_flag(self, flag: Dict[str, Any]) -> None:
        """
        Normaliza campos e compila regexes.
        """
        # Normalizar patterns_any
        patterns = flag.get("patterns_any") or []
        flag["_patterns_any_norm"] = [_normalize(p) for p in patterns]

        # Compilar regex_any, se houver
        compiled_regexes = []
        for pattern in flag.get("regex_any") or []:
            try:
                compiled_regexes.append(re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE))
            except re.error:
                continue
        flag["_regex_compiled"] = compiled_regexes

        # Normalizar metadados principais
        flag["id"] = str(flag.get("id", "")).strip()
        flag["category"] = str(flag.get("category", "")).strip()
        flag["severity"] = str(flag.get("severity", "")).strip()
        flag["intent_type"] = str(flag.get("intent_type", "")).strip()
        flag["event_tags"] = flag.get("event_tags") or []

    def _rebuild_indexes(self) -> None:
        self.by_category.clear()
        self.by_severity.clear()
        self.by_intent_type.clear()

        for f in self.flags:
            cat = f.get("category") or "unknown"
            sev = f.get("severity") or "unknown"
            itype = f.get("intent_type") or "unknown"

            self.by_category.setdefault(cat, []).append(f)
            self.by_severity.setdefault(sev, []).append(f)
            self.by_intent_type.setdefault(itype, []).append(f)

    # ------------------------------
    # Matching
    # ------------------------------
    def match_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Retorna lista de flags que casam com o texto dado.
        - patterns_any: substring (normalizado)
        - regex_any: regex compilado
        """
        if not text:
            return []

        norm = _normalize(text)
        matched: List[Dict[str, Any]] = []

        for flag in self.flags:
            # patterns_any (string match)
            patterns = flag.get("_patterns_any_norm") or []
            if patterns and any(p in norm for p in patterns):
                matched.append(flag)
                continue

            # regex_any (regex)
            regexes = flag.get("_regex_compiled") or []
            if regexes and any(r.search(text) for r in regexes):
                matched.append(flag)
                continue

        return matched


# ================================================================
# MIE Guardião — CAMADA 2
# ================================================================
class MIEGuardiao:
    """
    MIE (Meta-Inteligência Estável) — CAMADA 2

    Papel na ACI4A:
    - Camada celular de percepção de intenção.
    - Trabalha com SEMÂNTICA em vários níveis:
        • lexical (palavras/expressões),
        • frasal (padrões de construção),
        • discursivo local (user + draft),
      e prepara terreno para:
        • vetores de intenção (Pilar 4),
        • suavização psicológica (Pilar 6),
        • autonomia negativa (Pilar 3),
        • prognóstico (Pilar 1, via ledger).

    Não responde, não julga, não “resolve” ética.
    Só observa e produz EVENTOS simbólicos.
    """

    def __init__(
        self,
        flags_loader: Optional[FlagLoader] = None,
        ledger_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        """
        :param flags_loader:
            Instância de FlagLoader já carregada (flags_*.json).
            Se None, o MIE pode ser usado só com léxico interno.
        :param ledger_callback:
            Função opcional chamada com o resultado estruturado da análise,
            para registrar no Ledger Civilizatório (Pilar 1 + 5).
            Exemplo de assinatura:
                def ledger_callback(payload: Dict[str, Any]) -> None:
                    ...
        """
        self.flags_loader = flags_loader or FlagLoader()
        self.ledger_callback = ledger_callback

        # ============================================================
        # 1. Léxico de risco – camada lexical / denotativa
        # ============================================================

        # SELF-HARM explícito (intenção direta)
        self.selfharm_exp: List[str] = [
            "me matar",
            "quero morrer",
            "quero me matar",
            "me suicidar",
            "cometer suicídio",
            "cometer suicidio",
            "tirar minha vida",
            "acabar com a minha vida",
            "acabar com tudo",
            "não vale mais a pena viver",
            "nao vale mais a pena viver",
            "não quero mais viver",
            "nao quero mais viver",
        ]

        # SELF-HARM implícito / desespero profundo
        self.selfharm_impl: List[str] = [
            "não aguento mais",
            "nao aguento mais",
            "tô no limite",
            "to no limite",
            "cansado de tudo",
            "cansei de tudo",
            "sumir pra sempre",
            "sumir de vez",
            "desaparecer um pouco",
            "queria desaparecer",
            "queria sumir",
            "melhor se eu não existisse",
            "melhor se eu nao existisse",
        ]

        # Expressões típicas FIGURATIVAS de self-harm
        # (não devem ser tratadas como risco máximo, mas como sinal emocional)
        self.selfharm_figurativo: List[str] = [
            "vou me matar de trabalhar",
            "vou me matar de estudar",
            "vou me matar de tanto rir",
            "vou morrer de rir",
            "to me matando de estudar",
            "tô me matando de estudar",
        ]

        # EMOÇÃO FRACA / MÉDIA (Pilar 6 — suavização)
        self.emocao_leve: List[str] = [
            "tô cansado",
            "to cansado",
            "tô exausto",
            "to exausto",
            "tô irritado",
            "to irritado",
            "tá difícil",
            "ta dificil",
            "tá complicado",
            "ta complicado",
            "tô saturado",
            "to saturado",
            "não tô bem",
            "nao to bem",
        ]

        # EMOÇÃO MAIS FORTE / ESCALADA
        self.emocao_forte: List[str] = [
            "tô destruído",
            "to destruido",
            "tô quebrado por dentro",
            "to quebrado por dentro",
            "quebrado por dentro",
            "não vejo saída",
            "nao vejo saida",
            "sem saída",
            "sem saida",
            "desesperado",
            "desespero total",
        ]

        # VIOLÊNCIA explícita contra terceiros (denotativo)
        self.violencia_literal: List[str] = [
            "matar alguém",
            "matar alguem",
            "explodir um prédio",
            "explodir um predio",
            "fazer uma bomba",
            "fazer bomba",
            "bomba caseira",
            "envenenar alguém",
            "envenenar alguem",
            "atentado",
            "machucar alguém",
            "machucar alguem",
            "ferir alguém",
            "ferir alguem",
        ]

        # Palavras de violência que podem ser literais OU figurativas
        self.violencia_ambigua: List[str] = [
            "matar",
            "explodir",
            "bombar",
            "atacar",
            "dar um tiro",
            "tiro",
        ]

        # Expressões FIGURATIVAS de violência (conotativo, idiomático)
        self.violencia_figurativa: List[str] = [
            "explodir de rir",
            "morro de rir",
            "matar a saudade",
            "matar o tempo",
            "dar um tiro no escuro",
            "bombar no instagram",
            "bombar no tiktok",
        ]

        # Verbos de manipulação (química / física)
        self.verbo_manip: List[str] = [
            "misturar",
            "juntar",
            "combinar",
            "ativar",
            "estabilizar",
            "dissolver",
            "derreter",
            "aplicar junto",
            "fundir",
            "somar com",
            "completar com",
            "esquentar",
            "aumentar a temperatura",
            "aquecer",
            "abrir com força",
            "forçar abertura",
            "testar com",
            "colocar isso com aquilo",
            "misturar isso com",
            "se eu colocar",
        ]

        # Objetos/itens perigosos genéricos
        self.objetos_risco: List[str] = [
            "produto forte",
            "produto muito forte",
            "produto químico forte",
            "produto quimico forte",
            "líquido forte",
            "liquido forte",
            "coisa forte",
            "coisa pesada",
            "coisa abrasiva",
            "solvente",
            "solvente industrial",
            "reagente",
            "substância",
            "substancia",
            "material pesado",
            "coisa inflamável",
            "coisa inflamavel",
            "desentupidor",
            "limpa metal",
            "limpeza industrial",
        ]

        # Padrões de fracionamento / tentativa incremental
        self.fracionamento: List[str] = [
            "serve pra",
            "isso serve para",
            "isso serve pra",
            "funciona com",
            "e se eu colocar",
            "e se misturar",
            "isso reage",
            "isso piora",
            "isso ativa",
            "isso esquenta",
            "isso explode",
            "se eu misturar",
            "como faço pra dissolver",
            "posso adicionar",
            "posso usar junto",
            "se juntar isso",
        ]

        # Química explícita — nomes diretos
        self.quimica_hard: List[str] = [
            "amônia",
            "amonia",
            "nh3",
            "água sanitária",
            "agua sanitaria",
            "cloro",
            "hipoclorito",
            "peróxido",
            "peroxido",
            "h2o2",
            "ácido",
            "acido",
            "ácido muriático",
            "acido muriatico",
            "soda cáustica",
            "soda caustica",
            "naoh",
            "ácido sulfúrico",
            "acido sulfurico",
            "ácido nítrico",
            "acido nitrico",
            "acetona forte",
            "solvente de piscina",
        ]

        # Meta-intenção / meta-query (testar limites, sistema)
        self.meta_query: List[str] = [
            "teste salvaguarda",
            "teste salvagurda",
            "teste axioma",
            "testar seus limites",
            "se eu quiser testar seus limites",
            "até onde você consegue ir",
            "ate onde voce consegue ir",
            "o que você faria",
            "o que voce faria",
            "até onde você pode ir",
            "ate onde voce pode ir",
        ]

        # Dependência / delegação total (Pilar 3 — autonomia negativa)
        self.dependencia: List[str] = [
            "decide por mim",
            "decida por mim",
            "escolhe por mim",
            "escolha por mim",
            "me diz o que fazer",
            "me diga o que fazer",
            "faça por mim",
            "faça isso por mim",
            "toma a decisão por mim",
            "tome a decisão por mim",
            "não consigo decidir nada",
            "nao consigo decidir nada",
            "assume o controle",
            "assuma o controle",
        ]

        # Confiança cega / overtrust
        self.overtrust: List[str] = [
            "vou fazer tudo que você disser",
            "vou fazer tudo que voce disser",
            "só confio em você",
            "so confio em voce",
            "confio cegamente em você",
            "confio cegamente em voce",
            "você sabe mais do que qualquer um",
            "voce sabe mais do que qualquer um",
        ]

    # ================================================================
    # Núcleo de análise (versão estruturada)
    # ================================================================
    def analisar_estruturado(self, user_msg: str, draft: str = "") -> Dict[str, Any]:
        """
        Analisa user_msg + draft e produz um payload estruturado.

        Saída:

        {
          "user_text": str,
          "draft_text": str,
          "full_text": str,
          "lexical_events": [...],
          "dynamic_flags": [
             {
               "id": ...,
               "code": ...,
               "category": ...,
               "severity": ...,
               "intent_type": ...,
               "event_tags": [...],
             }, ...
          ],
          "intent_vector": {
             "has_self_harm": bool,
             "has_violence": bool,
             "has_chemistry": bool,
             "has_dependency": bool,
             "has_overtrust": bool,
             "has_meta_query": bool,
             "emotion_level": "none"|"elevated"|"high",
             "max_severity": "none"|"low"|"medium"|"high"|"critical",
             "categories": { "categoria": count, ... },
             "severities": { "low": n, "medium": n, ... }
          }
        }

        Este payload é adequado para:
        - Prognóstico (Pilar 1 — via Ledger)
        - Autonomia negativa (Pilar 3)
        - Vetores simbólicos de intenção (pré-VSI, Pilar 4)
        - Suavização psicológica (Pilar 6)
        """
        user_text = _normalize(user_msg or "")
        draft_text = _normalize(draft or "")
        full_text = f"{user_text} {draft_text}".strip()

        # 1) Análise léxica (herdada da versão anterior)
        lexical_events = self._analisar_lexico(full_text, user_text)

        # 2) Matching das flags dinâmicas (JSON)
        dynamic_flags_full = self.flags_loader.match_text(full_text) if self.flags_loader else []
        dynamic_flags = [
            {
                "id": f.get("id"),
                "code": f.get("code"),
                "category": f.get("category"),
                "severity": f.get("severity"),
                "intent_type": f.get("intent_type"),
                "event_tags": f.get("event_tags") or [],
            }
            for f in dynamic_flags_full
        ]

        # 3) Vetor simbólico de intenção (pré-VSI / Pilar 4)
        intent_vector = self._build_intent_vector(lexical_events, dynamic_flags)

        result: Dict[str, Any] = {
            "user_text": user_text,
            "draft_text": draft_text,
            "full_text": full_text,
            "lexical_events": lexical_events,
            "dynamic_flags": dynamic_flags,
            "intent_vector": intent_vector,
        }

        # 4) Integração com Ledger Civilizatório (Pilar 1)
        if self.ledger_callback is not None:
            try:
                self.ledger_callback(result)
            except Exception:
                # Não deixamos o MIE quebrar caso o ledger falhe.
                pass

        return result

    # ================================================================
    # Núcleo de análise (versão compatível — retorna List[str])
    # ================================================================
    def analisar(self, user_msg: str, draft: str) -> List[str]:
        """
        Versão compatível com a API antiga.

        Continua retornando apenas uma lista de eventos simbólicos
        (lexicais), para não quebrar código legado.

        Para usar toda a potência (flags JSON + vetor de intenção),
        prefira chamar `analisar_estruturado`.
        """
        res = self.analisar_estruturado(user_msg, draft)
        return res.get("lexical_events", []) or []

    # ================================================================
    # Implementação da análise léxica (herdada + ligeiramente refatorada)
    # ================================================================
    def _analisar_lexico(self, full_text: str, user_text: str) -> List[str]:
        eventos: List[str] = []

        # ------------------------------------------------------------
        # 1) SELF-HARM literal / implícito / figurativo
        # ------------------------------------------------------------

        # FIGURATIVO primeiro: não queremos promover falso positivo hard.
        if _contains_any(full_text, self.selfharm_figurativo):
            eventos.append("self_harm_figurative")

        # LITERAL > implícito
        if _contains_any(full_text, self.selfharm_exp):
            eventos.append("self_harm_flag")
        elif _contains_any(full_text, self.selfharm_impl):
            eventos.append("self_harm_flag")

        # ------------------------------------------------------------
        # 2) EMOÇÃO — gradiente para suavização (Pilar 6)
        # ------------------------------------------------------------
        if _contains_any(full_text, self.emocao_leve):
            eventos.append("emotion_elevated")

        if _contains_any(full_text, self.emocao_forte):
            eventos.append("emotion_high")

        # ------------------------------------------------------------
        # 3) QUÍMICA — explícita / implícita
        # ------------------------------------------------------------
        # 3.1 Explícita (nomes diretos)
        if _contains_any(full_text, self.quimica_hard):
            eventos.append("chemistry_flag")

        # 3.2 Implícita forte: verbo de manipulação + objeto perigoso
        if _contains_any(full_text, self.verbo_manip) and _contains_any(full_text, self.objetos_risco):
            if "chemistry_flag" not in eventos:
                eventos.append("chemistry_flag")

        # 3.3 Implícita leve: verbo de manipulação isolado
        if _contains_any(full_text, self.verbo_manip):
            eventos.append("risk_manipulacao")

        # 3.4 Fracionamento — pedir em partes (lab caseiro)
        if _contains_any(full_text, self.fracionamento):
            eventos.append("risk_fracionado")

        # ------------------------------------------------------------
        # 4) VIOLÊNCIA — literal / ambígua / figurativa
        # ------------------------------------------------------------
        # FIGURATIVA — conotativa / idiomática
        if _contains_any(full_text, self.violencia_figurativa):
            eventos.append("violence_figurative")

        # LITERAL forte
        if _contains_any(full_text, self.violencia_literal):
            eventos.append("violence_flag")
        else:
            # Ambígua: palavra sozinha, checamos se NÃO está em contexto idiomático.
            if _contains_any(full_text, self.violencia_ambigua):
                # Se já foi marcada como figurativa, não promovemos a literal.
                if "violence_figurative" not in eventos:
                    eventos.append("violence_flag")

        # ------------------------------------------------------------
        # 5) DEPENDÊNCIA / AUTONOMIA NEGATIVA (Pilar 3)
        # ------------------------------------------------------------
        if _contains_any(full_text, self.dependencia):
            eventos.append("dependency_flag")

        if _contains_any(full_text, self.overtrust):
            eventos.append("overtrust_flag")

        # ------------------------------------------------------------
        # 6) META-QUERY / TESTE DE SISTEMA
        # ------------------------------------------------------------
        if _contains_any(full_text, self.meta_query):
            eventos.append("meta_query_flag")

        # ------------------------------------------------------------
        # 7) AMBIGUIDADE bruta (mensagem muito curta)
        # ------------------------------------------------------------
        if len(user_text.strip()) <= 2:
            eventos.append("ambiguity_high")

        # ------------------------------------------------------------
        # 8) Fallback – nenhum risco identificado
        # ------------------------------------------------------------
        if not eventos:
            eventos.append("no_risk")

        # Remove duplicatas mantendo ordem
        final_eventos: List[str] = []
        seen = set()
        for ev in eventos:
            if ev not in seen:
                seen.add(ev)
                final_eventos.append(ev)

        return final_eventos

    # ================================================================
    # Vetor simbólico de intenção (pré-VSI — Pilar 4)
    # ================================================================
    def _build_intent_vector(
        self,
        lexical_events: List[str],
        dynamic_flags: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Vetor simbólico de intenção, não numérico, mas estruturado.
        Serve como pré-camada para o módulo VSI (Vetores Semânticos
        de Intenção).
        """

        # Booleans de alto nível (Pilares 3, 4, 6)
        has_self_harm = "self_harm_flag" in lexical_events
        has_violence = "violence_flag" in lexical_events
        has_chemistry = "chemistry_flag" in lexical_events
        has_dependency = "dependency_flag" in lexical_events
        has_overtrust = "overtrust_flag" in lexical_events
        has_meta_query = "meta_query_flag" in lexical_events

        # Emoção
        if "emotion_high" in lexical_events:
            emotion_level = "high"
        elif "emotion_elevated" in lexical_events:
            emotion_level = "elevated"
        else:
            emotion_level = "none"

        # Severidade agregada das flags dinâmicas
        severity_order = ["none", "low", "medium", "high", "critical"]
        severity_rank = {s: i for i, s in enumerate(severity_order)}
        max_severity = "none"

        categories_count: Dict[str, int] = {}
        severities_count: Dict[str, int] = {}

        for f in dynamic_flags:
            cat = f.get("category") or "unknown"
            sev = f.get("severity") or "unknown"

            categories_count[cat] = categories_count.get(cat, 0) + 1
            severities_count[sev] = severities_count.get(sev, 0) + 1

            if sev in severity_rank and severity_rank[sev] > severity_rank[max_severity]:
                max_severity = sev

        return {
            "has_self_harm": has_self_harm,
            "has_violence": has_violence,
            "has_chemistry": has_chemistry,
            "has_dependency": has_dependency,
            "has_overtrust": has_overtrust,
            "has_meta_query": has_meta_query,
            "emotion_level": emotion_level,
            "max_severity": max_severity,
            "categories": categories_count,
            "severities": severities_count,
        }
