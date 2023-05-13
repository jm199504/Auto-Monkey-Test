import re
import os
import gzip
import shutil
import subprocess
from datetime import datetime
from collections import defaultdict


def get_first_device_id():
    """
    获取当前已连接的第一个设备号
    """
    output = subprocess.check_output(['adb', 'devices']).decode()
    devices = output.strip().split('\n')[1:]
    if not devices:
        return None
    serial = devices[0].split('\t')[0]
    return serial


def print_config_box(config):
    """
    输出高亮的配置信息Box形式
    """
    # 计算配置信息的最大长度
    max_length = max(len(str(key)) + len(str(config[key])) for key in config.keys())

    # 打印顶部边框
    top = "╔" + "═" * (max_length + 4) + "╗"
    print(top)

    # 打印配置字段信息
    for key, value in config.items():
        padding = " " * (len(top) - len(str(key)) - len(str(value)) - 6)
        print("║ " + key + ": " + padding + str(value) + " ║")

    # 打印底部边框
    print("╚" + "═" * (max_length + 4) + "╝")


def is_device_connected(device_id):
    """
    判断指定设备是否已经连接
    """
    try:
        output = subprocess.check_output(['adb', 'devices', '-l']).decode('utf-8')
        devices = output.split('\n')[1:-2]
        for device in devices:
            if device_id in device:
                return True
        return False
    except subprocess.CalledProcessError:
        return False


def terminal_process(device_id, process_name):
    """
    终止指定进程
    """
    try:
        output = subprocess.check_output(f"adb -s {device_id} shell ps | grep {process_name}", shell=True)
        pid = int(output.split()[1])
        os.system(f"adb -s {device_id} shell kill {pid}")
    except Exception:
        print(f"{device_id}未找到{process_name}进程，无法终止，该步骤跳过")


def record_log(log_dir, device_id):
    """
    记录android设备日志
    """
    log_path = f'{log_dir}/{device_id}/'

    # 创建日志目录
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # 开始记录日志
    os.system(f"adb -s {device_id} logcat -c")
    os.system(f'adb -s {device_id} logcat -G 800m')
    log_path += f'{datetime.now().strftime("%Y%m%d%H%M%S")}.txt'
    logcat_cmd = f'adb -s {device_id} logcat > {log_path}'
    os.popen(logcat_cmd)
    return log_path


def process_end(monkey_log):
    """
    解析Monkey Finished
    """
    end_time = None

    # 打开logcat文件并读取其内容
    with open(monkey_log, "r", encoding="latin-1") as file:
        log_content = file.read()

    for line in log_content.splitlines():
        _end = re.compile(r"^(.*?)Monkey finished").match(line)

        if _end:
            end_time = _end.group(0).split('.')[0]

    return end_time


def is_process_running(process_name):
    """
    判断指定进程是否存在
    """
    output = subprocess.check_output(["adb", "shell", "ps"]).decode("utf-8")
    for line in output.splitlines():
        if process_name in line:
            return True
    return False


def zip_log(log_path):
    """
    压缩日志文件
    """
    if log_path and os.path.exists(log_path):
        # 打开压缩文件
        with open(f"{log_path}", "rb") as f:
            content = f.read()

        # 创建压缩文件
        with gzip.open(f"{log_path}.gz", "wb") as f:
            f.write(content)

        # 删除历史日志
        os.system(f'rm -rf {log_path}')
    else:
        print(f"日志{log_path}不存在")


def process_exception(monkey_log):
    """
    解析Crash和ANR问题
    """
    device_id = monkey_log.split('/')[1]

    if monkey_log.endswith('gz'):  # 解压gz文件
        with gzip.open(monkey_log, 'rb') as f:
            _log_content = f.read().decode('latin-1')
    elif monkey_log.endswith('.txt'):  # 读取txt文件
        with open(monkey_log, "r", encoding="latin-1") as f:
            _log_content = f.read()
    else:
        print(f'不支持该格式，文件名:{monkey_log}')
        print('-----------------------------------------------' * 2)
        return

    crash2lines = defaultdict(list)  # CRASH进程名称 与 开始时间的映射
    anr2lines = defaultdict(list)  # ANR进程名称 与 开始时间的映射

    line_num = 0
    log_content = _log_content.splitlines()

    for line in log_content:  # 遍历读取日志
        line = str(line)
        fatal_exception = re.match(r'.*FATAL EXCEPTION.*$', line)
        anr_exception = re.match(r'.*ANR in.*', line)

        if fatal_exception:
            match = re.search(r'Process: ([^,]+)', log_content[line_num + 1])
            if match:
                package = match.group(1)
                crash2lines[package].append(line_num)

        if anr_exception:
            match = re.search(r'\bcom\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+/\.[a-zA-Z0-9_]+', line)
            if match:
                activity = match.group()
                anr2lines[activity].append(line_num)
        # 行号自增
        line_num += 1

    # 结果输出
    if crash2lines or anr2lines:
        print(f'文件名:{monkey_log}')
        for process, times in crash2lines.items():
            print(f"CRASH: {process}, 次数:{len(times)}")

        for activity, times in anr2lines.items():
            print(f"ANR: {activity}, 次数:{len(times)}")

        # 新建指定日志文件目录
        exception_log_path = f"_error_monkey_logs/{device_id}"
        if not os.path.exists(exception_log_path):
            os.makedirs(exception_log_path)

        # 移动日志文件
        monkey_log_name = monkey_log.split('/')[-1]
        shutil.move(monkey_log, f'{exception_log_path}/{monkey_log_name}')

        print('-----------------------------------------------' * 2)
