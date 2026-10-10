# Story log

Decisions about published stories that the checks or `docs/story-craft.md` would otherwise flag. Read the entry for
a story before you "fix" one of these during `/verify-story` or a rework. Newest entries first.

## The Last Bus from Innsmouth (`site/adventures/innsmouth.yaml`)

**2026-10-10: short screens, at the author's request.** After playing it, the author found the text far too long,
with scenery on almost every early screen. The story was trimmed from about 28,000 words of main text to 17,500, and
nine long scenes were split into two screens with a decision between them. Don't grow the descriptions back.

- **Rhythm (story-craft §1):** about 44% of sections are short beats under 60 words, against the guide's ~30%. No
  set piece runs past about 230 words, against the guide's 250-500. A place gets a sentence or two the first time
  you see it, and the scene then moves on to the person, the choice or the danger.
- Numbers after the trim: 241 sections, about 80 seen words per screen (72 in the early game), and an average
  playthrough of about 34 sections, or roughly 2,900 words.

**2026-10-07: solo, and long, by the author's choice.** Both were decided in the `/new-story` interview and the
first stats run. Leave them alone unless the author asks again.

- **No companions (story-craft §7):** the reader goes alone, as Lovecraft's narrator did. Allies (Eddie, Zadok, Ruth
  and Jonas, Shea) travel with you only as journal words (RUTH, BOAT). There is no `companion_break` target, and
  the engine hides the party panel for a story without `companions`.
- **Length (story-craft §1):** the author asked for "around 200 screens" and an average path of 30-40, then chose
  the path over the screen count. The day has five visits (arrival, 1:00, 2:30, 4:00 and 6:00), and the story runs
  to 232 sections against the guide's 150-180.
- **Source:** adapted from *The Shadow over Innsmouth* (public domain). In Lovecraft an island people teach Obed
  the rite. Here the island was already empty (story-craft §8), and the town has dissenters (Ruth Eliot) alongside
  Zadok.

Numbers at the time: 232 sections, about 28,000 words of main text, an average playthrough of 32.4 sections, 22
endings (21 reached in simulation), and deaths in about 4% of runs. All `targets:` were met.

## A Fistful of Cows (`site/adventures/fistful-of-cows.yaml`)

**2026-10-04: rhythm and death rate accepted as they are.** The author reviewed both after the first playtest and
decided they suit this story. Leave them alone unless the author asks again.

- **Rhythm (story-craft §1):** 17 short beats under 60 words, or about 8% of 220 sections, against the guide's
  ~30%. There are 13 long set pieces over 250 words, against 5-8. The story is a wry, talkative western pastiche,
  and its scenes run long on purpose.
- **Death rate (story-craft §7):** under 1% of simulated runs end in death, against the guide's 2-5%. The danger in
  this story is losing the farm or yourself to the dream, not dying. Madness, the lost endings and the "into the
  dream" endings carry that weight.

Numbers at the time: 220 sections, 30,874 words, an average playthrough of 31.1 sections, 18 endings, and a
companion break in 16% of runs. All `targets:` were met.
