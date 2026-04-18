#!/usr/bin/env python3
"""One-shot topology reconciliation. Idempotent. Safe to re-run."""
import yaml
import re
from pathlib import Path
import shutil
import sys

ROOT = Path('.')
DATA_ROOT = ROOT / 'data/world/hollow_crown'
VAULT_ROOT = ROOT / 'prompts/world_vault/hollow_crown'

# ID remappings: old_id -> new_id
ID_RENAMES = {
    'central_draconic_grasslands': 'central-draconic-grasslands',
    'southern_dark_quadrant': 'southern-dark-quadrant',
    'southwestern_mystic_wetlands': 'southwestern-mystic-wetlands',
    'western_temperate_forest': 'western-temperate-forest',
    'northeastern_volcanic_highlands': 'northeastern-volcanic-highlands',
    'hollow_crown': 'hollow-crown',
    'grasslands_edge_post': 'grasslands-edge-post',
    'volcanic-highlands': 'northeastern-volcanic-highlands',  # fix wrong reference
    'mystic-wetlands': 'southwestern-mystic-wetlands',  # fix wrong reference
    'temperate-forest': 'western-temperate-forest',  # fix wrong reference
    'beneath-southern-dark-quadrant': 'southern-dark-quadrant',  # consolidate
}

# Pairs that must be bidirectional (if missing on either side, add it)
RECIPROCATE_PAIRS = [
    ('ashfield', 'draconic-grasslands-edge'),
    ('ashfield-fields', 'drakenvale-city'),
    ('ashfield-fields', 'scalemere'),
    ('deephollow', 'crystal-caverns'),
    ('deephollow', 'stronghold-of-drakenvale'),
    ('deephollow', 'zarkharath'),
    ('dracelune', 'scalemere'),
    ('drakenvale-city', 'draconic-grasslands-edge'),
    ('hall-of-scales', 'drakenvale-city'),
    ('hall-of-scales', 'draconic-grasslands-edge'),
    ('infernal-forge', 'cinderpit'),
    ('infernal-forge', 'zarkharath'),
    ('lastmark', 'stronghold-of-drakenvale'),
    ('mirefall', 'dracelune'),
    ('platinum-oath-monastery', 'greymantle'),
    ('platinum-oath-monastery', 'rift-of-discord-edge'),
    ('rift-of-discord-edge', 'greymantle'),
    ('rift-of-discord-edge', 'platinum-oath-approach'),
    ('scalemere', 'drakenvale-city'),
    ('shadowed-hollows', 'rift-of-discord'),
    ('shadowed-hollows-approach', 'greymantle'),
    ('shadowed-hollows-approach', 'rift-of-discord-edge'),
    ('silverwood-trail', 'dewhollow'),
    ('silverwood-trail', 'dracelune'),
    ('stonemark', 'drakenvale-city'),
    ('vaelmere', 'feywood-glade'),
    ('vaelmere', 'feywood-glade-border'),
    ('vaelmere', 'thornveil'),
    ('zarkharath', 'stronghold-of-drakenvale'),
    ('scalemere', 'crystalhaven'),  # new lake route
    ('drakenvale-city', 'crystalhaven'),  # new lake route
]

# Connections to remove (legacy)
REMOVE_CONNECTIONS = [
    ('dracelune', 'thornveil'),
]

# Eryndor/Lastmark region parent fix
REPLACE_IN_CONNECTIONS = {
    'eryndors-lair': {'inner-ramparts': 'alpine-peaks'},
    'lastmark': {'inner-ramparts': 'alpine-peaks'},
}

# --- Helpers ---

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False, width=1000)

def iter_yaml_files():
    for p in sorted(DATA_ROOT.rglob('*.yaml')):
        yield p

def find_file_by_id(target_id):
    """Find the YAML file whose 'id' field equals target_id."""
    for p in iter_yaml_files():
        try:
            data = load_yaml(p)
            if data and data.get('id') == target_id:
                return p
        except Exception:
            pass
    return None

def find_md_mirror(yaml_path):
    """Find the corresponding markdown mirror in prompts/world_vault."""
    rel = yaml_path.relative_to(DATA_ROOT)
    candidate = VAULT_ROOT / rel.with_suffix('.md')
    if candidate.exists():
        return candidate
    return None

def update_md_frontmatter_and_body(md_path, old_id_or_ref, new_id_or_ref):
    """Replace references in markdown frontmatter and connected-nodes section."""
    if not md_path or not md_path.exists():
        return False
    text = md_path.read_text()
    # Simple whole-word token replacement. Our IDs are unique enough.
    pattern = re.compile(r'(?<![A-Za-z0-9_\-])' + re.escape(old_id_or_ref) + r'(?![A-Za-z0-9_\-])')
    new_text = pattern.sub(new_id_or_ref, text)
    if new_text != text:
        md_path.write_text(new_text)
        return True
    return False

