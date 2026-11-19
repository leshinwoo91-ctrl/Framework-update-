# Daftar op patchset tahap 1 (39 op)

Kolom *op* mengikuti jenis op installer: `patch` (sisip di sebelum/sesudah anchor), `replace` (ganti teks), `new_file`, `asset`.

| # | op | file | keterangan |
|---|---|---|---|
| 0 | patch | `smali/com/esaptonor/ege/environment/MeisterActivity.smali` | mods folder creation |
| 1 | patch | `AndroidManifest.xml` | AndroidManifest.xml all-files-access permission |
| 2 | new_file | `smali/SrpgFw.smali` | SrpgFw host class (port 1.00) |
| 3 | patch | `smali/h81.smali` | h81.a() modLoadTextures call (1.00) |
| 4 | replace | `smali/yo.smali` | yo custom texture decode branch (1.00) |
| 5 | patch | `smali/k80.smali` | k80 mod loaders (ships/torpedoes/weapons) |
| 6 | patch | `smali/lk0.smali` | ei modAmmo field |
| 7 | replace | `smali/bm0.smali` | jj ammo detail panel launcher lookup |
| 8 | replace | `smali/nk0.smali` | nk0 ammo fire-check slot (1.00) |
| 9 | replace | `smali/nk0.smali` | nk0 ammo consume slot (1.00) |
| 10 | replace | `smali/w8.smali` | w8.N1 ammo type range (was h1.r4) |
| 11 | replace | `smali/w8.smali` | w8.a2 ammo type range (was h1.w4) |
| 12 | replace | `smali/fz.smali` | m5 ammo pickup type |
| 13 | replace | `smali/ro.smali` | c3 HUD ammo type |
| 14 | replace | `smali/y60.smali` | w7 f8.w size |
| 15 | replace | `smali/y60.smali` | w7 f8.o size |
| 16 | replace | `smali/wz.smali` | e6 fleet size limit (8 -> 12) |
| 17 | patch | `smali/g70.smali` | a8.d() damage-array bounds clamp |
| 18 | patch | `smali/y60.smali` | w7 damage-tick nextInt bounds clamp |
| 19 | new_file | `smali/ModsScreen.smali` | ModsScreen class (1.00) |
| 20 | asset | `assets/modloader/button_mods.png` | button_mods.png asset |
| 21 | patch | `smali/uv.smali` | h4 modsBtn field |
| 22 | patch | `smali/uv.smali` | uv.a() Mods button construction (1.00) |
| 23 | patch | `smali/uv.smali` | uv.f() Mods button tap dispatch (1.00) |
| 24 | patch | `smali/uv.smali` | h4.f() Mods button per-frame tick |
| 25 | replace | `smali/uv.smali` | uv.b() Mods button touch-up dispatch (1.00) |
| 26 | replace | `smali/uv.smali` | uv.b() Mods button touch-down dispatch (1.00) |
| 27 | patch | `smali/uv.smali` | uv.a() Mod Framework version label (1.00) |
| 28 | patch | `res/values/public.xml` | public.xml ic_launcher id |
| 29 | replace | `AndroidManifest.xml` | AndroidManifest.xml icon restore |
| 30 | patch | `smali/w60.smali` | q7 modDebrisSprites field |
| 31 | patch | `smali/y60.smali` | y60 modDebrisIndex field (1.00) |
| 32 | replace | `smali/ff.smali` | ff.b() custom debris sprite check (1.00) |
| 33 | patch | `smali/ff.smali` | l1.b() debris-exhausted suppress check |
| 34 | patch | `smali/y60.smali` | y60 custom debris prepare site 1 (1.00) |
| 35 | patch | `smali/y60.smali` | y60 custom debris prepare site 2 (1.00) |
| 36 | patch | `smali/df.smali` | df.c() save preview: begin (1.00) |
| 37 | patch | `smali/df.smali` | df.c() save preview: restore (1.00) |
| 38 | patch | `smali/df.smali` | df.f() real load: strict ship definitions (1.00) |

Nama kelas 0.9995 yang masih muncul di keterangan (misalnya `h4`, `w7`, `e6`) adalah nama asal op tersebut. File targetnya sudah memakai nama 1.00.
