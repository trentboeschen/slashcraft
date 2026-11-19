"""Report entities in the data that have no entry in entities.json (and entries no longer in the game).

Usage: python3 check_entities.py data/entities-data.json data/entities.json
"""
import json, sys
data = json.load(open(sys.argv[1]))['entities']
content = json.load(open(sys.argv[2]))
kinds = content['_kinds']
missing = sorted(k for k in data if k not in content)
extra = sorted(k for k in content if not k.startswith('_') and k not in data)
bad = sorted(k for k, v in content.items() if not k.startswith('_') and v.get('kind') not in kinds)
print('entities:', len(data), '| missing entries:', missing or 'none',
      '| no longer in game:', extra or 'none', '| unknown kind:', bad or 'none')
sys.exit(1 if missing or bad else 0)
