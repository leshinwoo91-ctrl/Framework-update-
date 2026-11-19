"""Terapkan patchset.json framework ke salinan folder smali (simulasi patcher). argv: patchset.json src_root dst_root"""
import json, os, shutil, sys
ps, src, dst = sys.argv[1:4]
d = json.load(open(ps))
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(src, dst)
cache = {}
def get(f):
    p = os.path.join(dst, f)
    if f not in cache:
        cache[f] = open(p, encoding='utf-8').read() if os.path.exists(p) else None
    return cache[f]
ok = fail = 0
for o in d['ops']:
    f, op = o['file'], o['op']
    if not f.startswith('smali/'):
        continue
    t = get(f)
    if op == 'new_file':
        if t is not None: print('EXISTS', f); fail += 1; continue
        cache[f] = o['code']; ok += 1; continue
    if op == 'append':
        if t is None: print('NOFILE', f); fail += 1; continue
        cache[f] = t + o['code']; ok += 1; continue
    if op == 'patch':
        a = o['anchor']
        if t is None or a not in t: print('MISS', op, f, o.get('name')); fail += 1; continue
        if t.count(a) > 1: print('AMBIGUOUS', op, f, o.get('name')); fail += 1; continue
        i = t.index(a)
        cache[f] = (t[:i + len(a)] + o['code'] + t[i + len(a):]) if o['after'] else (t[:i] + o['code'] + t[i:])
        ok += 1; continue
    if op == 'replace':
        if t is None or o['old'] not in t: print('MISS', op, f, o.get('name')); fail += 1; continue
        if t.count(o['old']) > 1: print('AMBIGUOUS', op, f, o.get('name')); fail += 1; continue
        cache[f] = t.replace(o['old'], o['new'], 1); ok += 1; continue
    print('UNKNOWN', op)
for f, t in cache.items():
    if t is None: continue
    p = os.path.join(dst, f); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(t)
print('ok', ok, 'fail', fail)
