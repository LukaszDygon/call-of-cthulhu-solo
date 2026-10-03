"""Structural checks for an adventure: links, reachability, state that is set and used, and fair rolls.

These catch what a machine can catch. Narrative continuity (time of day, who is present, what the reader has
been told) needs a reader: see docs/story-craft.md and the continuity-auditor agent.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from gamebook.adventure import (
    TRAINED,
    UNIVERSAL,
    Adventure,
    all_conditions,
    all_effects,
    choices,
    edges,
    entry_points,
    leaves,
    rolled_skills,
    sections,
    targets,
)

DIFFICULTIES = {"regular", "hard", "extreme"}
STATUSES = {"with", "broken", "lost", "dead"}


@dataclass(frozen=True)
class Finding:
    level: str  # "error" or "warning"
    where: str  # "section 41", "investigator guide", "top level"
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.where}: {self.message}"


def check(adv: Adventure) -> list[Finding]:
    """All findings for one adventure, errors first."""
    found: list[Finding] = []
    for rule in (_top_level, _links, _shape, _reachability, _state, _self_conditions, _rolls, _investigators):
        found.extend(rule(adv))
    return sorted(found, key=lambda f: f.level != "error")


def errors(adv: Adventure) -> list[Finding]:
    return [f for f in check(adv) if f.level == "error"]


def _err(where: str, message: str) -> Finding:
    return Finding("error", where, message)


def _warn(where: str, message: str) -> Finding:
    return Finding("warning", where, message)


def _top_level(adv: Adventure) -> list[Finding]:
    missing = [k for k in ("title", "start", "sections", "skills", "investigators") if not adv.get(k)]
    return [_err("top level", f"missing `{k}`") for k in missing]


def _links(adv: Adventure) -> list[Finding]:
    secs = sections(adv)
    found = [
        _err("top level", f"`{k}` points at missing section {adv[k]}")
        for k in ("start", "on_death", "on_madness")
        if k in adv and str(adv[k]) not in secs
    ]
    for sid, choice in choices(adv):
        if not targets(choice):
            found.append(_err(f"section {sid}", f"choice {choice.get('text')!r} has neither `to` nor `roll`"))
        for t in targets(choice):
            if t not in secs:
                found.append(
                    _err(f"section {sid}", f"choice {choice.get('text')!r} points at missing section {t}")
                )
    return found


def _shape(adv: Adventure) -> list[Finding]:
    found = []
    for sid, sec in sections(adv).items():
        where = f"section {sid}"
        if not str(sec.get("text", "")).strip():
            found.append(_err(where, "has no text"))
        if sec.get("ending") and sec.get("choices"):
            found.append(_err(where, "is an ending but has choices"))
        if not sec.get("ending") and not sec.get("choices"):
            found.append(_err(where, "has no choices and is not an ending (dead end)"))
        for extra in sec.get("extra") or []:
            if not str(extra.get("text", "")).strip():
                found.append(_err(where, "has an extra with no text"))
    if not any(s.get("ending") for s in sections(adv).values()):
        found.append(_err("top level", "no ending sections"))
    return found


def _reachability(adv: Adventure) -> list[Finding]:
    secs = sections(adv)
    out: dict[str, list[str]] = {sid: [] for sid in secs}
    for src, dst, _, _ in edges(adv):
        out[src].append(dst)
    seen: set[str] = set()
    todo = [s for s in entry_points(adv) if s in secs]
    while todo:
        sid = todo.pop()
        if sid not in seen:
            seen.add(sid)
            todo.extend(t for t in out.get(sid, []) if t in secs)
    return [_err(f"section {sid}", "cannot be reached from the start") for sid in secs if sid not in seen]


def _state(adv: Adventure) -> list[Finding]:
    """Items, journal words and companions: defined, obtainable when required, and used when set."""
    items, journal = set(adv.get("items") or {}), set(adv.get("journal") or {})
    companions = {c["id"] for c in adv.get("companions") or []}
    kits = {i for inv in adv.get("investigators") or [] for i in inv.get("kit", [])}
    gained = kits | {e["gain"] for _, e in all_effects(adv) if "gain" in e}
    noted = {e["note"] for _, e in all_effects(adv) if "note" in e}
    found = [_err("investigators", f"kit item {i!r} is not defined in `items`") for i in sorted(kits - items)]

    for sid, e in all_effects(adv):
        where = f"section {sid}"
        for key, pool, kind in (
            ("gain", items, "item"),
            ("lose", items, "item"),
            ("note", journal, "journal word"),
            ("unnote", journal, "journal word"),
        ):
            if key in e and e[key] not in pool:
                found.append(_err(where, f"{key} {e[key]!r}: no such {kind}"))
        if "companion" in e and e["companion"] != "all" and e["companion"] not in companions:
            found.append(_err(where, f"no companion {e['companion']!r}"))
        if "status" in e and e["status"] not in STATUSES:
            found.append(_err(where, f"unknown companion status {e['status']!r}"))

    required_items: set[str] = set()
    used_notes: set[str] = set()
    for sid, cond in all_conditions(adv):
        where = f"section {sid}"
        for key in ("item", "no_item"):
            if key in cond and cond[key] not in items:
                found.append(_err(where, f"requires {key} {cond[key]!r}: no such item"))
        for key in ("note", "no_note"):
            if key in cond:
                used_notes.add(cond[key])
                if cond[key] not in journal:
                    found.append(_err(where, f"requires {key} {cond[key]!r}: no such journal word"))
        for key in ("with", "broken", "gone"):
            if key in cond and cond[key] not in companions:
                found.append(_err(where, f"requires {key} {cond[key]!r}: no such companion"))
        if "item" in cond:
            required_items.add(cond["item"])
            if cond["item"] not in gained:
                found.append(_err(where, f"requires item {cond['item']!r}, which nobody can ever get"))
        if "note" in cond and cond["note"] not in noted:
            found.append(_err(where, f"requires journal word {cond['note']!r}, which is never noted"))

    bonus_items = {i for i, d in (adv.get("items") or {}).items() if d.get("bonus")}
    for word in sorted(noted - used_notes):
        found.append(_warn("journal", f"{word} is noted but nothing ever checks it: a hook without a payoff"))
    for item in sorted(gained - required_items - bonus_items):
        found.append(_warn("items", f"{item!r} can be obtained but is never required and gives no bonus"))
    for word in sorted(journal - noted):
        found.append(_warn("journal", f"{word} is defined but never noted"))
    return found


def _self_conditions(adv: Adventure) -> list[Finding]:
    """A section's effects apply before its extras and choices are shown, so conditions on state the same
    section sets are always true (or always false) there. That is almost always a mistake."""
    found = []
    for sid, sec in sections(adv).items():
        sets_notes = {e["note"] for e in sec.get("effects") or [] if "note" in e}
        sets_items = {e["gain"] for e in sec.get("effects") or [] if "gain" in e}
        blocks = [("extra", x) for x in sec.get("extra") or []] + [
            ("choice", c) for c in sec.get("choices") or []
        ]
        for kind, block in blocks:
            for leaf in leaves(block.get("requires")):
                for key, pool in (
                    ("note", sets_notes),
                    ("no_note", sets_notes),
                    ("item", sets_items),
                    ("no_item", sets_items),
                ):
                    if key in leaf and leaf[key] in pool:
                        always = "false" if key.startswith("no_") else "true"
                        found.append(
                            _warn(
                                f"section {sid}",
                                f"{kind} requires {key} {leaf[key]!r}, which this section's own effects set, so it is always {always}",
                            )
                        )
    return found


def _rolls(adv: Adventure) -> list[Finding]:
    """Every roll is open to everyone, gated behind the skill it needs, or trained by two investigators."""
    known = set(adv.get("skills") or {}) | UNIVERSAL
    investigators = adv.get("investigators") or []
    found = []
    for sid, choice in choices(adv):
        if "roll" not in choice:
            continue
        where = f"section {sid}"
        skills = rolled_skills(choice)
        unknown = [s for s in skills if s not in known]
        if unknown:
            found.append(_err(where, f"rolls unknown skill(s) {unknown}"))
        if choice["roll"].get("difficulty", "regular") not in DIFFICULTIES:
            found.append(_err(where, f"unknown difficulty {choice['roll'].get('difficulty')!r}"))
        if set(skills) & UNIVERSAL or any("skill" in c for c in leaves(choice.get("requires"))):
            continue
        trained = [
            inv["id"]
            for inv in investigators
            if any((inv.get("skills") or {}).get(s, 0) >= TRAINED for s in skills)
        ]
        if len(investigators) > 1 and len(trained) < 2:
            found.append(
                _err(
                    where,
                    f"rolls {skills}, trained by only {trained or 'nobody'}; add a skill, gate the choice, or offer another way",
                )
            )
    return found


def _investigators(adv: Adventure) -> list[Finding]:
    rolled = Counter(s for _, c in choices(adv) if "roll" in c for s in rolled_skills(c))
    found = []
    for inv in adv.get("investigators") or []:
        where = f"investigator {inv.get('id')}"
        ch = inv.get("characteristics") or {}
        if {"CON", "SIZ"} <= set(ch) and inv.get("hp") != (ch["CON"] + ch["SIZ"]) // 10:
            found.append(
                _warn(
                    where, f"hp {inv.get('hp')} should be (CON + SIZ) / 10 = {(ch['CON'] + ch['SIZ']) // 10}"
                )
            )
        useful = {s for s, v in (inv.get("skills") or {}).items() if v >= TRAINED and s in rolled}
        if len(useful) < 3:
            found.append(
                _err(
                    where,
                    f"only gets to roll {sorted(useful)} of their trained skills; the story should test at least three",
                )
            )
    return found
