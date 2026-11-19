# Rencana berikutnya

## Tahap 1: selesai, menunggu tes di HP
- Perlu konfirmasi bahwa `versionName` game yang terpasang persis `1.00`.
- Uji coba: tombol Mods, kapal custom, senjata/torpedo custom, batas fleet 12, dan load save.

## Tahap 2: komoditas
- Komoditas custom
- Batas komoditas 8 → 50
- Ikon komoditas

## Tahap 3: dunia
- Planet custom, sistem bintang, hyperlane
- Visual planet

## Member yang belum terpetakan
Semuanya hanya dipakai di tahap 2/3, jadi tidak mempengaruhi tahap 1.
- `l6.S4`
- `oi.g(III[F)V`
- `j3`: hanya muncul di komentar
- `q4.<init>` → `vw`: tidak punya constructor di kedua versi (sama seperti aslinya)

## Gabung dengan mod menu
Mod menu Space RPG 4 ada di repo terpisah. Hook-nya (`patch_hooks.py`) akan dipasang di atas smali yang sudah dipatch framework, setelah tahap 1 terbukti jalan.

Kedua patch sama-sama menyentuh `MeisterActivity` dan `y60`, tapi di titik yang berbeda. Script hook juga akan berhenti sendiri kalau polanya berubah.
