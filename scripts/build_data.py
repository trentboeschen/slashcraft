"""Build commands-data.json from Mojang's official command data.

Usage:
  python3 build_data.py <java_commands.json> <java_version> <bedrock_commands.json> <bedrock_version> <out.json>

Java data: misode/mcmeta "<version>-summary" tag, commands/data.json
           (the game's own data-generator command tree).
Bedrock data: Mojang/bedrock-samples, metadata/command_modules/mojang-commands.json
"""
import json, sys, datetime

# Java names that are just another spelling of a shared command.
JAVA_CANON = {'msg': 'tell', 'experience': 'xp'}
JAVA_LEVELS = {'everyone': 0, 'moderators': 1, 'gamemasters': 2, 'admins': 3, 'owners': 4}


def java_paths(name, node, limit=400):
    out = []
    def walk(n, parts, depth):
        if len(out) >= limit:
            return
        if n.get('executable'):
            out.append(parts)
        if 'redirect' in n:
            out.append(parts + ['…'])
            return
        if depth > 9:
            if n.get('children'):
                out.append(parts + ['…'])
            return
        for k, c in (n.get('children') or {}).items():
            walk(c, parts + [k if c['type'] == 'literal' else f'<{k}>'], depth + 1)
    walk(node, ['/' + name], 0)
    return out


def compress(paths, max_lines=14):
    """Fold 'a b' + 'a b c' into 'a b [c]' and keep the list short."""
    lines = [' '.join(p) for p in paths]
    changed = True
    while changed:
        changed = False
        s = set(lines)
        for l in sorted(lines, key=len, reverse=True):
            ext = [m for m in lines if m.startswith(l + ' ')]
            if len(ext) == 1 and l in s:
                m = ext[0]
                rest = m[len(l) + 1:]
                if rest == '…':
                    continue
                new = f'{l} [{rest}]'
                lines = [x for x in lines if x not in (l, m)] + [new]
                changed = True
                break
    lines = sorted(dict.fromkeys(lines))
    for keep in (3, 2):
        if len(lines) > max_lines:
            short = []
            for l in lines:
                toks = l.split(' ')
                k = ' '.join(toks[:keep]) + (' …' if len(toks) > keep else '')
                if k not in short:
                    short.append(k)
            lines = short
    return lines


def java_level(node):
    p = node.get('permissions')
    if not p:
        return 0
    lvl = (p.get('permission') or {}).get('level')
    return JAVA_LEVELS.get(lvl, 2)


def build_java(path):
    tree = json.load(open(path))['children']
    cmds, aliases = {}, {}
    for name, node in tree.items():
        if 'redirect' in node and not node.get('children'):
            target = node['redirect'][0]
            aliases.setdefault(JAVA_CANON.get(target, target), []).append(name)
            continue
        key = JAVA_CANON.get(name, name)
        cmds[key] = {
            'typed': name,
            'level': java_level(node),
            'syntax': compress(java_paths(name, node)),
        }
    for key, al in aliases.items():
        if key in cmds:
            cmds[key]['aliases'] = sorted(a for a in al if a != cmds[key]['typed'])
    # 'tell' is itself an alias of msg in Java: make sure it shows.
    if 'tell' in cmds and 'tell' not in cmds['tell'].get('aliases', []) and cmds['tell']['typed'] != 'tell':
        cmds['tell'].setdefault('aliases', []).append('tell')
    return cmds


def build_bedrock(path):
    d = json.load(open(path))
    enums = {e['name'].lower(): [v['value'] for v in e['values']] for e in d['command_enums']}
    cmds = {}
    for c in d['commands']:
        lines = []
        for ov in c['overloads']:
            parts = ['/' + c['name']]
            for prm in ov['params']:
                t = prm['type']['name']
                ev = enums.get(t.lower())
                if ev and len(ev) == 1:
                    parts.append(f'[{ev[0]}]' if prm['is_optional'] else ev[0])
                    continue
                label = '|'.join(ev) if ev and len(ev) <= 6 else (prm['name'] or t.lower())
                parts.append(f'[{label}]' if prm['is_optional'] else f'<{label}>')
            lines.append(' '.join(parts))
        lines = list(dict.fromkeys(lines))
        if len(lines) > 14:
            lines = compress([l.split(' ') for l in lines])
        cmds[c['name']] = {
            'typed': c['name'],
            'official': c['description'],
            'level': c['permission_level'],
            'cheats': c['requires_cheats'],
            'aliases': [a['name'] for a in c['aliases']],
            'syntax': lines,
        }
    return cmds


if __name__ == '__main__':
    jpath, jver, bpath, bver, out = sys.argv[1:6]
    data = {
        'built': datetime.date.today().isoformat(),
        'java': {'version': jver, 'commands': build_java(jpath)},
        'bedrock': {'version': bver, 'commands': build_bedrock(bpath)},
    }
    json.dump(data, open(out, 'w'), indent=1)
    print('java', len(data['java']['commands']), 'bedrock', len(data['bedrock']['commands']))
