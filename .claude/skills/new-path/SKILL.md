---
name: new-path
description: Adds a new branch to an existing adventure in site/adventures/. The branch is either a side quest that leaves the main path and rejoins it changed, or a quick alternative ending (bizarre, wonderful, or scolding for a reckless choice). It finds or confirms where to branch, designs the branch against every way in and the state it carries, writes numbered sections into the published file, then verifies them. Use when the user wants more variety, a new route, a side quest or a new ending in a story that already exists.
---

# New Path

Grows a finished story without breaking it. The branch must change something (story-craft §2) and fit every path
into the place where it leaves (story-craft §5).

## Arguments
- `slug` or a path to the adventure (default: the most recently changed file in `site/adventures/`)
- optionally, the idea: where it leaves, what happens, how it ends

## Before anything

Read `docs/story-craft.md` (§2 and §5 most of all) and `docs/adventure-format.md`. The numbered file is the source
of truth. There is no draft to go back to, so edit it directly.

## Workflow

### 1. Find where to branch
```bash
uv run gamebook choices site/adventures/<slug>.yaml --all
uv run gamebook stats site/adventures/<slug>.yaml
```
Good places to branch:
- a cosmetic decision, or one with twins
- a section that every playthrough passes through (a bottleneck)
- a single-choice section in the middle of an act
- an act with no quick ending or no side quest

If the user brought an idea, check it against these. If not, propose 2-4 branches with AskUserQuestion,
recommended first. Each one says where it leaves, its shape (side quest or quick ending), and what it changes.

### 2. Read the ground
```bash
uv run gamebook edges site/adventures/<slug>.yaml --section <leaves-from> <rejoins-at>
```
Read the section the branch leaves from, the section a side quest rejoins, and every way into both. Note:
- the time of day, and where everyone is (present, bound, broken or gone)
- which journal words and items may be held on arrival
- what each person in the scene has witnessed on each path. A rescuer can only react to what they saw.

### 3. Design the branch
Write a short plan, and get the user's approval before writing prose:
- **Shape:**
  - **side quest:** 2-6 sections, rejoining at a section whose text fits the new way in. It must carry something
    back: a journal word, an item or a companion's state, with a named section downstream where it pays off. If
    nothing downstream can use it, add the payoff (a choice or an extra) too.
  - **quick ending:** 1-3 sections. Bizarre, wonderful, or scolding when the choice was reckless.
- **The choice that leads there:** one imperative line, offered beside the existing options. It must promise what
  the branch delivers. Gate it with `requires` when only some readers should see it.
- **A way back:** a side branch can offer the main path again, so curiosity isn't punished.
- **Plot-critical state:** if the main path later needs something to have happened (a companion taken, an item
  lost), the branch must make it happen too, or rejoin before it.
- **New words and items:** each one with where it is set and where it pays off. Also list where a reader would
  *try* to use it (story-craft §4), and make those places work too.
- **Introductions:** every person, place or thing the branch names must be introduced on every path into it, or
  described instead of named.

### 4. Write it
- New sections take the next free numbers and go in the file beside the section they leave from. A side quest
  rejoins with `to:` an existing section.
- Apply the edits as a Python patch script of exact-match replacements that asserts each match count, as
  `/verify-story` does, so a silent non-match can't slip through.
- Write for every way in: neutral main text, path-specific lines in `extra`. Endings handle the companions who may
  be present (`with`, `broken`, `gone`).
- Style as in story-craft §9. In a scolding ending, the narrator names the reckless thing plainly, and the last line
  lands.
- If existing sections now read wrongly from the new route (they name a place this route never saw), fix them in
  the same patch.
- If the branch takes the story past its `targets:` (sections, endings reached), update them and tell the user.

### 5. Check
```bash
uv run gamebook check site/adventures/<slug>.yaml     # 0 errors, 0 warnings
uv run gamebook choices site/adventures/<slug>.yaml   # the decision you branched from is no longer cosmetic
uv run gamebook stats site/adventures/<slug>.yaml     # targets met, and the new ending is reached
uv run pytest -q
```

### 6. Verify
Run `/verify-story <slug>`. Tell the auditor which sections are new, which existing sections changed, and which
convergence sections gained a way in.

### 7. Report
Give:
- the new sections, and the choice that leads to them
- the branch's shape, what it carries back and where that pays off
- the `choices` and `stats` numbers, before and after
