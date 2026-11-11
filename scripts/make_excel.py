# -*- coding: utf-8 -*-
"""集計Excel の生成 (openpyxl)"""
import json
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "/home/hatch/workspace/estat-analysis/sample-01/output"
S = json.load(open(f"{OUT}/agg_summary.json"))
W = json.load(open(f"{OUT}/ward_minami.json"))

wb = Workbook()
HDR = PatternFill("solid", fgColor="1F5FA6")
HDRF = Font(color="FFFFFF", bold=True, size=10)
TITLE = Font(bold=True, size=13)
THIN = Border(*[Side(style="thin", color="B0B7C3")] * 4)

def sheet(ws, title, rows, widths=None, note=None):
    ws["A1"] = title; ws["A1"].font = TITLE
    r0 = 3
    for j, h in enumerate(rows[0], 1):
        c = ws.cell(row=r0, column=j, value=h); c.fill = HDR; c.font = HDRF; c.border = THIN
    for i, row in enumerate(rows[1:], r0 + 1):
        for j, v in enumerate(row, 1):
            c = ws.cell(row=i, column=j, value=v); c.border = THIN
            if isinstance(v, float): c.number_format = '#,##0.0'
            elif isinstance(v, int): c.number_format = '#,##0'
    if widths:
        for j, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(j)].width = w
    if note:
        ws.cell(row=r0 + len(rows) + 1, column=1, value=note).font = Font(size=9, color="666666")
    return ws

def g(tag, key): return S[tag][key]

# ---- 1. 要約 ----
ws = wb.active; ws.title = "要約"
ws["A1"] = "出店エリア診断レポート（サンプル） 集計Excel"; ws["A1"].font = Font(bold=True, size=14)
ws["A2"] = "対象：相模大野駅（相模原市南区）中心 半径500m／1km商圏 ― 学習塾・英会話教室の2校目出店を想定"
rows = [
    ["指標", "半径500m", "半径1km", "備考"],
    ["総人口（2020年国勢調査）", int(g("age2020_500_overlap", "人口（総数）")), int(g("age2020_1000_overlap", "人口（総数）")), "250mメッシュ集計（重なり方式）"],
    ["総人口（2015年）", int(g("age2015_500_overlap", "人口総数")), int(g("age2015_1000_overlap", "人口総数")), "同上"],
    ["総人口の増減（2015→2020）", "+4.6%", "+5.1%", ""],
    ["世帯数（2020年）", int(g("hh2020_500_overlap", "世帯総数")), int(g("hh2020_1000_overlap", "世帯総数")), ""],
    ["世帯数（2015年）", int(g("hh2015_500_overlap", "世帯総数")), int(g("hh2015_1000_overlap", "世帯総数")), ""],
    ["学齢人口 6～15歳 推計（2020年）", round(g("age2020_500_overlap", "学齢_対象6-15推計")), round(g("age2020_1000_overlap", "学齢_対象6-15推計")), "5歳階級からの按分推計"],
    ["うち小学生 6～11歳 推計", round(g("age2020_500_overlap", "学齢_小学生6-11推計")), round(g("age2020_1000_overlap", "学齢_小学生6-11推計")), ""],
    ["うち中学生等 12～15歳 推計", round(g("age2020_500_overlap", "学齢_中学生等12-15推計")), round(g("age2020_1000_overlap", "学齢_中学生等12-15推計")), ""],
    ["学齢人口 6～15歳 推計（2015年）", round(g("age2015_500_overlap", "学齢_対象6-15推計")), round(g("age2015_1000_overlap", "学齢_対象6-15推計")), ""],
    ["学齢人口の増減（2015→2020）", "+10.5%", "+9.0%", ""],
    ["核家族世帯数（2020年）", int(g("hh2020_500_overlap", "核家族世帯数一般世帯数")), int(g("hh2020_1000_overlap", "核家族世帯数一般世帯数")), ""],
    ["学習塾の事業所数（2021年経済センサス）", int(S["ec2021_mesh500m"]["500"]["Ｏ823学習塾"]), int(S["ec2021_mesh500m"]["1000"]["Ｏ823学習塾"]), "500mメッシュ集計"],
    ["外国語会話教授業の事業所数（2021年）", int(S["ec2021_mesh500m"]["500"]["Ｏ82K外国語会話教授業"]), int(S["ec2021_mesh500m"]["1000"]["Ｏ82K外国語会話教授業"]), ""],
    ["小学校数（2021年）", int(S["ec2021_mesh500m"]["500"]["Ｏ812小学校"]), int(S["ec2021_mesh500m"]["1000"]["Ｏ812小学校"]), ""],
    ["中学校数（2021年）", int(S["ec2021_mesh500m"]["500"]["Ｏ813中学校"]), int(S["ec2021_mesh500m"]["1000"]["Ｏ813中学校"]), ""],
]
r0 = 4
for j, h in enumerate(rows[0], 1):
    c = ws.cell(row=r0, column=j, value=h); c.fill = HDR; c.font = HDRF; c.border = THIN
