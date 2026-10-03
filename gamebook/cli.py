"""`gamebook` command line: check, stats, edges and assemble adventures."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from gamebook import adventure as A
from gamebook.assemble import AssembleError, assemble, draft_parts
from gamebook.checks import check
from gamebook.simulate import simulate, target_failures, word_profile
from gamebook.variety import KINDS, analyse

DEFAULT_INDEX = Path("site/adventures/index.yaml")


def adventure_files(paths: list[str]) -> list[Path]:
    """Expand an adventures index (or the default one, when no paths are given) into the files it lists."""
    result: list[Path] = []
    for path in [Path(p) for p in paths] or [DEFAULT_INDEX]:
        if path.name == "index.yaml":
            listed = yaml.safe_load(path.read_text(encoding="utf-8"))["adventures"]
            result.extend(path.parent / entry["file"] for entry in listed)
        else:
            result.append(path)
    return result


def cmd_check(args: argparse.Namespace) -> int:
    failed = False
    for path in adventure_files(args.files):
        try:
            adv = A.load(path)
        except (A.DuplicateKeyError, OSError, ValueError) as exc:
            print(f"{path}: cannot load: {exc}")
            failed = True
            continue
        findings = check(adv)
        errors = [f for f in findings if f.level == "error"]
        warnings = [f for f in findings if f.level == "warning"]
        print(f"{path}: {len(errors)} error(s), {len(warnings)} warning(s)")
        for f in findings:
            print(f"  {f}")
        failed |= bool(errors) or (args.strict and bool(warnings))
    return 1 if failed else 0


def cmd_stats(args: argparse.Namespace) -> int:
    adv = A.load(args.file)
    stats = simulate(adv, runs_per_investigator=args.runs, seed=args.seed)
    profile = word_profile(adv)
    print(f"{adv.get('title')}: {profile['sections']} sections, {profile['words']} words")
    print(f"  short beats (<60 words): {profile['short']}   long set pieces (>250 words): {profile['long']}")
    if stats.lengths:
        print(
            f"  playthrough length: mean {stats.path_mean:.1f}, min {min(stats.lengths)}, max {max(stats.lengths)} sections"
        )
    print(f"  a companion broke in {stats.companion_break:.0%} of {stats.runs} runs")
    print("  endings:")
    for title, n in stats.endings.most_common():
        print(f"    {n / stats.runs:6.1%}  {title}")
    secs = A.sections(adv)
    never = sorted((s for s in secs if stats.visits[s] == 0), key=int)
    rare = sorted(secs, key=lambda s: stats.visits[s])[: args.rare]
    print(
        f"  rarest sections: {', '.join(f'{s} {secs[s].get("title")!r} {stats.visits[s] / stats.runs:.1%}' for s in rare)}"
    )
    if never:
        print(f"  never reached in simulation: {never}")
    failures = target_failures(adv, stats)
    for line in failures:
        print(f"  TARGET MISSED: {line}")
    if not failures and adv.get("targets"):
        print("  all targets met")
    return 1 if failures else 0


def _ancestors(adv: A.Adventure) -> dict[str, set[str]]:
    """Every section from which each section can be reached (ignoring conditions)."""
    incoming: dict[str, set[str]] = defaultdict(set)
    for src, dst, _, _ in A.edges(adv):
        incoming[dst].add(src)
    result: dict[str, set[str]] = {}
    for sid in A.sections(adv):
        seen: set[str] = set()
        todo = list(incoming[sid])
        while todo:
            s = todo.pop()
            if s not in seen:
                seen.add(s)
                todo.extend(incoming[s])
        result[sid] = seen
    return result


def cmd_edges(args: argparse.Namespace) -> int:
    """For each section: every way in, and the state that may already be set on arrival."""
    adv = A.load(args.file)
    secs = A.sections(adv)
    incoming: dict[str, list[str]] = defaultdict(list)
    for src, dst, outcome, choice in A.edges(adv):
        how = "" if outcome == "to" else f" [{outcome}]"
        incoming[dst].append(f"from {src} {secs[src].get('title')!r}: {choice.get('text')!r}{how}")
    ancestors = _ancestors(adv)
    wanted = (
        [str(s) for s in args.section]
        if args.section
        else sorted(secs, key=lambda s: (-len(incoming[s]), int(s)))
    )
    for sid in wanted:
        sec = secs[sid]
        before = ancestors[sid]
        notes, items, companions = set(), set(), set()
        for anc in before:
            for e in [
                *(secs[anc].get("effects") or []),
                *(e for c in secs[anc].get("choices") or [] for e in c.get("effects") or []),
            ]:
                notes |= {e["note"]} if "note" in e else set()
                items |= {e["gain"]} if "gain" in e else set()
                if "companion" in e:
                    companions.add(f"{e['companion']}:{e.get('status', 'san')}")
        print(
            f"== {sid} {sec.get('title')!r}  ({len(incoming[sid])} ways in{', ending' if sec.get('ending') else ''})"
        )
        for line in incoming[sid] or ["(entry point)"]:
            print(f"   {line}")
        print(f"   may already hold notes: {', '.join(sorted(notes)) or '-'}")
        print(f"   may already hold items: {', '.join(sorted(items)) or '-'} (plus starting kits)")
        print(f"   upstream companion changes: {', '.join(sorted(companions)) or '-'}")
    return 0


def cmd_choices(args: argparse.Namespace) -> int:
    """Which decisions change something, and which are cosmetic."""
    adv = A.load(args.file)
    secs = A.sections(adv)
    report = analyse(adv)

    def name(sid: str | None) -> str:
        return f"{sid} {secs[sid].get('title')!r}" if sid else "-"

    counts = ", ".join(f"{report.count(k)} {k}" for k in KINDS)
    print(
        f"{adv.get('title')}: {len(report.decisions)} decisions: {counts} ({report.cosmetic_share:.0%} cosmetic)"
    )
    print(f"  every playthrough passes through: {', '.join(name(s) for s in report.bottlenecks) or '-'}")
    cosmetic = [d for d in report.decisions if d.kind == "cosmetic"]
    if cosmetic:
        print("  cosmetic decisions (whatever the reader picks, the same scenes and state follow):")
        for d in cosmetic:
            print(f"    {name(d.section)} -> rejoins at {name(d.pairs[0].rejoin)}")
            for c in dict.fromkeys(t for p in d.pairs for t in (p.a, p.b)):
                print(f"        {c!r}")
    twins = [(d, p) for d in report.decisions if d.kind != "cosmetic" for p in d.twins]
    if twins:
        print("  twin options inside other decisions (these two change nothing between them):")
        for d, p in twins:
            print(f"    {name(d.section)}: {p.a!r} / {p.b!r} -> rejoin at {name(p.rejoin)}")
    if args.all:
        print("  every decision:")
        for d in report.decisions:
            print(f"    {d.kind:8} {name(d.section)}")
    failures = [line for line in target_failures(adv, None) if "cosmetic" in line]
    for line in failures:
        print(f"  TARGET MISSED: {line}")
    return 1 if failures else 0


def cmd_assemble(args: argparse.Namespace) -> int:
    parts = [p for path in args.parts for p in draft_parts(Path(path))]
    try:
        text = assemble(parts)
    except AssembleError as exc:
        print(f"cannot assemble: {exc}")
        return 1
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"{len(A.sections(A.loads(text)))} sections written to {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gamebook", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="structural checks: links, reachability, hooks, fair rolls")
    p.add_argument(
        "files", nargs="*", help="adventure files or an index.yaml (default: site/adventures/index.yaml)"
    )
    p.add_argument("--strict", action="store_true", help="fail on warnings too")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("stats", help="simulate random playthroughs and compare against `targets:`")
    p.add_argument("file")
    p.add_argument("--runs", type=int, default=400, help="runs per investigator (default 400)")
    p.add_argument("--seed", type=int, default=1926)
    p.add_argument("--rare", type=int, default=8, help="how many of the rarest sections to list")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser(
        "edges", help="ways into each section and the state possible on arrival (for continuity audits)"
    )
    p.add_argument("file")
    p.add_argument("--section", nargs="*", help="only these section numbers (default: all, busiest first)")
    p.set_defaults(func=cmd_edges)

    p = sub.add_parser("choices", help="which decisions change something, and which are cosmetic")
    p.add_argument("file")
    p.add_argument("--all", action="store_true", help="list every decision with its kind")
    p.set_defaults(func=cmd_choices)

    p = sub.add_parser("assemble", help="number a draft written with named sections")
    p.add_argument("parts", nargs="+", help="a drafts/<slug>/ directory, or part files in order")
    p.add_argument("-o", "--output", required=True)
    p.set_defaults(func=cmd_assemble)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
