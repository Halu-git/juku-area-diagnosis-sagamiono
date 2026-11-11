# -*- coding: utf-8 -*-
"""競合マップ: 町丁別 競合教室数コロプレイス + Excelへの競合シート追加"""
import sys, math
sys.path.insert(0, "/home/hatch/workspace/estat-analysis/sample-01/scripts")
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Polygon as MplPolygon
import matplotlib.patheffects as pe
from chome import read_dbf, read_shp, xy, DATA, OUT

for f in font_manager.findSystemFonts():
    if "NotoSansCJK" in f: font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"

comp = pd.read_csv(f"{DATA}/competitors_sagamiono.csv")
comp = comp[~comp["備考"].astype(str).str.contains("圏外の可能性", na=False)].copy()
comp["chome"] = comp["所在地（町名・丁目）"].str.replace("相模原市南区", "", regex=False)
KANJI = str.maketrans("123456789", "一二三四五六七八九")
comp["chome"] = comp["chome"].str.translate(KANJI)  # 境界データの漢数字表記に合わせる
cnt = comp.groupby("chome").size().to_dict()
print("counts:", cnt, "total:", len(comp))

fields, recs = read_dbf(f"{DATA}/boundary14/r2ka14.dbf")
shapes = read_shp(f"{DATA}/boundary14/r2ka14.shp")
target = {}
for rec, rings in zip(recs, shapes):
    name = rec["S_NAME"]
    if name in cnt:
        target[name] = rings

fig, ax = plt.subplots(figsize=(7.4, 7.4))
cmap = plt.cm.Blues
norm = plt.Normalize(0, 36)
for name, rings in target.items():
    v = cnt[name]
    for ring in rings:
        pts = [xy(lat, lon) for lon, lat in ring]
        ax.add_patch(MplPolygon(pts, closed=True, facecolor=cmap(norm(v)),
                                edgecolor="#33506e", linewidth=0.7))
    cx = sum(p[0] for ring in rings for p in [xy(la, lo) for lo, la in ring]) / sum(len(ring) for ring in rings)
    cy = sum(p[1] for ring in rings for p in [xy(la, lo) for lo, la in ring]) / sum(len(ring) for ring in rings)
    ax.annotate(f"{name.replace('相模大野', '相模大野')}\n{v}件", (cx, cy), ha="center", va="center",
                fontsize=8.5, fontweight="bold",
                color="white" if v >= 5 else "#12314e",
                path_effects=[pe.withStroke(linewidth=2.5, foreground="#12314e" if v >= 5 else "white")])
ax.add_patch(Circle((0, 0), 1000, fill=False, edgecolor="#1f5fa6", linewidth=1.4))
ax.add_patch(Circle((0, 0), 500, fill=False, edgecolor="#1f5fa6", linewidth=1.1, linestyle="--"))
ax.plot(0, 0, marker="*", markersize=17, color="#d43a2f", markeredgecolor="white", markeredgewidth=0.8)
ax.annotate("相模大野駅", (0, 0), textcoords="offset points", xytext=(10, -16), fontsize=10, fontweight="bold",
            path_effects=[pe.withStroke(linewidth=3, foreground="white")])
ax.set_xlim(-1250, 1250); ax.set_ylim(-1250, 1250); ax.set_aspect("equal")
ax.set_xlabel("相模大野駅からの距離（m）", fontsize=9); ax.set_ylabel("距離（m）", fontsize=9)
ax.set_title("図：町丁別の競合教室数（Web確認 2026年11月、半径1km圏内 48件）", fontsize=11)
fig.tight_layout(); fig.savefig(f"{OUT}/fig/competitor_map.png", dpi=200); plt.close(fig)
print("map saved")

# Excel へ競合シート追加
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side
wb = load_workbook(f"{OUT}/sample01_集計.xlsx")
if "競合リスト" in wb.sheetnames: del wb["競合リスト"]
ws = wb.create_sheet("競合リスト")
HDR = PatternFill("solid", fgColor="1F5FA6"); HDRF = Font(color="FFFFFF", bold=True, size=10)
THIN = Border(*[Side(style="thin", color="B0B7C3")] * 4)
ws["A1"] = "競合リスト：相模大野駅 半径1km圏内の学習塾・英会話教室（Web確認、2026-11-11）"
ws["A1"].font = Font(bold=True, size=12)
cols = list(comp.columns)
for j, h in enumerate(cols, 1):
    c = ws.cell(row=3, column=j, value=h); c.fill = HDR; c.font = HDRF; c.border = THIN
for i, (_, r) in enumerate(comp.iterrows(), 4):
    for j, col in enumerate(cols, 1):
        c = ws.cell(row=i, column=j, value=r[col]); c.border = THIN
for j, w in enumerate([38, 12, 24, 22, 52, 44], 1):
    from openpyxl.utils import get_column_letter
    ws.column_dimensions[get_column_letter(j)].width = w
ws.cell(row=3 + len(comp) + 2, column=1,
        value="注：圏外の可能性ありとして除外した4件（創英ゼミナール相模大野校、学研教室文京教室、Oasis英会話・相模大野、明光義塾東林間教室）は data/competitors_sagamiono.csv に記録。経済センサス2021では圏内の学習塾39事業所・外国語会話教授業8事業所。").font = Font(size=9, color="666666")
wb.save(f"{OUT}/sample01_集計.xlsx")
print("excel updated")
