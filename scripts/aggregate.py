# -*- coding: utf-8 -*-
"""
商圏集計マスター: メッシュ集計 (2020/2015/EC2021) + 町丁集計 + 境界ポリゴン処理
出力: output/agg_summary.json, 各種CSV
"""
import math, json, struct
import pandas as pd
import numpy as np

DATA = "/home/hatch/workspace/estat-analysis/sample-01/data"
OUT  = "/home/hatch/workspace/estat-analysis/sample-01/output"
LAT0, LON0 = 35.53222, 139.43836
R_EARTH = 6371000.0
KX = math.pi/180 * R_EARTH * math.cos(math.radians(LAT0))
KY = math.pi/180 * R_EARTH

def xy(lat, lon):
    return (lon - LON0) * KX, (lat - LAT0) * KY

AGE_GROUPS = ["０～４歳","５～９歳","１０～１４歳","１５～１９歳","２０～２４歳","２５～２９歳",
              "３０～３４歳","３５～３９歳","４０～４４歳","４５～４９歳","５０～５４歳","５５～５９歳",
              "６０～６４歳","６５～６９歳","７０～７４歳","７５～７９歳","８０～８４歳","８５～８９歳",
              "９０～９４歳","９５歳以上"]   # 2020年メッシュの階級 (最上位は95歳以上)
AGE_GROUPS_2015 = AGE_GROUPS[:17] + ["８５歳以上"]  # 2015年メッシュの階級 (最上位は85歳以上)
def age_col(df, g, suffix="人口総数"):
    # 2020: '５～９歳人口総数' / 2015: '５～９歳人口総数' (same pattern)
    c = f"{g}{suffix}"
    return c if c in df.columns else None

def school_split(age_sums):
    """5歳階級 (総数) から学齢人口を按分推計"""
    a = age_sums
    elem = a["５～９歳"]*4/5 + a["１０～１４歳"]*2/5     # 6-11歳
    juni = a["１０～１４歳"]*3/5 + a["１５～１９歳"]*1/5   # 12-15歳
    return elem, juni, elem + juni

keys = pd.read_csv(f"{OUT}/mesh_keys_distance.csv", dtype={"KEY_CODE": str})
keys["KEY_CODE"] = keys["KEY_CODE"].str.zfill(10)
kmap_min = dict(zip(keys.KEY_CODE, keys.dmin))
kmap_cen = dict(zip(keys.KEY_CODE, keys.dcen))

def agg_mesh(df, value_cols, tag):
    df = df.copy()
    df["KEY_CODE"] = df["KEY_CODE"].astype(str).str.zfill(10)
    df["dmin"] = df["KEY_CODE"].map(kmap_min)
    df["dcen"] = df["KEY_CODE"].map(kmap_cen)
    res = {}
    for radius in (500, 1000):
        for method, col in (("overlap", "dmin"), ("centroid", "dcen")):
            sub = df[df[col] <= radius]
            res[f"{tag}_{radius}_{method}"] = {c: float(sub[c].sum()) for c in value_cols}
            res[f"{tag}_{radius}_{method}_cells"] = int(len(sub))
    return res, df

summary = {}

# ---- 2020 年齢別 ----
age20 = pd.read_pickle(f"{OUT}/age20.pkl")
pop20 = pd.read_pickle(f"{OUT}/pop20.pkl")
age15 = pd.read_pickle(f"{OUT}/age15.pkl")
pop15 = pd.read_pickle(f"{OUT}/pop15.pkl")

cols20 = ["人口（総数）", "人口（総数）男", "人口（総数）女"] + [f"{g}人口総数" for g in AGE_GROUPS]
r20, age20d = agg_mesh(age20, cols20, "age2020")
summary.update(r20)
cols_p20 = ["世帯総数", "一般世帯数", "核家族世帯数一般世帯数", "６歳未満世帯員のいる世帯数一般世帯数"]
rp20, _ = agg_mesh(pop20, cols_p20, "hh2020")
summary.update(rp20)

cols15 = ["人口総数", "人口総数男", "人口総数女"] + [f"{g}人口総数" for g in AGE_GROUPS_2015]
r15, age15d = agg_mesh(age15, cols15, "age2015")
summary.update(r15)
cols_p15 = ["世帯総数", "一般世帯数", "核家族の一般世帯数", "６歳未満世帯員のいる一般世帯数"]
rp15, _ = agg_mesh(pop15, cols_p15, "hh2015")
summary.update(rp15)

# 学齢推計などを要約に付加
def add_school(summary, tag, prefix):
    for radius in (500, 1000):
        for method in ("overlap", "centroid"):
            d = summary[f"{tag}_{radius}_{method}"]
            ages = {g: d[f"{g}人口総数"] for g in ("５～９歳", "１０～１４歳", "１５～１９歳")}
            e, j, t = school_split(ages)
            summary[f"{tag}_{radius}_{method}"]["学齢_小学生6-11推計"] = e
            summary[f"{tag}_{radius}_{method}"]["学齢_中学生等12-15推計"] = j
            summary[f"{tag}_{radius}_{method}"]["学齢_対象6-15推計"] = t
            summary[f"{tag}_{radius}_{method}"]["参考_5-14歳"] = ages["５～９歳"] + ages["１０～１４歳"]
