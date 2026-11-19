"""Debug suara (votes) pemetaan field. argv: smali_lama smali_baru map.json Kelas.field [...]"""
import os
import sys, importlib.util, json
spec = importlib.util.spec_from_file_location("sm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "smalimap.py")); sm = importlib.util.module_from_spec(spec); spec.loader.exec_module(sm)
old = sm.parse_tree(sys.argv[1]); new = sm.parse_tree(sys.argv[2])
mp = json.load(open(sys.argv[3]))["classes"]
sm.NEWSET.update(mp.values())
allm = {}
for on, nn in mp.items():
    allm[on] = sm.map_members(old[on], new[nn], mp)[1]
fv, mv = sm.seq_votes(old, new, mp, allm)
for key in sys.argv[4:]:
    c, f = key.split(".", 1)
    for (oc, mem), cnt in fv.items():
        if oc == c and mem.startswith(f + ":"):
            print(key, mem, cnt.most_common(4))
