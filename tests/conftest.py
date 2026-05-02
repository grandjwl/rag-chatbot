# llmServer/tests/conftest.py

import pytest

from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_embedding import FakeEmbedding
from tests.fakes.fake_reranker import FakeReranker

from tests.fakes.fake_vector_repository import FakeVectorRepository
from tests.fakes.fake_rdb_repository import FakeRDBRepository
from tests.fakes.fake_conversation_repository import FakeConversationRepository

from tests.fakes.fake_retrieval_engine import FakeRetrievalEngine
from tests.fakes.fake_metadata_bundle import build_fake_metadata

# -----------------------------
# Model Fakes
# -----------------------------

@pytest.fixture
def fake_llm():
    return FakeLLM()


@pytest.fixture
def fake_embedding():
    return FakeEmbedding()


@pytest.fixture
def fake_reranker():
    return FakeReranker()


# -----------------------------
# Repository Fakes
# -----------------------------

@pytest.fixture
def fake_vector_repo():
    return FakeVectorRepository()


@pytest.fixture
def fake_rdb_repo():
    return FakeRDBRepository()


@pytest.fixture
def fake_conversation_repo():
    return FakeConversationRepository(rows=[])


# -----------------------------
# Retrieval
# -----------------------------

@pytest.fixture
def fake_retrieval_engine():
    return FakeRetrievalEngine()


# -----------------------------
# Metadata
# -----------------------------

@pytest.fixture(scope="session")
def fake_metadata():
    return build_fake_metadata()