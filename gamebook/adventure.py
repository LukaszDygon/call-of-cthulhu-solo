"""Load an adventure YAML file and walk its parts. The format is documented in docs/adventure-format.md."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

CHARACTERISTICS = frozenset({"STR", "CON", "SIZ", "DEX", "APP", "INT", "POW", "EDU"})
UNIVERSAL = CHARACTERISTICS | {"Luck", "Dodge"}  # rolls anyone can make on equal terms
TRAINED = 40  # a skill at this value or above counts as trained
REF_KEYS = ("to", "success", "failure", "fumble")

Adventure = dict[str, Any]
Section = dict[str, Any]


class DuplicateKeyError(ValueError):
    """Two equal keys in one mapping. PyYAML would silently keep the last one and lose the first."""


class _StrictLoader(yaml.SafeLoader):
    pass


def _strict_mapping(loader: _StrictLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    seen: set[Any] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise DuplicateKeyError(f"duplicate key {key!r} at line {key_node.start_mark.line + 1}")
        seen.add(key)
    return loader.construct_mapping(node, deep)


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _strict_mapping)


def loads(text: str) -> Adventure:
    """Parse adventure YAML, refusing duplicate keys."""
    return yaml.load(text, Loader=_StrictLoader)  # noqa: S506 - a SafeLoader subclass


def load(path: Path | str) -> Adventure:
    return loads(Path(path).read_text(encoding="utf-8"))


def sections(adv: Adventure) -> dict[str, Section]:
    """Sections keyed by their number as a string (the engine looks them up the same way)."""
    return {str(k): v for k, v in (adv.get("sections") or {}).items()}


def choices(adv: Adventure) -> Iterator[tuple[str, dict[str, Any]]]:
    for sid, sec in sections(adv).items():
        for choice in sec.get("choices") or []:
            yield sid, choice


def targets(choice: dict[str, Any]) -> list[str]:
    """Every section a choice can lead to: `to`, or each outcome of its roll."""
    if "roll" in choice:
        return [str(choice["roll"][k]) for k in ("success", "failure", "fumble") if k in choice["roll"]]
    return [str(choice["to"])] if "to" in choice else []


def leaves(req: Any) -> list[dict[str, Any]]:
    """Flatten a `requires` block (a condition, a list of them, or `any:`) into single conditions."""
    if not req:
        return []
    if isinstance(req, list):
        return [leaf for r in req for leaf in leaves(r)]
    if "any" in req:
        return [leaf for r in req["any"] for leaf in leaves(r)]
    return [req]


def rolled_skills(choice: dict[str, Any]) -> list[str]:
    skill = choice["roll"]["skill"]
    return list(skill) if isinstance(skill, list) else [skill]


def all_effects(adv: Adventure) -> Iterator[tuple[str, dict[str, Any]]]:
    """(section, effect) for section effects and choice effects."""
    for sid, sec in sections(adv).items():
        for effect in sec.get("effects") or []:
            yield sid, effect
        for choice in sec.get("choices") or []:
            for effect in choice.get("effects") or []:
                yield sid, effect


def all_conditions(adv: Adventure) -> Iterator[tuple[str, dict[str, Any]]]:
    """(section, condition) for every leaf condition on extras and choices."""
    for sid, sec in sections(adv).items():
        for extra in sec.get("extra") or []:
            for leaf in leaves(extra.get("requires")):
                yield sid, leaf
        for choice in sec.get("choices") or []:
            for leaf in leaves(choice.get("requires")):
                yield sid, leaf


def edges(adv: Adventure) -> Iterator[tuple[str, str, str, dict[str, Any]]]:
    """(from, to, outcome, choice) for every link; outcome is 'to', 'success', 'failure' or 'fumble'."""
    for sid, choice in choices(adv):
        if "roll" in choice:
            for outcome in ("success", "failure", "fumble"):
                if outcome in choice["roll"]:
                    yield sid, str(choice["roll"][outcome]), outcome, choice
        elif "to" in choice:
            yield sid, str(choice["to"]), "to", choice


def entry_points(adv: Adventure) -> list[str]:
    """The start section plus the death and madness sections, which can be reached from anywhere."""
    return [str(adv[k]) for k in ("start", "on_death", "on_madness") if k in adv]


def word_count(sec: Section) -> int:
    return len(str(sec.get("text", "")).split())
