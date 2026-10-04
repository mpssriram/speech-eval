import pytest

from speecheval.transcripts import (
    canonical_excerpt,
    compare_transcript,
    normalize_tokens,
    _escape_table,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Four score", ["four", "score"]),
        ("1962", ["one", "thousand", "nine", "hundred", "and", "sixty", "two"]),
        ("don't", ["dont"]),
        ("well-being", ["wellbeing"]),
        ("&", ["and"]),
        ("10,000", ["ten", "thousand"]),
        ("48-story", ["forty", "eight", "story"]),
        ("C-1", ["c", "one"]),
    ],
)
def test_normalize_tokens(text: str, expected: list[str]) -> None:
    """Changing the transcript token contract must break this test."""
    assert normalize_tokens(text) == expected


def test_compare_transcript_reports_relative_asr_time() -> None:
    words = [
        {"word": "We", "start": 10.2, "end": 10.4},
        {"word": "choose", "start": 10.5, "end": 10.8},
        {"word": "now", "start": 10.9, "end": 11.1},
    ]

    differences = compare_transcript("We choose today", words, cut_start_s=10.0)

    assert differences == [
        {
            "kind": "replace",
            "transcript": "today",
            "asr": "now",
            "start_s": 0.9,
        }
    ]


def test_canonical_excerpt_uses_only_matched_cut_span() -> None:
    canonical = "Before this. We choose to go. After that."
    words = [
        {"word": "Before", "start": 1.0, "end": 1.2},
        {"word": "this", "start": 1.3, "end": 1.5},
        {"word": "We", "start": 5.0, "end": 5.2},
        {"word": "choose", "start": 5.3, "end": 5.5},
        {"word": "to", "start": 5.6, "end": 5.7},
        {"word": "go", "start": 5.8, "end": 6.0},
        {"word": "After", "start": 9.0, "end": 9.2},
        {"word": "that", "start": 9.3, "end": 9.5},
    ]

    assert canonical_excerpt(canonical, words, 4.5, 6.5) == "We choose to go."


def test_multiline_poem_edits_stay_in_one_markdown_row() -> None:
    assert _escape_table("heart!\nhear the bells; |") == "heart! hear the bells; \\|"
