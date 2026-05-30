// ============================================================
// iOS Shortcuts → Scriptable → GitHub API → GHA 触发
// 用法: 快捷指令「时间触发」每天美东 8:00 运行此脚本
// ============================================================

const GITHUB_TOKEN = "";  // ⬅️ GitHub Personal Access Token (repo + workflow 权限)
const REPO_OWNER = "devin7758521";
const REPO_NAME = "stock_screener_github_pages";
const WORKFLOW_FILE = "pages.yml";

// ——— 动态计算 NYSE 休市日 (永久有效) ———
function nthWeekdayOfMonth(year, month, weekday, n) {
  // 返回 month 月第 n 个 weekday (0=Sun)
  let count = 0;
  const last = new Date(year, month + 1, 0).getDate();
  for (let d = 1; d <= last; d++) {
    const dt = new Date(year, month, d);
    if (dt.getDay() === weekday) {
      count++;
      if (count === n) return dt;
    }
  }
  return null;
}

function lastWeekdayOfMonth(year, month, weekday) {
  const last = new Date(year, month + 1, 0).getDate();
  for (let d = last; d >= 1; d--) {
    const dt = new Date(year, month, d);
    if (dt.getDay() === weekday) return dt;
  }
  return null;
}

function easterSunday(year) {
  // Anonymous Gregorian algorithm (valid for any year)
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(year, month - 1, day);
}

function observedHoliday(year, month, day) {
  // 周末顺延: 周六 → 周五, 周日 → 周一
  const dt = new Date(year, month, day);
  if (dt.getDay() === 0) return new Date(year, month, day + 1);   // Sun → Mon
  if (dt.getDay() === 6) return new Date(year, month, day - 1);   // Sat → Fri
  return dt;
}

function nyseHolidays(year) {
  const easter = easterSunday(year);
  const goodFriday = new Date(easter.getTime() - 86400000 * 2); // Good Friday = Easter - 2 days

  return [
    observedHoliday(year, 0, 1),                                     // New Year's Day
    nthWeekdayOfMonth(year, 0, 1, 3),                                // MLK Day (Jan 3rd Mon)
    nthWeekdayOfMonth(year, 1, 1, 3),                                // Presidents' Day (Feb 3rd Mon)
    goodFriday,                                                       // Good Friday
    lastWeekdayOfMonth(year, 4, 1),                                   // Memorial Day (May last Mon)
    observedHoliday(year, 5, 19),                                     // Juneteenth
    observedHoliday(year, 6, 4),                                      // Independence Day
    nthWeekdayOfMonth(year, 8, 1, 1),                                 // Labor Day (Sep 1st Mon)
    nthWeekdayOfMonth(year, 10, 4, 4),                                // Thanksgiving (Nov 4th Thu)
    observedHoliday(year, 11, 25),                                    // Christmas
  ];
}

function isHolidayOrWeekend() {
  const now = new Date();
  const et = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const day = et.getDay();
  if (day === 0 || day === 6) return true;

  // 检查是否等于任一 NYSE 休市日
  const y = et.getFullYear(), m = et.getMonth(), d = et.getDate();
  return nyseHolidays(y).some(h =>
    h.getFullYear() === y && h.getMonth() === m && h.getDate() === d
  );
}

async function triggerWorkflow() {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_FILE}/dispatches`;
  const req = new Request(url);
  req.method = "POST";
  req.headers = {
    "Authorization": `Bearer ${GITHUB_TOKEN}`,
    "Accept": "application/vnd.github+json",
  };
  req.body = JSON.stringify({ ref: "main" });
  await req.load();
}

function show(msg) {
  const n = new Notification();
  n.title = "美股推送";
  n.body = msg;
  n.schedule();
}

async function main() {
  if (!GITHUB_TOKEN) {
    show("未配置 GITHUB_TOKEN");
    return;
  }

  if (isHolidayOrWeekend()) {
    show("今日休市/周末，跳过");
    return;
  }

  try {
    await triggerWorkflow();
    show("GHA 已触发，几分钟后收到飞书推送");
  } catch (e) {
    show("触发失败: " + e.message);
  }
}

await main();
Script.complete();
