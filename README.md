## Auto-Monkey

### Auto-Monkey在adb shell monkey基础上新增以下功能：
1. 支持指定运行时长（单位：小时），默认无限运行Monkey直至手动终止；
2. 支持分批下发Monkey测试指令并自动记录日志（logcat方式）；
3. 支持对日志进行自动压缩，极大优化磁盘空间占用；
4. 支持android设备重启，Monkey测试可继续进行；
5. 支持自动分析crash和anr，抽离对应日志文件提取至指定目录；

### 使用方法
```commandline
python3 main.py -packages com.aaa,com.bbb [-device 123456] [-hours 12] [-throttle 500] [-per 20000]
```
- packages：应用进程包列表
- hours：运行小时（选填，默认无限时长）
- throttle：执行间隔毫秒（选填，默认200毫秒，android设备性能越弱，间隔建议越大）
- per：单次运行次数（选填，即每执行<per>次后保存一次日志）

### `main`实现流程：
1. 通过`argparse`接收用户配置
2. `test_monkey()`方法：
   2.1 终止Monkey进程

   2.2 终止Logcat进程
   
   2.3 下发Logcat开始记录日志
   
   2.4 下发`adb shell monkey`命令
   
   2.5 轮询Logcat日志文件，判断是否检测到`Monkey finished`字段
   
   2.6 终止Monkey进程
   
   2.7 终止Logcat进程
   
   2.8 压缩日文文件
   
   2.9 等待5秒缓存
3. 根据用户设定运行时长或者无限时循环`test_monkey()`
