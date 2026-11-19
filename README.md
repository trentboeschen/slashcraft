# Slashcraft

**Every Minecraft command, explained for kids.** Slashcraft is a small, free browser guide for young players who are starting to type commands. It covers every command in both editions and teaches command blocks step by step.

- **Java (PC) and Bedrock (Xbox, Switch, PlayStation, tablets, Windows):** one switch at the top changes every example to the right edition.
- **Start here:** short lessons for complete beginners. They cover turning on cheats, opening chat, reading a command, `@p` / `@a` / `@e`, filters, coordinates and `~`, and fixing errors.
- **All commands:** search, categories, difficulty stars, plain explanations, copyable examples, and the official syntax.
- **Command blocks:** Impulse, Chain and Repeat blocks, Conditional blocks, `/execute` built up one piece at a time, and six projects with exact settings.
- **Hide what you know:** fold away lessons once they've sunk in, or turn off the beginner reminders.

No ads, no tracking, no accounts. Settings are saved only in your own browser.

## Where the command data comes from

The command lists and syntax come straight from Mojang's own game files, not from a wiki:

| Edition | Source | Updated |
|---|---|---|
| Java | [misode/mcmeta](https://github.com/misode/mcmeta): the command tree exported by the game's built-in data generator, for the latest **stable** release | Every release |
| Bedrock | [Mojang/bedrock-samples](https://github.com/Mojang/bedrock-samples): `metadata/command_modules/mojang-commands.json`, published by Mojang | Every release |

The kid-friendly explanations, examples and lessons are written by hand. They live in [`data/content.json`](data/content.json) and [`index.html`](index.html).

## Project layout

```
index.html                 The whole app (HTML, CSS and JS in one file). Lessons are written here.
data/commands-data.json    Generated. Official command list + syntax for both editions. Don't edit by hand.
data/content.json          Hand-written. One entry per command: explanation, examples, tips.
scripts/update.sh          Downloads the latest official data and rebuilds commands-data.json.
scripts/build_data.py      Turns Mojang's raw command data into commands-data.json.
scripts/check_coverage.py  Lists any command that has no entry in content.json.
.github/workflows/         Data checks on every push, plus a weekly check for new Minecraft releases.
```

## Running it locally

The page loads its data with `fetch`, so open it through a local web server rather than double-clicking the file:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Publishing with GitHub Pages

1. Go to **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**, then pick **main** and **/ (root)**.
3. The site will be live at `https://trentboeschen.github.io/slashcraft/` in a minute or two.

## Updating for a new Minecraft release

**Automatic:** the *Check for new Minecraft commands* workflow runs every Tuesday. When Java or Bedrock gets a new release, it opens a pull request with the refreshed data. To let it open pull requests, turn on **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**. You can also run it any time from the **Actions** tab.

**By hand:**

```bash
scripts/update.sh          # rebuilds only if a new release is out
scripts/update.sh --force  # rebuild anyway
```

If it reports **missing explanations**, add an entry for each new command to `data/content.json`:

```json
"newcommand": {
  "cat": "fx",
  "lvl": 2,
  "kid": "One plain sentence a 9-year-old understands.",
  "ex": [
    ["both", "/newcommand @s", "What this example does, in kid words."],
    ["j", "/newcommand @s java_only_way", "Java-only example."],
    ["b", "/newcommand @s bedrock_way", "Bedrock-only example."]
  ],
  "tip": "Optional extra help.",
  "block": "Optional: how it's useful in a command block."
}
```

- **cat:** `move`, `items`, `build`, `mobs`, `world`, `chat`, `fx`, `logic`, `admin` or `tools`.
- **lvl:** `1` Starter, `2` Builder, `3` Expert. Expert commands are hidden unless the reader turns them on.
- **Examples** must work when copied exactly. Remember the edition differences: Java uses `limit=1,sort=nearest` and `distance=..10`; Bedrock uses `c=1` and `r=10`.
- Java's `/msg` is stored as `tell`, and `/experience` as `xp`.

Then run `python3 scripts/check_coverage.py data/commands-data.json data/content.json` until it reports no missing explanations.

## License

The code and hand-written content are released under the [MIT License](LICENSE).

Slashcraft is not an official Minecraft product. It is not approved by or associated with Mojang or Microsoft. Command names and syntax come from data that Mojang publishes.
