#!/usr/bin/env bash
# Refresh data/commands-data.json and data/entities-data.json from Mojang's official data.
#
#   scripts/update.sh          only rebuild if a new Java or Bedrock release is out
#   scripts/update.sh --force  rebuild even if the versions haven't changed
#
# Sources:
#   Java    - misode/mcmeta: the game's own data-generator output (command tree, entity
#             list, entity groups) for the latest stable release
#   Bedrock - Mojang/bedrock-samples, main branch (current release): command metadata and
#             the vanilla behavior pack's entity files (for families)
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

echo "Downloading Java $JV entity list and groups..."
curl -sSfL -o registries.json "https://raw.githubusercontent.com/misode/mcmeta/${JV}-summary/registries/data.json"
git clone -q --depth 1 --filter=blob:none --sparse --branch "${JV}-data-json" https://github.com/misode/mcmeta.git jdata
(cd jdata && git sparse-checkout set --skip-checks data/minecraft/tags/entity_type)

echo "Downloading Bedrock commands and entities..."
git clone -q --depth 1 --filter=blob:none --sparse https://github.com/Mojang/bedrock-samples.git bs
(cd bs && git sparse-checkout set --skip-checks metadata/command_modules behavior_pack/entities version.json)
BV=$(python3 -I -c "import json;print(json.load(open('bs/version.json'))['latest']['version'].rsplit('.',1)[0])")

read -r OLD_JV OLD_BV < <(python3 -I -c "import json,sys;d=json.load(open(sys.argv[1]));print(d['java']['version'],d['bedrock']['version'])" "$ROOT/data/commands-data.json")
echo "Current: Java $OLD_JV, Bedrock $OLD_BV"
echo "Latest:  Java $JV, Bedrock $BV"

if [[ "$JV" == "$OLD_JV" && "$BV" == "$OLD_BV" && "${1:-}" != "--force" ]]; then
  echo "Already up to date."
  exit 0
fi

python3 -I "$ROOT/scripts/build_data.py" java.json "$JV" bs/metadata/command_modules/mojang-commands.json "$BV" "$ROOT/data/commands-data.json"
python3 -I "$ROOT/scripts/build_entities.py" registries.json jdata/data/minecraft/tags/entity_type \
  bs/metadata/command_modules/mojang-commands.json bs/behavior_pack/entities "$JV" "$BV" "$ROOT/data/entities-data.json"
echo
status=0
python3 -I "$ROOT/scripts/check_coverage.py" "$ROOT/data/commands-data.json" "$ROOT/data/content.json" || status=2
python3 -I "$ROOT/scripts/check_entities.py" "$ROOT/data/entities-data.json" "$ROOT/data/entities.json" || status=2
if [[ $status -ne 0 ]]; then
  echo
  echo "New commands or mobs need kid-friendly entries in data/content.json or data/entities.json (see README)."
fi
exit $status
