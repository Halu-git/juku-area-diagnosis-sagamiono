# -*- coding: utf-8 -*-
"""レポート用グラフ・図の生成 (matplotlib, 日本語フォント)"""
import json, math
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Rectangle
import matplotlib.patheffects as pe

OUT = "/home/hatch/workspace/estat-analysis/sample-01/output"
FIG = "/home/hatch/workspace/estat-analysis/sample-01/output/fig"
import os; os.makedirs(FIG, exist_ok=True)

for f in font_manager.findSystemFonts():
    if "NotoSansCJK" in f or "NotoSansJP" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False
C_MAIN = "#1f5fa6"; C_SUB = "#e07b39"; C_GRAY = "#8a8f98"; C_LIGHT = "#c9d8ea"

S = json.load(open(f"{OUT}/agg_summary.json"))

# ---------- 1. 人口ピラミッド (1km圏 2020) ----------
pyr = pd.DataFrame(S["pyramid_1km_overlap"])
fig, ax = plt.subplots(figsize=(7.2, 6.4))
y = np.arange(len(pyr))
ax.barh(y, -pyr["male"], color=C_MAIN, height=0.78, label="男性")
ax.barh(y, pyr["female"], color=C_SUB, height=0.78, label="女性")
ax.set_yticks(y); ax.set_yticklabels(pyr["age"], fontsize=8)
ax.set_xlabel("人", fontsize=9)
ax.set_title("図：商圏（半径1km）の年齢別人口ピラミッド（2020年国勢調査）", fontsize=11)
ax.legend(fontsize=9); ax.grid(axis="x", color="#e5e7eb")
ax.set_axisbelow(True)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
xt = ax.get_xticks(); ax.set_xticklabels([f"{abs(int(v)):,}" for v in xt], fontsize=8)
fig.tight_layout(); fig.savefig(f"{FIG}/pyramid.png", dpi=200); plt.close(fig)

# ---------- 2. 学齢人口の推移 2015->2020 ----------
labels = ["500m圏\n小学生(6-11)", "500m圏\n中学生等(12-15)", "1km圏\n小学生(6-11)", "1km圏\n中学生等(12-15)"]
v15 = [S["age2015_500_overlap"]["学齢_小学生6-11推計"], S["age2015_500_overlap"]["学齢_中学生等12-15推計"],
       S["age2015_1000_overlap"]["学齢_小学生6-11推計"], S["age2015_1000_overlap"]["学齢_中学生等12-15推計"]]
v20 = [S["age2020_500_overlap"]["学齢_小学生6-11推計"], S["age2020_500_overlap"]["学齢_中学生等12-15推計"],
       S["age2020_1000_overlap"]["学齢_小学生6-11推計"], S["age2020_1000_overlap"]["学齢_中学生等12-15推計"]]