add_school(summary, "age2020", "2020")
add_school(summary, "age2015", "2015")

# セル単位の保存 (2020, 両半径・overlap)
cells = age20d[["KEY_CODE", "dmin", "dcen", "人口（総数）"] + [f"{g}人口総数" for g in AGE_GROUPS]].copy()
cells = cells.merge(pop20[["KEY_CODE", "世帯総数"]], on="KEY_CODE", how="left")
e_list, j_list, t_list = [], [], []
for _, row in cells.iterrows():
    ages = {g: (row[f"{g}人口総数"] if pd.notna(row[f"{g}人口総数"]) else 0) for g in AGE_GROUPS}
    e, j, t = school_split(ages)
    e_list.append(e); j_list.append(j); t_list.append(t)
cells["学齢6-15推計"] = t_list
cells["in500"] = cells.dmin <= 500
cells["in1000"] = cells.dmin <= 1000
cells[cells.in1000].to_csv(f"{OUT}/mesh_cells_1km.csv", index=False)

# 年齢ピラミッド用 (1km overlap, 男女別)
age20m = age20d.copy()
sub = age20m[age20m.dmin <= 1000]
pyr = []
for g in AGE_GROUPS:
    pyr.append({"age": g.replace("歳", ""), "male": float(sub[f"{g}人口男"].sum()),
                "female": float(sub[f"{g}人口女"].sum()), "total": float(sub[f"{g}人口総数"].sum())})
pd.DataFrame(pyr).to_csv(f"{OUT}/age_pyramid_1km.csv", index=False)
summary["pyramid_1km_overlap"] = pyr

# ---- 経済センサス 2021 (500mメッシュ H) ----
ec = pd.read_csv(f"{DATA}/ec2021_estab_h500/tblT001164H5339.txt", encoding="cp932", dtype=str)
ec = ec.iloc[1:].copy()  # 1行目は項目名行
# 事業所数ブロックは T001164001-070 (071以降は従業者数で同名ラベルが重複するためコードで扱う)
CODE2NAME = {"T001164046": "Ｏ823学習塾", "T001164048": "Ｏ82K外国語会話教授業",
             "T001164038": "Ｏ812小学校", "T001164039": "Ｏ813中学校",
             "T001164037": "Ｏ811幼稚園", "T001164040": "Ｏ814高等学校，中等教育学校"}
ec = ec.rename(columns=CODE2NAME)
ec["KEY_CODE"] = ec["KEY_CODE"].astype(str).str.zfill(9)
def mesh9_sw(code):
    p_lat, p_lon = int(code[0:2]), int(code[2:4])
    s_lat, s_lon = int(code[4]), int(code[5])
    t_lat, t_lon = int(code[6]), int(code[7])
    f = int(code[8])
    lat = p_lat/1.5 + s_lat*(5/60) + t_lat*(30/3600) + (15/3600 if f in (3,4) else 0)
    lon = 100 + p_lon + s_lon*(7.5/60) + t_lon*(45/3600) + (22.5/3600 if f in (2,4) else 0)
    return lat, lon
def cell_dmin(code, dlat, dlon):
    la, lo = mesh9_sw(code) if len(code) == 9 else (None, None)
    xa, ya = xy(la, lo); xb, yb = xy(la + dlat, lo + dlon)
    dx = 0.0 if xa <= 0 <= xb else min(abs(xa), abs(xb))
    dy = 0.0 if ya <= 0 <= yb else min(abs(ya), abs(yb))
    return math.hypot(dx, dy)
ec["dmin"] = ec["KEY_CODE"].apply(lambda c: cell_dmin(c, 15/3600, 22.5/3600))
ec_cols = ["Ｏ823学習塾", "Ｏ82K外国語会話教授業", "Ｏ812小学校", "Ｏ813中学校", "Ｏ811幼稚園", "Ｏ814高等学校，中等教育学校"]
for c in ec_cols:
    ec[c] = pd.to_numeric(ec[c], errors="coerce")
ecres = {}
for radius in (500, 1000):
    s = ec[ec.dmin <= radius]
    ecres[str(radius)] = {c: float(s[c].sum()) for c in ec_cols}
    ecres[str(radius)]["cells"] = int(len(s))
summary["ec2021_mesh500m"] = ecres
ec[ec.dmin <= 1000][["KEY_CODE", "dmin"] + ec_cols].to_csv(f"{OUT}/ec_mesh_cells_1km.csv", index=False)

with open(f"{OUT}/agg_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1, default=float)
print("summary keys:", len(summary))
for k in ("age2020_500_overlap", "age2020_1000_overlap", "hh2020_1000_overlap"):
    print(k, summary[k])
print("EC:", ecres)
