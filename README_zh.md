| 支持的目标芯片 | ESP32 | ESP32-C2 | ESP32-C3 | ESP32-C6 | ESP32-H2 | ESP32-S3 |
| --------------- | ----- | -------- | -------- | -------- | -------- | -------- |

# ESP-IDF GATT 服务器服务表示例

本示例演示了如何创建一个 GATT 服务，并在同一位置定义属性表。提供的 API 使用户无需像 BLUEDROID 实现中那样逐个添加属性。本示例还展示了创建属性表的另一种方法（见 [gatt_server_demo](../gatt_server)）。

有关本示例的更多信息，请查看此[教程](tutorial/Gatt_Server_Service_Table_Example_Walkthrough.md)。

## 使用示例

在项目配置和构建之前，请确保使用以下命令设置正确的芯片目标：

```bash
idf.py set-target <chip_name>
```

### 硬件要求

* 搭载 ESP32/ESP32-C3/ESP32-H2/ESP32-C2/ESP32-S3 SoC 的开发板（如 ESP32-DevKitC、ESP-WROVER-KIT 等）
* 用于供电和烧录的 USB 数据线

有关详细信息，请参阅[开发板](https://www.espressif.com/en/products/devkits)。

### 构建和烧录

运行 `idf.py -p PORT flash monitor` 来构建、烧录和监控项目。

（退出串口监控器，请输入 ``Ctrl-]``。）

有关配置和使用 ESP-IDF 构建项目的完整步骤，请参阅[入门指南](https://idf.espressif.com/)。

## 示例输出

```
I (0) cpu_start: Starting scheduler on APP CPU.
I (512) BTDM_INIT: BT controller compile version [1342a48]
I (522) system_api: Base MAC address is not set
I (522) system_api: read default base MAC address from EFUSE
I (522) phy_init: phy_version 4670,719f9f6,Feb 18 2021,17:07:07
I (942) GATTS_TABLE_DEMO: create attribute table successfully, the number handle = 8

I (942) GATTS_TABLE_DEMO: SERVICE_START_EVT, status 0, service_handle 40
I (962) GATTS_TABLE_DEMO: advertising start successfully
```

## 问题排查

如有任何技术问题，请直接在 GitHub 上提交 [issue](https://github.com/espressif/esp-idf/issues)。我们将会尽快回复您。
