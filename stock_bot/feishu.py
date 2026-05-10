import requests
from .config import FEISHU_WEBHOOK, REQUEST_TIMEOUT


def send_feishu_message(text, dry_run=False):
    if dry_run or not FEISHU_WEBHOOK:
        print("\n========== 飞书消息预览 ==========")
        print(text[:6000])
        print("========== 预览结束 ==========")
        return True
    payload = {"msg_type": "text", "content": {"text": text}}
    try:
        r = requests.post(FEISHU_WEBHOOK, json=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        print("飞书推送成功")
        return True
    except Exception as e:
        print(f"飞书推送失败：{e}")
        return False