for i, row in enumerate(rows[1:], r0 + 1):
    for j, v in enumerate(row, 1):
        c = ws.cell(row=i, column=j, value=v); c.border = THIN
        if isinstance(v, int): c.number_format = '#,##0'
for j, w in enumerate([42, 16, 16, 34], 1): ws.column_dimensions[get_column_letter(j)].width = w
ws.cell(row=r0 + len(rows) + 1, column=1,
        value="結論：条件付きで「出す」。学齢人口は両商圏とも増加（500m +10.5%、1km +9.0%）し母数は厚い。一方で競合は密度が高く、集団指導の正面参入は避け、小学生高学年～中学生の英語・個別指導での差別化が前提。").font = Font(bold=True, size=10)

# ---- 2. メッシュ集計の方法別比較 ----
rows = [["年", "半径", "方式", "総人口", "世帯数", "学齢6-15推計", "小学生6-11", "中学生等12-15", "セル数"]]
for yr, atag, htag, tp in ((2020, "age2020", "hh2020", "人口（総数）"), (2015, "age2015", "hh2015", "人口総数")):
    for radius in (500, 1000):
        for method in ("overlap", "centroid"):
            a = S[f"{atag}_{radius}_{method}"]; h = S[f"{htag}_{radius}_{method}"]
            rows.append([yr, f"{radius}m", "重なり" if method == "overlap" else "中心点",
                         int(a[tp]), int(h["世帯総数"]), round(a["学齢_対象6-15推計"]),
                         round(a["学齢_小学生6-11推計"]), round(a["学齢_中学生等12-15推計"]),
                         S[f"{atag}_{radius}_{method}_cells"] if f"{atag}_{radius}_{method}_cells" in S else ""])
sheet(wb.create_sheet("商圏人口_方式別"), "商圏人口：集計方式別の比較（250mメッシュ）", rows,
      [8, 10, 10, 14, 12, 14, 12, 14, 8],
      note="主方式は「重なり」（円と一部でも重なるセルを全量計上）。「中心点」はセル中心が円内にある場合のみ計上。範囲の目安として併記。")

# ---- 3. 年齢別人口 ----
pyr = pd.DataFrame(S["pyramid_1km_overlap"])
tot = pyr["total"].sum()
rows = [["年齢階級", "男性", "女性", "総数", "構成比%"]]
for _, r in pyr.iterrows():
    rows.append([r["age"], int(r["male"]), int(r["female"]), int(r["total"]), round(r["total"] / 62389 * 100, 2)])
sheet(wb.create_sheet("年齢別人口_1km"), "年齢（5歳階級）別人口：商圏 半径1km（2020年国勢調査）", rows, [12, 12, 12, 12, 10],
      note="構成比の分母は商圏総人口 62,389人（年齢不詳を含むため年齢階級の合計とは一致しない）。")

# ---- 4. 町丁別 ----
ch = pd.read_csv(f"{OUT}/chome_trade_area.csv")
rows = [["市区町村", "町丁・字等", "駅からの最短距離m", "総人口", "世帯数", "5～9歳", "10～14歳", "15～19歳",
         "小学生6-11推計", "中学生等12-15推計", "学齢6-15推計", "学齢割合%"]]
for _, r in ch.iterrows():
    rows.append([r["CITY_NAME"], r["S_NAME"], r["mindist_m"], r["総数"], r["世帯数_境界DBF"], r["5～9歳"], r["10～14歳"],
                 r["15～19歳"], round(r["小学生6-11推計"], 0) if pd.notna(r["小学生6-11推計"]) else "",
                 round(r["中学生等12-15推計"], 0) if pd.notna(r["中学生等12-15推計"]) else "",
                 round(r["学齢6-15推計"], 0) if pd.notna(r["学齢6-15推計"]) else "",
                 round(r["学齢割合%"], 1) if pd.notna(r["学齢割合%"]) else ""])
sheet(wb.create_sheet("町丁別_1km交差"), "町丁別人口：半径1km円と交差する町丁（町丁全体の値、2020年国勢調査 小地域集計）", rows,
      [14, 20, 14, 10, 10, 9, 9, 9, 13, 14, 12, 10],
      note="町丁の全部が円内に入るわけではないため、合計はメッシュ集計の商圏人口とは一致しない（町丁の偏りを見るための表）。世帯数は境界データ付属値。鵜野森（二）など2町丁は年齢別が秘匿・欠落のため学齢推計なし。")

