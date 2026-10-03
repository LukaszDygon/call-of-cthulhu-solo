"""Random playthroughs that follow the same rules as site/app.js, to measure an adventure's shape.

The simulated reader picks a random open choice and rolls dice without spending Luck, so the numbers describe
the story's structure, not a careful player's odds.
"""

from __future__ import annotations

import random
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from gamebook.adventure import CHARACTERISTICS, Adventure, rolled_skills, sections, word_count
from gamebook.variety import analyse

STEP_LIMIT = 300


class Run:
    """One playthrough with one investigator."""

    def __init__(self, adv: Adventure, inv: dict[str, Any], rng: random.Random) -> None:
        self.adv, self.inv, self.rng = adv, inv, rng
        self.secs = sections(adv)
        self.hp, self.san, self.luck = inv["hp"], inv["san"], inv["luck"]
        self.items: set[str] = set(inv.get("kit", []))
        self.notes: set[str] = set()
        self.comp = {c["id"]: {"san": c["san"], "status": "with"} for c in adv.get("companions") or []}
        self.path: list[str] = []
        self.dead_end: str | None = None

    def dice(self, expr: Any) -> int:
        s = str(expr).replace(" ", "").upper()
        sign = -1 if s.startswith("-") else 1
        total = 0
        for term in s.lstrip("+-").split("+"):
            if "D" in term:
                n, d = term.split("D")
                total += sum(self.rng.randint(1, int(d)) for _ in range(int(n or 1)))
            else:
                total += int(term or 0)
        return sign * total

    def skill(self, name: str) -> int:
        if name in CHARACTERISTICS:
            return self.inv["characteristics"][name]
        if name == "Luck":
            return self.luck
        skills = self.inv.get("skills") or {}
        if name == "Dodge":
            return skills.get("Dodge", self.inv["characteristics"]["DEX"] // 2)
        return skills.get(name, (self.adv.get("skills") or {}).get(name, 0))

    def check(self, req: Any) -> bool:
        if not req:
            return True
        if isinstance(req, list):
            return all(self.check(r) for r in req)
        status = lambda cid: self.comp.get(cid, {}).get("status")  # noqa: E731
        tests = {
            "any": lambda v: any(self.check(r) for r in v),
            "item": lambda v: v in self.items,
            "no_item": lambda v: v not in self.items,
            "note": lambda v: v in self.notes,
            "no_note": lambda v: v not in self.notes,
            "with": lambda v: status(v) == "with",
            "broken": lambda v: status(v) == "broken",
            "gone": lambda v: status(v) in ("lost", "dead"),
            "skill": lambda v: self.skill(v) >= req.get("min", 50),
            "investigator": lambda v: self.inv["id"] in (v if isinstance(v, list) else [v]),
        }
        return all(tests[k](v) for k, v in req.items() if k in tests)

    def sanity_loss(self, spec: Any, current: int) -> int:
        passed, failed = str(spec).split("/")
        return max(0, self.dice(passed if self.rng.randint(1, 100) <= current else failed))

    def apply(self, effects: list[dict[str, Any]] | None) -> None:
        for e in effects or []:
            if "companion" in e:
                ids = (
                    [i for i, c in self.comp.items() if c["status"] == "with"]
                    if e["companion"] == "all"
                    else [e["companion"]]
                )
                for cid in ids:
                    c = self.comp[cid]
                    if "status" in e:
                        c["status"] = e["status"]
                    if "san" in e and c["status"] == "with":
                        loss = (
                            self.sanity_loss(e["san"], c["san"])
                            if "/" in str(e["san"])
                            else -self.dice(e["san"])
                        )
                        c["san"] -= loss
                        if c["san"] <= 0:
                            c["status"] = "broken"
                continue
            if "san" in e:
                loss = self.sanity_loss(e["san"], self.san) if "/" in str(e["san"]) else -self.dice(e["san"])
                self.san = min(self.inv["san"], self.san - loss)
            if "hp" in e:
                self.hp = min(self.inv["hp"], self.hp + self.dice(e["hp"]))
            if "luck" in e:
                self.luck += self.dice(e["luck"])
            if "gain" in e:
                self.items.add(e["gain"])
            if "lose" in e:
                self.items.discard(e["lose"])
            if "note" in e:
                self.notes.add(e["note"])
            if "unnote" in e:
                self.notes.discard(e["unnote"])

    def enter(self, sid: Any) -> str:
        sid = str(sid)
        self.path.append(sid)
        sec = self.secs[sid]
        self.apply(sec.get("effects"))
        if not sec.get("ending"):
            if self.hp <= 0 and "on_death" in self.adv and sid != str(self.adv["on_death"]):
                return self.enter(self.adv["on_death"])
            if self.san <= 0 and "on_madness" in self.adv and sid != str(self.adv["on_madness"]):
                return self.enter(self.adv["on_madness"])
        return sid

    def play(self) -> dict[str, Any] | None:
        """Play to an ending; returns the ending section, or None on a dead end or runaway loop."""
        sid = self.enter(self.adv["start"])
        while not self.secs[sid].get("ending"):
            open_choices = [c for c in self.secs[sid].get("choices") or [] if self.check(c.get("requires"))]
            if not open_choices or len(self.path) >= STEP_LIMIT:
                self.dead_end = sid
                return None
            choice = self.rng.choice(open_choices)
            self.apply(choice.get("effects"))
            if "roll" in choice:
                r = choice["roll"]
                value = max(self.skill(s) for s in rolled_skills(choice))
                target = {"regular": value, "hard": value // 2, "extreme": value // 5}[
                    r.get("difficulty", "regular")
                ]
                nxt = r["success"] if self.rng.randint(1, 100) <= target else r["failure"]
            else:
                nxt = choice["to"]
            sid = self.enter(nxt)
        return self.secs[sid]


@dataclass
class Stats:
    runs: int = 0
    lengths: list[int] = field(default_factory=list)
    endings: Counter[str] = field(default_factory=Counter)
    visits: Counter[str] = field(default_factory=Counter)
    broken_runs: int = 0
    dead_ends: Counter[str] = field(default_factory=Counter)

    @property
    def path_mean(self) -> float:
        return statistics.mean(self.lengths) if self.lengths else 0.0

    @property
    def companion_break(self) -> float:
        return self.broken_runs / self.runs if self.runs else 0.0


def simulate(adv: Adventure, runs_per_investigator: int = 400, seed: int = 1926) -> Stats:
    rng = random.Random(seed)
    stats = Stats()
    for inv in adv.get("investigators") or []:
        for _ in range(runs_per_investigator):
            run = Run(adv, inv, rng)
            ending = run.play()
            stats.runs += 1
            stats.visits.update(set(run.path))
            if ending is None:
                stats.dead_ends[run.dead_end or "?"] += 1
                continue
            stats.lengths.append(len(run.path))
            stats.endings[str(ending.get("title"))] += 1
            stats.broken_runs += any(c["status"] == "broken" for c in run.comp.values())
    return stats


def word_profile(adv: Adventure, short: int = 60, long: int = 250) -> dict[str, int]:
    words = [word_count(s) for s in sections(adv).values()]
    return {
        "sections": len(words),
        "words": sum(words),
        "short": sum(w < short for w in words),
        "long": sum(w > long for w in words),
    }


def target_failures(adv: Adventure, stats: Stats | None) -> list[str]:
    """Compare against the adventure's optional `targets:` block (see docs/adventure-format.md).
    Without `stats`, only the structural targets are checked."""
    t = adv.get("targets") or {}
    out = []
    n = len(sections(adv))
    if "sections" in t and not t["sections"][0] <= n <= t["sections"][1]:
        out.append(f"{n} sections, target {t['sections'][0]}-{t['sections'][1]}")
    if "cosmetic_choices" in t:
        report = analyse(adv)
        if report.cosmetic_share > t["cosmetic_choices"]:
            out.append(
                f"{report.cosmetic_share:.0%} of {len(report.decisions)} decisions are cosmetic, target at most {t['cosmetic_choices']:.0%} (run `gamebook choices`)"
            )
    if stats is None:
        return out
    if "path_mean" in t and not t["path_mean"][0] <= stats.path_mean <= t["path_mean"][1]:
        out.append(
            f"average playthrough {stats.path_mean:.1f} sections, target {t['path_mean'][0]}-{t['path_mean'][1]}"
        )
    if (
        "companion_break" in t
        and not t["companion_break"][0] <= stats.companion_break <= t["companion_break"][1]
    ):
        out.append(
            f"a companion broke in {stats.companion_break:.0%} of runs, target {t['companion_break'][0]:.0%}-{t['companion_break'][1]:.0%}"
        )
    if "endings_reached" in t and len(stats.endings) < t["endings_reached"]:
        out.append(f"only {len(stats.endings)} endings reached in simulation, target {t['endings_reached']}")
    if stats.dead_ends:
        out.append(f"dead ends at sections {sorted(stats.dead_ends)}")
    return out
