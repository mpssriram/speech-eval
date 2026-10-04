import pytest

from speecheval.transcripts import normalize_tokens


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Four score", ["four", "score"]),
        ("1962", ["one", "thousand", "nine", "hundred", "and", "sixty", "two"]),
        ("don't", ["dont"]),
        ("well-being", ["wellbeing"]),
        ("&", ["and"]),
    ],
)
def test_normalize_tokens(text: str, expected: list[str]) -> None:
    """Changing the transcript token contract must break this test."""
    assert normalize_tokens(text) == expected

