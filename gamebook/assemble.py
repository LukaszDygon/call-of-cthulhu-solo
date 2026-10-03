"""Turn draft parts written with named sections (`the-reef:`, `to: the-reef`) into one numbered adventure.

Drafting with names keeps links readable while the story is still moving. Numbering happens once, in file
order, and the numbered file becomes the source of truth.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from gamebook.adventure import loads

_SECTION_KEY = re.compile(r"^  ([a-z][a-z0-9-]*):(\s*)$", flags=re.M)
_REFERENCE = re.compile(r"\b(to|success|failure|fumble|start|on_death|on_madness): ([a-z][a-z0-9-]*)\b")


class AssembleError(ValueError):
    pass


def draft_parts(path: Path) -> list[Path]:
    """A directory's *.yaml files in name order (1-header.yaml, 2-act-one.yaml, ...), or a single file."""
    return sorted(path.glob("*.yaml")) if path.is_dir() else [path]


def assemble(parts: Iterable[Path]) -> str:
    """Concatenate the parts, number the named sections in order, and rewrite every reference."""
    text = "".join(p.read_text(encoding="utf-8") for p in parts)
    if "\nsections:\n" not in text:
        raise AssembleError("no top-level `sections:` block found")
    head, body = text.split("\nsections:\n", 1)
    names = _SECTION_KEY.findall(body)
    ids = [name for name, _ in names]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise AssembleError(f"duplicate section names: {dupes}")
    number = {name: str(n) for n, name in enumerate(ids, 1)}
    unknown: set[str] = set()

    def renumber(m: re.Match[str]) -> str:
        if m.group(2) not in number:
            unknown.add(m.group(2))
            return m.group(0)
        return f"{m.group(1)}: {number[m.group(2)]}"

    head, body = _REFERENCE.sub(renumber, head), _REFERENCE.sub(renumber, body)
    if unknown:
        raise AssembleError(f"references to undefined sections: {sorted(unknown)}")
    body = _SECTION_KEY.sub(lambda m: f"  {number[m.group(1)]}:{m.group(2)}", body)
    result = head + "\nsections:\n" + body
    loads(result)  # must still parse, with no duplicate keys
    return result
