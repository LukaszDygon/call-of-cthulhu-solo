# Story craft

How to write a branching solo adventure that reads as one continuous story on every path.

These lessons come from writing *Fog Over Mercy Island*. A playtester read about 20% of its first draft (133
sections) and reported six seams. Two full audits of every link then found 63 more, including bugs that the first
round of fixes introduced. A later playtest found two more problems: a rescuer who doubted an island he had just
steered toward, and choices that all led the same way. The rework added side quests and quick endings (161
sections, 18 endings).

*A Fistful of Cows* (220 sections) added an open-world day (§1) and the last lesson in §4. Three audit passes
passed it, then a human playtester found work that never paid off where they reached for it: a confession nobody
would act on, a key that opened nothing until the final night, and a charm that only helped if a roll failed.
Every one of those hooks technically had a payoff.

The skills (`/new-story`, `/new-path`, `/verify-story`) and the `continuity-auditor` agent all work from this
document. Deliberate exceptions for one story go in `docs/story-log.md`.

## 1. Shape

- **Size:** about 120-140 sections for the main line, with an average playthrough of 20-30 sections. Side quests
  and quick endings (§2) can take it to 150-180. Paths branch and then reconverge. Set these as `targets:` so they
  are tested.
- **Rhythm:** about 30% short beats under 60 words (fight turns, roll outcomes, transitions). Add 5-8 long set
  pieces of 250-500 words, where a new place is described or a whole conversation happens. The rest sit around
  80-200 words.
- **Acts and hubs:** each act opens at a convergence section. Inside an act, offer 2-3 routes. A "night" hub
  where the reader picks one activity is a cheap way to add variety. A hub must never be a bottleneck that every
  playthrough walks through: give each act a route around it (§2).
- **Open-world days.** A town the reader can tour in any order makes a good investigation day. Use journal words
  as a clock (`NOON`, `LATE`): each hub sets the next word, and every place reachable at more than one hour gets
  paired exits gated on them. Keep the text of those places neutral about the hour, and clear the words at dusk.
  Make lingering cost something: two visits are safe, and a third means driving home in the dark.
- **Endings:** 6-10 main endings, plus the quick endings off the side branches (§2). Include at least:
  - a triumph earned through a long-range payoff
  - a plain escape
  - a bittersweet ending
  - a "claimed" ending (the reader joins the horror)
  - a lost ending
  - `on_death` and `on_madness`
- **Random runs are not players.** Triumphs can be rare in `gamebook stats` as long as a purposeful reader can
  reach them. Quick endings can be common in simulation for the same reason: a random reader takes every
  reckless option a real one would think twice about.

## 2. Choices that matter

A reader who feels that every choice leads to the same place stops believing in the choices. The first draft of
Mercy Island had nine endings, all of them in Act Four, and every playthrough walked through the same seven scenes
to get there. Its decisions changed a journal word here and there, then rejoined the main path one section later.

- **Every decision changes something.** Each option must differ from the others in at least one of:
  - where it leads: a different scene, a side quest or an ending
  - what it leaves behind: a journal word, an item or a companion's state that something later checks
  - what it risks: a different roll, cost or danger

  Options that lead to the same scenes and leave the same state are **cosmetic**. `gamebook choices` lists them,
  and the `cosmetic_choices` target (0.1 is a good default) fails the tests when there are too many.
- **Approaches are not decisions.** "Grab the rope" (STR) or "Call down to him" (Charm) lets each investigator
  play to their strengths, and that's good. But two approaches to the same outcome are **twins**: a decision made
  only of twins is cosmetic. Add an option that goes somewhere else ("Drop out of sight, and trail him home").
