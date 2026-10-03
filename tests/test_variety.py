"""The choices report tells decisions that change something from the ones that don't."""

from pathlib import Path

from gamebook import adventure as A
from gamebook.simulate import target_failures
from gamebook.variety import analyse

TINY = Path(__file__).parent / "fixtures" / "tiny.yaml"


def kinds(adv):
    return {d.section: d.kind for d in analyse(adv).decisions}


def test_options_that_rejoin_with_the_same_state_are_cosmetic():
    # Section 1: "Look around" and "Listen" both lead to 2 or 3, and on to the door at 4.
    assert kinds(A.load(TINY))["1"] == "cosmetic"


def test_options_that_can_end_differently_are_a_fork():
    door = next(d for d in analyse(A.load(TINY)).decisions if d.section == "4")
    assert door.kind == "fork"
    # The key and the remembered sight both open the door: twins inside a fork.
    assert any({p.a, p.b} == {"Unlock it.", "Remember what you saw."} for p in door.twins)


def test_different_lasting_state_is_flavour():
    adv = A.load(TINY)
    adv["sections"][1]["choices"][1]["effects"] = [{"gain": "key"}]
    assert kinds(adv)["1"] == "flavour"


def test_a_route_of_its_own_is_a_detour():
    adv = A.load(TINY)
    secs = adv["sections"]
    secs[10] = {"title": "A", "text": "a", "choices": [{"text": "On.", "to": 11}]}
    secs[11] = {"title": "B", "text": "b", "choices": [{"text": "On.", "to": 12}]}
    secs[12] = {"title": "C", "text": "c", "choices": [{"text": "Back.", "to": 4}]}
    secs[3]["choices"].append({"text": "Take the long way round.", "to": 10})
    assert kinds(adv)["3"] == "detour"


def test_choices_that_are_never_open_together_are_not_a_decision():
    adv = A.load(TINY)
    adv["sections"][3]["choices"] = [
        {"text": "With the key.", "requires": {"item": "key"}, "to": 6},
        {"text": "Without it.", "requires": {"no_item": "key"}, "to": 7},
    ]
    assert "3" not in kinds(adv)


def test_bottlenecks_are_the_sections_every_playthrough_passes():
    assert analyse(A.load(TINY)).bottlenecks == ["1", "4"]


def test_cosmetic_choices_target():
    adv = A.load(TINY)  # two decisions, one of them cosmetic
    adv["targets"] = {"cosmetic_choices": 0.25}
    assert any("decisions are cosmetic" in line for line in target_failures(adv, None))
    adv["targets"] = {"cosmetic_choices": 0.5}
    assert target_failures(adv, None) == []
