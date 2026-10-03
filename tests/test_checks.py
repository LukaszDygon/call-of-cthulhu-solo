"""The checker accepts a clean adventure and catches each kind of mistake we have actually made."""

import copy
from pathlib import Path

import pytest

from gamebook import adventure as A
from gamebook.checks import check, errors

TINY = Path(__file__).parent / "fixtures" / "tiny.yaml"


@pytest.fixture
def tiny():
    return A.load(TINY)


def messages(adv, level=None):
    return [f"{f.where}: {f.message}" for f in check(adv) if level in (None, f.level)]


def test_clean_adventure_has_no_findings(tiny):
    assert messages(tiny) == []


def test_duplicate_keys_are_refused():
    text = TINY.read_text(encoding="utf-8").replace("  9:\n    title: Mad", "  8:\n    title: Mad")
    with pytest.raises(A.DuplicateKeyError):
        A.loads(text)


def test_missing_link(tiny):
    tiny["sections"][3]["choices"][0]["to"] = 99
    assert any("missing section 99" in m for m in messages(tiny, "error"))


def test_unreachable_section(tiny):
    tiny["sections"][10] = {"title": "Orphan", "text": "Nobody comes here.", "ending": "lost"}
    assert any(m.startswith("section 10: cannot be reached") for m in messages(tiny, "error"))


def test_dead_end_section(tiny):
    del tiny["sections"][5]["choices"]
    assert any("dead end" in m for m in messages(tiny, "error"))


def test_hook_without_payoff_is_a_warning(tiny):
    tiny["journal"]["CLOSE"] = "Mae sits close beside you."
    tiny["sections"][3].setdefault("effects", []).append({"note": "CLOSE"})
    assert "journal: CLOSE is noted but nothing ever checks it: a hook without a payoff" in messages(
        tiny, "warning"
    )


def test_required_state_must_be_obtainable(tiny):
    tiny["sections"][2]["effects"] = [e for e in tiny["sections"][2]["effects"] if e.get("gain") != "key"]
    assert any("requires item 'key', which nobody can ever get" in m for m in messages(tiny, "error"))


def test_condition_set_by_the_same_section_is_flagged(tiny):
    # The section-83 bug: an extra gated on a note that the section's own effects set is always shown.
    tiny["sections"][2]["extra"] = [{"requires": {"note": "SEEN"}, "text": "You knew all along."}]
    assert any("always true" in m for m in messages(tiny, "warning"))


def test_roll_only_one_investigator_can_make_is_an_error(tiny):
    tiny["sections"][3]["choices"].append(
        {"text": "Sneak.", "roll": {"skill": "Stealth", "success": 4, "failure": 4}}
    )
    assert any("trained by only ['b']" in m for m in messages(tiny, "error"))


def test_gated_roll_is_allowed(tiny):
    tiny["sections"][3]["choices"].append(
        {
            "text": "Sneak.",
            "requires": {"skill": "Stealth", "min": 50},
            "roll": {"skill": "Stealth", "success": 4, "failure": 4},
        }
    )
    assert errors(tiny) == []


def test_investigator_needs_three_tested_skills(tiny):
    for sec in tiny["sections"].values():
        for choice in sec.get("choices") or []:
            if choice.get("roll", {}).get("skill") == "Climb":
                choice["roll"]["skill"] = "STR"
    assert any("investigator a: only gets to roll" in m for m in messages(tiny, "error"))


def test_hit_points_follow_the_rules(tiny):
    broken = copy.deepcopy(tiny)
    broken["investigators"][0]["hp"] = 14
    assert any("hp 14 should be" in m for m in messages(broken, "warning"))
