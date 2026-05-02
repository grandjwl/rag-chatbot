# ============================================================
# File
#   tests/unit/test_refine_service.py
#
# Run
#   PYTHONPATH=. pytest tests/unit/test_refine_service.py -v
#
# 목적
#   RefineService 로직 검증
# ============================================================

import pytest

from app.services.refine_service import RefineService


@pytest.mark.asyncio
async def test_refine_basic(fake_metadata):

    service = RefineService(metadata_bundle=fake_metadata)

    result = await service.resolve("매출 보여줘")

    assert "refined_question" in result
    assert "synonym_hint" in result


@pytest.mark.asyncio
async def test_refine_synonym(fake_metadata):

    service = RefineService(metadata_bundle=fake_metadata)

    result = await service.resolve("매출액 알려줘")

    refined = result["refined_question"]

    # synonym mapping 확인
    assert isinstance(refined, str)


@pytest.mark.asyncio
async def test_refine_empty_question(fake_metadata):

    service = RefineService(metadata_bundle=fake_metadata)

    result = await service.resolve("")

    assert result["refined_question"] == ""