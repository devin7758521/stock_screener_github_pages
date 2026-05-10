# 美股强势股观察系统 - GitHub Pages版

> Nasdaq-100 + S&P 500 股票池，GitHub Actions 定时运行，GitHub Pages 展示 Dashboard。仅用于研究和自动化学习，不构成投资建议。

## 功能

- 周K强势实体阳线筛选
- 日K强势实体阳线确认
- 成交量放大与20日平均成交额过滤
- 25/60周线、均线排列、相对强度评分
- DeepSeek摘要（可选）
- 飞书推送（可选）
- GitHub Pages Dashboard
- 页面参数开关/滑块调节
- 最近10天缓存，自动清理10天前缓存

## 本地运行

```bash
pip install -r requirements.txt
python main.py --dry-run --site-output
python -m pytest tests -q
```

然后打开：

```text
public/index.html
```

## GitHub Secrets

如需AI摘要和飞书推送，请在仓库 Settings → Secrets and variables → Actions 添加：

```text
DEEPSEEK_API_KEY
FEISHU_WEBHOOK
```

## GitHub Pages设置

仓库 Settings → Pages → Source 选择 GitHub Actions。

## 运行时间

`.github/workflows/pages.yml` 默认美股收盘后运行：北京时间周二至周六 07:30。
