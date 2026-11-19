"""Report commands in the data that have no kid-friendly entry in content.json (and vice versa)."""
import json, sys
data = json.load(open(sys.argv[1])); content = json.load(open(sys.argv[2]))
names = set(data['java']['commands']) | set(data['bedrock']['commands'])
missing = sorted(n for n in names if n not in content)
extra = sorted(n for n in content if not n.startswith('_') and n not in names)
print('commands:', len(names), '| missing explanations:', missing or 'none', '| no longer in game:', extra or 'none')
sys.exit(1 if missing else 0)
