import os
"""Cari method baru yang paling mirip dengan method lama. argv: old_root new_root Kelas method_sig_prefix [topN]"""
import sys, importlib.util
spec = importlib.util.spec_from_file_location("sm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "smalimap.py")); sm = importlib.util.module_from_spec(spec); spec.loader.exec_module(sm)
old_root, new_root, cname, msig = sys.argv[1:5]
top = int(sys.argv[5]) if len(sys.argv) > 5 else 5
o = sm.parse_file(f"{old_root}/{cname}.smali")
ms = [m for m in o.methods if (m["name"] + "(" + m["params"] + ")" + m["ret"]).startswith(msig)]
new = sm.parse_tree(new_root)
for m in ms:
    res = []
    for c in new.values():
        for x in c.methods:
            if x["static"] != m["static"] or len(x["params"]) and m["params"] == "" and False:
                continue
            s = 3 * sm.jacc(m["strings"], x["strings"]) + 2 * sm.jacc(m["nums"], x["nums"]) + 3 * sm.jacc(m["ops"], x["ops"])
            s -= abs(x["n"] - m["n"]) / max(x["n"], m["n"], 1)
            res.append((s, c.name, x["name"] + "(" + x["params"] + ")" + x["ret"], x["n"]))
    res.sort(reverse=True)
    print("LAMA", cname, m["name"] + "(" + m["params"] + ")" + m["ret"], "n=", m["n"])
    for r in res[:top]: print("   %.2f %s.%s n=%d" % r)
