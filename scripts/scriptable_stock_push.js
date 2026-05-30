// ============================================================
// iOS Shortcuts → Scriptable → GitHub API → GHA 触发
// 用法: 快捷指令「时间触发」每天美东 8:00 运行此脚本
// ============================================================

const GITHUB_TOKEN = "";  // ⬅️ GitHub Personal Access Token (repo + workflow 权限)
const REPO_OWNER = "devin7758521";
const REPO_NAME = "stock_screener_github_pages";
const WORKFLOW_FILE = "pages.yml";

// 2026 NYSE 休市日
const HOLIDAYS_2026 = [
  "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
  "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
  "2026-11-26", "2026-12-25",
];

function isHolidayOrWeekend() {
  const now = new Date();
  const et = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const day = et.getDay();
  if (day === 0 || day === 6) return true;
  const ds = [
    et.getFullYear(),
    String(et.getMonth() + 1).padStart(2, "0"),
    String(et.getDate()).padStart(2, "0"),
  ].join("-");
  return HOLIDAYS_2026.includes(ds);
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
