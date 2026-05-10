# Stock Screener GitHub Pages

## 行为准则

### 修改代码前先搜索验证
- 遇到 API 报错（如 yfinance Invalid Crumb），先搜索错误信息和已验证的解决方案，再动手改代码
- 加新功能前，先搜索目标库/API 的当前状态、版本兼容性和已知问题
- 不确定方案是否可行时，先搜索实测案例或 GitHub issues 验证
- 不要凭训练数据中的记忆直接改代码

### 项目结构
- `stock_bot/` — Python 后端（strategy, runner, universe, fundamentals, market_data, etc.）
- `public/` — 前端（index.html, app.js, style.css）
- `scripts/` — 工具脚本（clean_cache.py）
- `.github/workflows/pages.yml` — GitHub Actions 定时运行 + 部署

### 数据源优先级
1. **价格数据**: yfinance + curl_cffi（主）→ yf.download（回退）
2. **股票清单**: GitHub datasets CSV → 缓存 → universe_fallback.json
3. **基本面**: yfinance（主）→ LongBridge/长桥 OpenAPI（需 token）→ universe 名称映射
