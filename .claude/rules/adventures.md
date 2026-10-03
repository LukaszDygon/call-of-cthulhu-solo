---
paths:
  - "site/adventures/**"
  - "drafts/**"
---

# Writing adventures

The full guides are `docs/story-craft.md` (how to write) and `docs/adventure-format.md` (the YAML). These are the
rules people break most often:

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
- **After editing:** run `uv run gamebook check` (0 errors, 0 warnings) and `uv run pytest -q`. For anything beyond
  a typo, run `/verify-story`.
