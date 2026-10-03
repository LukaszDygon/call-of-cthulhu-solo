---
name: new-story
description: Writes a new solo adventure from interview to a numbered, checked YAML file in site/adventures/. Covers the interview, the story bible (timeline, cast with ages, places, items and journal words with their payoffs), a named section map, drafting act by act, and assembly. It then hands over to /verify-story. Use when the user wants a new story or adventure.
---

# New Story

Turns a premise into a published adventure that holds together on every path.

## Before anything

Read `docs/story-craft.md` and `docs/adventure-format.md`. They are the rules. Open
`site/adventures/mercy-island.yaml` as the worked example of the header, investigators, companions, items, journal
and section style.

## Rules

- **The premise is the user's.** Ask; don't invent the theme, setting or antagonist. You may offer options marked
  as suggestions. Get approval for the bible and for the section map before writing prose.
- Never copy Chaosium scenario text. Don't make a real people the cult (story-craft §7).
- Leave `site/app.js` alone. If the format truly can't express something, propose the engine change first. If it's
  approved, change `site/app.js`, `gamebook/simulate.py` and `docs/adventure-format.md` together.
- Drafts live in `drafts/<slug>/`, which is git-ignored. After the first `/verify-story`, the numbered file is the
  source of truth, so edit only that.

## Workflow

### 1. Interview
Use AskUserQuestion, at most four questions per round, with a recommended option first. Settle:
- setting, era and premise
- the community and its secret (check sensitivity)
- length: sections and average playthrough (default 120-140 and 20-30)
- 4-6 investigator archetypes
- companions: who they are and how fragile (default Sanity 15-20)
- tone and prose style
- the endings wanted

Re-ask only what is still unclear.

### 2. Bible: `drafts/<slug>/bible.md`
- Premise, backstory and a **dated timeline**.
- **Cast table:** name, role, age in the story year, birth year, relationships, the section where the reader
  first meets them. Do the generation arithmetic now.
- **Places:** fixed geography, and where each place is first introduced.
- **Investigators:** a skills table plus a coverage matrix of rolled skills × archetypes. Every rolled skill
  must have 2+ trained archetypes, or be gated. Each archetype needs 3+ useful skills and one path of their own.
- **Companions:** starting Sanity, what "broken" looks like, the first point where they can break.
- **Items and journal words:** id, where set, where used, the payoff. Nothing without a payoff.
- **Acts:** a time-of-day timeline for each act, its hubs and convergence points.
- **Endings:** each one and how it is reached.

Summarise the bible for the user and get approval.

### 3. Section map: `drafts/<slug>/map.md`
One line per section, with named ids:

`id | title | beat or set piece | exits (choice → target, success/failure) | sets | requires`

Mark every **convergence section** (3+ ways in). For each one, note its incoming states and plan neutral main
text plus `extra` lines. Estimate the average path and confirm every hook in the bible has its payoff edge. Show the
user the act structure and get approval.

### 4. Draft
- `drafts/<slug>/1-header.yaml`: the top level and the `targets:` block, ending with `sections:`.
- `drafts/<slug>/2-act-one.yaml`, `3-act-two.yaml` and so on: sections keyed by named id. Links use names
  (`to: the-reef`).
- Write one act per pass. Before writing each section, list its ways in from the map, and write for all of them
  (story-craft §4). Keep companion dialogue out of shared text once they can break.
- Mix short beats with 5-8 long set pieces (story-craft §1).

### 5. Assemble and check
```bash
uv run gamebook assemble drafts/<slug>/ -o site/adventures/<slug>.yaml
uv run gamebook check site/adventures/<slug>.yaml     # 0 errors, 0 warnings
uv run gamebook stats site/adventures/<slug>.yaml     # all targets met, no dead ends
```
- Add `- file: <slug>.yaml` to `site/adventures/index.yaml`.
- Iterate on the drafts and re-assemble until check and stats are clean. Then run `uv run pytest -q`.

### 6. Verify
Run `/verify-story <slug>`. Don't call a story done before its continuity audit.

### 7. Report
Report the section count, word count, average path, endings, the stats targets, and where to play it.
