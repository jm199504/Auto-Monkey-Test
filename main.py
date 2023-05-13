"""
Auto-Monkey
"""
import os
import time
import argparse

import settings
from utils import (
    get_first_device_id,
    print_config_box,
    is_device_connected,
    terminal_process,
    record_log,
    process_end,
    is_process_running,
    zip_log,
)


# 接收和解析Monkey的运行配置
parser = argparse.ArgumentParser(description='接收Monkey的运行配置')
parser.add_argument('-packages', metavar='packages', type=str, help='应用程序包白名单', required=True)
parser.add_argument('-device', metavar='device-id', type=str, help='设备号')
parser.add_argument('-hours', metavar='hour', type=int, help='运行小时')
parser.add_argument('-throttle', metavar='throttle', type=int, help='执行间隔毫秒')
parser.add_argument('-per', metavar='per-times', type=int, help='单次运行次数')
args = parser.parse_args()

# 明确配置信息
packages = args.packages
device_id = args.device if args.device else get_first_device_id()
hours = args.hour if args.hours else "Unlimited(∞)"
per_times = args.per if args.per else settings.PER_TIMES
throttle = args.throttle if args.throttle else settings.THROTTLE
per_waiting_time = int(per_times / 100)  # 单次等待时间

# 判断是否已连接android设备
if not device_id:
    raise Exception("未成功连接android设备")
is_connected = is_device_connected(device_id)
if not is_connected:
    raise Exception(f"未成功连接到指定android设备：{device_id}")

# 输出执行配置
print("请确定以下Monkey运行配置，将于10秒后启动Monkey Testing")
user_config = {
    "packages": packages,
    "device-id": device_id,
    "run-hours": hours,
    "per-time": per_times,
    "throttle": throttle,
}
print(user_config)
print_config_box(user_config)

time.sleep(10)  # 等待10秒以用户确认

# 配置Monkey测试脚本
monkey_cmd = f"adb -s {device_id} " if device_id else "adb "
monkey_cmd += f"shell monkey -v-v-v --throttle {throttle} --pct-touch 60 --pct-motion 30 " \
              f"--ignore-crashes --ignore-timeouts --ignore-security-exceptions --ignore-native-crashes"
for package in packages.split(','):
    monkey_cmd += f" -p {package}"
monkey_cmd += f" {per_times}"


def monkey_test():
    log_path = None  # 日志缺省路径

    terminal_process(device_id, 'com.android.commands.monkey')  # 终止Monkey进程
    terminal_process(device_id, 'logcat')  # 终止日志进程

    try:  # 开始记录日志和执行Monkey
        log_path = record_log('_monkey_logs', device_id)
        os.system(monkey_cmd)
        print(f'{device_id}开始执行Monkey')
    except Exception:
        pass

    try:  # 轮询解析日志
        start_time = time.time()
        while time.time() - start_time < per_waiting_time:
            if not os.path.exists(log_path) or process_end(log_path):  # 解析到Monkey Finished则跳出日志解析轮询
                break
            if not is_process_running('com.android.commands.monkey'):
                print(f"{device_id}设备未查询到Monkey正在执行，退出轮询")
                break
    except Exception:
        pass

    terminal_process(device_id, 'com.android.commands.monkey')  # 终止Monkey进程
    terminal_process(device_id, 'logcat')  # 终止日志

    try:
        zip_log(log_path)
    except Exception:
        pass

    # 等待5秒
    time.sleep(5)


if isinstance(args.hour, int):
    action_time = time.time()
    while time.time() - action_time < int(args.hour) * 3600:
        monkey_test()
else:  # 始终执行
    while True:
        monkey_test()
