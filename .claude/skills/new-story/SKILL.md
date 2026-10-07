---
name: new-story
description: Writes a new solo adventure from interview to a numbered, checked YAML file in site/adventures/. Covers the interview, the story bible (timeline, cast with ages, places, items and journal words with their payoffs, and each act's side quests and quick endings), a named section map where every decision changes something, drafting act by act, and assembly. It then hands over to /verify-story. Use when the user wants a new story or adventure. To add a branch to an existing story, use /new-path instead.
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
- Never copy Chaosium scenario text. Don't make a real people the cult (story-craft §8).
- **Choices must matter** (story-craft §2). No decision may be cosmetic. Every act gets at least one side quest
  that rejoins the main path changed, and one quick ending that is bizarre, wonderful or, for reckless choices,
  scolding.
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
- **Companions:** starting Sanity, what "broken" looks like, and the first point where they can break. Work that
  point out from the harshest path, and again after you tune Sanity for the target.
- **Items and journal words:** id, where set, where used, the payoff. Nothing without a payoff. Also list every
  place a reader would *try* to use each one: showing the confession to the gendarme, taking the key to its lock,
  wearing the charm into the danger. Each must work, or the text says why not (story-craft §4).
- **Acts:** a time-of-day timeline for each act, its hubs and convergence points.
- **Divergences:** for each act, its side quests (where they leave, what they carry back, where that pays off) and
  its quick endings (the choice that leads there, and whether the ending is bizarre, wonderful or scolding). Give
  each act a route around its hub, so no scene after the opening is one that every reader must see.
- **Endings:** each one, how it is reached, and **where the reader is** when it happens (on the island, at sea,
  captive). Write a separate ending, or extras, for each place: a rescuer reacts only to what they saw on that
  path.

Summarise the bible for the user and get approval.

### 3. Section map: `drafts/<slug>/map.md`
One line per section, with named ids:

`id | title | beat or set piece | exits (choice → target, success/failure) | sets | requires`

Mark every **convergence section** (3+ ways in). For each one, note its incoming states and plan neutral main
text plus `extra` lines. Mark places reachable at more than one time of day (story-craft §1, open-world days):
keep their text neutral about the hour, and pair their exits on the clock words.

Mark every **decision** (2+ options open together) with its kind, and what each option changes:
- **fork:** an option can end the story differently
- **side quest:** an option has its own route of 3+ sections before rejoining
- **flavour:** the options rejoin quickly but leave different state that something later checks

No option may be a twin of another unless the decision also offers somewhere else to go. A decision made only of
twins is cosmetic: the choice changes nothing.

Estimate the average path and confirm every hook in the bible has its payoff edge. Show the user the act structure,
with its side quests and quick endings, and get approval.

### 4. Draft
- `drafts/<slug>/1-header.yaml`: the top level and the `targets:` block, ending with `sections:`.
- `drafts/<slug>/2-act-one.yaml`, `3-act-two.yaml` and so on: sections keyed by named id. Links use names
  (`to: the-reef`).
- Write one act per pass. Before writing each section, list its ways in from the map, and write for all of them
  (story-craft §5). Keep companion dialogue out of shared text once they can break.
- Mix short beats with 5-8 long set pieces (story-craft §1).
- In any section with extras, and in every ending, put the closing line in a final always-on extra.
- YAML: write any `text:` that contains `: ` as a block scalar (`text: |`), and keep one `extra:` key per section.
  If the default companion fates (came through, broken in mind, lost, dead) don't fit, set `fates:` in the header.
- Write quick endings with the same care as the main ones. A scolding ending names the reckless thing plainly, in
  the narrator's voice ("He asked you how many bullets you had."). Handle the companions who may be present.

### 5. Assemble and check
```bash
uv run gamebook assemble drafts/<slug>/ -o site/adventures/<slug>.yaml
uv run gamebook check site/adventures/<slug>.yaml     # 0 errors, 0 warnings
uv run gamebook stats site/adventures/<slug>.yaml     # all targets met, no dead ends
uv run gamebook choices site/adventures/<slug>.yaml   # no cosmetic decisions; bottlenecks only in the opening
```
- Put `cosmetic_choices: 0.1` in the `targets:` block, so the tests fail if decisions go cosmetic.
- If `choices` lists a bottleneck after the opening, give that act a route around it.
- Add `- file: <slug>.yaml` to `site/adventures/index.yaml`.
- Iterate on the drafts and re-assemble until check and stats are clean. Then run `uv run pytest -q`.
- The tests check `targets:` with 300 runs per investigator, while `stats` uses 400. Leave a margin (a section or
  two of average path, a few points of companion breaks) so the tests don't fail at random.

### 6. Verify
Run `/verify-story <slug>`. Don't call a story done before its continuity audit.

### 7. Report
Report the section count, word count, average path, endings, the stats targets, and where to play it. If the
author accepts a departure from story-craft (rhythm, death rate, length), record it in `docs/story-log.md`.
