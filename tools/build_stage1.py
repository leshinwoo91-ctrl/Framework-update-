#!/usr/bin/env python3
"""Bangun patchset framework untuk Space RPG 4 v1.00 — TAHAP 1.

Isi tahap 1: inti framework (startup, folder mods, log), tekstur custom, kapal custom,
senjata & torpedo custom, amunisi, debris kapal custom, batas fleet 12, tombol Mods +
layar Mods, label versi, proteksi save.

argv: patchset_lama.json draft_terjemahan.json smali_baru_root out.json
Semua anchor diambil sebagai TEKS PERSIS dari smali 1.00 (installer mewajibkan anchor unik).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fuzzy  # noqa: E402

orig_ps, draft_ps, root, out = sys.argv[1:5]
O = json.load(open(orig_ps))["ops"]
D = json.load(open(draft_ps))["ops"]
FILES = {}


def text(f):
    if f not in FILES:
        FILES[f] = open(os.path.join(root, f[len("smali/"):]), encoding="utf-8").read()
    return FILES[f]


def strip_lines(t):
    return "\n".join(l for l in t.split("\n") if not l.strip().startswith(".line"))


def method_range(t, sig):
    i = t.find(".method")
    while i != -1:
        e = t.find("\n", i)
        if t[i:e].rstrip().endswith(" " + sig):
            end = t.find(".end method", e)
            return i, end + len(".end method")
        i = t.find(".method", e)
    raise SystemExit("method tidak ada: " + sig)


def exact(f, lines, scope=None, to_method_end=False):
    """Cari baris (abaikan .line) dan kembalikan teks PERSIS dari file."""
    t = text(f)
    lo, hi = (0, len(t)) if scope is None else method_range(t, scope)
    seg = t[lo:hi]
    a = "\n".join("    " + l if not l.startswith(".") and not l.startswith(":") else l for l in lines)
    r = fuzzy.find(seg, "\n".join(lines))
    if r is None:
        raise SystemExit("anchor 1.00 tidak ketemu di %s: %r" % (f, lines[:2]))
    s, e = r
    if to_method_end:
        e = seg.find(".end method", s) + len(".end method")
    return seg[s:e]


ops = []


def add(op):
    ops.append(op)


def draft_exact(i):
    """Op yang anchor-nya sudah cocok longgar: ambil ulang sebagai teks persis."""
    o = dict(D[i])
    o.pop("_note", None)
    key = "anchor" if o["op"] == "patch" else "old"
    t = text(o["file"])
    r = fuzzy.find(t, o[key])
    if r is None:
        raise SystemExit("op %d tidak ketemu" % i)
    a = t[r[0]:r[1]]
    # pertahankan apakah anchor lama diawali indentasi atau tidak
    if not o[key].startswith(" "):
        a = a.lstrip(" ")
    o[key] = a
    if o["op"] == "replace":
        o["new"] = strip_lines(o["new"])
    else:
        o["code"] = strip_lines(o["code"])
    return o


# ---------------------------------------------------------------- inti
o = dict(D[0])
o["code"] = "\n    invoke-static/range {p0 .. p0}, LSrpgFw;->modStartup(Landroid/app/Activity;)V\n"
add(o)
add(dict(D[1]))  # manifest (ditangani installer)

# ---------------------------------------------------------------- kelas host SrpgFw
host_fields = "".join(D[i]["code"] for i in (7, 9, 14, 69, 105, 113))
host_methods = "".join(D[i]["code"] for i, x in enumerate(D) if x["file"] == "smali/SrpgFw.smali" and x["op"] == "append")
for i in (75, 111, 112):  # patch di dalam kode framework sendiri
    x = D[i]
    a = x["anchor"] if x["op"] == "patch" else x["old"]
    if host_methods.count(a) != 1:
        raise SystemExit("host anchor %d tidak unik" % i)
    if x["op"] == "replace":
        host_methods = host_methods.replace(a, x["new"], 1)
    else:
        host_methods = host_methods.replace(a, a + x["code"] if x.get("after", True) else x["code"] + a, 1)

# hanya method yang dibutuhkan tahap 1 (closure dari titik panggil)
bodies = {m.group(1): m.group(0) for m in re.finditer(
    r"^\.method [^\n]*?([\w$<>]+)\([^)]*\)\S+\n.*?^\.end method\n?", host_methods, re.M | re.S)}
calls = {k: set(re.findall(r"LSrpgFw;->(\w+)\(", v)) for k, v in bodies.items()}
ENTRY = {"modStartup", "modLoadTextures", "modLoadShips", "modLoadTorpedoes", "modLoadWeapons",
         "modResolveTexturePath", "modFallbackBitmap", "modAmmoSlot", "modAmmoItemId", "modAmmoTypeOfItem",
         "modAmmoLauncher", "modAmmoHudType", "modPrepareDebrisSprite", "modBuildMainMenuButton",
         "modCheckMainMenuModsButton", "modBuildMainMenuVersionLabel", "modListInstalled",
         "modMenuLoadBegin", "modMenuLoadEnd"}
ModsScreen = D[87]["code"]
ENTRY |= set(re.findall(r"LSrpgFw;->(\w+)\(", ModsScreen))
need, st = set(), list(ENTRY)
while st:
    x = st.pop()
    if x in need or x not in bodies:
        continue
    need.add(x)
    st += list(calls[x])
missing = sorted(ENTRY - set(bodies))
host = (".class public LSrpgFw;\n.super Ljava/lang/Object;\n.source \"SrpgFw.java\"\n\n"
        "# Helper Mod Framework (dulu ditempel ke h1 di v0.9995), di-port ke v1.00.\n\n"
        + host_fields + "\n" + "".join(bodies[k] for k in bodies if k in need))
add({"op": "new_file", "file": "smali/SrpgFw.smali", "code": host, "name": "SrpgFw host class (port 1.00)"})

# h81.a() == h1.a() lama: muat tekstur di awal inisialisasi data
add({"op": "patch", "file": "smali/h81.smali", "after": True,
     "anchor": exact("smali/h81.smali", [".method public static a()V", ".locals 17"]),
     "code": "\n\n    invoke-static {}, LSrpgFw;->modLoadTextures()V",
     "name": "h81.a() modLoadTextures call (1.00)"})

# tekstur custom: cabang decode di yo.onDrawFrame
old13 = exact("smali/yo.smali", [
    "invoke-virtual {v0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;",
    "move-result-object v10",
    "iget-object v11, v1, Lkj0;->b:Ljava/lang/Object;",
    "check-cast v11, Landroid/graphics/BitmapFactory$Options;",
    "invoke-static {v10, v8, v11}, Landroid/graphics/BitmapFactory;->decodeResource(Landroid/content/res/Resources;ILandroid/graphics/BitmapFactory$Options;)Landroid/graphics/Bitmap;",
    "move-result-object v12"], scope="onDrawFrame(Ljavax/microedition/khronos/opengles/GL10;)V")
add({"op": "replace", "file": "smali/yo.smali", "old": old13, "name": "yo custom texture decode branch (1.00)",
     "new": "    const v2, 0x10000\n    sub-int v2, v8, v2\n    if-gez v2, :modtex_vanilla\n\n"
            "    invoke-static {v8}, LSrpgFw;->modResolveTexturePath(I)Ljava/lang/String;\n    move-result-object v12\n"
            "    iget-object v11, v1, Lkj0;->b:Ljava/lang/Object;\n    check-cast v11, Landroid/graphics/BitmapFactory$Options;\n"
            "    invoke-static {v12, v11}, Landroid/graphics/BitmapFactory;->decodeFile(Ljava/lang/String;Landroid/graphics/BitmapFactory$Options;)Landroid/graphics/Bitmap;\n"
            "    move-result-object v12\n    if-nez v12, :modtex_done\n"
            "    invoke-static {v8}, LSrpgFw;->modFallbackBitmap(I)Landroid/graphics/Bitmap;\n    move-result-object v12\n"
            "    goto :modtex_done\n\n    :modtex_vanilla\n" + old13 + "\n\n    :modtex_done"})

# loader kapal / torpedo / senjata (dulu s8, sekarang k80)
add({"op": "patch", "file": "smali/k80.smali", "after": True,
     "anchor": exact("smali/k80.smali", ["iput-boolean v8, v1, Lk80;->c:Z"]),
     "code": "\n    invoke-static {}, LSrpgFw;->modLoadTextures()V\n    invoke-static {}, LSrpgFw;->modLoadShips()V\n"
             "    invoke-static {}, LSrpgFw;->modLoadTorpedoes()V\n    invoke-static {}, LSrpgFw;->modLoadWeapons()V",
     "name": "k80 mod loaders (ships/torpedoes/weapons)"})

# amunisi
add(draft_exact(68))   # lk0.modAmmo field
add(draft_exact(70))   # bm0 ammo detail panel
add({"op": "replace", "file": "smali/nk0.smali", "name": "nk0 ammo fire-check slot (1.00)",
     "old": exact("smali/nk0.smali", ["iget-object p0, v1, Lh70;->s:[I", "iget v0, v0, Llk0;->a:I", "aget p0, p0, v0"]).lstrip(" "),
     "new": "iget-object p0, v1, Lh70;->s:[I\n    invoke-static {v0}, LSrpgFw;->modAmmoSlot(Llk0;)I\n    move-result v0\n    aget p0, p0, v0"})
add({"op": "replace", "file": "smali/nk0.smali", "name": "nk0 ammo consume slot (1.00)",
     "old": exact("smali/nk0.smali", ["iget-object v0, v0, Lh70;->s:[I", "iget v1, v5, Llk0;->a:I", "aget v2, v0, v1"]).lstrip(" "),
     "new": "iget-object v0, v0, Lh70;->s:[I\n    invoke-static {v5}, LSrpgFw;->modAmmoSlot(Llk0;)I\n    move-result v1\n    aget v2, v0, v1"})
for sig, lab, nm in (("N1(Ljava/util/ArrayList;Ly60;)V", ":cond_0", "w8.N1 ammo type range (was h1.r4)"),
                     ("a2(Ljava/util/ArrayList;Ly60;)V", ":cond_3", "w8.a2 ammo type range (was h1.w4)")):
    add({"op": "replace", "file": "smali/w8.smali", "name": nm,
         "old": exact("smali/w8.smali", ["const/16 v2, 0x14", "if-ge v0, v2, " + lab, "add-int/lit8 v2, v0, 0x50"], scope=sig).lstrip(" "),
         "new": "const/16 v2, 0x40\n    if-ge v0, v2, %s\n    invoke-static {v0}, LSrpgFw;->modAmmoItemId(I)I\n    move-result v2" % lab})
add(draft_exact(80))   # fz ammo pickup type
add(draft_exact(81))   # ro HUD ammo type
add(draft_exact(82))   # y60 h70.A size
add(draft_exact(83))   # y60 h70.s size
add(draft_exact(84))   # wz fleet size 8 -> 12
add(draft_exact(85))   # g70 damage-array clamp
add(draft_exact(86))   # y60 nextInt clamp

# layar & tombol Mods
add({"op": "new_file", "file": "smali/ModsScreen.smali", "code": ModsScreen, "name": "ModsScreen class (1.00)"})
a89 = dict(D[89])
add(a89)
add(draft_exact(90))   # uv.modsBtn field
add({"op": "patch", "file": "smali/uv.smali", "after": True, "name": "uv.a() Mods button construction (1.00)",
     "anchor": exact("smali/uv.smali", ["const/4 v9, 0x1", "iput-boolean v9, v0, La20;->f:Z",
                                       "invoke-virtual {v3, v0}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z"], scope="a()V"),
     "code": "\n    invoke-static/range {p0 .. p0}, LSrpgFw;->modBuildMainMenuButton(Luv;)V"})
add({"op": "patch", "file": "smali/uv.smali", "after": True, "name": "uv.f() Mods button tap dispatch (1.00)",
     "anchor": exact("smali/uv.smali", ["iput-object v9, v1, Luv;->J:Ljava/lang/String;", ":cond_19"], scope="f(J)V"),
     "code": "\n    invoke-static {v1}, LSrpgFw;->modCheckMainMenuModsButton(Luv;)V"})
add(draft_exact(96))   # per-frame tick
for kind, c_in, c_out, lab in (("e", ":cond_a", ":cond_b", "up"), ("d", ":cond_12", ":cond_14", "down")):
    prev = "iget-object v1, p0, Luv;->j:Lcl0;"
    old = exact("smali/uv.smali", [c_in, prev,
                                   "invoke-virtual {v1, p2, p3, v0, p1}, Lcl0;->%s(FFILandroid/view/MotionEvent;)Z" % kind,
                                   "move-result v1", "if-eqz v1, " + c_out], scope="b(Landroid/view/MotionEvent;FF)Z")
    new = old.replace("if-eqz v1, " + c_out, "if-eqz v1, :modsbtn_%s_check" % lab, 1)
    tail = ("\n    goto :goto_0\n\n    :modsbtn_%s_check\n    iget-object v1, p0, Luv;->modsBtn:Lcl0;\n"
            "    invoke-virtual {v1, p2, p3, v0, p1}, Lcl0;->%s(FFILandroid/view/MotionEvent;)Z\n"
            "    move-result v1\n    if-eqz v1, %s") % (lab, kind, c_out)
    if kind == "e":
        add({"op": "replace", "file": "smali/uv.smali", "old": old, "new": new + tail,
             "name": "uv.b() Mods button touch-up dispatch (1.00)"})
    else:
        # touch-down: setelah 'if-eqz v1, :cond_14' langsung ada :cond_13/:goto_0 return
        add({"op": "replace", "file": "smali/uv.smali", "old": old, "new": new + tail + "\n    goto :goto_0",
             "name": "uv.b() Mods button touch-down dispatch (1.00)"})
add({"op": "patch", "file": "smali/uv.smali", "after": True, "name": "uv.a() Mod Framework version label (1.00)",
     "anchor": exact("smali/uv.smali", ["add-int/lit8 v10, v10, 0x4", "int-to-float v10, v10", "mul-float/2addr v9, v10",
                                       "mul-float v9, v9, v36", "sub-float/2addr v11, v9", "iput v11, v7, Lw5;->e:F",
                                       "iget-object v9, v2, Lzi0;->c:Ly20;", "iget v9, v9, Ly20;->b:I", "int-to-float v9, v9",
                                       "iget-object v10, v2, Lzi0;->h:Lel0;", "iget v10, v10, Lel0;->h:I", "int-to-float v10, v10",
                                       "mul-float v10, v10, v27", "sub-float/2addr v9, v10", "iput v9, v7, Lw5;->f:F",
                                       "iget-object v9, v2, Lzi0;->d:Lkj0;", "invoke-virtual {v9, v15}, Lkj0;->a(I)Lhj0;",
                                       "move-result-object v9", "invoke-virtual {v7, v9}, Lc20;->h(Lhj0;)V",
                                       "invoke-virtual {v7, v12}, Lnl;->j(I)Lll;", "move-result-object v7",
                                       "invoke-virtual {v3, v7}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z"], scope="a()V"),
     "code": "\n    invoke-static/range {p0 .. p0}, LSrpgFw;->modBuildMainMenuVersionLabel(Luv;)V"})
add(dict(D[101]))
add(dict(D[102]))

# debris kapal custom
add(draft_exact(103))  # w60.modDebrisSprites
add({"op": "patch", "file": "smali/y60.smali", "after": True, "name": "y60 modDebrisIndex field (1.00)",
     "anchor": exact("smali/y60.smali", [".field public t:Lw60;"]), "code": D[104]["code"]})
old107 = exact("smali/ff.smali", [
    "sget-object p5, Lso;->j:Lzi0;", "iget-object p5, p5, Lzi0;->d:Lkj0;", "if-nez p9, :cond_0", "const p6, 0x7f080169",
    ":goto_0", "invoke-virtual {p5, p6}, Lkj0;->a(I)Lhj0;", "move-result-object p5", "goto :goto_1", ":cond_0",
    "const p6, 0x7f08016a", "goto :goto_0", ":goto_1", "invoke-virtual {v1, p5}, Lc20;->h(Lhj0;)V",
    "invoke-virtual {v1, p1}, Lc20;->g([F)V"], scope="b([FFFFFFFFI)V")
new107 = strip_lines(D[107]["new"])
pre = new107[:new107.index("    :mdb_vanilla_pick")]
add({"op": "replace", "file": "smali/ff.smali", "old": old107, "name": "ff.b() custom debris sprite check (1.00)",
     "new": pre + "    :mdb_vanilla_pick\n" + old107 + "\n\n    :mdb_bound"})
add(draft_exact(108))  # ff.b debris suppress
add({"op": "patch", "file": "smali/y60.smali", "after": False, "name": "y60 custom debris prepare site 1 (1.00)",
     "anchor": exact("smali/y60.smali", ["move-object/from16 v35, v9", "move-object/from16 v36, v11",
                                        "invoke-virtual/range {v35 .. v44}, Lff;->b([FFFFFFFFI)V"], scope="a(J)V"),
     "code": "    invoke-static {v0}, LSrpgFw;->modPrepareDebrisSprite(Ly60;)V\n\n"})
add({"op": "patch", "file": "smali/y60.smali", "after": False, "name": "y60 custom debris prepare site 2 (1.00)",
     "anchor": exact("smali/y60.smali", ["move-object/from16 v35, v10",
                                        "invoke-virtual/range {v35 .. v44}, Lff;->b([FFFFFFFFI)V"], scope="a(J)V"),
     "code": "    invoke-static {v0}, LSrpgFw;->modPrepareDebrisSprite(Ly60;)V\n\n"})

# proteksi save (definisi kapal custom yang hilang)
add({"op": "patch", "file": "smali/df.smali", "after": True, "name": "df.c() save preview: begin (1.00)",
     "anchor": exact("smali/df.smali", [".method public final c()[Lpd;", ".locals 8"]),
     "code": "\n    invoke-static {}, LSrpgFw;->modMenuLoadBegin()V"})
add({"op": "patch", "file": "smali/df.smali", "after": False, "name": "df.c() save preview: restore (1.00)",
     "anchor": exact("smali/df.smali", ["return-object v0"], scope="c()[Lpd;", to_method_end=True),
     "code": "    invoke-static {}, LSrpgFw;->modMenuLoadEnd()V\n\n"})
add({"op": "patch", "file": "smali/df.smali", "after": True, "name": "df.f() real load: strict ship definitions (1.00)",
     "anchor": exact("smali/df.smali", [".method public final f()Lpd;", ".locals 8"]),
     "code": "\n    invoke-static {}, LSrpgFw;->modMenuLoadEnd()V"})

base = json.load(open(orig_ps))
res = {k: v for k, v in base.items() if k != "ops"}
res["game_version"] = "1.00"
res["framework_version"] = base["framework_version"] + "-port1.00-stage1"
res["ported_from"] = base["game_version"]
res["ops"] = ops
json.dump(res, open(out, "w"), indent=1)
print("ops:", len(ops), "| method SrpgFw:", len(need), "| entry tanpa body:", missing)
