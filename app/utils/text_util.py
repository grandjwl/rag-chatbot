# app/utils/text_util.py

from rapidfuzz import process, fuzz

# ================== 1번 노드 refine_service==================

# 1차 필터 수식 --> fuzz, ratio 관련해서 알아봐라!!!!!!
# 유사도 (threshold) 값보다 유사하면 해당 제조사 / 벤더사 이름 반환.
def get_fuzzy_match(word: str, choices: list, threshold: int = 70) -> str:
    """
    단어와 리스트(제조사/벤더)를 비교해 임계값 이상의 최적 매칭 결과를 반환합니다.
    """
    if not word or not choices:
        return None
        
    match = process.extractOne(word, choices, scorer=fuzz.ratio)
    if match and match[1] > threshold:
        return match[0]
    return None

# 2차 필터 수식
def calculate_match_score(word: str, target: str) -> float:
    """
    단어와 대상 문자열 간의 문자 포함 비율을 계산합니다.
    """
    if not word or not target:
        return 0.0
    
    match_count = sum(c in target for c in word)
    return match_count / max(len(word), len(target))

def is_valid_part_number_match(word: str, target: str, threshold: float = 0.8) -> bool:
    """
    파트넘버로서의 유효성과 유사도 임계값을 체크합니다.
    """
    if len(word) <= 5:
        return False
    
    # 대소문자 구분 없이 비교하되, 이미 동일한 경우는 제외하기 위해 Service에서 체크하도록 함
    score = calculate_match_score(word, target)
    return score > threshold

