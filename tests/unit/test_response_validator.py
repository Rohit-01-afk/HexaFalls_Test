"""
Unit tests for ResponseValidator, ValidationReason Enum, and ValidationResult model.
"""

from backend.services.response_validator import ResponseValidator, ValidationReason, ValidationResult


def test_response_validator_valid_answers() -> None:
    """Verify ResponseValidator passes valid technical answers."""
    res1 = ResponseValidator.validate_response("Turn off the main breaker switch before replacing the wiring harness.")
    assert res1.valid is True
    assert res1.reason == ValidationReason.VALID
    assert res1.response_length > 0

    res2 = ResponseValidator.validate_response("I could not find this information in the manual.")
    assert res2.valid is True
    assert res2.reason == ValidationReason.VALID


def test_response_validator_empty_and_none() -> None:
    """Verify ResponseValidator detects None and empty string responses."""
    res_none = ResponseValidator.validate_response(None)
    assert res_none.valid is False
    assert res_none.reason == ValidationReason.EMPTY
    assert res_none.response_length == 0

    res_empty = ResponseValidator.validate_response("")
    assert res_empty.valid is False
    assert res_empty.reason == ValidationReason.EMPTY
    assert res_empty.response_length == 0


def test_response_validator_whitespace_only() -> None:
    """Verify ResponseValidator detects whitespace-only strings."""
    res = ResponseValidator.validate_response("   \n\t  \n ")
    assert res.valid is False
    assert res.reason == ValidationReason.WHITESPACE_ONLY


def test_response_validator_punctuation_only() -> None:
    """Verify ResponseValidator detects punctuation-only strings."""
    res1 = ResponseValidator.validate_response("...")
    assert res1.valid is False
    assert res1.reason == ValidationReason.PUNCTUATION_ONLY

    res2 = ResponseValidator.validate_response(" ? - , . : ")
    assert res2.valid is False
    assert res2.reason == ValidationReason.PUNCTUATION_ONLY


def test_response_validator_malformed_output() -> None:
    """Verify ResponseValidator detects malformed or non-alphanumeric outputs."""
    res = ResponseValidator.validate_response("x")
    assert res.valid is False
    assert res.reason == ValidationReason.MALFORMED_OUTPUT
