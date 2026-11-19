"""Build data/entities-data.json from Mojang's official entity data.

Usage:
  python3 build_entities.py <java_registries.json> <java_entity_tags_dir> \
      <bedrock_commands.json> <bedrock_entities_dir> <java_version> <bedrock_version> <out.json>

Java:    misode/mcmeta "<version>-summary" registries/data.json (entity_type list) and
         "<version>-data-json" data/minecraft/tags/entity_type/*.json (entity groups).
Bedrock: Mojang/bedrock-samples metadata/command_modules/mojang-commands.json (the
         EntityType list /summon and type= accept) and behavior_pack/entities/*.json
         (each entity's families, used by the family= filter).

One row per thing in the game. A row has the Java ID(s), the Bedrock ID(s), which
Java groups (entity type tags) it's in, and which Bedrock families it has.
"""
import json, os, re, sys, datetime

# Bedrock ID -> Java ID, where the two editions spell it differently.
B2J = {
    'evocation_illager': 'evoker', 'evocation_fang': 'evoker_fangs',
    'zombie_pigman': 'zombified_piglin', 'ender_crystal': 'end_crystal',
    'fireworks_rocket': 'firework_rocket', 'xp_orb': 'experience_orb',
    'xp_bottle': 'experience_bottle', 'thrown_trident': 'trident',
    'tropicalfish': 'tropical_fish', 'fishing_hook': 'fishing_bobber',
    'eye_of_ender_signal': 'eye_of_ender', 'wind_charge_projectile': 'wind_charge',
    'breeze_wind_charge_projectile': 'breeze_wind_charge',
    'wither_skull_dangerous': 'wither_skull',
    'villager_v2': 'villager', 'zombie_villager_v2': 'zombie_villager',
}
# Bedrock has one boat and one chest boat; Java has one per wood type.
GROUPED = {'boat': '#boat', 'chest_boat': None}
# Bedrock IDs that aren't real gameplay things (editor tools, unused, duplicates).
B_SKIP = {'tripod_camera', 'frostbite', 'ice_ball', 'villager_v2', 'zombie_villager_v2', 'agent'}
# Bedrock things every world has that aren't in the behavior pack or /summon list.
B_BUILTIN = ['player', 'item', 'falling_block', 'painting']


def load_json_loose(path):
    """Read JSON that may contain // and /* */ comments (Mojang's files sometimes do)."""
    t = open(path, encoding='utf-8-sig').read()
    out, i, n, in_str = [], 0, len(t), False
    while i < n:
        c = t[i]
        if in_str:
            out.append(c)
            if c == '\\':
                out.append(t[i + 1]); i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True; out.append(c)
        elif t.startswith('//', i):
            while i < n and t[i] != '\n':
                i += 1
            continue
        elif t.startswith('/*', i):
            i = t.find('*/', i) + 2
            continue
        else:
            out.append(c)
        i += 1
    return json.loads(re.sub(r',(\s*[}\]])', r'\1', ''.join(out)))


def java_tags(tag_dir):
    raw = {}
    for f in os.listdir(tag_dir):
        if f.endswith('.json'):
            raw[f[:-5]] = [v if isinstance(v, str) else v['id'] for v in json.load(open(os.path.join(tag_dir, f)))['values']]
    resolved = {}
    def res(name, seen=()):
        if name in resolved:
            return resolved[name]
        out = set()
        for v in raw.get(name, []):
            if v.startswith('#'):
                sub = v[1:].split(':')[-1]
                if sub not in seen:
                    out |= res(sub, seen + (name,))
            else:
                out.add(v.split(':')[-1])
        resolved[name] = out
        return out
    for n in raw:
        res(n)
    return resolved


def bedrock_families(ent_dir):
    fams = {}
    for f in sorted(os.listdir(ent_dir)):
        if not f.endswith('.json'):
            continue
        ent = load_json_loose(os.path.join(ent_dir, f))['minecraft:entity']
        ident = ent['description']['identifier'].split(':')[-1]
        found = set()
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == 'minecraft:type_family':
                        found.update(v.get('family', []))
                    else:
                        walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(ent)
        fams[ident] = sorted(found)
    return fams


def main(reg_path, tag_dir, bcmd_path, bent_dir, jver, bver, out):
    java_ids = json.load(open(reg_path))['entity_type']
    java_ids = [j.split(':')[-1] for j in java_ids]
    tags = java_tags(tag_dir)

    bcmd = json.load(open(bcmd_path))
    enum = next(e for e in bcmd['command_enums'] if e['name'] == 'EntityType')
    summonable = {v['value'] for v in enum['values'] if ':' not in v['value']}
    fams = bedrock_families(bent_dir)
    bedrock_ids = (summonable | set(fams) | set(B_BUILTIN)) - B_SKIP
    bedrock_ids = {b for b in bedrock_ids if not b.startswith('editor')}

    rows = {}
    def row(key):
        return rows.setdefault(key, {'java': [], 'bedrock': [], 'java_tags': [], 'families': [], 'summon_bedrock': False})

    boat_tag = tags.get('boat', set())
    for j in java_ids:
        if j in boat_tag:
            key = 'boat'
        elif j.endswith('_chest_boat') or j.endswith('_chest_raft'):
            key = 'chest_boat'
        else:
            key = j
        row(key)['java'].append(j)

    for b in sorted(bedrock_ids):
        key = B2J.get(b, b)
        r = row(key)
        r['bedrock'].append(b)
        if b in summonable:
            r['summon_bedrock'] = True
        for f in fams.get(b, []):
            if f not in r['families']:
                r['families'].append(f)

    for key, r in rows.items():
        js = set(r['java'])
        r['java_tags'] = sorted(t for t, members in tags.items() if js and js <= members) if js else []
        if key == 'boat' and js:
            r['java_tags'] = sorted(set(r['java_tags']) | {'boat'})
        r['java'].sort()
        r['families'] = sorted(r['families'])
        if not r['bedrock']:
            r.pop('summon_bedrock')

    data = {
        'built': datetime.date.today().isoformat(),
        'java_version': jver, 'bedrock_version': bver,
        'java_tags': {t: sorted(m) for t, m in sorted(tags.items())},
        'entities': dict(sorted(rows.items())),
    }
    json.dump(data, open(out, 'w'), indent=1)
    print('entities', len(rows), '| java', sum(1 for r in rows.values() if r['java']),
          '| bedrock', sum(1 for r in rows.values() if r['bedrock']))


if __name__ == '__main__':
    main(*sys.argv[1:8])
