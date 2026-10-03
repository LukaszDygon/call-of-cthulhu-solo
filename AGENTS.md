# AGENTS.md

Single source of truth for AI agents working in **Call of Cthulhu Solo**. `CLAUDE.md` imports this file.

## What this repo is

Solo gamebooks in the style of the Call of Cthulhu RPG. A static, YAML-driven player lives in `site/`. A Python
toolkit (`gamebook/`) checks adventures and simulates playthroughs. Stories are the product: their continuity
matters as much as the code.

Every push to `main` deploys `site/` to GitHub Pages (https://lukaszdygon.github.io/call-of-cthulhu-solo/). The
deploy refuses to publish if `gamebook check --strict` fails, so keep it green.

## Commands

```bash
uv sync                                                  # install (dev tools included)
uv run python -m http.server 8000 -d site                # play at http://127.0.0.1:8000/
uv run pytest -q                                         # tests (run after every change)
uv run ruff check . && uv run ruff format .              # lint and format
uv run gamebook check site/adventures/<slug>.yaml        # structure: links, reachability, hooks, fair rolls
uv run gamebook stats site/adventures/<slug>.yaml        # simulated playthroughs vs the story's `targets:`
uv run gamebook edges site/adventures/<slug>.yaml        # every way into each section, for continuity work
uv run gamebook assemble drafts/<slug>/ -o site/adventures/<slug>.yaml
node tools/smoke.mjs http://127.0.0.1:8000/              # headless Chrome playthroughs (server must be running)
```

## Repo map

| Path | Purpose |
| :--- | :--- |
| `site/app.js` | The engine: rolls, Sanity, Luck, companions, conditions, saving, full screen |
| `site/style.css`, `site/index.html` | The 1920s campaign-book look and the page shell |
| `site/adventures/` | `index.yaml` plus one YAML file per adventure |
| `gamebook/adventure.py` | Strict loader (duplicate keys fail) and helpers to walk sections, links and state |
| `gamebook/checks.py` | Structural checks |
| `gamebook/simulate.py` | Random playthroughs mirroring the engine's rules, and `targets:` |
| `gamebook/assemble.py` | Named-section drafts to a numbered file |
| `gamebook/cli.py` | The `gamebook` command |
| `tests/` | The checker against `fixtures/tiny.yaml`, and every published adventure against its targets |
| `docs/adventure-format.md` | The YAML format |
| `docs/story-craft.md` | How to write stories that hold together; the brief for every story skill and agent |
| `.claude/skills/` | `new-story`, `verify-story` |
| `.claude/agents/continuity-auditor.md` | Read-only, edge-by-edge continuity audit |
| `.claude/rules/adventures.md` | Writing rules, loaded when touching adventures |

## Workflow for stories

1. `/new-story`: interview, bible, section map, drafts, assemble, check.
2. `/verify-story`: automated checks, a two-pass continuity audit with fixes, a smoke test.
3. A human playtest. Fix what it finds with `/verify-story` again.

## Conventions

- Simplicity first: stdlib before packages, plain browser JavaScript, no build step for the site.
- The engine (`site/app.js`), the simulator (`gamebook/simulate.py`) and `docs/adventure-format.md` describe the
  same rules. Change them together.
- Python: type hints on public functions, `from __future__ import annotations`, no `print` outside `gamebook/cli.py`.
  New behaviour gets a test.
- Commits: `story(<slug>): ...` for adventures, `feat:`, `fix:`, `test:`, `docs:`, `chore:` otherwise.

## Do not

- Copy Chaosium text, or make a real people the cult (`docs/story-craft.md` §7).
- Add dependencies without asking.
- Commit `drafts/`. It's scratch space; the numbered file in `site/adventures/` is the source of truth.
- Push unless the user asks.
