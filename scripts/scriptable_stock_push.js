// ============================================================
// Stock Screener → Scriptable → Feishu Push
// 使用方法: Scriptable 中复制此脚本，iOS Shortcuts 定时触发
// 美东时间 8:00 AM 执行
// ============================================================

const DATA_URL = "https://devin7758521.github.io/stock_screener_github_pages/data/latest.json";
const FEISHU_WEBHOOK = "";  // ⬅️ 填你的飞书 webhook URL

// 2026 NYSE 全休市日 (10天)
const HOLIDAYS_2026 = [
  "2026-01-01", // New Year's Day
  "2026-01-19", // MLK Day
  "2026-02-16", // Presidents' Day
  "2026-04-03", // Good Friday
  "2026-05-25", // Memorial Day
  "2026-06-19", // Juneteenth
  "2026-07-03", // Independence Day (observed, Jul 4 is Sat)
  "2026-09-07", // Labor Day
  "2026-11-26", // Thanksgiving
  "2026-12-25", // Christmas
];

function isHolidayOrWeekend() {
  const now = new Date();
  // 转美东
  const et = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const day = et.getDay();
  if (day === 0 || day === 6) return true; // 周末
  const dateStr = et.getFullYear() + "-" +
    String(et.getMonth() + 1).padStart(2, "0") + "-" +
    String(et.getDate()).padStart(2, "0");
  return HOLIDAYS_2026.includes(dateStr);
}

async function main() {
  if (isHolidayOrWeekend()) {
    console.log("今日休市/周末，跳过");
    return;
  }

  try {
    const req = new Request(DATA_URL);
    const resp = await req.loadJSON();
    const items = resp.items || [];
    const candidates = items.filter(i => i.default_pass);

    if (candidates.length === 0) {
      console.log("今日无符合条件的股票");
      return;
    }

    const names = candidates.map((item, i) =>
      `${i + 1}. ${item.symbol} ${item.name || ""}`
    ).join("\n");

    const msg = [
      `【美股强势股观察】${resp.generated_at || ""}`,
      `市场状态: ${resp.market_status || "--"}  | 候选: ${candidates.length} 只`,
      "",
      names,
      "",
      ` 页面: https://devin7758521.github.io/stock_screener_github_pages/`,
    ].join("\n");

    // 发送飞书
    if (FEISHU_WEBHOOK) {
      const fb = new Request(FEISHU_WEBHOOK);
      fb.method = "POST";
      fb.headers = { "Content-Type": "application/json" };
      fb.body = JSON.stringify({ msg_type: "text", content: { text: msg } });
      await fb.loadJSON();
    }

    // 同时显示通知
    const notif = new Notification();
    notif.title = "美股强势股推送";
    notif.body = msg.substring(0, 200);
    await notif.schedule();

    console.log("推送成功: " + candidates.length + " 只");
  } catch (e) {
    console.log("推送失败: " + e.message);
  }
}

await main();
Script.complete();
