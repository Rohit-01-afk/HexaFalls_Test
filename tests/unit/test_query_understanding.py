"""
Unit test suite for QueryUnderstandingService intent classification, confidence calculation, and fallback behavior.
"""

import pytest
from backend.schemas.query_intent import QueryIntent, QueryIntentType
from backend.services.query_understanding_service import QueryUnderstandingService


def test_analyze_query_definition():
    """Test definition question triggers."""
    q1 = QueryUnderstandingService.analyze_query("What is a hydraulic accumulator?")
    assert q1.intent == QueryIntentType.DEFINITION
    assert q1.confidence >= 0.85
    assert "what is" in q1.matched_keywords
    assert q1.normalized_query == "what is a hydraulic accumulator"
    assert "definition" in q1.reason

    q2 = QueryUnderstandingService.analyze_query("Define heat exchanger concept")
    assert q2.intent == QueryIntentType.DEFINITION
    assert q2.confidence >= 0.70
    assert "define" in q2.matched_keywords


def test_analyze_query_procedure():
    """Test procedure question triggers."""
    q1 = QueryUnderstandingService.analyze_query("How do I replace the cooling fan assembly?")
    assert q1.intent == QueryIntentType.PROCEDURE
    assert q1.confidence >= 0.85
    assert "how do i" in q1.matched_keywords
    assert "replace" in q1.matched_keywords

    q2 = QueryUnderstandingService.analyze_query("Steps to configure network settings")
    assert q2.intent == QueryIntentType.PROCEDURE
    assert q2.confidence >= 0.85
    assert "steps to" in q2.matched_keywords
    assert "configure" in q2.matched_keywords


def test_analyze_query_safety():
    """Test safety question triggers."""
    q1 = QueryUnderstandingService.analyze_query("Warning about high voltage hazards!")
    assert q1.intent == QueryIntentType.SAFETY
    assert q1.confidence >= 0.70
    assert "warning" in q1.matched_keywords
    assert "hazard" in q1.matched_keywords

    q2 = QueryUnderstandingService.analyze_query("What safety precautions are required?")
    assert q2.intent == QueryIntentType.SAFETY
    assert q2.confidence >= 0.85
    assert "safety precautions" in q2.matched_keywords


def test_analyze_query_comparison():
    """Test comparison question triggers."""
    q1 = QueryUnderstandingService.analyze_query("Difference between Mode A and Mode B")
    assert q1.intent == QueryIntentType.COMPARISON
    assert q1.confidence >= 0.85
    assert "difference between" in q1.matched_keywords

    q2 = QueryUnderstandingService.analyze_query("Compare hydraulic versus electric motor")
    assert q2.intent == QueryIntentType.COMPARISON
    assert q2.confidence >= 0.70
    assert "compare" in q2.matched_keywords or "versus" in q2.matched_keywords


def test_analyze_query_diagram():
    """Test diagram question triggers."""
    q1 = QueryUnderstandingService.analyze_query("Show Figure 5 circuit diagram")
    assert q1.intent == QueryIntentType.DIAGRAM
    assert q1.confidence >= 0.85
    assert "show figure" in q1.matched_keywords or "circuit diagram" in q1.matched_keywords

    q2 = QueryUnderstandingService.analyze_query("Flowchart of operation and schematic")
    assert q2.intent == QueryIntentType.DIAGRAM
    assert q2.confidence >= 0.70
    assert "flowchart" in q2.matched_keywords or "schematic" in q2.matched_keywords


def test_analyze_query_troubleshooting():
    """Test troubleshooting question triggers."""
    q1 = QueryUnderstandingService.analyze_query("How to fix error code E-04?")
    assert q1.intent == QueryIntentType.TROUBLESHOOTING
    assert q1.confidence >= 0.85
    assert "how to fix" in q1.matched_keywords or "error code" in q1.matched_keywords

    q2 = QueryUnderstandingService.analyze_query("Issue with pressure relief valve failure")
    assert q2.intent == QueryIntentType.TROUBLESHOOTING
    assert q2.confidence >= 0.70
    assert "issue" in q2.matched_keywords or "failure" in q2.matched_keywords


def test_analyze_query_general_fallback():
    """Test fallback to general intent when no triggers match."""
    q = QueryUnderstandingService.analyze_query("Hydraulic pressure setting 250 bar")
    assert q.intent == QueryIntentType.GENERAL
    assert q.confidence == 0.0
    assert q.matched_keywords == []
    assert "fell back to general category" in q.reason


def test_analyze_query_edge_cases():
    """Test edge cases such as empty string, whitespace, punctuation, and uppercase."""
    # 1. Empty string
    q_empty = QueryUnderstandingService.analyze_query("")
    assert q_empty.intent == QueryIntentType.GENERAL
    assert q_empty.confidence == 0.0
    assert q_empty.matched_keywords == []
    assert q_empty.normalized_query == ""

    # 2. Whitespace string
    q_space = QueryUnderstandingService.analyze_query("   \t \n ")
    assert q_space.intent == QueryIntentType.GENERAL
    assert q_space.confidence == 0.0

    # 3. Uppercase and punctuation
    q_upper = QueryUnderstandingService.analyze_query("HOW DO I INSTALL THE BRACKET???")
    assert q_upper.intent == QueryIntentType.PROCEDURE
    assert q_upper.confidence >= 0.85
    assert q_upper.normalized_query == "how do i install the bracket"
    assert "how do i" in q_upper.matched_keywords
    assert "install" in q_upper.matched_keywords