log = []

def record(msg):
    log.append(msg)
    print(msg, flush=True)

# --- Step 1: Move misplaced silverwood_trail ---

def move_silverwood_trail():
    src_yaml = DATA_ROOT / 'surface/feywood_glade/silverwood_trail.yaml'
    dst_yaml = DATA_ROOT / 'surface/western_temperate_forest/silverwood_trail.yaml'
    src_md = VAULT_ROOT / 'surface/feywood_glade/silverwood_trail.md'
    dst_md = VAULT_ROOT / 'surface/western_temperate_forest/silverwood_trail.md'

    moved = []
    if src_yaml.exists() and not dst_yaml.exists():
        dst_yaml.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_yaml), str(dst_yaml))
        moved.append(f'YAML: {src_yaml} -> {dst_yaml}')
    elif dst_yaml.exists() and src_yaml.exists():
        # both exist — prefer dst, remove src
        src_yaml.unlink()
        moved.append(f'YAML: removed duplicate {src_yaml}')
    elif dst_yaml.exists():
        moved.append(f'YAML: already at destination {dst_yaml}')

    if src_md and src_md.exists() and not dst_md.exists():
        dst_md.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_md), str(dst_md))
        moved.append(f'MD: {src_md} -> {dst_md}')
    elif dst_md.exists() and src_md and src_md.exists():
        src_md.unlink()
        moved.append(f'MD: removed duplicate {src_md}')
    elif dst_md.exists():
        moved.append(f'MD: already at destination {dst_md}')

    for m in moved:
        record(f'[silverwood-move] {m}')

# --- Step 2: Rename IDs in-place and rewrite all connection references ---

def apply_id_renames():
    # Phase 1: update the 'id' field where the file's current id matches a key
    for p in iter_yaml_files():
        try:
            data = load_yaml(p)
        except Exception as e:
            record(f'[skip-parse-error] {p}: {e}')
            continue
        if not data or not isinstance(data, dict):
            continue
        cur_id = data.get('id')
        if cur_id in ID_RENAMES and cur_id != ID_RENAMES[cur_id]:
            new_id = ID_RENAMES[cur_id]
            data['id'] = new_id
            save_yaml(p, data)
            record(f'[id-rename] {p.name}: {cur_id} -> {new_id}')
            # Update markdown mirror's id field
            md = find_md_mirror(p)
            if md and md.exists():
                update_md_frontmatter_and_body(md, cur_id, new_id)

    # Phase 2: walk every YAML, update any connection references, parent references, region references
    for p in iter_yaml_files():
        try:
            data = load_yaml(p)
        except Exception:
            continue
        if not data or not isinstance(data, dict):
            continue
        changed = False

        # connections
        conns = data.get('connections', []) or []
        new_conns = []
        seen = set()
        for c in conns:
            replacement = ID_RENAMES.get(c, c)
            if replacement not in seen:
                new_conns.append(replacement)
                seen.add(replacement)
            if replacement != c:
                changed = True
        if new_conns != conns:
            data['connections'] = new_conns

        # parent_location_id
        for field in ['parent_location_id', 'region_id']:
            if field in data and data[field] in ID_RENAMES:
                old = data[field]
                data[field] = ID_RENAMES[old]
                changed = True

        if changed:
            save_yaml(p, data)
            record(f'[conn-rewrite] {p.name}: connections/parents normalized')
            md = find_md_mirror(p)
            if md and md.exists():
                for old, new in ID_RENAMES.items():
                    if old != new:
                        update_md_frontmatter_and_body(md, old, new)

# --- Step 3: Apply per-location specific replacements (Eryndor/Lastmark) ---

def apply_specific_replacements():
    for loc_id, replacements in REPLACE_IN_CONNECTIONS.items():
        fp = find_file_by_id(loc_id)
        if not fp:
            record(f'[specific-replace] skipped: no file for id={loc_id}')
            continue
        data = load_yaml(fp)
        conns = data.get('connections', []) or []
        new_conns = []
        changed = False
        for c in conns:
            if c in replacements:
                replacement = replacements[c]
                if replacement not in new_conns:
                    new_conns.append(replacement)
                changed = True
            else:
                if c not in new_conns:
                    new_conns.append(c)
        if changed:
            data['connections'] = new_conns
            # Also fix parent_location_id if it matches
            for old_val, new_val in replacements.items():
                if data.get('parent_location_id') == old_val:
                    data['parent_location_id'] = new_val
            save_yaml(fp, data)
            record(f'[specific-replace] {loc_id}: {replacements}')
            md = find_md_mirror(fp)
            if md:
                for old, new in replacements.items():
                    update_md_frontmatter_and_body(md, old, new)

