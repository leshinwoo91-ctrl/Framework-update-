# SRPG4 Mod Framework: port ke Space RPG 4 v1.00

Port **SRPG4-Mod-Framework v0.8.6** (karya [reaperyeah420-cpu](https://github.com/reaperyeah420-cpu/SRPG4-Mod-Framework), awalnya untuk game v0.9995) ke **Space RPG 4 v1.00** (`com.esaptonor.spacerpg4`).
Port ini dikerjakan bertahap. Framework asli tetap milik pembuatnya, dan repo ini hanya berisi hasil port beserta tool untuk membuatnya.

**Status: Tahap 1 selesai.** Sudah lolos uji statis, tapi belum dites di HP.

## Isi repo

| Folder | Isi |
|---|---|
| `installer/` | `ModFrameworkInstaller-v0.8.6-port1.00-stage1.apk`, installer asli dengan patchset versi 1.00. Bisa langsung dipakai. |
| `patchset/` | `patchset_1.00_stage1.json` (39 op). Kalau mau, bisa dimasukkan sendiri ke installer asli. |
| `map/` | Peta kelas dan member 0.9995 → 1.00 (486 kelas) |
| `tools/` | Tool port: mapper, penerjemah patchset, builder tahap 1, simulator installer, verifikasi rujukan |
| `tools/sign/` | Tool align dan sign APK installer |
| `docs/` | Daftar op, metode port, rencana tahap berikutnya |

## Yang ikut di tahap 1
- Inti framework: startup, folder `mods`, log
- Tekstur custom
- **Kapal custom** dan debris kapal custom
- **Senjata custom** (blaster, misil, beam), **torpedo custom**, dan amunisi custom
- Batas fleet 8 → 12
- Tombol **Mods** dan layar Mods di menu utama, plus label versi framework
- Proteksi save (definisi kapal custom yang hilang)

## Belum ikut
- **Tahap 2:** komoditas custom (batas 8 → 50, ikon)
- **Tahap 3:** planet, sistem bintang, hyperlane, visual planet

Bagian mod yang berisi fitur di atas akan diabaikan dulu.

## Cara pakai
1. **Backup save.** Uninstall versi Play Store akan menghapus save.
2. Pastikan game yang terpasang **v1.00 dari Play Store** (base + split APK). Installer menolak kalau `versionName` tidak persis `1.00`.
3. Install APK dari `installer/`, lalu jalankan patch seperti biasa.
   - APK ini di-sign ulang dengan kunci lain, jadi kalau installer asli masih terpasang, uninstall dulu.
   - SHA-256: `a98cb9d488fde684990ef5cf9005c748912743cf8dae38ad8f2dc702b24013ae`
4. Salin mod ke `Android/data/com.esaptonor.spacerpg4/files/mods/`, lalu buka game. Tombol **Mods** ada di menu utama.

## Kalau gagal
- **Saat patch:** kirim pesan error dari installer, misalnya `anchor not found in ...`.
- **Saat main/crash:** kirim logcat dengan filter `SRPG4` dan `AndroidRuntime`.

## Catatan teknis singkat
- Helper framework yang dulu ditempel ke kelas `h1` sekarang ada di kelas baru `SrpgFw`. Alasannya, `h1` dipecah di 1.00 menjadi `w8`, `h81`, `l60`, dan `tk0`.
- Semua anchor diambil sebagai teks persis dari smali 1.00. Hasilnya diuji dengan aturan installer (anchor harus persis dan unik): 35/35 op smali berhasil diterapkan.
- Hasil patch berhasil dirakit jadi dex. Sebanyak 1.150 rujukan field/method sudah dicek, dan semuanya ada di 1.00.
- Detail lengkap ada di [docs/PORTING.md](docs/PORTING.md) dan [docs/OPS_TAHAP1.md](docs/OPS_TAHAP1.md).

## Kredit
- Framework asli: **reaperyeah420-cpu** (komunitas Discord Space RPG 4). Dipakai dan dikembangkan dengan izin.
- Port 1.00: leshinwoo91-ctrl
