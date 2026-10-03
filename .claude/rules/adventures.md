---
paths:
  - "site/adventures/**"
  - "drafts/**"
---

# Writing adventures

The full guides are `docs/story-craft.md` (how to write) and `docs/adventure-format.md` (the YAML). These are the
rules people break most often:

- **Every choice changes something:** where it leads, what it leaves behind, or what it risks. Two options that
  reach the same scenes with the same state are cosmetic. Approaches (same outcome, different skill) are fine only
  beside an option that goes somewhere else. Check with `uv run gamebook choices <file>`.
- **Diverge properly.** A side quest rejoins the main path changed (a word, an item or a companion's state that pays
  off). A quick ending is short and very different: bizarre, wonderful, or scolding when the reader was reckless.
  Every act gets one of each. Nothing after the opening should be a scene every playthrough must pass through.
- **Who saw what.** A character reacts only to what they witnessed on that path. A captain who answered flares
  fired from the island can't doubt the island exists. Check endings and rescues for where the reader is.
- **Fit every way in.** A section reached from several places gets neutral main text. Path-specific lines go in
  `extra` (`before: true` to put one first). Check with `uv run gamebook edges <file> --section N`.
- **Time is continuous.** A choice that ends a day says so. Never repeat or skip a night.
- **Introduce before naming.** No place, person or object appears in a choice or text before every path to it has
  met it.
- **Every hook pays off.** Each journal word and item is used later. Each character promise gets its scene.
- **Respect state.** Plot-critical status changes happen on every path. Bound people can't act. Released isn't fled.
  Confiscated items stay gone (`lose:`).
- **Companions can break.** Late shared text doesn't give them lines. Gate those with `with:` / `broken:`.
- **No condition on state that the same section's `effects` set:** effects apply first.
- **Do the arithmetic** on ages and dates in the story year.
- **Style:** pulp, second person, present tense, short sentences, no emojis. Choice text is one quoted imperative
  line.
- **After editing:** run `uv run gamebook check` (0 errors, 0 warnings), `uv run gamebook choices` and
  `uv run pytest -q`. For anything beyond a typo, run `/verify-story`. To add a branch to a finished story, use
  `/new-path`.