x = np.arange(4); w = 0.36
fig, ax = plt.subplots(figsize=(7.2, 3.9))
ax.bar(x - w/2, v15, w, color=C_GRAY, label="2015年")
ax.bar(x + w/2, v20, w, color=C_MAIN, label="2020年")
for xi, (a, b) in enumerate(zip(v15, v20)):
    ax.text(xi - w/2, a + 60, f"{a:,.0f}", ha="center", fontsize=8)
    ax.text(xi + w/2, b + 60, f"{b:,.0f}", ha="center", fontsize=8)
    ax.text(xi, max(a, b) + 330, f"+{(b/a-1)*100:.1f}%", ha="center", fontsize=9, color=C_MAIN, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylabel("人（5歳階級からの按分推計）", fontsize=9)
ax.set_title("図：学齢人口の推移（2015年→2020年）", fontsize=11)
ax.legend(fontsize=9); ax.grid(axis="y", color="#e5e7eb"); ax.set_axisbelow(True)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.set_ylim(0, max(v20) * 1.22)
fig.tight_layout(); fig.savefig(f"{FIG}/school_trend.png", dpi=200); plt.close(fig)

# ---------- 3. 年齢3区分の構成比: 商圏1km vs 南区 ----------
def shares(d, total_key, young, mid, old):
    t = d[total_key]
    return [young/t*100, mid/t*100, old/t*100]
a20 = S["age2020_1000_overlap"]
def grp(d, keys_y, keys_m, keys_o, tot):
    yv = sum(d[f"{g}人口総数"] for g in keys_y); mv = sum(d[f"{g}人口総数"] for g in keys_m); ov = sum(d[f"{g}人口総数"] for g in keys_o)
    return [yv/tot*100, mv/tot*100, ov/tot*100]
Y = ["０～４歳", "５～９歳", "１０～１４歳"]
M = ["１５～１９歳","２０～２４歳","２５～２９歳","３０～３４歳","３５～３９歳","４０～４４歳","４５～４９歳","５０～５４歳","５５～５９歳","６０～６４歳"]
O = ["６５～６９歳","７０～７４歳","７５～７９歳","８０～８４歳","８５～８９歳","９０～９４歳","９５歳以上"]
area = grp(a20, Y, M, O, a20["人口（総数）"])
# 南区: 15歳未満 31,234 / 総数 281,411 (表3 再掲より 15-64歳, 65歳以上を算出)
ward = [31234/281411*100, 170188/281411*100, 70792/281411*100]  # 表3再掲の確定値 (年齢不詳 9,197人を含むため合計は100%にならない)
fig, ax = plt.subplots(figsize=(7.2, 2.9))
cats = ["0～14歳", "15～64歳", "65歳以上"]
xx = np.arange(3); w = 0.36
ax.bar(xx - w/2, area, w, color=C_MAIN, label="商圏（半径1km）")
ax.bar(xx + w/2, ward, w, color=C_GRAY, label="相模原市南区")
for xi, (a, b) in enumerate(zip(area, ward)):
    ax.text(xi - w/2, a + 1, f"{a:.1f}%", ha="center", fontsize=9)
    ax.text(xi + w/2, b + 1, f"{b:.1f}%", ha="center", fontsize=9)
ax.set_xticks(xx); ax.set_xticklabels(cats, fontsize=10)
ax.set_ylabel("構成比（%）", fontsize=9)
ax.set_title("図：年齢3区分の構成比（2020年）", fontsize=11)
ax.legend(fontsize=9); ax.grid(axis="y", color="#e5e7eb"); ax.set_axisbelow(True)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.set_ylim(0, max(max(area), max(ward)) * 1.25)
fig.tight_layout(); fig.savefig(f"{FIG}/age_shares.png", dpi=200); plt.close(fig)
print("age shares area:", [round(v, 2) for v in area], "ward(draft):", [round(v, 2) for v in ward])

# ---------- 4. 商圏メッシュ地図 (学齢6-15推計/セル) ----------
cells = pd.read_csv(f"{OUT}/mesh_cells_1km.csv", dtype={"KEY_CODE": str})
keys = pd.read_csv(f"{OUT}/mesh_keys_distance.csv", dtype={"KEY_CODE": str})
cells = cells.merge(keys[["KEY_CODE", "sw_lat", "sw_lon"]], on="KEY_CODE", how="left")
LAT0, LON0 = 35.53222, 139.43836
KX = math.pi/180 * 6371000 * math.cos(math.radians(LAT0)); KY = math.pi/180 * 6371000
def XY(lat, lon): return (lon - LON0) * KX, (lat - LAT0) * KY
DLAT, DLON = 7.5/3600, 11.25/3600
fig, ax = plt.subplots(figsize=(7.4, 7.4))
vals = cells["学齢6-15推計"].clip(lower=0)
norm = plt.Normalize(0, max(60, vals.quantile(0.98)))
cmap = plt.cm.YlOrBr
for _, r in cells.iterrows():
    x0, y0 = XY(r.sw_lat, r.sw_lon); x1, y1 = XY(r.sw_lat + DLAT, r.sw_lon + DLON)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=cmap(norm(r["学齢6-15推計"])),
                           edgecolor="white", linewidth=0.3))
ax.add_patch(Circle((0, 0), 1000, fill=False, edgecolor=C_MAIN, linewidth=1.6))
ax.add_patch(Circle((0, 0), 500, fill=False, edgecolor=C_MAIN, linewidth=1.2, linestyle="--"))
ax.plot(0, 0, marker="*", markersize=17, color="#d43a2f", markeredgecolor="white", markeredgewidth=0.8)
ax.annotate("相模大野駅", (0, 0), textcoords="offset points", xytext=(10, 8), fontsize=10, fontweight="bold",
            path_effects=[pe.withStroke(linewidth=3, foreground="white")])
ax.annotate("半径1km", (690, 700), fontsize=9, color=C_MAIN)
ax.annotate("半径500m", (330, 330), fontsize=9, color=C_MAIN)
ax.set_xlim(-1250, 1250); ax.set_ylim(-1250, 1250); ax.set_aspect("equal")
ax.set_xlabel("相模大野駅からの距離（m）", fontsize=9); ax.set_ylabel("距離（m）", fontsize=9)
ax.set_title("図：商圏メッシュ別 学齢人口（6～15歳・推計）の分布（250mメッシュ）", fontsize=11)
sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, shrink=0.85); cb.set_label("学齢人口（人/セル）", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/mesh_map.png", dpi=200); plt.close(fig)
print("charts done")
