import math

import pytest
import torch

from speecheval.verify import (
    acoustic_decision, ctc_score, sentence_units, substitute_candidate,
    _candidate_window, build_sentence_windows,
)


def test_ctc_score_sums_all_valid_paths_and_divides_by_frames() -> None:
    probabilities = torch.tensor([[0.4, 0.6], [0.7, 0.3]], dtype=torch.float64)
    score = ctc_score(probabilities.log(), [1], blank=0)
    expected = math.log(0.6 * 0.3 + 0.6 * 0.7 + 0.4 * 0.3) / 2
    assert score == pytest.approx(expected, abs=1e-12)
    assert ctc_score(probabilities.log(), [], blank=0) == pytest.approx(math.log(0.4 * 0.7) / 2)


def test_impossible_alignment_is_not_treated_as_evidence_to_delete_text() -> None:
    emission = torch.tensor([[0.4, 0.6]], dtype=torch.float64).log()
    assert ctc_score(emission, [1, 1]) is None
    assert acoustic_decision(None, -0.1, 0.05) == "UNSURE"


@pytest.mark.parametrize(("a", "b", "expected"), [
    (-0.5, -0.44, "APPLY_B"), (-0.44, -0.5, "KEEP_A"),
    (-0.5, -0.48, "UNSURE"), (-0.5, -0.5, "UNSURE"),
])
def test_acoustic_margin(a: float, b: float, expected: str) -> None:
    assert acoustic_decision(a, b, 0.05) == expected


def test_sentence_units_and_poem_lines_preserve_character_positions() -> None:
    text = "One sentence. Two; Three: Next."
    assert [s["text"] for s in sentence_units(text, False)] == ["One sentence.", "Two;", "Three:", "Next."]
    poem = "O Captain! my Captain!\n  Fallen cold and dead."
    units = sentence_units(poem, True)
    assert len(units) == 2
    for unit in units:
        assert poem[unit["char_start"]:unit["char_end"]] == unit["text"]


def test_substitution_is_local_including_insertions_and_deletions() -> None:
    assert substitute_candidate("that that nation", 5, 9, "this") == "that this nation"
    assert substitute_candidate("We choose", 0, 0, "Again") == "Again We choose"
    assert substitute_candidate("We choose today", 10, 15, "") == "We choose "


def test_missing_stanzas_use_all_affected_windows_instead_of_one_short_clip() -> None:
    text = "First line.\nSecond line.\nThird line."
    words = [{"word": word, "start": float(i), "end": i + .4}
             for i, word in enumerate(["First", "line", "Second", "line", "Third", "line"])]
    windows = build_sentence_windows(text, words, 0.0, 7.0, .3, True)
    item = {"transcript_start": text.index("Second"), "transcript_end": len(text) - 1, "asr": ""}
    selected = _candidate_window(text, item, windows)
    assert selected["candidate_a"] == "Second line.\nThird line."
    assert selected["sentence_indices"] == [1, 2]
    assert selected["end_s"] - selected["start_s"] > 3.0
