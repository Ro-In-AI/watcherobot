# WatcheRobot Hardware

WatcheRobot 是一款基于 Seeed SenseCAP Watcher 的开源桌面机器人扩展底座，采用立创 EDA 设计，对标 M5Stack Chan。

## 定位

Watcher 本身是一款"空间监测/视觉触发器"设备，通过 WatcheRobot 扩展底座可变身模块化桌面机器人，赋予其：

- 触摸交互
- 运动机构（舵机扩展）
- 充放电管理（含电池电压检测）
- WS2812 RGB 状态指示灯
- 陀螺仪 (IMU) + 磁力传感器

## 文件结构

```
Hardware/
├── README.md              # 本文件
├── LICENSE                # 开源许可证
├── PCB.pcbdoc             # PCB 设计文件 (立创 EDA 专业版)
├── PCB.schdoc             # 原理图文件 (立创 EDA 专业版)
├── Schematic_PDF.pdf      # 原理图 PDF 版本
├── Assets/                # 设计资源图片
│   ├── render.png         # PCB 渲染图
│   ├── render.gif         # PCB 3D 动画
│   ├── WatcheRobot.png    # 产品效果图
│   └── M5StackChan.png   # 参考对象图
├── BOM/                   # 物料清单
│   └── BOM.xls           # 元器件物料清单
└── Gerber/                # Gerber 生产文件
    ├── *.GTL              # 顶层铜层
    ├── *.GBL              # 底层铜层
    ├── *.GTO              # 顶层丝印
    ├── *.GBO              # 底层丝印
    ├── *.GTS              # 顶层阻焊
    ├── *.GBS              # 底层阻焊
    ├── *.DRL              # 钻孔文件
    └── PCB下单必读.txt    # PCB 下单说明
```

## 快速开始

1. 查看 `Schematic_PDF.pdf` 了解电路设计
2. 使用立创 EDA 打开 `PCB.schdoc` 和 `PCB.pcbdoc` 进行修改
3. 生产文件位于 `Gerber/` 目录，可直接用于 PCB 制造
4. 参考 `BOM/BOM.xls` 采购元器件

## 参考

- [M5Stack Chan 官方文档](https://docs.m5stack.com/en/StackChan)
- [SenseCAP Watcher 硬件概述](https://wiki.seeedstudio.com/cn/watcher_hardware_overview)
