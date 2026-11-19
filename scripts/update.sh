#!/usr/bin/env bash
# Refresh data/commands-data.json from Mojang's official command data.
#
#   scripts/update.sh          only rebuild if a new Java or Bedrock release is out
#   scripts/update.sh --force  rebuild even if the versions haven't changed
#
# Sources:
#   Java    - misode/mcmeta (the game's own data-generator command tree), latest stable release
#   Bedrock - Mojang/bedrock-samples, main branch (current release)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

echo "Downloading Java release list..."
curl -sSfL -o versions.json https://raw.githubusercontent.com/misode/mcmeta/summary/versions/data.json
JV=$(python3 -I -c "import json;print(next(v['id'] for v in json.load(open('versions.json')) if v['stable']))")

echo "Downloading Java $JV commands..."
curl -sSfL -o java.json "https://raw.githubusercontent.com/misode/mcmeta/${JV}-summary/commands/data.json"

echo "Downloading Bedrock commands..."
git clone -q --depth 1 --filter=blob:none --sparse https://github.com/Mojang/bedrock-samples.git bs
(cd bs && git sparse-checkout set --skip-checks metadata/command_modules version.json)
BV=$(python3 -I -c "import json;print(json.load(open('bs/version.json'))['latest']['version'].rsplit('.',1)[0])")

read -r OLD_JV OLD_BV < <(python3 -I -c "import json,sys;d=json.load(open(sys.argv[1]));print(d['java']['version'],d['bedrock']['version'])" "$ROOT/data/commands-data.json")
echo "Current: Java $OLD_JV, Bedrock $OLD_BV"
echo "Latest:  Java $JV, Bedrock $BV"

if [[ "$JV" == "$OLD_JV" && "$BV" == "$OLD_BV" && "${1:-}" != "--force" ]]; then
  echo "Already up to date."
  exit 0
fi

python3 -I "$ROOT/scripts/build_data.py" java.json "$JV" bs/metadata/command_modules/mojang-commands.json "$BV" "$ROOT/data/commands-data.json"
echo
python3 -I "$ROOT/scripts/check_coverage.py" "$ROOT/data/commands-data.json" "$ROOT/data/content.json" || {
  echo
  echo "New commands need kid-friendly entries in data/content.json (see README)."
  exit 2
}
