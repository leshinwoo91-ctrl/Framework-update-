# Metode port 0.9995 → 1.00

Game di-obfuscate dengan R8, jadi nama kelas berubah total antar versi. Contohnya `k4` di 0.9995 menjadi `uv` di 1.00.
Port dilakukan dalam 4 langkah.

## 1. Pemetaan kelas: `tools/smalimap.py`

```bash
python3 -I tools/smalimap.py <smali_0.9995> <smali_1.00> map.json
```

- **Sidik jari kelas.** Setiap kelas diberi sidik jari dari string konstan, konstanta numerik besar, bentuk field/method (tipe obfuscated dinormalisasi jadi `O`), dan superclass/interface.
- **Skor dan kunci.** Setiap pasangan kandidat diberi skor, dan pasangan yang paling yakin dikunci lebih dulu.
- **Propagasi.** Setelah kelas A → A' terkunci, tipe field/param pada posisi yang cocok ikut menjadi bukti untuk kelas yang dirujuk.
- **Member.** Field dan method dipetakan dengan dua cara:
  - **Suara urutan pemakaian.** Urutan akses member di method yang sudah dipetakan disejajarkan dengan difflib.
  - **Aturan identitas** (nama dan tipe sama), yang hanya dipakai kalau himpunan field kedua kelas identik.
- **Kasus ragu.** Grup multi-tipe yang belum yakin diberi tanda `?`, lalu dicek manual.

Hasilnya ada di `map/class_map_0.9995_to_1.00.json` (486 kelas).

Contoh kesalahan yang ditemukan lalu diperbaiki: pemetaan berdasarkan urutan deklarasi sempat salah (`f8.o` → `h70.s`, `f8.w` → `h70.A`). Sekarang suara pemakaian diprioritaskan.

## 2. Terjemahan patchset: `tools/translate_patchset.py`

```bash
python3 -I tools/translate_patchset.py patchset_0.9995.json map.json <smali_1.00> draft.json
```

- Mengganti nama kelas, member, dan path file target.
- Menerjemahkan tipe di dalam signature member, termasuk untuk owner yang tidak di-obfuscate seperti `ModsScreen`.
- 5 member helper `h1` dipetakan manual ke `SrpgFw`.
- Melaporkan anchor yang tidak ditemukan.

## 3. Bangun patchset tahap 1: `tools/build_stage1.py`

```bash
python3 -I tools/build_stage1.py patchset_0.9995.json draft.json <smali_1.00> patchset_1.00_stage1.json
```

Setiap anchor diambil ulang sebagai **teks persis** dari smali 1.00. `fuzzy.py` dipakai untuk mencarinya sambil mengabaikan `.line` dan baris kosong.

Perbaikan khusus 1.00:
- **Op 0:** activity di 1.00 ada di `v1`, bukan `v0`. Solusinya `invoke-static/range {p0 .. p0}`.
- **`BitmapFactory.Options`:** di 1.00 field ini bertipe `Object` (`kj0.b`), jadi ditambah `check-cast`.
- **Anchor debris 109/110:** isinya identik, jadi dibuat unik dengan menyertakan baris sebelumnya.

## 4. Verifikasi

```bash
python3 -I tools/apply_patchset.py patchset_1.00_stage1.json <smali_1.00> hasil/   # simulasi installer
python3 -I tools/verify_refs.py hasil/ --patchset patchset_1.00_stage1.json        # cek rujukan
python3 -I tools/coverage.py patchset_1.00_stage1.json map.json                    # cakupan map
```

`apply_patchset.py` meniru aturan installer:
- Jenis op: `asset`, `new_file`, `replace`, `patch`, `append`.
- Anchor harus persis dan unik. Kalau tidak, error `anchor not found / ambiguous`.
- Key `after` wajib ada.
- Op di luar `smali/` dilewati.

Hasilnya:
- 35/35 op smali berhasil.
- Hasil patch bisa dirakit jadi dex.
- 547 + 603 rujukan dicek, 0 gagal.

Tool bantu:
- `findmethod.py`: cari method 1.00 yang paling mirip dengan method lama.
- `debugvotes.py`: lihat suara pemetaan untuk satu field.

## Aturan installer yang penting

- `game_version` di patchset harus sama persis dengan `versionName` game yang terpasang.
- Installer sendiri yang menambahkan izin `MANAGE_EXTERNAL_STORAGE`.

## Sign installer: `tools/sign/`

```bash
python3 tools/sign/realign.py asli.apk unsigned.apk assets/patchset.json=patchset_1.00_stage1.json
java -cp apksig-8.5.2.jar:. Sign unsigned.apk hasil.apk kunci.p12 <password>
java -cp apksig-8.5.2.jar:. Verify hasil.apk
```

- `realign.py` mengganti file di APK, lalu me-*align* entri STORED ke 4 byte lewat extra field 0xD935.
- `Sign` menandatangani APK dengan v1, v2, dan v3.

Kunci `.p12` sengaja **tidak** di-upload. Pakai kuncimu sendiri.