# ---- 5. 事業所 (EC) ----
ecm = S["ec2021_mesh500m"]
rows = [["項目（2021年経済センサス-活動調査、500mメッシュ）", "半径500m", "半径1km"],
        ["学習塾（事業所数）", int(ecm["500"]["Ｏ823学習塾"]), int(ecm["1000"]["Ｏ823学習塾"])],
        ["外国語会話教授業（事業所数）", int(ecm["500"]["Ｏ82K外国語会話教授業"]), int(ecm["1000"]["Ｏ82K外国語会話教授業"])],
        ["小学校（校数）", int(ecm["500"]["Ｏ812小学校"]), int(ecm["1000"]["Ｏ812小学校"])],
        ["中学校（校数）", int(ecm["500"]["Ｏ813中学校"]), int(ecm["1000"]["Ｏ813中学校"])],
        ["幼稚園（園数）", int(ecm["500"]["Ｏ811幼稚園"]), int(ecm["1000"]["Ｏ811幼稚園"])],
        ["高等学校・中等教育学校（校数）", int(ecm["500"]["Ｏ814高等学校，中等教育学校"]), int(ecm["1000"]["Ｏ814高等学校，中等教育学校"])],
        ["（参考）相模原市南区 全産業事業所数", 7465, ""],
        ["（参考）相模原市南区 全産業従業者数", 83233, ""],
        ["（参考）相模原市南区 教育・学習支援業 事業所数", 364, ""],
        ["（参考）相模原市南区 教育・学習支援業 従業者数", 4969, ""]]
sheet(wb.create_sheet("事業所_経済センサス"), "事業所・学校数（経済センサス）", rows, [46, 14, 14],
      note="区レベルの参考値は町丁集計（産業大分類別）の合算。メッシュ値と集計単位が異なるため単純比較はできない。")

# ---- 6. 出典・方法 ----
rows = [["項目", "内容"],
        ["中心点", "相模大野駅（北緯35.53222度、東経139.43836度）"],
        ["商圏", "半径500m（徒歩圏の核）／半径1km（徒歩＋自転車圏）の2重"],
        ["集計方式（主）", "250mメッシュ（5次メッシュ）のうち円と一部でも重なるセルを全量計上（重なり方式）。中心点方式も併記"],
        ["学齢人口の推計", "5歳階級人口から按分：小学生6-11歳＝(5-9歳)×4/5＋(10-14歳)×2/5、中学生等12-15歳＝(10-14歳)×3/5＋(15-19歳)×1/5。あくまで推計値"],
        ["秘匿処理", "メッシュ統計の秘匿セルは合算先セルに含めて公表されているため、秘匿行を除外し合算先行の値を計上（二重計上回避）"],
        ["出典1", "総務省統計局「令和2年国勢調査 地域メッシュ統計」5歳階級別人口（統計表ID T001196、JGD2011、250mメッシュ、第1次地域区画5339）／人口及び世帯（T001142）。e-Stat 統計GISより2026-11-11取得"],
        ["出典2", "総務省統計局「平成27年国勢調査 地域メッシュ統計」5歳階級別人口（T001178）／その1 人口等基本集計に関する事項（T000876）。同上"],
        ["出典3", "総務省統計局「令和2年国勢調査 小地域集計」第3表 男女，年齢（5歳階級）別人口（政府統計コード00200521、統計表情報ID 000032163290［神奈川県］・000032163275［東京都］）、第1表相当 男女別人口，外国人人口及び世帯数（000032163289・000032163274）。e-Statより2026-11-11取得"],
        ["出典4", "総務省・経済産業省「令和3年経済センサス-活動調査 地域メッシュ統計」産業別事業所数等（T001164、500mメッシュ、JGD2011）／小地域集計 産業（大分類）別民営事業所数及び男女別従業者数（T001167）。e-Stat 統計GISより2026-11-11取得"],
        ["出典5", "町丁・字等境界データ：e-Stat 統計GIS「令和2年国勢調査 町丁・字等境界データ」（JGD2011、神奈川県・東京都）"],
        ["データの限界", "国勢調査は2020年10月1日時点。2025年調査のメッシュ・小地域集計は未提供のため、人口の鮮度は2020年が最新。経済センサスは2021年6月1日時点。"]]
sheet(wb.create_sheet("出典・方法"), "出典・集計方法", rows, [18, 130])

wb.save(f"{OUT}/sample01_集計.xlsx")
print("excel saved")
