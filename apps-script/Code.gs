/**
 * 商耕即時動態標籤 — Google Apps Script Web App
 *
 * 部署為「網路應用程式」後，會回傳一份即時產生的 KML，
 * 由 live_map.kml 中的 <NetworkLink> 每 60 秒抓取一次，
 * 在 Google Earth 上於各商圈中心點顯示文字標籤。
 *
 * 試算表欄位 (第 1 列為標題列，從第 2 列開始讀取)：
 *   A 欄 WKT         多邊形字串 (鎖定，管理員維護)
 *   B 欄 Sequence_ID 商圈編號   (鎖定，管理員維護)
 *   C 欄 業務         負責業務
 *   D 欄 售           在售物件數量
 *   E 欄 租           在租物件數量
 *   F 欄 負責委託     該商圈負責業務已接進委託數
 *   G 欄 店內委託     店內於該商圈物件數
 *   H 欄 更新時間     業務自行填寫
 */

function doGet() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = sheet.getDataRange().getValues();

  var kml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  kml += '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>\n';
  kml += '  <Style id="TextLabelOnly">\n';
  kml += '    <IconStyle><scale>0</scale></IconStyle>\n';
  kml += '    <LabelStyle><scale>0.8</scale></LabelStyle>\n';
  kml += '  </Style>\n';

  // 從第 2 列開始讀取 (跳過標題列)
  for (var i = 1; i < data.length; i++) {
    var wkt        = data[i][0];                   // A 欄: WKT 多邊形字串
    var seqId      = formatInt(data[i][1]);        // B 欄: Sequence_ID (商圈編號)
    var sales      = data[i][2] || "無";           // C 欄: 業務
    var sell       = formatInt(data[i][3]);        // D 欄: 售
    var rent       = formatInt(data[i][4]);        // E 欄: 租
    var res        = formatInt(data[i][5]);        // F 欄: 負責委託
    var com        = formatInt(data[i][6]);        // G 欄: 店內委託
    var updateTime = formatDateStr(data[i][7]);    // H 欄: 更新時間 (僅年月日)

    // 解析 A 欄 WKT 並計算商圈中心點
    var center = getCenterFromWKT(wkt);

    if (center) {
      var label = "商圈" + seqId + "\n" +
                  sales + "\n" +
                  "售:" + sell + "\n" +
                  "租:" + rent + "\n" +
                  "負責委託:" + res + "\n" +
                  "店內委託:" + com + "\n" +
                  updateTime;

      kml += '  <Placemark>\n';
      kml += '    <name>' + escapeXml(label) + '</name>\n';
      kml += '    <styleUrl>#TextLabelOnly</styleUrl>\n';
      kml += '    <Point><coordinates>' + center.lon + ',' + center.lat + ',0</coordinates></Point>\n';
      kml += '  </Placemark>\n';
    }
  }

  kml += '</Document></kml>';
  return ContentService.createTextOutput(kml).setMimeType(ContentService.MimeType.XML);
}

// 解析 WKT 格式並計算中心點 (取外接矩形 bounding box 的中心)
function getCenterFromWKT(wktStr) {
  if (!wktStr || typeof wktStr !== 'string') return null;

  var matches = wktStr.match(/-?\d+(\.\d+)?\s+-?\d+(\.\d+)?/g);
  if (!matches || matches.length === 0) return null;

  var lons = [];
  var lats = [];

  for (var j = 0; j < matches.length; j++) {
    var parts = matches[j].trim().split(/\s+/);
    if (parts.length >= 2) {
      var lon = parseFloat(parts[0]);
      var lat = parseFloat(parts[1]);
      if (!isNaN(lon) && !isNaN(lat)) {
        lons.push(lon);
        lats.push(lat);
      }
    }
  }

  if (lons.length === 0 || lats.length === 0) return null;

  var minLon = Math.min.apply(null, lons);
  var maxLon = Math.max.apply(null, lons);
  var minLat = Math.min.apply(null, lats);
  var maxLat = Math.max.apply(null, lats);

  return {
    lon: (minLon + maxLon) / 2,
    lat: (minLat + maxLat) / 2
  };
}

// 數字防呆轉換
function formatInt(val) {
  if (val === "" || val === null || val === undefined) return "0";
  var num = parseFloat(val);
  return isNaN(num) ? val : Math.round(num).toString();
}

// 日期格式轉換 (僅保留年月日 yyyy/MM/dd)
function formatDateStr(val) {
  if (val === "" || val === null || val === undefined) return "無";
  if (val instanceof Date) {
    return Utilities.formatDate(val, Session.getScriptTimeZone(), "yyyy/MM/dd");
  }
  return val.toString();
}

// XML 特殊字元轉義
function escapeXml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
