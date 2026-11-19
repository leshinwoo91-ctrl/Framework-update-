#!/usr/bin/env python3
"""Pemetaan kelas & member obfuscated antara dua versi smali (lama -> baru).

Pakai: python3 -I smalimap.py <smali_lama> <smali_baru> <out.json> [kelas_target,...]
Metode:
  1. Sidik jari tiap kelas: string konstan, konstanta numerik besar, bentuk field/method
     (tipe obfuscated dinormalisasi jadi 'O'), superclass/interface.
  2. Kandidat diberi skor; pasangan paling yakin dikunci dulu.
  3. Propagasi: setelah kelas A->A' terkunci, tipe field/param yang posisinya cocok
     ikut memberi bukti untuk kelas yang dirujuk.
  4. Member (field/method) dipetakan di dalam pasangan kelas yang sudah terkunci.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

OBF = re.compile(r"L([a-z][a-z0-9]{0,3});")


def is_obf(cname):
    return re.fullmatch(r"[a-z][a-z0-9]{0,3}", cname) is not None


def norm_type(t, mp=None, side="old"):
    def r(m):
        n = m.group(1)
        if mp is not None:
            if side == "old" and n in mp:
                return "L#" + mp[n] + ";"
            if side == "new" and n in NEWSET:
                return "L#" + n + ";"
        return "LO;"
    return OBF.sub(r, t)


NEWSET = set()


class Cls:
    __slots__ = ("name", "sup", "ifaces", "fields", "methods", "strings", "nums", "flags", "refs")


def parse_tree(root):
    out = {}
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if not f.endswith(".smali"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root)[:-6]
            if "/" in rel:  # hanya kelas obfuscated di root
                continue
            c = parse_file(p)
            if c:
                out[c.name] = c
    return out


def parse_file(p):
    c = Cls()
    c.ifaces, c.fields, c.methods = [], [], []
    c.strings, c.nums, c.refs = Counter(), Counter(), Counter()
    c.sup, c.flags, c.name = "", "", None
    cur = None
    with open(p, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith(".line") or s.startswith("#"):
                continue
            if s.startswith(".class"):
                parts = s.split()
                c.name = parts[-1][1:-1]
                c.flags = " ".join(x for x in parts[1:-1] if x in ("abstract", "interface", "enum", "final"))
            elif s.startswith(".super"):
                c.sup = s.split()[1]
            elif s.startswith(".implements"):
                c.ifaces.append(s.split()[1])
            elif s.startswith(".field"):
                body = s.split(" = ")[0]
                m = re.match(r"\.field ((?:[a-z]+ )*)(\S+):(\S+)", body)
                if m:
                    c.fields.append((m.group(2), m.group(3), "static" in m.group(1)))
            elif s.startswith(".method"):
                m = re.match(r"\.method ((?:[a-z-]+ )*)([^\s(]+)\((.*?)\)(\S+)", s)
                cur = {"name": m.group(2), "params": m.group(3), "ret": m.group(4),
                       "static": "static" in m.group(1), "strings": Counter(), "nums": Counter(),
                       "ops": Counter(), "refs": Counter(), "n": 0, "seq": []}
                c.methods.append(cur)
            elif s.startswith(".end method"):
                cur = None
            elif cur is not None and not s.startswith("."):
                op = s.split()[0]
                if op.startswith(":"):
                    continue
                cur["ops"][op] += 1
                cur["n"] += 1
                if op.startswith("const-string"):
                    v = s.split(", ", 1)[1]
                    cur["strings"][v] += 1
                    c.strings[v] += 1
                elif op.startswith("const"):
                    v = s.rsplit(", ", 1)[-1].split()[0]
                    try:
                        iv = int(v, 16)
                    except ValueError:
                        iv = None
                    if iv is not None and abs(iv) >= 256 and op not in ("const/high16",):
                        cur["nums"][iv] += 1
                        c.nums[iv] += 1
                    elif op in ("const/high16", "const", "const-wide") and "#" in s:
                        cur["nums"][s.split("#")[-1].strip()] += 1
                        c.nums[s.split("#")[-1].strip()] += 1
                fr = re.search(r"(L[\w/$]+;)->([\w$<>]+)(:\S+|\([^)]*\)\S+)", s)
                if fr and (op.startswith("iget") or op.startswith("iput") or op.startswith("sget")
                           or op.startswith("sput") or op.startswith("invoke")):
                    cur["seq"].append((op.split("/")[0], fr.group(1), fr.group(2), fr.group(3)))
                for m in OBF.finditer(s):
                    cur["refs"][m.group(1)] += 1
                    c.refs[m.group(1)] += 1
    return c if c.name else None


def shape(c, mp=None, side="old"):
    f = Counter((norm_type(t, mp, side), st) for _, t, st in c.fields)
    m = Counter((norm_type("(" + x["params"] + ")" + x["ret"], mp, side), x["static"]) for x in c.methods
                if x["name"] not in ("<clinit>",))
    return f, m


def jacc(a, b):
    if not a and not b:
        return 0.0
    inter = sum((a & b).values())
    uni = sum((a | b).values())
    return inter / uni if uni else 0.0


def class_score(o, n, mp=None):
    s = 0.0
    js = jacc(o.strings, n.strings)
    s += 6.0 * js
    s += 2.0 * jacc(o.nums, n.nums)
    fo, mo = shape(o, mp, "old")
    fn, mn = shape(n, mp, "new")
    s += 2.0 * jacc(fo, fn)
    s += 2.0 * jacc(mo, mn)
    if norm_type(o.sup, mp, "old") == norm_type(n.sup, mp, "new"):
        s += 0.5
    if o.flags == n.flags:
        s += 0.3
    if Counter(norm_type(i, mp, "old") for i in o.ifaces) == Counter(norm_type(i, mp, "new") for i in n.ifaces):
        s += 0.3
    # ukuran mirip
    ao, an = len(o.methods) + len(o.fields), len(n.methods) + len(n.fields)
    if ao and an:
        s += 0.7 * min(ao, an) / max(ao, an)
    return s


def build_map(old, new, rounds=4):
    mp = {}           # lama -> baru
    used = set()
    # indeks string -> kelas baru, untuk membatasi kandidat
    sidx = defaultdict(set)
    for n in new.values():
        for st in n.strings:
            sidx[st].add(n.name)
    for r in range(rounds):
        cand = []
        for o in old.values():
            if o.name in mp:
                continue
            pool = set()
            for st in o.strings:
                if len(sidx.get(st, ())) <= 40:
                    pool |= sidx.get(st, set())
            if not pool:
                # kelas tanpa string: kandidat dengan bentuk sama persis
                fo, mo = shape(o, mp)
                pool = {n.name for n in new.values() if n.name not in used and
                        len(n.fields) == len(o.fields) and abs(len(n.methods) - len(o.methods)) <= 2}
            scored = sorted(((class_score(o, new[x], mp), x) for x in pool if x not in used), reverse=True)
            if not scored:
                continue
            best = scored[0]
            second = scored[1][0] if len(scored) > 1 else 0.0
            cand.append((best[0], best[0] - second, o.name, best[1]))
        thr_s, thr_m = [(4.0, 0.8), (3.0, 0.5), (2.5, 0.3), (2.0, 0.2)][min(r, 3)]
        cand.sort(reverse=True)
        added = 0
        for sc, margin, on, nn in cand:
            if on in mp or nn in used:
                continue
            if sc >= thr_s and margin >= thr_m:
                mp[on] = nn
                used.add(nn)
                NEWSET.add(nn)
                added += 1
        # propagasi lewat tipe field/method yang posisinya cocok
        added += propagate(old, new, mp, used)
        print("ronde", r, "kelas terpetakan:", len(mp), "(+%d)" % added, file=sys.stderr)
    return mp


def propagate(old, new, mp, used):
    votes = defaultdict(Counter)
    for on, nn in list(mp.items()):
        o, n = old[on], new.get(nn)
        if n is None:
            continue
        # field: cocokkan berdasarkan urutan & tipe non-obf yang sama
        if len(o.fields) == len(n.fields):
            for (fa, ta, sa), (fb, tb, sb) in zip(o.fields, n.fields):
                for a, b in zip(OBF.findall(ta), OBF.findall(tb)):
                    votes[a][b] += 1
        # method dengan signature sama setelah normalisasi
        bym = defaultdict(list)
        for m in n.methods:
            bym[(norm_type("(" + m["params"] + ")" + m["ret"], mp, "new"), len(m["params"]))].append(m)
        for m in o.methods:
            k = (norm_type("(" + m["params"] + ")" + m["ret"], mp, "old"), len(m["params"]))
            if len(bym.get(k, [])) == 1:
                mm = bym[k][0]
                sa = "(" + m["params"] + ")" + m["ret"]
                sb = "(" + mm["params"] + ")" + mm["ret"]
                for a, b in zip(OBF.findall(sa), OBF.findall(sb)):
                    votes[a][b] += 1
    added = 0
    for a, cnt in votes.items():
        if a in mp or a not in old:
            continue
        b, v = cnt.most_common(1)[0]
        tot = sum(cnt.values())
        if b in used or b not in new:
            continue
        if v >= 2 and v / tot >= 0.75 and class_score(old[a], new[b], mp) >= 1.5:
            mp[a] = b
            used.add(b)
            NEWSET.add(b)
            added += 1
    return added


def map_members(o, n, mp):
    fm, mm = {}, {}
    groups_o, groups_n = defaultdict(list), defaultdict(list)
    for f in o.fields:
        groups_o[(norm_type(f[1], mp, "old"), f[2])].append(f)
    for f in n.fields:
        groups_n[(norm_type(f[1], mp, "new"), f[2])].append(f)
    for k, lo in groups_o.items():
        ln = groups_n.get(k, [])
        if len(lo) == len(ln):
            for a, b in zip(lo, ln):
                # tipe unik = pasti; tipe ganda = hanya tebakan urutan (ditandai ragu)
                fm[a[0] + ":" + a[1]] = (b[0] + ":" + b[1]) if len(lo) == 1 else ("?" + b[0] + ":" + b[1])
    for m in o.methods:
        sig = norm_type("(" + m["params"] + ")" + m["ret"], mp, "old")
        cands = [x for x in n.methods if norm_type("(" + x["params"] + ")" + x["ret"], mp, "new") == sig
                 and x["static"] == m["static"]]
        if not cands:
            continue
        def sim(x):
            return (3 * jacc(m["strings"], x["strings"]) + 2 * jacc(m["nums"], x["nums"]) +
                    2 * jacc(m["ops"], x["ops"]) + (1 if m["name"] in ("<init>", "<clinit>") and x["name"] == m["name"] else 0))
        best = max(cands, key=sim)
        key = m["name"] + "(" + m["params"] + ")" + m["ret"]
        mm[key] = best["name"] + "(" + best["params"] + ")" + best["ret"]
    return fm, mm


def seq_votes(old, new, mp, mmaps):
    """Selaraskan urutan akses field/method dalam pasangan method yang sudah terpetakan."""
    import difflib
    fv, mv = defaultdict(Counter), defaultdict(Counter)
    for on, nn in mp.items():
        o, n = old[on], new.get(nn)
        if n is None:
            continue
        nmeth = {x["name"] + "(" + x["params"] + ")" + x["ret"]: x for x in n.methods}
        for m in o.methods:
            key = m["name"] + "(" + m["params"] + ")" + m["ret"]
            tgt = mmaps.get(on, {}).get(key)
            if not tgt or tgt not in nmeth:
                continue
            a, b = m["seq"], nmeth[tgt]["seq"]
            if not a or not b:
                continue
            ka = [(x[0], norm_type(x[1], mp, "old"), norm_type(x[3], mp, "old")) for x in a]
            kb = [(x[0], norm_type(x[1], mp, "new"), norm_type(x[3], mp, "new")) for x in b]
            sm = difflib.SequenceMatcher(None, ka, kb, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag != "equal":
                    continue
                for x, y in zip(a[i1:i2], b[j1:j2]):
                    oc = x[1][1:-1]
                    if not is_obf(oc):
                        continue
                    k = (oc, x[2] + x[3])
                    v = y[2] + y[3]
                    (mv if x[3].startswith("(") else fv)[k][(y[1][1:-1], v)] += 1
    return fv, mv


def main():
    old_root, new_root, out = sys.argv[1:4]
    targets = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    old, new = parse_tree(old_root), parse_tree(new_root)
    global OLDT, NEWT
    OLDT, NEWT = old, new
    print("kelas lama", len(old), "baru", len(new), file=sys.stderr)
    mp = build_map(old, new)
    res = {"classes": mp, "members": {}}
    allm = {}
    for on, nn in mp.items():
        fm, mm = map_members(old[on], new[nn], mp)
        allm[on] = (fm, mm)
    fv, mv = seq_votes(old, new, mp, {k: v[1] for k, v in allm.items()})
    for on, nn in mp.items():
        fm, mm = allm[on]
        fm, mm = dict(fm), dict(mm)
        o_, n_ = old[on], new[nn]
        so = sorted((f[0], norm_type(f[1], mp, "old")) for f in o_.fields)
        sn = sorted((f[0], norm_type(f[1], mp, "new")) for f in n_.fields)
        if so == sn:  # nama field tidak berubah antarversi -> petakan identik
            ntype = {f[0]: f[1] for f in n_.fields}
            for f in o_.fields:
                fm[f[0] + ":" + f[1]] = f[0] + ":" + ntype[f[0]]
        for (oc, mem), cnt in fv.items():
            if oc != on:
                continue
            (cls, tgt), v = cnt.most_common(1)[0]
            if cls == nn and v / sum(cnt.values()) >= 0.6 and v >= 2:
                cur = fm.get(mem)
                if cur is None or cur.startswith("?"):
                    fm[mem] = tgt
        for (oc, mem), cnt in mv.items():
            if oc != on:
                continue
            (cls, tgt), v = cnt.most_common(1)[0]
            if cls == nn and v / sum(cnt.values()) >= 0.6:
                mm.setdefault(mem, tgt)
        if targets and on not in targets:
            continue
        res["members"][on] = {"fields": fm, "methods": mm}
        res.setdefault("uncertain", {})[on] = sorted(k for k, v in fm.items() if v.startswith("?"))
    if targets:
        res["unmapped_targets"] = [t for t in targets if t not in mp]
    json.dump(res, open(out, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
