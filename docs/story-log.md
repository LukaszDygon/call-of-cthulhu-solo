# Story log

Decisions about published stories that the checks or `docs/story-craft.md` would otherwise flag. Read the entry for
a story before you "fix" one of these during `/verify-story` or a rework. Newest entries first.

## A Very American Dream (`site/adventures/american-dream.yaml`)

**2026-10-28, after the first playtest: no more than five choices on a screen, and every beat is followed
through.** The author found screens with up to nine options, and dramatic beats (the phone call at the start) with
nothing on the next screen. Keep both rules when you add to the story.

- **At most five visible choices.** Crowded screens were split at a natural fork into a short follow-on screen:
  - Midnight's allies → 375
  - the hut's song and stopping it → 376/377
  - Sweetwater's front and back gates → 378/379
  - the salt's song → 380
  
  At the dish and the salt, taking the tab replaces opening your arms, since both lead to the same end. The refusal
  moved from The Retainer to Mrs. Voss. KSUN left the morning list but stays at noon and 3:30. Friday lost its
  north road, which 238 still offers.
- **Follow-through bridges (373-374, 381-408):** a chase, a capture, a gunshot or a failed roll now gets a line on
  screen before the story moves on. The random-run madness rate fell to about 1.5%, because the merged hinge
  choice is offered once instead of twice. A reader who chases the dream still goes mad about half the time.

Numbers after the playtest fixes: 408 sections, about 25,000 words, an average path of 34.2, 0 cosmetic decisions,
about 8% death and 1.5% madness in random runs. By kind of reader, a careful one dies 0% of the time, a reckless one
70%, and one who chases the dream goes mad 49%. All `targets:` were met, with `sections` raised to [380, 420].

**2026-10-28: written to the author's brief, with these departures from story-craft.** All were settled in the
`/new-story` interview, or in tuning afterwards. Leave them alone unless the author asks again.

- **Solo (story-craft §7):** there are no companions. Bix, Owen, Agnes and Ruiz are journal words (BIX, OWEN, AGNES,
  RUIZ, CRUISER, VAN), as in Innsmouth. There's no `companion_break` target.
- **Length (§1):** the author asked for "about 300 screens" with an average play of 40. The approved map came to 305
  sections. Drafting, a third Wednesday visit, the audit bridges and the death scenes took it to 372.
- **Path target:** a playthrough that reaches a main ending averages about 40 sections. Random runs average about 34,
  because they also take the quick endings and the three-strikes Spat Out endings. That's why `path_mean` is
  [32, 42]. Don't pad the story to push the random mean up.
- **The core rule is the author's:** going along with the weirdest thing raises Luck and costs a little Sanity.
  Refusing a coincidence notes SNAG, then SNAG2, and a third refusal in one act ends the story (Bakersfield,
  Barstow, Needles). The triple copies of each resist choice are deliberate.
- **Madness and death come from choices, not dice (§7).** These are the author's rules. They superseded the first
  draft, where madness was near zero and death came almost only from falls at the dish.
  - *Madness* is embracing life in the dream "experientially forever". Choices that go deeper than the coincidences
    ask cost fixed Sanity, not rolls:
    - the punch, Sol's pool, conducting the Bowl and walking on the still sea: -8 each
    - the tar vision and the headsets: -10
    - a Daybreak tab: -15
    - a tab or open arms at the hinge (346, 367): -30
    A reader who chases the dream goes mad.
  - *Death* comes from fighting overwhelming odds or stupid stunts:
    - ramming the grey car (368): -6 HP
    - fighting the Hollow men: -8 (369, which also notes LISTENERS) and -8 (370)
    - rushing the guarded gate (371): -11
    - going for Calloway's gun (372): -9
    These kill a reader who is already hurt. The gate kills almost anyone. Every second refusal of the city in an act
    also costs 1 HP. The dice-only falls and shocks at the dish were softened to 1D6.
  - *Simulated by kind of reader:*
    - careful, going along: 0% death, 1% madness, 10% triumph
    - reckless: 65% death
    - chasing the dream: 48% madness, 36% claimed
    - random: about 9% death and 3% madness
  - Death is above the guide's 2-5% because random readers take the suicidal options as often as any other. Don't
    soften the fights to bring the random number down.
- **Fake coincidences (Acts 3-4):** the author approved grey, silent fakes that lead into Helion's hands. The tell is
  planted in Act 2 (GREY), and it warns at each fake.
- **Three lines, no trunk:** the Current, the Straight World and Helion's Side. Revision 2 of the map was rebuilt on
  them at the author's request, so that no scene after the opening is one every reader must see.

Numbers at the time: 372 sections, about 23,900 words, an average of about 64 words of main text per screen, 157
decisions (0 cosmetic), 25 endings (23 reached in random simulation), about 9% death and 3% madness in random runs.
All `targets:` were met.

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
