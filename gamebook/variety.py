"""Do the reader's choices matter? Classify every decision by what its options change.

A decision is a section offering two or more choices that can be open at the same time. Each pair of options is
followed forward to the rejoin: the nearest section that every path from both options must pass through.

- fork:     no rejoin. The options can end the story in different places.
- detour:   one option walks a route of its own, DETOUR sections or more, before the rejoin (a side quest).
- flavour:  the routes are short, but they leave different lasting state behind (a journal word, an item or a
            companion's status that something later checks).
- cosmetic: the same scenes and the same state. Whatever the reader picks, nothing changes.

A decision takes the best kind among its pairs. Two options that are cosmetic to each other are "twins".
docs/story-craft.md §2 explains what to do about them.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

from gamebook.adventure import Adventure, Section, leaves, sections, targets

DETOUR = 3  # sections of an option's own route, before the rejoin, that make it a side quest
KINDS = ("fork", "detour", "flavour", "cosmetic")  # best first

Choice = dict[str, Any]


@dataclass(frozen=True)
class Pair:
    a: str  # choice text
    b: str
    kind: str
    rejoin: str | None


@dataclass
class Decision:
    section: str
    title: str
    kind: str
    pairs: list[Pair] = field(default_factory=list)

    @property
    def twins(self) -> list[Pair]:
        return [p for p in self.pairs if p.kind == "cosmetic"]


@dataclass
class Report:
    decisions: list[Decision]
    bottlenecks: list[str]  # sections that every playthrough passes through

    def count(self, kind: str) -> int:
        return sum(d.kind == kind for d in self.decisions)

    @property
    def cosmetic_share(self) -> float:
        return self.count("cosmetic") / len(self.decisions) if self.decisions else 0.0


def analyse(adv: Adventure) -> Report:
    secs = sections(adv)
    succ = {
        sid: [t for c in sec.get("choices") or [] for t in targets(c) if t in secs]
        for sid, sec in secs.items()
    }
    must = _must_pass(secs, succ)
    checked = _checked(adv)
    decisions = []
    for sid, sec in secs.items():
        options = sec.get("choices") or []
        pairs = [
            _compare(a, b, secs, succ, must, checked)
            for a, b in combinations(options, 2)
            if not _exclusive(a.get("requires"), b.get("requires"))
        ]
        if pairs:
            best = min(pairs, key=lambda p: KINDS.index(p.kind)).kind
            decisions.append(Decision(sid, str(sec.get("title")), best, pairs))
    start = str(adv.get("start"))
    bottlenecks = sorted(must.get(start, set()), key=int) if start in secs else []
    return Report(sorted(decisions, key=lambda d: int(d.section)), bottlenecks)


def _must_pass(secs: dict[str, Section], succ: dict[str, list[str]]) -> dict[str, set[str]]:
    """For each section, the sections every path from it passes through on the way to an ending (itself
    included). Post-dominators, by iterating to a fixed point so that loops are handled."""
    every = set(secs)
    must = {sid: {sid} if not succ[sid] else set(every) for sid in secs}
    changed = True
    while changed:
        changed = False
        for sid in secs:
            if not succ[sid]:
                continue
            new = {sid} | set.intersection(*(must[t] for t in succ[sid]))
            if new != must[sid]:
                must[sid], changed = new, True
    return must


def _checked(adv: Adventure) -> set[tuple[str, str]]:
    """State that something in the story looks at: journal words, items and companions in a `requires`, plus
    items that give a bonus die."""
    found = {("item", i) for i, d in (adv.get("items") or {}).items() if d.get("bonus")}
    for sec in sections(adv).values():
        for block in [*(sec.get("extra") or []), *(sec.get("choices") or [])]:
            for leaf in leaves(block.get("requires")):
                for key in ("note", "no_note", "item", "no_item"):
                    if key in leaf:
                        found.add((key.removeprefix("no_"), leaf[key]))
                for key in ("with", "broken", "gone"):
                    if key in leaf:
                        found.add(("companion", leaf[key]))
    return found


def _lasting(effects: list[dict[str, Any]] | None, checked: set[tuple[str, str]]) -> set[str]:
    out = set()
    for e in effects or []:
        for key, kind, sign in (
            ("note", "note", "+"),
            ("unnote", "note", "-"),
            ("gain", "item", "+"),
            ("lose", "item", "-"),
        ):
            if key in e and (kind, e[key]) in checked:
                out.add(f"{sign}{e[key]}")
        if "status" in e and (e["companion"] == "all" or ("companion", e["companion"]) in checked):
            out.add(f"{e['companion']}:{e['status']}")
    return out


_OPPOSITE = {"note": "no_note", "no_note": "note", "item": "no_item", "no_item": "item"}
_COMPANION = ("with", "broken", "gone")


def _required(req: Any) -> list[dict[str, Any]]:
    """Conditions that must all hold. Alternatives under `any:` are skipped: none of them is required."""
    if not req:
        return []
    if isinstance(req, list):
        return [leaf for r in req for leaf in _required(r)]
    return [] if "any" in req else [req]


def _exclusive(ra: Any, rb: Any) -> bool:
    """True when two choices can never be open at the same time, because their conditions contradict."""
    for x in _required(ra):
        for y in _required(rb):
            for key, value in x.items():
                if key in _OPPOSITE and y.get(_OPPOSITE[key]) == value:
                    return True
                if key in _COMPANION and any(y.get(k) == value for k in _COMPANION if k != key):
                    return True
                if key == "investigator" and "investigator" in y:
                    mine = set(value if isinstance(value, list) else [value])
                    theirs = set(
                        y["investigator"] if isinstance(y["investigator"], list) else [y["investigator"]]
                    )
                    if not mine & theirs:
                        return True
    return False


def _region(start: list[str], stop: str, succ: dict[str, list[str]]) -> dict[str, int]:
    """Sections reachable from `start` (at distance 1) without passing through `stop`."""
    dist: dict[str, int] = {}
    todo = deque((s, 1) for s in start if s != stop)
    while todo:
        sid, d = todo.popleft()
        if sid in dist:
            continue
        dist[sid] = d
        todo.extend((t, d + 1) for t in succ[sid] if t != stop and t not in dist)
    return dist


def _distance(start: list[str], goal: str, succ: dict[str, list[str]]) -> int:
    seen, todo = set(), deque((s, 1) for s in start)
    while todo:
        sid, d = todo.popleft()
        if sid == goal:
            return d
        if sid not in seen:
            seen.add(sid)
            todo.extend((t, d + 1) for t in succ[sid])
    return 10**6


def _own_route(start: list[str], stop: str, succ: dict[str, list[str]], other: dict[str, int]) -> int:
    """Sections on the shortest walk from an option to the rejoin that the other option never shows."""
    best: dict[str, int] = {}
    todo = deque((s, int(s not in other)) for s in start if s != stop)
    shortest = 10**6
    while todo:
        sid, own = todo.popleft()
        if sid in best and best[sid] <= own:
            continue
        best[sid] = own
        for t in succ[sid]:
            if t == stop:
                shortest = min(shortest, own)
            else:
                todo.append((t, own + int(t not in other)))
    return 0 if shortest == 10**6 else shortest


def _compare(
    a: Choice,
    b: Choice,
    secs: dict[str, Section],
    succ: dict[str, list[str]],
    must: dict[str, set[str]],
    checked: set[tuple[str, str]],
) -> Pair:
    ta, tb = targets(a), targets(b)
    common = set.intersection(*(must[t] for t in ta + tb if t in must)) if ta and tb else set()
    if not common:
        return Pair(a.get("text", ""), b.get("text", ""), "fork", None)
    rejoin = min(common, key=lambda s: (max(_distance(ta, s, succ), _distance(tb, s, succ)), int(s)))
    ra, rb = _region(ta, rejoin, succ), _region(tb, rejoin, succ)
    if max(_own_route(ta, rejoin, succ, rb), _own_route(tb, rejoin, succ, ra)) >= DETOUR:
        kind = "detour"
    elif _state(a, ra, secs, must, checked) != _state(b, rb, secs, must, checked):
        kind = "flavour"
    else:
        kind = "cosmetic"
    return Pair(a.get("text", ""), b.get("text", ""), kind, rejoin)


def _state(
    choice: Choice,
    region: dict[str, int],
    secs: dict[str, Section],
    must: dict[str, set[str]],
    checked: set[tuple[str, str]],
) -> tuple[set[str], set[str]]:
    """Lasting state an option leaves behind before the rejoin: what it can leave (the effects of every section and
    choice on its route) and what it always leaves (its own effects, and those of sections on every path)."""
    always = _lasting(choice.get("effects"), checked)
    starts = [t for t in targets(choice) if t in must]
    on_every_path = set.intersection(*(must[t] for t in starts)) if starts else set()
    can = set(always)
    for sid in region:
        effects = _lasting(secs[sid].get("effects"), checked)
        can |= effects
        if sid in on_every_path:
            always |= effects
        for c in secs[sid].get("choices") or []:
            can |= _lasting(c.get("effects"), checked)
    return can, always