# --- Step 4: Remove legacy connections ---

def remove_connections():
    for src, tgt in REMOVE_CONNECTIONS:
        fp = find_file_by_id(src)
        if not fp:
            record(f'[remove-conn] skipped: no file for id={src}')
            continue
        data = load_yaml(fp)
        conns = data.get('connections', []) or []
        if tgt in conns:
            data['connections'] = [c for c in conns if c != tgt]
            save_yaml(fp, data)
            record(f'[remove-conn] {src}: removed -> {tgt}')
            md = find_md_mirror(fp)
            if md:
                text = md.read_text()
                text = re.sub(r'^- ' + re.escape(tgt) + r'\n', '', text, flags=re.MULTILINE)
                text = re.sub(r'^-\s*`' + re.escape(tgt) + r'`\s*\n', '', text, flags=re.MULTILINE)
                md.write_text(text)

# --- Step 5: Reciprocate pairs ---

def reciprocate_pairs():
    for a, b in RECIPROCATE_PAIRS:
        fa = find_file_by_id(a)
        fb = find_file_by_id(b)
        if not fa:
            record(f'[reciprocate] skipped: no file for id={a}')
            continue
        if not fb:
            record(f'[reciprocate] skipped: no file for id={b}')
            continue
        # Ensure a lists b
        da = load_yaml(fa)
        ca = da.get('connections', []) or []
        if b not in ca:
            ca.append(b)
            da['connections'] = ca
            save_yaml(fa, da)
            record(f'[reciprocate] {a}: + {b}')
            md = find_md_mirror(fa)
            if md:
                add_to_md_connections(md, b)
        # Ensure b lists a
        db = load_yaml(fb)
        cb = db.get('connections', []) or []
        if a not in cb:
            cb.append(a)
            db['connections'] = cb
            save_yaml(fb, db)
            record(f'[reciprocate] {b}: + {a}')
            md = find_md_mirror(fb)
            if md:
                add_to_md_connections(md, a)

def add_to_md_connections(md_path, new_id):
    """Add new_id to both the frontmatter connections: list and the 'Connected Nodes' section."""
    text = md_path.read_text()

    # Frontmatter connections list
    fm_match = re.search(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        # Find connections: block
        conn_match = re.search(r'(^connections:\s*\n((?:-\s+.+\n)+))', fm, re.MULTILINE)
        if conn_match:
            if f'- {new_id}\n' not in conn_match.group(2):
                new_block = conn_match.group(1).rstrip('\n') + f'\n- {new_id}\n'
                new_fm = fm.replace(conn_match.group(1), new_block)
                text = text.replace(fm, new_fm, 1)

    # 'Connected Nodes' section with backticked list
    cn_match = re.search(r'(## Connected Nodes\s*\n\n((?:-\s+`[^`]+`\s*\n)+))', text)
    if cn_match:
        if f'`{new_id}`' not in cn_match.group(2):
            addition = f'- `{new_id}`\n'
            new_section = cn_match.group(1).rstrip('\n') + '\n' + addition
            text = text.replace(cn_match.group(1), new_section, 1)

    md_path.write_text(text)

# --- Step 6: Final validation ---

def validate():
    all_ids = set()
    conns_map = {}
    errors = []

    for p in iter_yaml_files():
        try:
            data = load_yaml(p)
            if data and 'id' in data:
                all_ids.add(data['id'])
                conns_map[data['id']] = data.get('connections', []) or []
        except Exception as e:
            errors.append(f'parse-error: {p}: {e}')

    forward = set()
    for a, cs in conns_map.items():
        for b in cs:
            if b not in all_ids:
                forward.add((a, b))

    one_way = []
    for a, cs in conns_map.items():
        for b in cs:
            if b in conns_map and a not in conns_map[b]:
                one_way.append((a, b))

    record('')
    record('=' * 60)
    record(f'VALIDATION: {len(all_ids)} locations')
    record(f'VALIDATION: {len(forward)} forward references remaining')
    for a, b in sorted(forward):
        record(f'  FORWARD: {a} -> {b}')
    record(f'VALIDATION: {len(one_way)} one-way connections remaining')
    for a, b in sorted(one_way):
        record(f'  ONEWAY: {a} -> {b}')
    if errors:
        record(f'VALIDATION ERRORS: {errors}')

# --- Main ---

def main():
    record('Starting topology reconciliation')
    move_silverwood_trail()
    record('--- rename pass ---')
    apply_id_renames()
    record('--- specific replacements ---')
    apply_specific_replacements()
    record('--- remove legacy connections ---')
    remove_connections()
    record('--- reciprocate pairs ---')
    reciprocate_pairs()
    record('--- validation ---')
    validate()
    record('Done.')

if __name__ == '__main__':
    main()