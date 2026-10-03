# Adventure format

An adventure is one YAML file in `site/adventures/`, listed in `site/adventures/index.yaml`.
The engine (`site/app.js`) reads it in the browser. The toolkit (`gamebook/`) checks it and simulates it.
Keep this document, the engine and `gamebook/simulate.py` in step: they describe the same rules.

## Top level

| Key | Meaning |
| :--- | :--- |
| `id`, `title`, `series`, `subtitle` | Names shown on the cover (`series` is the small kicker line) |
| `blurb` | Cover text; paragraphs separated by blank lines |
| `investigator_intro` | One line above the investigator picker |
| `targets` | Optional shape the story is tested against (see below) |
| `start` | First section number |
| `on_death`, `on_madness` | Ending sections the engine jumps to when HP or Sanity reaches 0 |
| `bouts` | Short lines picked at random for a bout of madness (losing 5+ Sanity at once) |
| `skills` | Base chance for every skill the story rolls (untrained value) |
| `investigators` | The playable characters (below) |
| `companions` | Non-player party members with their own Sanity (below) |
| `items` | `id: {name, text, bonus: [skills]}`. `bonus` grants a bonus die on those skills while carried |
| `journal` | `WORD: text`. Words the reader notes, shown with their text in the journal |
| `sections` | Numbered sections (below) |

### `targets`

```yaml
targets:
  sections: [120, 140]        # total section count
  path_mean: [20, 30]         # average sections per simulated playthrough
  companion_break: [0.1, 0.5] # share of runs in which a companion breaks
  endings_reached: 8          # distinct endings reached in simulation
```

`uv run gamebook stats` and `tests/test_adventures.py` fail when a target is missed.

### Investigators

```yaml
- id: guide
  occupation: Alaska Guide
  name: Sadie Burke
  age: 41
  bio: One or two sentences. *Italics* and **bold** work.
  characteristics: {STR: 65, CON: 75, SIZ: 55, DEX: 60, APP: 45, INT: 60, POW: 55, EDU: 45}
  hp: 13          # (CON + SIZ) / 10, rounded down
  san: 55         # usually POW
  luck: 55
  skills: {Survival (Arctic): 75, Track: 60}   # trained skills only; others use the base chance
  kit: [rifle]    # item ids they start with
```

`Dodge` defaults to DEX / 2. A skill counts as **trained** at 40 or more.

### Companions

```yaml
- id: mae
  name: Mae Tolliver
  short: Mae          # used in messages and tags
  role: One line shown on the sheet.
  san: 18             # low on purpose: companions should be able to break
  breaks: What the reader sees when this companion's Sanity hits 0.
```

A companion's status is `with` (the default), `broken` (still there, but mad), `lost` or `dead`.
At 0 Sanity the engine sets `broken`.

## Sections

```yaml
sections:
  41:
    title: Lances in the Fog
    effects: [...]      # applied on entering; their results show BELOW the text
    text: |
      Paragraphs separated by blank lines. *italic*, **bold**.
    extra:              # optional paragraphs, shown when `requires` holds
      - requires: {note: JONAH}
        text: Jonah steps out from behind you.
      - requires: {no_note: MAE}
        before: true    # shown BEFORE the main text
        text: ...
      - text: An extra with no requires always shows, so text can continue after conditional lines.
    choices: [...]      # none for an ending
    ending: escape      # marks an ending; any word (triumph, escape, bittersweet, lost, madness, death...)
```

Order of display: outcome of the roll that led here → `before` extras → text → other extras (in list order) →
effect results → choices.

Effects apply **before** extras and choices are evaluated. A condition on state that the same section sets is
always true (or always false). `gamebook check` warns about it.

### Choices

```yaml
- text: "Go up on deck and listen."
  to: 2
- text: "Climb the headland."
  requires: {no_note: ALLY}
  effects: [{gain: rope}]          # applied when the choice is taken, before any roll
  roll: {skill: Climb, difficulty: hard, success: 26, failure: 27, fumble: 28, bonus: 1}
```

- `skill` may be a list. The investigator rolls their best.
- `difficulty` is `regular` (skill), `hard` (half) or `extreme` (a fifth).
- `bonus` adds bonus dice; negative values add penalty dice.
- A fumble is 100, or 96+ when the skill is under 50. It goes to `fumble` if given, else `failure`.
- The reader may spend Luck to turn a failed non-fumble roll into a pass, point for point (not on Luck rolls).
- Tags shown on a choice come from its positive `requires` (an item name, `Journal: WORD`, a skill, a companion).

### Effects

| Effect | Meaning |
| :--- | :--- |
| `san: "1/1D4"` | Sanity roll: lose 1 on a pass, 1D4 on a fail. Losing 5+ at once triggers a bout of madness (penalty die on the next roll) |
| `san: "-2"`, `san: "+1D3"` | Straight change |
| `hp: "-1D6"`, `luck: -5` | Straight changes |
| `gain: id`, `lose: id` | Items |
| `note: WORD`, `unnote: WORD` | Journal words |
| `companion: mae` (or `all`) + `san: ...` | Companion Sanity (a roll if it has `/`). `all` means every companion still `with` you |
| `companion: wren` + `status: lost` | Set a companion's status |

### Conditions (`requires`)

A single condition, or a list (all must hold), or `{any: [...]}`. A map with several keys means all of them.

| Condition | Holds when |
| :--- | :--- |
| `item: id` / `no_item: id` | carrying / not carrying |
| `note: WORD` / `no_note: WORD` | noted / not noted |
| `with: mae` | companion is present and sane |
| `broken: mae` | companion is present but broken |
| `gone: wren` | companion is lost or dead |
| `skill: Medicine` + `min: 50` | investigator's skill is at least `min` (default 50) |
| `investigator: [doctor, guide]` | playing one of these |

## Drafting with names

Write drafts in `drafts/<slug>/` using names instead of numbers (`the-reef:` and `to: the-reef`).
Split the parts by act (`1-header.yaml`, `2-act-one.yaml`, ...). Then run
`uv run gamebook assemble drafts/<slug>/ -o site/adventures/<slug>.yaml`.
Sections are numbered in file order. The numbered file becomes the source of truth and `drafts/` is git-ignored.
