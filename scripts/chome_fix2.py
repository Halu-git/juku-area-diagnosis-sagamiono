# -*- coding: utf-8 -*-
"""町丁集計の最終補完: 15-19歳を表3から再取得して再計算 / EC町丁は区総計行を確認"""
import pandas as pd, numpy as np, json

DATA = "/home/hatch/workspace/estat-analysis/sample-01/data"
OUT  = "/home/hatch/workspace/estat-analysis/sample-01/output"

def load_t3(path):
    df = pd.read_csv(path, encoding="cp932", header=4, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df
def num(s): return pd.to_numeric(s.replace({"-": None, "X": None, "x": None}), errors="coerce")

sel = pd.read_pickle(f"{OUT}/chome_1km_polys.pkl")
sel["city_code"] = sel["KEY_CODE"].str[:5]
sel["aza_code"] = sel["KEY_CODE"].str[5:]
ch = pd.read_csv(f"{OUT}/chome_trade_area.csv")

rows = []
for pref, f3 in (("14", "kanagawa_2020_table3_age.csv"), ("13", "tokyo_2020_table3_age.csv")):
    t3 = load_t3(f"{DATA}/{f3}")
    t3 = t3[t3["男女"] == "総数"].copy()
    t3["full_name"] = t3["大字・町名"].fillna("") + t3["字・丁目名"].fillna("")
    for c in ("0～4歳", "15～19歳"): t3[c] = num(t3[c])
    s = sel[sel.pref == pref]
    m = s.merge(t3[["市区町村コード", "町丁字コード", "0～4歳", "15～19歳"]],
                left_on=["city_code", "aza_code"], right_on=["市区町村コード", "町丁字コード"], how="left")
    # 名称フォールバック
    for i, r in m[m["15～19歳"].isna()].iterrows():
        cand = t3[(t3["市区町村名"] == r["CITY_NAME"]) & (t3["full_name"] == r["S_NAME"])]
        if len(cand):
            m.loc[i, "0～4歳"] = cand.iloc[0]["0～4歳"]
            m.loc[i, "15～19歳"] = cand.iloc[0]["15～19歳"]
    rows.append(m[["S_NAME", "CITY_NAME", "0～4歳", "15～19歳"]])
add = pd.concat(rows)
ch = ch.drop(columns=["0～4歳", "15～19歳"], errors="ignore").merge(add, on=["S_NAME", "CITY_NAME"], how="left")
ch["小学生6-11推計"] = ch["5～9歳"]*4/5 + ch["10～14歳"]*2/5
ch["中学生等12-15推計"] = ch["10～14歳"]*3/5 + ch["15～19歳"]*1/5
ch["学齢6-15推計"] = ch["小学生6-11推計"] + ch["中学生等12-15推計"]
ch["学齢割合%"] = ch["学齢6-15推計"] / ch["総数"] * 100
ch = ch.sort_values("学齢6-15推計", ascending=False)
ch.to_csv(f"{OUT}/chome_trade_area.csv", index=False)
print("町丁合計: 総数", ch["総数"].sum(), "世帯", ch["世帯数_境界DBF"].sum(),
      "学齢6-15推計", round(ch["学齢6-15推計"].sum(), 0),
      " (小学生", round(ch["小学生6-11推計"].sum(), 0), "/ 中学生等", round(ch["中学生等12-15推計"].sum(), 0), ")")
print("NaN残:", ch["学齢6-15推計"].isna().sum(), "町丁")

# --- EC 2021: 区・市レベルの総計行を探す ---
ec = pd.read_pickle(f"{OUT}/ec_chome_raw.pkl")
labels = ec.iloc[0]
ecb = ec.iloc[1:]
names = ecb["AZA_NAME"].astype(str)
for pat in ("相模原市南区", "相模原市", "町田市"):
    sub = ecb[names == pat]
    print(pat, "rows:", len(sub))
    if len(sub):
        print("  全産業事業所数:", sub["T001167001"].tolist(), " 従業者数:", sub["T001167019"].tolist(),
              " 教育事業所数:", sub["T001167015"].tolist())
# AZA_CODE が全0桁の総計行
z = ecb[ecb["AZA_CODE"].astype(str).str.fullmatch(r"0+")]
print("AZA_CODE all-zero rows:", len(z), z[["KEY_CODE", "CITY_NAME", "AZA_NAME"]].head(3).to_string() if len(z) else "")
