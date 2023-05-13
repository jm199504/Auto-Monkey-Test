import os

from utils import process_exception

# 解析Monkey日志
log_dir = "_monkey_logs"
device_dirs = os.listdir(log_dir)

for device in device_dirs:
    device_dir = f'{log_dir}/{device}'
    if not os.path.isdir(device_dir):  # 非目录跳过
        continue
    for index, log in enumerate(os.listdir(device_dir)):
        print(f"【{device}日志扫描进度：{index+1}/{len(os.listdir(device_dir))}】")
        process_exception(f"{device_dir}/{log}")
