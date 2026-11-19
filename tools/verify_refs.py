"""Verifikasi rujukan member di file smali tertentu terhadap seluruh tree hasil patch.
argv: tree_root file1.smali [file2 ...]  (atau --patchset ps.json untuk ambil potongan kode)"""
import json
import os
import re
import sys

root = sys.argv[1]
targets = sys.argv[2:]
cache = {}


def load(cname):
    if cname in cache:
        return cache[cname]
    p = os.path.join(root, cname + ".smali")
    if not os.path.exists(p):
        cache[cname] = None
        return None
    fields, methods, sup = set(), set(), None
    for l in open(p, encoding="utf-8"):
        if l.startswith(".super"):
            sup = l.split()[1][1:-1]
        elif l.startswith(".field"):
            m = re.match(r"\.field ((?:[a-z]+ )*)(\S+):(\S+)", l.split(" = ")[0].strip())
            fields.add(m.group(2) + ":" + m.group(3))
        elif l.startswith(".method"):
            methods.add(l.strip().split()[-1])
    cache[cname] = (fields, methods, sup)
    return cache[cname]


def has(cname, mem, is_field):
    seen = 0
    while cname and seen < 20:
        info = load(cname)
        if info is None:
            return None  # kelas framework/android: tidak dicek
        if mem in (info[0] if is_field else info[1]):
            return True
        cname = info[2]
        seen += 1
    return False


texts = []
if targets and targets[0] == "--patchset":
    ps = json.load(open(targets[1]))
    for o in ps["ops"]:
        if o["file"].startswith("smali/"):
            texts.append((o.get("name"), (o.get("code") or "") + "\n" + (o.get("new") or "")))
else:
    for t in targets:
        texts.append((t, open(t, encoding="utf-8").read()))

bad, n, missing_cls = [], 0, set()
for name, t in texts:
    for m in re.finditer(r"L([\w/$]+);->([\w$<>]+)(:[^\s,`)}]+|\([^)]*\)\S+)", t):
        c, mem, sig = m.group(1), m.group(2), m.group(3)
        isf = sig.startswith(":")
        key = mem + sig if not isf else mem + sig
        r = has(c, key, isf)
        if r is None:
            if not c.startswith(("android/", "java/", "javax/", "org/json", "dalvik/", "kotlin/")):
                missing_cls.add(c)
            continue
        n += 1
        if not r:
            bad.append((name, c, mem + sig))
    for m in re.finditer(r"L([a-z][a-z0-9]{0,3});", t):
        if load(m.group(1)) is None:
            missing_cls.add(m.group(1))
print("rujukan dicek:", n, "| gagal:", len(bad), "| kelas tak dikenal:", sorted(missing_cls))
for b in sorted(set(bad))[:60]:
    print("  GAGAL", b)
