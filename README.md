# Call of Cthulhu Solo

Solo gamebooks in the style of the Call of Cthulhu RPG, played in the browser.
You read numbered sections, make choices and roll d100 against your investigator's skills.
You also manage Sanity, Luck and hit points, and companions who can break.

Every adventure is a single human-readable YAML file. A small Python toolkit checks a story's structure and simulates
thousands of playthroughs to measure its shape. Claude Code skills help you write new stories that stay continuous
across every branch.

The first adventure is **Fog Over Mercy Island**: a 1926 naturalist expedition to an uncharted Aleutian island.
It has 133 sections, six investigators and nine endings.

## Play

```bash
uv sync
uv run python -m http.server 8000 -d site     # then open http://127.0.0.1:8000/
```

The site is static (`site/`), so any static host works. It needs js-yaml from cdnjs and three Google Fonts.

## Repo map

| Path | What |
| :--- | :--- |
| `site/index.html`, `site/app.js`, `site/style.css` | The player: a YAML-driven engine with no build step |
| `site/adventures/` | `index.yaml` lists the adventures; one `<slug>.yaml` per story |
| `gamebook/` | Python toolkit: `adventure.py` (strict loader), `checks.py`, `simulate.py`, `assemble.py`, `cli.py` |
| `tests/` | pytest: the checker against `fixtures/tiny.yaml`, and every published adventure against its `targets:` |
| `tools/smoke.mjs` | Headless Chrome playthroughs of the real page (console errors, dead ends) |
| `docs/adventure-format.md` | The YAML format, field by field |
| `docs/story-craft.md` | How to write a story that holds together: the lessons behind the skills |
| `.claude/` | Claude Code setup: skills `new-story` and `verify-story`, the `continuity-auditor` agent, writing rules |

## Commands

```bash
uv run pytest -q                                           # all tests
uv run ruff check . && uv run ruff format .                # lint and format
uv run gamebook check [site/adventures/<slug>.yaml]        # links, reachability, hooks, fair rolls (default: all)
uv run gamebook stats site/adventures/<slug>.yaml          # simulated playthroughs vs the story's targets
uv run gamebook edges site/adventures/<slug>.yaml          # every way into each section (for continuity work)
uv run gamebook assemble drafts/<slug>/ -o site/adventures/<slug>.yaml   # number a named-section draft
node tools/smoke.mjs http://127.0.0.1:8000/                # browser playthroughs (needs Chrome and a running server)
```

## Writing a new story

In Claude Code, run `/new-story`. It interviews you, plans the story bible and the section map, drafts with named
sections, assembles and numbers them, then hands over to `/verify-story`.

`/verify-story` runs the automated checks and has the `continuity-auditor` agent read every link. It then fixes the
findings and runs the auditor again to verify the fixes.

Without Claude, read `docs/adventure-format.md` and `docs/story-craft.md`, then use the commands above.

## Credits

This is an unofficial fan engine with no affiliation to Chaosium Inc. Call of Cthulhu is their trademark.
The rules are paraphrased in the spirit of the 7th edition: d100 roll-under, graded successes, Luck and Sanity.
All story text is original. H. P. Lovecraft's stories, quoted in places, are in the public domain.
