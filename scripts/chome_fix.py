# -*- coding: utf-8 -*-
"""町丁集計の補完: 名称マッチで未マッチ町丁を救済 + EC町丁集計の結合"""
import pandas as pd, numpy as np, json

DATA = "/home/hatch/workspace/estat-analysis/sample-01/data"
OUT  = "/home/hatch/workspace/estat-analysis/sample-01/output"

def load_t3(path):
    df = pd.read_csv(path, encoding="cp932", header=4, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df
def num(s): return pd.to_numeric(s.replace({"-": None, "X": None, "x": None}), errors="coerce")

AGE = ["総数","0～4歳","5～9歳","10～14歳","15～19歳"]
sel = pd.read_pickle(f"{OUT}/chome_1km_polys.pkl")
ch = pd.read_csv(f"{OUT}/chome_trade_area.csv")
miss = ch[ch["総数"].isna()]
print("未マッチ:", miss[["CITY_NAME", "S_NAME"]].to_string())

t3k = load_t3(f"{DATA}/kanagawa_2020_table3_age.csv")
t3k = t3k[t3k["男女"] == "総数"].copy()
t3k["full_name"] = t3k["大字・町名"].fillna("") + t3k["字・丁目名"].fillna("")
for c in AGE: t3k[c] = num(t3k[c])
for _, row in miss.iterrows():
    cand = t3k[(t3k["市区町村名"] == row["CITY_NAME"]) & (t3k["full_name"] == row["S_NAME"])]
    if len(cand):
        r = cand.iloc[0]
        print("救済:", row["S_NAME"], "level", r["地域階層レベル"], "総数", r["総数"])
        i = ch[(ch["CITY_NAME"] == row["CITY_NAME"]) & (ch["S_NAME"] == row["S_NAME"])].index[0]
        for c in AGE: ch.loc[i, c] = r[c]
ch["小学生6-11推計"] = ch["5～9歳"]*4/5 + ch["10～14歳"]*2/5
ch["中学生等12-15推計"] = ch["10～14歳"]*3/5 + ch["15～19歳"]*1/5
ch["学齢6-15推計"] = ch["小学生6-11推計"] + ch["中学生等12-15推計"]
ch["学齢割合%"] = ch["学齢6-15推計"] / ch["総数"] * 100
ch = ch.rename(columns={"SETAI": "世帯数_境界DBF", "JINKO": "人口_境界DBF"})
ch = ch.drop(columns=["世帯数"], errors="ignore")
ch = ch.sort_values("学齢6-15推計", ascending=False)
ch.to_csv(f"{OUT}/chome_trade_area.csv", index=False)
print("\n交差町丁 合計: 総数", ch["総数"].sum(), "世帯(DBF)", ch["世帯数_境界DBF"].sum(),
      "学齢6-15推計", round(ch["学齢6-15推計"].sum(), 0))

# ---- 経済センサス 2021 町丁 (T001167, 神奈川) ----
ec = pd.read_pickle(f"{OUT}/ec_chome_raw.pkl")
labels = ec.iloc[0]
ec = ec.iloc[1:].copy()
name2code = {}
for c in ec.columns:
    lab = str(labels[c]).strip()
    if lab.startswith("AR_"): name2code["全産業_事業所数"] = c
    if lab == "O_教育，学習支援業": name2code["教育学習支援業_事業所数"] = c
    if lab.startswith("男女計AR_"): name2code["全産業_従業者数"] = c
    if lab == "男女計O_教育，学習支援業": name2code["教育学習支援業_従業者数"] = c
print("EC cols:", name2code)
ec["KEY_CODE"] = ec["KEY_CODE"].astype(str).str.zfill(11)
for nm, c in name2code.items():
    ec[nm] = pd.to_numeric(ec[c], errors="coerce")
selk = sel[sel.pref == "14"][["KEY_CODE", "S_NAME"]]
m = selk.merge(ec[["KEY_CODE"] + list(name2code.keys())], on="KEY_CODE", how="left")
m.to_csv(f"{OUT}/ec_chome_trade_area.csv", index=False)
print(m.to_string())
print("EC町丁合計(南区・交差町丁):", {nm: m[nm].sum() for nm in name2code})
