---
name: verify-story
description: Verifies an adventure in site/adventures/. It runs the automated checks (gamebook check, stats and choices, pytest), then a two-pass continuity audit by the continuity-auditor agent (audit, fix, then a verification pass that catches regressions), then a headless-Chrome smoke test. It fixes what it finds, including characters who react to things they never saw and choices that change nothing. Use after /new-story or /new-path, after editing a story, or when a reader reports a continuity problem.
---

# Verify Story

A playtester sees about a fifth of a branching story. This covers the rest. On *Fog Over Mercy Island*, six
reported seams led to 63 fixes across two audit passes.

## Arguments
- `slug` or a path to the adventure (default: the most recently changed file in `site/adventures/`).

## Workflow

### 1. Automated checks
```bash
uv run gamebook check site/adventures/<slug>.yaml
uv run gamebook stats site/adventures/<slug>.yaml
uv run gamebook choices site/adventures/<slug>.yaml
uv run pytest -q
```
- Fix every error. Fix warnings too, or tell the user why one stays. A "hook without a payoff" usually means a
  missing scene, not a word to delete.
- If a target is missed, look at the rarest sections and the ending spread before changing numbers.
- For each **cosmetic decision** that `choices` lists, give one option somewhere else to go: a side quest that
  comes back changed, or a quick ending (story-craft §2). If more than one or two fixes are needed, plan them with
  `/new-path` instead of patching one by one. Twins inside a decision that also has a real alternative can stay.
- If a **bottleneck** after the opening is listed, the act around it needs a route that skips it.

### 2. Continuity audit, pass 1
Launch the `continuity-auditor` agent (Agent tool, `subagent_type: continuity-auditor`) with the file path. If that
agent type isn't available in the session (it loads at startup), launch a `general-purpose` agent and tell it to
read `.claude/agents/continuity-auditor.md` as its brief and stay read-only. If the user reported specific seams,
include them:
- as examples of the kind of problem to look for
- marked "already being fixed", if you are fixing them yourself in parallel

Don't edit the file while the agent is reading it.

### 3. Fix
Fix **every** finding in the numbered YAML. Small text changes are safest as a Python patch script of exact-match
replacements that asserts each match count and reports any misses. That way a silent non-match can't slip
through.
- **Bridging sections:** use the next free number, place them in the file beside the sections they join, and link
  them in.
- **Path-specific lines:** put them in `extra`, with `before: true` when the line must come first. Order the extras
  deliberately.
- **Re-check:** after the edits, run `uv run gamebook check` (0 errors) and `uv run pytest -q`.

### 4. Continuity audit, pass 2
Resume the **same** auditor with SendMessage, so it keeps its map of the story. Tell it what changed (new sections,
new journal words, engine or format changes) and ask for:
- (a) items not fixed
- (b) regressions the fixes introduced
- (c) anything missed

Fix again. Stop when a pass finds nothing above LOW, or after three passes; then report what remains.

### 5. Browser smoke test
```bash
uv run python -m http.server 8000 -d site     # run in the background
node tools/smoke.mjs http://127.0.0.1:8000/ --runs 6
```
- Expect no console errors and no dead ends. Stop the server afterwards.
- If the sandbox refuses the port or Chrome, say so and give the user the commands to run.

### 6. Report
Give:
- the findings fixed, grouped by kind: time, introductions, hooks, state, positions, companions, facts,
  witnesses, choices
- the final `gamebook stats` and `gamebook choices` numbers
- anything left open, and why

Point the user at a human playtest next.