- **A divergence takes one of two shapes:**
  - **Side quest:** it leaves the main path for 2-6 sections somewhere new, then rejoins it **changed**. It
    carries back a journal word, an item or a companion's state that pays off later. In Mercy Island, a night in
    Halloway's hut can give the Closing Verse or the boathouse key. A sleepwalk toward the glowing glacier, fought
    off, teaches the safe moraine path for Act Three.
  - **Quick ending:** a very different ending, 1-3 sections from the choice. Make it **bizarre** (follow the
    footprints into the sea, and find a drowned church with Captain Brandt in the third row) or **wonderful**
    (slip through the reef by night with Jonah, before the tithe). When the reader was reckless, make it
    **scolding**: the narrator says plainly what they did wrong ("He asked you how many bullets you had. It was a
    fair question."). An early escape can scold too: "You found it. You left it before breakfast."
- **Every act needs both.** At least one quick ending or route that skips the act's hub, and at least one side
  quest. `gamebook choices` prints the sections every playthrough passes through: keep that list to the opening.
- **Offer a way back.** A side branch can offer the main path again ("Let him win. Turn inland after all"), so a
  reader who strays is not punished for curiosity. It also keeps the simulation honest: a reckless quick ending one
  click from a busy hub swamps the ending spread and drags the average path down. Give it a second step with a way
  out ("Tear up the receipt, and walk away").
- **Quick endings still need a proper ending.** Write them as carefully as the main ones, with a closing line that
  lands, and handle the companions who may be present.

## 3. Investigators and fair rolls

- Build 4-6 archetypes **for this scenario**. Each persona's skills fit who they are. Each needs at least three
  trained skills (40%+) that the story actually rolls.
- Every rolled skill must be trained by at least two archetypes. If only one archetype has it:
  - gate the choice behind it (`requires: {skill: Medicine, min: 50}`), or
  - roll a list that includes a characteristic (`skill: [STR, Climb]`).
- Use lists for broad tests: social `[Persuade, Charm, Fast Talk]`, physical `[STR, Climb]`, lore
  `[Occult, Anthropology, History]`.
- Give each archetype one path that is theirs. In Mercy Island:
  - the doctor treats the sick child
  - the folklorist borrows the hymnal
  - the photographer's camera gets proof
  - the guide's dynamite can seal the cave
- Every starting kit item should matter later.

## 4. Every hook pays off

- Every journal word that is noted must be checked somewhere, by a choice or an extra. Every item must be
  required somewhere or give a bonus. `gamebook check` warns about both.
- **Plant early, pay off late.**
  - A dory saved in the Act 1 shipwreck becomes an Act 4 escape.
  - A ledger stolen in Act 2 turns the finale.
  - Knowing a secret (TITHE) should unlock something: an easier roll, a new argument.
- **Character beats are hooks too.** If a companion promises "I've got your back", there must be a later scene
  where she acts on it. A line like "Mae sits closer to you than to anyone" with no payoff reads as a non sequitur.
- **Plot-critical changes must happen on every path.** If the climax needs Wren taken by the cult, every path
  into the climax must take him. That includes the path where the reader spent the day locked in an ice-house.
- **States must change behaviour downstream.** If the leader *releases* the party, nobody should chase them to the
  boats afterwards.
- **Pay off where the reader reaches for it.** Ask where a reader would *try* to use each thing they worked for,
  not just where you planned its payoff, and make each of those places work or say why it can't.
  - Evidence of a lie should stop what the lie set in motion. Show the gendarme the confession, and the false
    complaint is dealt with. Hold it at the climax, and the condemnation should not happen.
  - A key should open its lock as soon as the reader holds it, not only on the final night.
  - A charm given against a danger should work wherever that danger is met, not only after a failed roll.
- **One word, one meaning.** If a word is set in several places, every one must earn what its payoffs assume. If
  the climax says "she promised", every section that notes the word must show the promise.
- A section's own `effects` apply before its extras and choices. Never gate something in a section on state that
  the same section sets or clears (`note`, `unnote`, `gain`, `lose`; `gamebook check` warns). To change state on the
  way out, put the effect on the exit choices instead. A companion Sanity hit in a section's own effects can break
  someone before that section's `broken:` extras are read.

## 5. Continuity across every edge

The reader walks one path, but you are writing a graph. Read each edge (choice → target) as continuous prose.
`gamebook edges` lists every way into a section and the state that may already be set on arrival.

- **Time.** Keep a timeline. A choice that ends a day should say so ("Climb down before dark"). The next
  section must neither repeat a night nor skip one. If a rite is "at moonrise", walking times must fit. Don't open
  with "In the morning…" after a choice that was mid-afternoon.
- **Introductions.** Never name a place, person or object before the reader has met it **on every path** to
  that point.
  - "Take the book to the cooper's house" fails if the cooper's house hasn't been introduced yet.
  - "Break into the boathouse" fails for a reader who never learned there was one.
  - Introduce it in the section itself, or describe it instead of naming it.
- **Show what you refer back to.** "Hands still bloody from the boathouse door" needs the attempt on the page.
  Add a short bridging section.
- **Convergence sections** must fit every way in. Write the main text neutrally and put path-specific lines in
  `extra`. Use `before: true` when the line must come first.
- **Antecedents.** "She is the cutter *Haida*" fails on a path where no ship has appeared. Endings are reached
  from many places, so check them hardest.
- **Who saw what.** A character's knowledge and reactions must fit what they witnessed **on that path**. A cutter
  captain who picks up a boat at sea can doubt there was ever an island. The same captain, steering toward flares
  fired from the island's own headland, cannot. For every ending and rescue, ask where the reader physically is
  (on the island, at sea, bound, alone) and how they were found. When the answers differ, write separate scenes,
  or neutral text with extras.
- **Choices keep their promises.** "Call it murder, to her face" must lead to a confrontation, not a gentle plea.
- **No game logic in prose.** Not "in the dory, or a boat of their own if you had none". Split it into extras.
- **Where is everyone?**
  - If you fall into a crevasse alone, your companions must rejoin you on the page before they speak.
  - Someone who is bound cannot walk away, read aloud or take an arm until they are cut free.
  - If an ally walks with you, gate off the routes that would separate you.
- **Who has what?**
  - A confiscated knife stays gone, unless the text says nobody searched his boot.
  - An item handed over needs a `lose:` effect.
- **Companions may be broken or gone late in the story.** Don't give them dialogue or actions in shared text
  after the first point where they can break. Gate those lines with `with:` / `broken:` extras, or attribute them
  neutrally ("somebody whispers", or the investigator says it).
- **Extras render in list order.** Read each section with its worst combination of extras switched on. A line
  that closes a scene ("What do we do?") must come last. In any section with extras, and in every ending, put the
  closing line in a final always-on extra (one with no `requires`), so that no path-specific line can land after
  it.
- **Repetition.** Look for the same phrase in a section's first and last paragraph, or the same idea in two
  extras.

## 6. Facts and arithmetic

- Keep a bible table: every named character's age in the story year, birth year, relationships and key dates.
  **Do the arithmetic.** An 80-year-old in 1926 cannot be the great-granddaughter of a captain who was an adult
  in 1843. A man of 60 in 1926 was 15 in 1881.
- Count heads: "four survivors out of five" must match who was aboard. Count within a scene too: if one cow of
  fourteen is on the roof, thirteen stand in the ring.
- Picture every set piece. Cows standing nose to tail in a ring cannot all face inward.
- The narrator's claims are facts too. "Nobody will tell you why" is false once a character tells you.
- Fix the geography (the village north along the coast, the glacier inland), and make every route's text match it.
- One bell, in one place.

## 7. Sanity and danger

- **Investigator Sanity:**
  - unease: 0/1
  - horrors: 1/1D4 to 1/1D6
  - the reveal: 1/1D8 to 1D4/1D10
  - Losing 5+ at once is a bout of madness.
- **Companions:** start them at 15-20 Sanity, so one breaks in roughly a third of the runs that reach the climax.
  Give the reader ways to steady them: rest, brandy, Psychology. Track it with the `companion_break` target, and
  write what a broken companion looks like in later sections and endings. Work out the first point each companion
  can break from the harshest path, and work it out again after tuning Sanity for the target: tuning moves it.
- **Hit points:** falls and blades do 1D3-1D8. Death should be possible but rare, about 2-5% of random runs.

## 8. Sensitivity and sources

- Don't cast real peoples as cultists, as Lovecraft often did with non-white and Indigenous cultures. Use invented
  or settler communities (Mercy Landing descends from a lost 1843 sealing colony). Give them understandable motives
  and dissenters.
- Lovecraft's stories, such as *The Call of Cthulhu* (1928), are public domain and can be quoted. Chaosium's
  scenario text is not. Paraphrase mechanics and write all story text new.

## 9. Style

- Vivid pulp, in the second person and present tense. Short sentences, with no run-ons. Use concrete sensory
  detail rather than piling up adjectives, and save words like "eldritch" and "cyclopean" for when they land.
- Dialogue in period voice. Isolated communities speak an older English.
- No emojis.
- Choice text is one imperative line. In YAML, wrap it in double quotes and use single quotes inside.

## 10. The process that worked

1. **Interview:** theme, setting, length, archetypes, tone, sensitivities.
2. **Bible:** premise, backstory, a timeline with ages, the cast, places, an items and words table (set at / used
   at), the act outline and the endings.
3. **Section map** with named ids and every edge, before any prose.
4. **Draft act by act** in `drafts/<slug>/`, then `gamebook assemble`.
5. **Automated checks:** `gamebook check` (no errors, no warnings), `gamebook stats` (targets met) and
   `gamebook choices` (no cosmetic decisions, no bottlenecks after the opening).
6. **Continuity audit by a fresh reader** (the `continuity-auditor` agent) over every edge. Fix everything it
   finds.
7. **Second audit pass by the same agent** to verify the fixes. On Mercy Island this found 18 more problems,
   several introduced by the first round of fixes.
8. **Browser smoke test** (`node tools/smoke.mjs`), then a human playtest. Playtesters find what audits miss,
   above all effort that never pays off (§4). Fix what they find, then audit the changed sections again.
9. **Record the author's exceptions** to this guide in `docs/story-log.md`, so later audits don't undo them.

## Quick checklist

- [ ] `gamebook check`: 0 errors, 0 warnings. `gamebook stats`: all targets met, no dead ends.
- [ ] `gamebook choices`: no cosmetic decisions, and only the opening is shared by every playthrough. Each act has
  a side quest that comes back changed and a quick ending (bizarre, wonderful or scolding).
- [ ] Every character's reaction fits what they saw on that path. Every ending fits where the reader is.
- [ ] Timeline and ages add up. Head counts and geography are consistent.
- [ ] Each noted word and each item changes something later. Each character promise pays off.
- [ ] Everything the reader works for works where they would reach for it, and the endings respect it.
- [ ] Set pieces are physically possible, and their counts agree.
- [ ] Each convergence section reads right from every way in (`gamebook edges`).
- [ ] No place, person or object is named before every path has introduced it.
- [ ] Time of day is continuous across every edge.
- [ ] Bound, separated, released and captive states are respected downstream.
- [ ] Companions don't act normally where they may be broken. Endings handle `with`, `broken` and `gone`.
- [ ] Extras read in the right order with the worst combination switched on.
- [ ] No real culture cast as the cult. All text original.
