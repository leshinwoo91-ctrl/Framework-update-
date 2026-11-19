"""Pencarian anchor yang mengabaikan baris .line dan baris kosong.

find(text, anchor) -> (start, end) offset karakter di text asli, atau None.
"""
import re


def _lines(t):
    out = []  # (normalized_line, start_offset, end_offset)
    pos = 0
    for raw in t.split("\n"):
        s = raw.strip()
        if s and not s.startswith(".line"):
            out.append((s, pos, pos + len(raw)))
        pos += len(raw) + 1
    return out


def find(text, anchor, start_at=0):
    a = [s for s, _, _ in _lines(anchor)]
    if not a:
        return None
    tl = _lines(text)
    n = len(a)
    for i in range(len(tl) - n + 1):
        if tl[i][1] < start_at:
            continue
        if tl[i][0] == a[0] and all(tl[i + k][0] == a[k] for k in range(n)):
            st = tl[i][1]
            # sertakan indentasi awal baris
            ls = text.rfind("\n", 0, st) + 1
            en = tl[i + n - 1][2]
            # anchor yang diakhiri newline: ikutkan newline-nya
            if anchor.endswith("\n") and en < len(text) and text[en] == "\n":
                en += 1
            return ls, en
    return None


def count(text, anchor):
    c, pos = 0, 0
    while True:
        r = find(text, anchor, pos)
        if not r:
            return c
        c += 1
        pos = r[1]
