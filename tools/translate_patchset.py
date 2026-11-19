#!/usr/bin/env python3
"""Terjemahkan patchset.json framework dari 0.9995 ke 1.00 memakai map.json.

argv: patchset_lama.json map.json smali_baru_root out_patchset.json
- Nama kelas obfuscated diganti (Lh1; untuk helper framework -> LSrpgFw;).
- Member (field/method) diganti sesuai map; 5 member asli h1 dipetakan manual.
- Path file target diganti (smali/k4.smali -> smali/uv.smali, dst).
- Melaporkan op yang anchor/old-nya tidak ditemukan di smali baru.
"""
import json
import os
import re
import sys

ps, mpf, root, out = sys.argv[1:5]
d = json.load(open(ps))
mp = json.load(open(mpf))
cls = dict(mp["classes"])
mem = mp["members"]
HOST = "SrpgFw"  # kelas baru untuk helper framework (dulu ditempel ke h1)

H1_MANUAL = {
    "v2:[Lu7;": ("w8", "D1:[Lw60;"),
    "c0:[La4;": ("h81", "o0:[Lks;"),
    "d0:[La4;": ("h81", "p0:[Lks;"),
    "H4:[Lak;": ("l60", "p:[Llo0;"),
    "j(I)[Lkh;": ("tk0", "g(I)[Lvh0;"),
}

MEMBER = re.compile(r"L([a-z][a-z0-9]{0,3});->([\w$<>]+)(:[^\s,`)}]+|\([^)]*\)\S+)")
CLASS = re.compile(r"L([a-z][a-z0-9]{0,3});")
unknown = set()


def tr_member(m):
    c, n, sig = m.group(1), m.group(2), m.group(3)
    if c == "h1":
        key = n + sig
        if key in H1_MANUAL:
            nc, nm = H1_MANUAL[key]
            return "L%s;->%s" % (nc, nm)
        return "L%s;->%s%s" % (HOST, n, tr_types(sig))
    if c in cls:
        kind = "fields" if sig.startswith(":") else "methods"
        tgt = mem.get(c, {}).get(kind, {}).get(n + sig)
        if tgt and tgt.startswith("?"):
            unknown.add((c, n, sig, "RAGU"))
            tgt = tgt[1:]
        if tgt:
            return "L%s;->%s" % (cls[c], tgt)
        if n.startswith("mod"):
            return "L%s;->%s%s" % (cls[c], n, tr_types(sig))
        unknown.add((c, n, sig))
        return "L%s;->%s%s" % (cls[c], n, tr_types(sig))
    return m.group(0)


def tr_types(t):
    def r(m):
        n = m.group(1)
        if n == "h1":
            return "L%s;" % HOST
        return "L%s;" % cls.get(n, n)
    return CLASS.sub(r, t)


def tr(text):
    if text is None:
        return None
    text = MEMBER.sub(tr_member, text)
    # sisa tipe kelas yang berdiri sendiri (bukan member)
    out_parts = []
    last = 0
    for m in re.finditer(r"(L[\w/$]+;->[\w$<>]+)(:[^\s,`)}]+|\([^)]*\)\S+)", text):
        out_parts.append(tr_types(text[last:m.start()]))
        # pemilik sudah diterjemahkan (atau non-obfuscated): terjemahkan tipe di signature
        out_parts.append(m.group(1) + tr_types(m.group(2)))
        last = m.end()
    out_parts.append(tr_types(text[last:]))
    return "".join(out_parts)


def tr_file(f):
    m = re.match(r"smali/([a-z][a-z0-9]{0,3})\.smali$", f)
    if not m:
        return f
    c = m.group(1)
    if c == "h1":
        return "smali/%s.smali" % HOST
    return "smali/%s.smali" % cls.get(c, c)


new_ops, report = [], []
for o in d["ops"]:
    n = dict(o)
    n["file"] = tr_file(o["file"])
    for k in ("anchor", "code", "old", "new"):
        if k in n:
            n[k] = tr(n[k])
    if o["file"] == "smali/h1.smali" and o["op"] in ("patch", "replace"):
        n["_note"] = "anchor h1 lama: perlu ditinjau manual (h1 dipecah di 1.00)"
    new_ops.append(n)
    if n["op"] in ("patch", "replace") and n["file"].startswith("smali/"):
        a = n.get("anchor") if n["op"] == "patch" else n.get("old")
        p = os.path.join(root, n["file"][len("smali/"):])
        found = os.path.exists(p) and a in open(p, encoding="utf-8").read()
        report.append((found, o["op"], o["file"], n["file"], o.get("name")))

d2 = dict(d)
d2["ops"] = new_ops
d2["game_version"] = "1.00"
d2["ported_from"] = d.get("game_version")
json.dump(d2, open(out, "w"), indent=1)
ok = sum(1 for r in report if r[0])
print("anchor langsung ketemu:", ok, "/", len(report))
for r in report:
    if not r[0]:
        print("  BELUM", r[1], r[2], "->", r[3], "|", r[4])
print("member belum terpetakan:", sorted(unknown))
