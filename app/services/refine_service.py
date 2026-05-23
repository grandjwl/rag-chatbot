# llmServer/app/services/refine_service.py

from rapidfuzz import process, fuzz

from app.services.rerank_service import RerankService
from app.infra.vector.vector_repository import VectorRepository


def _fuzzy_match(word: str, choices: list, threshold: int = 70) -> str:
    if not word or not choices:
        return None
    match = process.extractOne(word, choices, scorer=fuzz.ratio)
    if match and match[1] > threshold:
        return match[0]
    return None


def _match_score(word: str, target: str) -> float:
    if not word or not target:
        return 0.0
    match_count = sum(c in target for c in word)
    return match_count / max(len(word), len(target))


def _valid_part_number(word: str, target: str, threshold: float = 0.8) -> bool:
    if len(word) <= 5:
        return False
    return _match_score(word, target) > threshold


class RefineService:
    """
    ============================================================
    [Domain Role]
    질문 내 엔티티 정제 전용 서비스 (Pre-SQL 단계)
    - 제조사 / 판매사 fuzzy 보정
    - part_number 벡터 기반 오타 보정
    - 동의어 힌트 추출 (SQLGen prompt 강화용)

    이 서비스는 DB 접근 없음.
    순수 텍스트 정제 & 힌트 생성 전용.

    ============================================================
    [Graph Input State Fields]
    - question: str

    (향후 확장 가능)
    - structured_memory: Optional[dict]  # 현재는 사용 안함

    ============================================================
    [Graph Output State Fields]
    - refined_question: str
        → 오타 보정 + part_number 정제된 질문

    - synonym_hint: str
        → SQL 생성 프롬프트에 삽입할 동의어 매핑 정보
        예:
        "'매출액' → 'revenue' (metric), '판매량' → 'quantity' (metric)"

    ============================================================
    [Internal Processing Stages]

    1) _fuzzy_correct()
       - 제조사 / 판매사 문자열 유사도 기반 교정
       - RapidFuzz 기반
       - FUZZY_THRESHOLD 이상일 경우 치환

    2) _vector_correct_part_number()
       - 벡터 검색 (top_k=3)
       - distance < REFINE_DISTANCE_THRESHOLD
       - type == "part_number"
       - 문자열 2차 검증 후 치환

    3) _retrieve_synonyms()
       - 벡터 검색 (top_k=10)
       - reranker 재정렬
       - score > SYNONYM_RERANK_THRESHOLD
       - canonical 매핑 힌트 문자열 생성

    ============================================================
    [Failure Modes]

    - 벡터 검색 실패 → candidates empty → 그냥 통과
    - reranker 실패 시 예외 발생 가능 (상위에서 처리 필요)
    - synonym 없음 → 빈 문자열 반환

    이 서비스는 error_type을 설정하지 않음.
    실패 시에도 question 그대로 반환하는 "Soft-Fail" 설계.

    ============================================================
    [Graph 위치]

    refine 단계에서 실행됨.
    Router 이전에 실행.

    Graph Flow:
        question
            ↓
        memory
            ↓    
        refine
            ↓
        router
            ↓
        sql_gen
    ============================================================
    """

    REFINE_FETCH_TOP_K = 3
    REFINE_DISTANCE_THRESHOLD = 0.15
    FUZZY_THRESHOLD = 70

    def __init__(
        self,
        refine_cache: dict,
        vector_repository: VectorRepository,
        reranker: RerankService,
    ):
        self.refine_cache = refine_cache
        self.vector_repository = vector_repository
        self.reranker = reranker

    # =========================
    # 1. 제조사/판매사 fuzzy(문자열 유사도 비교) 보정
    # 제조사 / 판매사 데이터 받아와 유사도 검색 후 70 이상이면 이상한 이름 바꿔주기 - FUZZY_THRESHOLD
    # 1차: rapidfuzz 기반 오타 보정 (준협 주석)
    # =========================
    def _fuzzy_correct(self, question: str) -> str:
        refined = question
        names = self.refine_cache.get("manufacturers", []) + self.refine_cache.get(
            "vendors", []
        )
        # print("DEBUG names in fuzzy:", names)
        for word in question.split():
            if len(word) >= 2:
                # Utils를 사용하여 "어떻게" 하는지 감춤
                matched_name = _fuzzy_match(word, names, self.FUZZY_THRESHOLD)
                if matched_name:
                    refined = refined.replace(word, matched_name)
        return refined

    # =========================
    # 2. part_number 벡터 보정
    # 1 관문 : 벡터 디비에서 유사도 검색
    # 2 관문 : 1관문 통과되면 문자열 비교
    # 2차: refine_store 벡터 검색으로 part_number 오타 보정 (준협 주석)
    # =========================
    async def _vector_correct_part_number(self, question: str) -> str:
        refined = question

        # 파트넘버 벡터 유사도 비교 (top_k 설정 가능. default:3)
        candidates = await self.vector_repository.search_by_text(
            collection_name="refine_store",
            query_text=question,
            top_k=self.REFINE_FETCH_TOP_K,
        )
        # print("DEBUG candidates in part_num:", candidates)
        
        for doc, meta, dist in candidates:
            # 1관문: 벡터 거리 체크
            if (
                dist < self.REFINE_DISTANCE_THRESHOLD
                and meta.get("type") == "part_number"
            ):
                # 2관문: 벡터 공간에서 비교했다면 -> 문자열로 세부 비교 (Utils 호출)
                candidate_part = meta.get("original_id")
                for word in question.split():
                    if _valid_part_number(word, candidate_part, threshold=0.8):
                        if word.upper() != doc.upper():
                            refined = refined.replace(word, candidate_part)

        return refined

    # =========================
    # 외부 호출용 API
    # =========================
    async def resolve(self, question: str) -> dict:
        """
        ============================================================
        [Input]
        - question: str

        ============================================================
        [Output Dict Structure]
        {
            "refined_question": str,
            "synonym_hint": str
        }

        ============================================================
        [Graph Integration Notes]

        Graph Node에서 호출 시:

            updated_state = state.model_copy(update={
                "refined_question": result["refined_question"],
                "synonym_hint": result["synonym_hint"]
            })

        retry_count / error_history에는 영향 없음.
        ============================================================
        """
        refined = self._fuzzy_correct(question)
        refined = await self._vector_correct_part_number(refined)
        synonym_hint = ""
        return {
            "refined_question": refined,
            "synonym_hint": synonym_hint,
        }
