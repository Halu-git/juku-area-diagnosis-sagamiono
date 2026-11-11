# -*- coding: utf-8 -*-
"""
町丁・字等境界 (e-Stat 統計GIS, 令和2年国勢調査 JGD2011) の純Python読み取りと
相模大野駅 中心 半径1km/500m 円との交差判定。
"""
import math, struct, json
import pandas as pd

DATA = "/home/hatch/workspace/estat-analysis/sample-01/data"
OUT  = "/home/hatch/workspace/estat-analysis/sample-01/output"
LAT0, LON0 = 35.53222, 139.43836
R_EARTH = 6371000.0
KX = math.pi/180 * R_EARTH * math.cos(math.radians(LAT0))
KY = math.pi/180 * R_EARTH
def xy(lat, lon): return (lon - LON0) * KX, (lat - LAT0) * KY

def read_dbf(path):
    with open(path, "rb") as f:
        raw = f.read()
    nrec = struct.unpack("<I", raw[4:8])[0]
    hlen = struct.unpack("<H", raw[8:10])[0]
    rlen = struct.unpack("<H", raw[10:12])[0]
    fields = []
    off = 32
    while raw[off] != 0x0D:
        name = raw[off:off+11].split(b"\x00")[0].decode("ascii")
        ftype = chr(raw[off+11])
        flen = raw[off+16]
        fields.append((name, ftype, flen))
        off += 32
    recs = []
    for i in range(nrec):
        rec = raw[hlen + i*rlen: hlen + (i+1)*rlen]
        if rec[0:1] == b"*":
            continue
        pos = 1; row = {}
        for name, ftype, flen in fields:
            v = rec[pos:pos+flen]
            try: v = v.decode("cp932").strip()
            except Exception: v = v.decode("latin1").strip()
            row[name] = v
            pos += flen
        recs.append(row)
    return fields, recs

def read_shp(path):
    with open(path, "rb") as f:
        raw = f.read()
    shapes = []
    off = 100
    while off < len(raw):
        recno, clen = struct.unpack(">2i", raw[off:off+8])
        content = raw[off+8: off+8+clen*2]
        stype = struct.unpack("<i", content[0:4])[0]
        if stype == 5:  # Polygon
            nparts, npts = struct.unpack("<2i", content[36:44])
            parts = struct.unpack(f"<{nparts}i", content[44:44+4*nparts])
            poff = 44 + 4*nparts
            pts = struct.unpack(f"<{npts*2}d", content[poff:poff+16*npts])
            coords = [(pts[2*i], pts[2*i+1]) for i in range(npts)]  # (lon, lat)
            rings = []
            idx = list(parts) + [npts]
            for a, b in zip(idx[:-1], idx[1:]):
                rings.append(coords[a:b])
            shapes.append(rings)
        else:
            shapes.append([])
        off += 8 + clen*2
    return shapes

def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay
    L2 = dx*dx + dy*dy
    if L2 == 0: return math.hypot(px-ax, py-ay)
    t = max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))

def poly_mindist(rings):
    best = 1e18
    for ring in rings:
        pts = [xy(lat, lon) for lon, lat in ring]
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            d = seg_dist(0.0, 0.0, ax, ay, bx, by)
            if d < best: best = d
    return best

def point_in_poly(rings, x=0.0, y=0.0):
    inside = False
    for ring in rings:
        pts = [xy(lat, lon) for lon, lat in ring]
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]; x2, y2 = pts[(i+1) % n]
            if (y1 > y) != (y2 > y):
                xin = (x2-x1) * (y-y1) / (y2-y1) + x1
                if x < xin: inside = not inside
    return inside

results = []
for pref, sub in (("14", "boundary14"), ("13", "boundary13")):
    fields, recs = read_dbf(f"{DATA}/{sub}/r2ka{pref}.dbf")
    print(pref, "fields:", fields)
    shapes = read_shp(f"{DATA}/{sub}/r2ka{pref}.shp")
    print(pref, "records:", len(recs), "shapes:", len(shapes))
    for rec, rings in zip(recs, shapes):
        if not rings: continue
        # 粗い絞り込み: 全頂点の最小距離が 1300m 超なら対象外
        quick = min(math.hypot(*xy(lat, lon)) for ring in rings for lon, lat in ring)
        if quick > 1300 and not point_in_poly(rings):
            continue
        d = 0.0 if point_in_poly(rings) else poly_mindist(rings)
        if d <= 1000:
            results.append({**rec, "mindist_m": round(d, 1), "pref": pref})

out = pd.DataFrame(results)
print(out.to_string())
out.to_pickle(f"{OUT}/chome_1km_polys.pkl")
out.drop(columns=[c for c in out.columns if c not in
                  ("KEY_CODE","PREF_NAME","CITY_NAME","S_NAME","mindist_m","pref")],
         errors="ignore").to_csv(f"{OUT}/chome_1km_list.csv", index=False)
