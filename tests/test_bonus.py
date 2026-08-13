"""
Additional test cases (bonus).

Run: pytest tests/ -v
"""

import os
from src.knowledge_base import build_knowledge_base
from src.pipeline import ask_question, get_llm
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture(scope="module")
def vector_store():
    return build_knowledge_base(DATA_DIR)


@pytest.fixture(scope="module")
def llm():
    return get_llm()


class TestBonus:
    def test_returns_exactly_three_sources(self, vector_store, llm):
        result = ask_question(vector_store, llm, "What services do you offer?")
        assert len(result["sources"]) == 3, "should retrieve exactly k=3 chunks"

    def test_pricing_question_avoids_product_faq(self, vector_store, llm):
        """The data/ dir includes two off-topic files (an employee handbook and
        an AcmeCloud product FAQ) whose pricing language could compete with the
        agency docs. Retrieval should keep them out of agency pricing queries."""
        result = ask_question(vector_store, llm, "How much does the Growth package cost?")
        sources_text = " ".join(result["sources"]).lower()
        assert "acmecloud" not in sources_text, (
            "agency pricing questions should not retrieve AcmeCloud product docs"
        )

    def test_whitespace_question_returns_valid_structure(self, vector_store, llm):
        result = ask_question(vector_store, llm, "   ")
        assert isinstance(result, dict)
        assert "answer" in result and "sources" in result