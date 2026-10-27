# 商耕即時動態地圖 (District Farming Live Map)

房仲商圈精耕（商耕）地圖系統。業務同仁在 Google 試算表填寫各商圈的在售／在租／委託數量，
系統每分鐘自動把資料同步成 KML 標籤，疊在 Google Earth 的商圈底圖上。

此處的程式碼與流程依據本人製作之《商耕系統說明書》透過claude進行重建，程式碼內容與說明書附錄一致，另外補上了部署資訊檔、
KML→WKT 轉換工具與整理過的文件。

## 系統架構

```
Google 試算表 (業務填寫 C~H 欄)
        │
        ▼
Apps Script Web App  (doGet)
   讀取整張工作表 → 以 A 欄 WKT 算出各商圈中心點
   → 產生只有文字標籤的 KML（IconStyle scale = 0）
        │  HTTPS
        ▼
live_map.kml  <NetworkLink>  每 60 秒重新抓取
        │
        ▼
Google Earth（兩個獨立圖層）
   ├─ 商圈最新版.kml ── 商圈底圖（多邊形，靜態）
   └─ live_map.kml  ── 顯示資訊（動態標籤）
```

底圖是用「Google 我的地圖」的多邊形工具劃設並編號商圈後匯出 .kml，再匯入 Google Earth。

## 目錄結構

| 路徑 | 說明 |
| --- | --- |
| `apps-script/Code.gs` | Web App 主程式，輸出即時 KML |
| `apps-script/appsscript.json` | 部署資訊（時區、Web App 權限） |
| `kml/live_map.kml` | NetworkLink 範本，`<href>` 需換成自己的部署網址 |
| `tools/kml_to_wkt.py` | 把商圈底圖 .kml 的座標轉成試算表 A 欄要的 WKT |
| `data/` | 放商圈底圖 .kml（預設不入版控） |
| `docs/操作說明.md` | 給業務同仁的日常操作說明 |
| `docs/建置與維護.md` | 部署、更新版本、改商圈範圍的流程 |

## 試算表欄位

| 欄 | 欄位 | 填寫者 |
| --- | --- | --- |
| A | WKT 多邊形字串（用於把資訊塊置中於商圈內） | 鎖定，管理員 |
| B | 商圈編號 Sequence_ID | 鎖定，管理員 |
| C | 負責業務 | 業務 |
| D | 在售物件（數量） | 業務 |
| E | 在租物件（數量） | 業務 |
| F | 負責委託（該商圈負責業務已接進委託數） | 業務 |
| G | 店內委託（店內於該商圈物件數） | 業務 |
| H | 更新時間 | 業務 |

第 1 列為標題列，程式從第 2 列開始讀取。

## 快速上手

1. 在試算表「擴充功能 → Apps Script」貼上 `apps-script/Code.gs`，執行一次確認無報錯。
2. 「部署 → 新增部署作業 → 網頁應用程式」，存取權限設為**任何人**（Google Earth 是匿名抓取），複製網址。
3. 把 `kml/live_map.kml` 的 `<href>` 換成該網址，存成 `live_map.kml`。
4. Google Earth →「檔案 → 匯入檔案 → 從裝置上傳」，分別匯入 `商圈最新版.kml` 與 `live_map.kml`。

詳細步驟與維護流程見 [`docs/建置與維護.md`](docs/建置與維護.md)。

## 已知注意事項

- 說明書內文把標籤寫成 `<hrerf>` / `<herf>`，正確的 KML 標籤是 **`<href>`**，本repo已修正。
- Web App 的存取權限若不是「任何人」，Google Earth 會抓不到資料（標籤不會出現）。
- `getCenterFromWKT()` 取的是外接矩形中心，凹形商圈的標籤可能落在多邊形之外，屬預期行為。
- 業務請務必在試算表填資料，**不要直接在 Google Earth 上編輯動態圖層**，否則會無法同步。
- `docs/` 內的說明書 PDF 已遮蔽個人資訊（帳號 email、部署作業 ID、Web App 網址、本機檔案路徑、同事姓名），截圖中的黑色區塊即為遮蔽處。
