from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class MetadataBundle:
    """
    앱 시작 시 1회 로딩되는 시스템 메타 스냅샷
    """

    refine_cache: Dict[str, List[str]]
    column_map: Dict[str, List[str]]
    data_stats: Dict[str, str]
    schema_context: str
    valid_joins: Dict[str, List[str]] = None
