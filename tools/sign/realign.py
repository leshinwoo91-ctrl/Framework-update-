"""Salin APK, ganti entry tertentu, dan ratakan (align 4) entry STORED. argv: in.apk out.apk name=path ..."""
import sys, zipfile, struct
src, dst = sys.argv[1], sys.argv[2]
repl = dict(a.split("=", 1) for a in sys.argv[3:])
zi = zipfile.ZipFile(src)
zo = zipfile.ZipFile(dst, "w")
for info in zi.infolist():
    if info.filename.startswith("META-INF/") and info.filename.upper().endswith((".SF", ".RSA", ".EC", ".DSA", "MANIFEST.MF")):
        continue
    data = open(repl[info.filename], "rb").read() if info.filename in repl else zi.read(info)
    ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    ni.compress_type = info.compress_type
    ni.external_attr = info.external_attr
    if ni.compress_type == zipfile.ZIP_STORED:
        off = zo.fp.tell()
        hdr = 30 + len(ni.filename.encode())
        pad = (4 - (off + hdr + 6) % 4) % 4
        ni.extra = struct.pack("<HHH", 0xD935, 2 + pad, 4) + b"\0" * pad
    zo.writestr(ni, data)
zo.close()
z = zipfile.ZipFile(dst)
bad = [i.filename for i in z.infolist() if i.compress_type == 0 and (i.header_offset + 30 + len(i.filename.encode()) + len(i.extra)) % 4]
print("entry:", len(z.infolist()), "| stored tidak rata:", bad)
