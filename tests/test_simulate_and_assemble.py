"""Simulation finds dead ends; assembly numbers named drafts and rewrites every link."""

from pathlib import Path

import pytest

from gamebook import adventure as A
from gamebook.assemble import AssembleError, assemble
from gamebook.simulate import simulate, target_failures

TINY = Path(__file__).parent / "fixtures" / "tiny.yaml"


def test_tiny_plays_to_an_ending_every_time():
    stats = simulate(A.load(TINY), runs_per_investigator=200)
    assert not stats.dead_ends
    assert set(stats.endings) <= {"Through", "Round About", "Dead", "Mad"}
    assert 4 <= stats.path_mean <= 6


def test_simulation_reports_a_dead_end():
    adv = A.load(TINY)
    # A choice that can never be taken leaves section 3 with no way out on some paths.
    adv["sections"][3]["choices"] = [{"text": "Use the key.", "requires": {"item": "key"}, "to": 4}]
    stats = simulate(adv, runs_per_investigator=100)
    assert "3" in stats.dead_ends
    assert any("dead ends" in line for line in target_failures(adv, stats))


def test_targets_are_checked():
    adv = A.load(TINY)
    adv["targets"] = {"sections": [100, 140], "path_mean": [20, 30]}
    failures = target_failures(adv, simulate(adv, runs_per_investigator=50))
    assert any(line.startswith("9 sections") for line in failures)
    assert any(line.startswith("average playthrough") for line in failures)


def write(tmp: Path, name: str, text: str) -> Path:
    path = tmp / name
    path.write_text(text, encoding="utf-8")
    return path


HEAD = "title: Draft\nstart: the-gate\nskills: {Climb: 20}\ninvestigators: []\n\nsections:\n"


def test_assemble_numbers_sections_in_order(tmp_path):
    parts = [
        write(tmp_path, "1-head.yaml", HEAD),
        write(
            tmp_path,
            "2-act.yaml",
            "  the-gate:\n    title: Gate\n    text: A gate.\n    choices:\n      - text: Climb\n        roll: {skill: Climb, success: the-end, failure: the-gate}\n",
        ),
        write(tmp_path, "3-end.yaml", "  the-end:\n    title: End\n    ending: escape\n    text: Out.\n"),
    ]
    adv = A.loads(assemble(parts))
    assert adv["start"] == 1
    assert adv["sections"][1]["choices"][0]["roll"] == {"skill": "Climb", "success": 2, "failure": 1}
    assert adv["sections"][2]["title"] == "End"


def test_assemble_refuses_unknown_links(tmp_path):
    parts = [
        write(
            tmp_path,
            "1.yaml",
            HEAD
            + "  the-gate:\n    title: Gate\n    text: A gate.\n    choices:\n      - text: Go\n        to: nowhere\n",
        )
    ]
    with pytest.raises(AssembleError, match="nowhere"):
        assemble(parts)
