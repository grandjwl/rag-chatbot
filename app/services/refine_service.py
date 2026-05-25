# llmServer/app/services/refine_service.py

import difflib
from app.services.retrieval.engine import RetrievalEngine


def _valid_part_number(word: str, target: str, threshold: float = 0.8) -> bool:
    if len(word) <= 5:
        return False
    match_count = sum(c in target for c in word)
    score = match_count / max(len(word), len(target))
    return score > threshold


def _company_name_match(word: str, target: str, threshold: float = 0.75) -> bool:
    if not (word.isascii() and word.isalpha()):
        return False
    ratio = difflib.SequenceMatcher(None, word.lower(), target.lower()).ratio()
    return ratio >= threshold


class RefineService:

    def __init__(self, engine: RetrievalEngine):
        self.engine = engine

    def _apply_corrections(self, question: str, candidates: list) -> str:
        refined = question
        words = question.split()

        for doc, meta, score in candidates:
            entity_type = meta.get("type")
            original = meta.get("original_id") or doc

            if entity_type == "part_number":
                for word in words:
                    if _valid_part_number(word, original) and word.upper() != doc.upper():
                        refined = refined.replace(word, original)

            elif entity_type in ("manufacturer", "vendor"):
                for word in words:
                    if _company_name_match(word, original) and word.lower() != original.lower():
                        refined = refined.replace(word, original)

        return refined

    async def resolve(self, question: str) -> dict:
        candidates = await self.engine.retrieve_entities(question, top_k=5)
        refined = self._apply_corrections(question, candidates)
        return {"refined_question": refined}
