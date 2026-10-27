#!/usr/bin/env python3
"""
kml_to_wkt.py — 將 Google 我的地圖匯出的 .kml 商圈底圖轉成 WKT，
                 輸出為可直接貼進試算表 A/B 欄的 CSV。

背景說明（核心原理：KML 與 WKT 的格式差異）
--------------------------------------------------
KML 檔內的原始座標（XML 標籤）：以逗號分隔經緯度、以空白分隔點
    <coordinates>121.531,25.041,0 121.532,25.042,0 121.531,25.041,0</coordinates>

WKT (Well-Known Text) 格式：以空白分隔經緯度、以逗號分隔點
    POLYGON ((121.531 25.041, 121.532 25.042, 121.531 25.041))

用法
----
    python3 kml_to_wkt.py 商圈最新版.kml -o 商圈WKT.csv

輸出欄位：WKT, Sequence_ID
    Sequence_ID 取自 Placemark 的 <name>（若為 "22.0" 這類字串會取整數 22）；
    無法解析時則依出現順序編號。

轉出後把 CSV 的兩欄貼到試算表的 A、B 欄（第 1 列為標題列），
其餘 C~H 欄由業務同仁自行填寫。
"""

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET

KML_NS = "{http://www.opengis.net/kml/2.2}"


def strip_ns(tag: str) -> str:
    """去掉 XML 標籤的 namespace，方便比對。"""
    return tag.split("}", 1)[-1]


def coords_to_wkt_ring(text: str) -> str:
    """把一段 <coordinates> 文字轉成 WKT 的環 (ring)，並丟棄高度值。"""
    points = []
    for token in text.split():
        parts = token.split(",")
        if len(parts) < 2:
            continue
        lon, lat = parts[0].strip(), parts[1].strip()
        if not lon or not lat:
            continue
        points.append(f"{lon} {lat}")

    if len(points) < 3:
        return ""

    # WKT 的多邊形必須閉合：頭尾為同一點
    if points[0] != points[-1]:
        points.append(points[0])

    return "(" + ", ".join(points) + ")"


def polygon_to_wkt(polygon: ET.Element) -> str:
    """把單一 <Polygon> 轉成 POLYGON WKT（含內環 / 挖空）。"""
    rings = []

    outer = polygon.find(f"{KML_NS}outerBoundaryIs/{KML_NS}LinearRing/{KML_NS}coordinates")
    if outer is None or not (outer.text or "").strip():
        return ""
    ring = coords_to_wkt_ring(outer.text)
    if not ring:
        return ""
    rings.append(ring)

    for inner in polygon.findall(f"{KML_NS}innerBoundaryIs/{KML_NS}LinearRing/{KML_NS}coordinates"):
        ring = coords_to_wkt_ring(inner.text or "")
        if ring:
            rings.append(ring)

    return "POLYGON (" + ", ".join(rings) + ")"


def parse_seq_id(name: str, fallback: int) -> str:
    """從 Placemark 名稱取出商圈編號，例如 "22.0" -> "22"、"商圈 7" -> "7"。"""
    if not name:
        return str(fallback)
    match = re.search(r"-?\d+(?:\.\d+)?", name)
    if not match:
        return str(fallback)
    try:
        return str(int(round(float(match.group()))))
    except ValueError:
        return str(fallback)


def extract(kml_path: str):
    """走訪整份 KML，回傳 [(wkt, sequence_id), ...]。"""
    tree = ET.parse(kml_path)
    root = tree.getroot()

    rows = []
    counter = 0

    for placemark in root.iter(f"{KML_NS}Placemark"):
        name_el = placemark.find(f"{KML_NS}name")
        name = (name_el.text or "").strip() if name_el is not None else ""

        # 一個 Placemark 可能含 MultiGeometry，內有多個 Polygon
        polygons = [el for el in placemark.iter() if strip_ns(el.tag) == "Polygon"]
        for polygon in polygons:
            wkt = polygon_to_wkt(polygon)
            if not wkt:
                continue
            counter += 1
            rows.append((wkt, parse_seq_id(name, counter)))

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="KML 商圈多邊形轉 WKT (試算表 A 欄用)")
    parser.add_argument("kml", help="來源 .kml 檔 (Google 我的地圖匯出)")
    parser.add_argument("-o", "--output", default="-", help="輸出 CSV 路徑，預設輸出到畫面")
    args = parser.parse_args()

    rows = extract(args.kml)
    if not rows:
        print("找不到任何多邊形，請確認這是「我的地圖」匯出的商圈底圖。", file=sys.stderr)
        return 1

    out = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8-sig")
    try:
        writer = csv.writer(out)
        writer.writerow(["WKT", "Sequence_ID"])
        writer.writerows(rows)
    finally:
        if out is not sys.stdout:
            out.close()
            print(f"已輸出 {len(rows)} 個商圈至 {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
