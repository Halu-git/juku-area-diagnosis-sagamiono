# -*- coding: utf-8 -*-
"""町丁集計: 1km圏交差町丁の人口・学齢・世帯 + 経済センサス町丁 (南区)"""
import pandas as pd, numpy as np, json

DATA = "/home/hatch/workspace/estat-analysis/sample-01/data"
OUT  = "/home/hatch/workspace/estat-analysis/sample-01/output"

def load_t3(path):
    df = pd.read_csv(path, encoding="cp932", header=4, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df
def load_t1(path):
    df = pd.read_csv(path, encoding="cp932", header=4, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df
def num(s):
    return pd.to_numeric(s.replace({"-": None, "X": None, "x": None}), errors="coerce")

sel = pd.read_pickle(f"{OUT}/chome_1km_polys.pkl")
sel["city_code"] = sel["KEY_CODE"].str[:5]
sel["aza_code"] = sel["KEY_CODE"].str[5:]

AGE = ["総数","0～4歳","5～9歳","10～14歳","15～19歳","20～24歳","25～29歳","30～34歳",
       "35～39歳","40～44歳","45～49歳","50～54歳","55～59歳","60～64歳","65～69歳",
       "70～74歳","75～79歳","80～84歳","85～89歳","90～94歳","95～99歳","100歳以上"]

frames = []
for pref, f3, f1 in (("14", "kanagawa_2020_table3_age.csv", "kanagawa_2020_table1_pop_hh.csv"),
                     ("13", "tokyo_2020_table3_age.csv", "tokyo_2020_table1_pop_hh.csv")):
    t3 = load_t3(f"{DATA}/{f3}")
    t3 = t3[(t3["男女"] == "総数") & (t3["地域階層レベル"] == "4")]
    t3 = t3.rename(columns={"市区町村コード": "city_code", "町丁字コード": "aza_code"})
    for c in AGE:
        if c in t3.columns: t3[c] = num(t3[c])
    t1 = load_t1(f"{DATA}/{f1}")
    t1 = t1[t1["地域階層レベル"] == "4"].rename(columns={"市区町村コード": "city_code", "町丁字コード": "aza_code"})
    t1["人口_表1"] = num(t1["総数"])
    # 世帯数は表1の最後の列 (列名が「世帯数」)
    hh_col = [c for c in t1.columns if c == "世帯数"]
    t1["世帯数"] = num(t1[hh_col[0]]) if hh_col else np.nan
    m = sel[sel.pref == pref].merge(
        t3[["city_code", "aza_code"] + [c for c in AGE if c in t3.columns]],
        on=["city_code", "aza_code"], how="left").merge(
        t1[["city_code", "aza_code", "人口_表1", "世帯数"]], on=["city_code", "aza_code"], how="left")
    frames.append(m)

ch = pd.concat(frames, ignore_index=True)
ch["小学生6-11推計"] = ch["5～9歳"]*4/5 + ch["10～14歳"]*2/5
ch["中学生等12-15推計"] = ch["10～14歳"]*3/5 + ch["15～19歳"]*1/5
ch["学齢6-15推計"] = ch["小学生6-11推計"] + ch["中学生等12-15推計"]
ch["学齢割合%"] = ch["学齢6-15推計"] / ch["総数"] * 100
cols = ["CITY_NAME", "S_NAME", "mindist_m", "総数", "世帯数", "5～9歳", "10～14歳",
        "小学生6-11推計", "中学生等12-15推計", "学齢6-15推計", "学齢割合%", "JINKO", "SETAI"]
ch_out = ch[cols].sort_values("学齢6-15推計", ascending=False)
ch_out.to_csv(f"{OUT}/chome_trade_area.csv", index=False)
print(ch_out.to_string())
print("\n交差町丁の単純合計 (町丁全体を含む):")
print("総数:", ch["総数"].sum(), " 世帯数:", ch["世帯数"].sum(), " 学齢6-15推計:", round(ch["学齢6-15推計"].sum(), 1))
print("南区のみ総数:", ch[ch.pref == '14']["総数"].sum(), " 学齢:", round(ch[ch.pref == '14']["学齢6-15推計"].sum(), 1))

# --- 南区・相模原市 全体 (D7 文脈) ---
t3k = load_t3(f"{DATA}/kanagawa_2020_table3_age.csv")
ward = t3k[(t3k["男女"] == "総数") & (t3k["地域階層レベル"] == "1")]
print("\n区レベル総数:")
print(ward[["市区町村コード", "市区町村名", "総数", "（再掲）15歳未満"]].to_string())

# --- 経済センサス 2021 町丁 (神奈川, T001167) ---
ec = pd.read_csv(f"{DATA}/ec2021_chome_industry/tblT001167C14.txt", encoding="cp932", dtype=str)
labels = ec.iloc[0]
print("\nEC chome columns:")
for c in ec.columns[:40]:
    print(c, str(labels[c]).strip()[:50])
ec.to_pickle(f"{OUT}/ec_chome_raw.pkl")
