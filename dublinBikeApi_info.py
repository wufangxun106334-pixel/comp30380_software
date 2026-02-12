import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
import sys
import os

# 导入配置
sys.path.append(os.getcwd())
try:
    import config
except ImportError:
    # 如果在子目录运行，尝试往上一级找
    sys.path.append(os.path.dirname(os.getcwd()))
    import config

# 每5分钟抓取一次，保存为独立 JSON 文件；出错不影响下一轮
output_dir = Path("data/dublinbike_status")
output_dir.mkdir(parents=True, exist_ok=True)


def fetch_and_save_once():
    ts = datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%dT%H%M%SZ")
    filename = output_dir / f"station_status_{ts_str}.json"
    try:
        resp = requests.get(config.BIKE_STATUS_URL, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"saved: {filename}")
    except Exception as e:
        print(f"error: {e}; will retry next cycle")


# 运行48小时自动停止
max_hours = 48
end_time = datetime.now(timezone.utc) + timedelta(hours=max_hours)

# 运行时可按下停止按钮中断
while datetime.now(timezone.utc) < end_time:
    fetch_and_save_once()
    time.sleep(300)
print("done: reached 48h timeout")
