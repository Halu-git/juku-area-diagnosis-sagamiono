# -*- coding: utf-8 -*-
"""
相模大野駅を中心とする半径500m/1km商圏のメッシュ集計
データ: e-Stat 統計GIS 地域メッシュ統計 250mメッシュ (第1次地域区画 5339)
 - 2020 国勢調査 5歳階級別人口 T001196 (JGD2011)
 - 2020 国勢調査 人口及び世帯 T001142 (JGD2011)
 - 2015 国勢調査 5歳階級別人口 T001177 -> 実際は T001178 (Q)
 - 2015 国勢調査 その1 人口等基本集計 T000876
秘匿処理: HTKSYORI=2 の行は値が '*' で秘匿先 (HTKSAKI) の行に合算済み。
          集計では HTKSYORI!=2 の行のみを合計する (二重計上回避)。
"""
import math, json
import pandas as pd
import numpy as np

DATA = "/home/hatch/workspace/estat-analysis/sample-01/data"
OUT  = "/home/hatch/workspace/estat-analysis/sample-01/output"

# 相模大野駅 中心座標 (出典: 駅位置の公開情報。レポートでは方法注記に明記)
LAT0, LON0 = 35.53222, 139.43836

# ---------- メッシュコード -> 緯度経度 (南西角) ----------
def mesh_sw(code: str):
    code = str(code).zfill(10)
    p_lat, p_lon = int(code[0:2]), int(code[2:4])
    s_lat, s_lon = int(code[4]), int(code[5])
    t_lat, t_lon = int(code[6]), int(code[7])
    f, q = int(code[8]), int(code[9])
    lat = p_lat / 1.5 + s_lat * (5/60) + t_lat * (30/3600) \
        + (15/3600 if f in (3,4) else 0) + (7.5/3600 if q in (3,4) else 0)
    lon = 100 + p_lon + s_lon * (7.5/60) + t_lon * (45/3600) \
        + (22.5/3600 if f in (2,4) else 0) + (11.25/3600 if q in (2,4) else 0)
    return lat, lon

DLAT = 7.5/3600   # 250mメッシュ 緯度幅
DLON = 11.25/3600 # 250mメッシュ 経度幅

def cell_distances(code):
    """中心点からセル矩形までの最小距離(m) と セル中心までの距離(m)"""
    la, lo = mesh_sw(code)
    R = 6371000.0
    kx = math.pi/180 * R * math.cos(math.radians(LAT0))
    ky = math.pi/180 * R
    x0, y0 = 0.0, 0.0
    xa, ya = (lo - LON0) * kx, (la - LAT0) * ky
    xb, yb = (lo + DLON - LON0) * kx, (la + DLAT - LAT0) * ky
    dx = 0.0 if xa <= x0 <= xb else min(abs(xa - x0), abs(xb - x0))
    dy = 0.0 if ya <= y0 <= yb else min(abs(ya - y0), abs(yb - y0))
    dmin = math.hypot(dx, dy)
    dcen = math.hypot((xa+xb)/2, (ya+yb)/2)
    return dmin, dcen

# ---------- メッシュファイル読み込み ----------
def load_mesh(path, tid):
    df = pd.read_csv(path, encoding="cp932", dtype=str, header=0)
    labels = df.iloc[0]  # 2行目が項目名
    df = df.iloc[1:].copy()
    rename = {}
    for c in df.columns:
        if c.startswith(tid):
            rename[c] = str(labels[c]).strip().replace("　", "")
    df = df.rename(columns=rename)
    df = df[df["HTKSYORI"] != "2"].copy()   # 秘匿行を除外 (合算先に含まれる)
    for c in df.columns:
        if c not in ("KEY_CODE", "HTKSYORI", "HTKSAKI", "GASSAN"):
            df[c] = pd.to_numeric(df[c].replace("*", np.nan), errors="coerce")
    return df

age20 = load_mesh(f"{DATA}/mesh2020_age5_q250/tblT001196Q5339.txt", "T001196")
pop20 = load_mesh(f"{DATA}/mesh2020_pop_hh_q250/tblT001142Q5339.txt", "T001142")
age15 = load_mesh(f"{DATA}/mesh2015_age5_q250/tblT001178Q5339.txt", "T001178")
pop15 = load_mesh(f"{DATA}/mesh2015_base_q250/tblT000876Q5339.txt", "T000876")

print("age20 cols:", [c for c in age20.columns][:8], "...")
print("pop20 cols:", list(pop20.columns))
print("age15 label sample:", [c for c in age15.columns][:8])
print("pop15 cols:", list(pop15.columns))

# 距離計算 (2020のキー集合を基準。2015も同一グリッド)
keys = age20[["KEY_CODE"]].drop_duplicates()
d = keys["KEY_CODE"].apply(cell_distances)
keys["dmin"] = [x[0] for x in d]
keys["dcen"] = [x[1] for x in d]
keys["sw_lat"] = keys["KEY_CODE"].apply(lambda c: mesh_sw(c)[0])
keys["sw_lon"] = keys["KEY_CODE"].apply(lambda c: mesh_sw(c)[1])
keys.to_csv(f"{OUT}/mesh_keys_distance.csv", index=False)
print("cells total(5339):", len(keys),
      "| overlap500:", (keys.dmin<=500).sum(), "| overlap1000:", (keys.dmin<=1000).sum(),
      "| centroid500:", (keys.dcen<=500).sum(), "| centroid1000:", (keys.dcen<=1000).sum())

json.dump({"keys_rows": len(keys)}, open(f"{OUT}/mesh_meta.json","w"))
age20.to_pickle(f"{OUT}/age20.pkl"); pop20.to_pickle(f"{OUT}/pop20.pkl")
age15.to_pickle(f"{OUT}/age15.pkl"); pop15.to_pickle(f"{OUT}/pop15.pkl")
print("saved pickles")
