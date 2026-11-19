# Notes for working on Slashcraft

Slashcraft is a kid-friendly guide to Minecraft commands for Java and Bedrock. The reader is a child who plays **Bedrock on Xbox** and **Java on Windows** and knows nothing about commands. Every word they see must be plain, short and friendly.

## Files

- `index.html`: the whole app, including the beginner and command-block lessons. Lesson text marked `data-ed="j"` or `data-ed="b"` is shown only for that edition.
- `data/commands-data.json` and `data/entities-data.json`: **generated** by `scripts/update.sh`. Never edit them by hand.
- `data/content.json`: hand-written explanations, one entry per command. The format is in the README.
- `data/entities.json`: hand-written kind/name/note for every entity. The format is in the README.
- `data/filters.json`: hand-written selector filter reference (both editions), recipes, and kid descriptions of Java entity tags and Bedrock families.

## Updating for a new release

1. Run `scripts/update.sh` (or `--force`). Exit code 2 means new commands or entities have no entry yet.
2. For every new command, and every command whose `syntax` changed in the diff of `data/commands-data.json`, research it first: minecraft.net / feedback.minecraft.net release notes, Microsoft Learn's Bedrock command reference, and minecraft.wiki.
3. Add or fix entries in `data/content.json`. Every example must match the syntax in `commands-data.json` for its edition (`limit=1,sort=nearest` / `distance=..10` on Java, `c=1` / `r=10` on Bedrock; `/effect give` on Java, `/effect` on Bedrock; gamerule, sound and particle names differ).
4. Add any new entity to `data/entities.json`. If Java and Bedrock spell its ID differently, add the pair to `B2J` in `scripts/build_entities.py` and rerun the update. Check release notes for new or changed selector filters and update `data/filters.json`.
5. `python3 scripts/check_coverage.py data/commands-data.json data/content.json` and `python3 scripts/check_entities.py data/entities-data.json data/entities.json` must both pass.
6. Test locally with `python3 -m http.server` and check both editions, including the Filters builder and Mobs tab.

## Rules

- No ads, trackers, analytics, or calls to outside servers except Google Fonts.
- Keep it a static site that works on GitHub Pages with no build step.
- Don't copy text from the Minecraft Wiki or other sites. Write explanations fresh.
