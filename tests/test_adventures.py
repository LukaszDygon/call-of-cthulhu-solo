"""Every published adventure (site/adventures/index.yaml) passes the checks and meets its own `targets:`."""

from pathlib import Path

import pytest
import yaml

from gamebook import adventure as A
from gamebook.checks import errors
from gamebook.simulate import simulate, target_failures

ADVENTURES = Path(__file__).resolve().parents[1] / "site" / "adventures"
FILES = [
    a["file"] for a in yaml.safe_load((ADVENTURES / "index.yaml").read_text(encoding="utf-8"))["adventures"]
]


def test_index_lists_existing_files():
    assert FILES
    assert all((ADVENTURES / f).is_file() for f in FILES)


@pytest.mark.parametrize("name", FILES)
def test_adventure_has_no_errors(name):
    adv = A.load(ADVENTURES / name)
    assert [str(f) for f in errors(adv)] == []


@pytest.mark.parametrize("name", FILES)
def test_adventure_meets_its_targets(name):
    adv = A.load(ADVENTURES / name)
    assert adv.get("targets"), "declare `targets:` so the shape of the story is tested"
    assert target_failures(adv, simulate(adv, runs_per_investigator=300)) == []
