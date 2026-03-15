/**
 * Bluetooth 常量定义
 * 基于 ESP32 BLE 机器人配置
 */

export const ROBOT_DEVICE_NAME = 'ESP_ROBOT';

export const BLUETOOTH_DEFAULT_CONFIG = {
  SCAN_TIMEOUT: 10000,
  CONNECT_TIMEOUT: 10000,
  RESCAN_DELAY: 3000,
  MAX_RESCAN_ATTEMPTS: 5,
  MTU_ANDROID: 512,
};

/** ESP32 BLE GATT Service UUID - 使用短格式 UUID */
export const BLUETOOTH_UUIDS = {
  // 主服务 UUID - 必须与 ESP32 ble.c 中的 GATTS_SERVICE_UUID_TEST 一致 (0x00FF)
  SERVICE_UUID: '00FF',

  // 特征值 UUID - 短格式
  SERVO_CTRL: 'FF01',  // 舵机控制 (读写 Notify)
  ACTION_CTRL: 'FF02',  // 动作控制 (读写)
  STATUS: 'FF03',       // 状态推送 (Notify)
};

/** 舵机配置 */
export const SERVO_CONFIG = {
  // 舵机数量
  SERVO_COUNT: 2,
  // 舵机ID
  SERVO_X: 0,  // X轴 - GPIO 12
  SERVO_Y: 1,  // Y轴 - GPIO 15
  // 角度范围
  ANGLE_MIN_X: 30,
  ANGLE_MAX_X: 150,
  ANGLE_MIN_Y: 95,
  ANGLE_MAX_Y: 150,
  // 默认角度
  DEFAULT_ANGLE: 90,
};

/** 预设动作 */
export const ACTIONS = [
  { id: 0, name: 'wave', label: '挥手' },
  { id: 1, name: 'greet', label: '问候' },
] as const;

/** BLE 命令格式 */
export const COMMANDS = {
  // 设置舵机（立即到达）
  SET_SERVO: (servoId: number, angle: number) => `SET_SERVO:${servoId}:${angle}`,
  // 持续移动（摇杆模式）
  // direction: 1 = 正向(右转), -1 = 反向(左转), 0 = 停止
  SERVO_MOVE: (servoId: number, direction: number) => `SERVO_MOVE:${servoId}:${direction}`,
  // 播放动作
  PLAY_ACTION: (actionId: number) => `PLAY_ACTION:${actionId}`,
  // 队列命令：将命令添加到队列（按顺序执行）
  // servoId: 舵机ID, angle: 目标角度, duration: 移动持续时间(ms)
  // ESP32 队列会自动按顺序执行，每条命令执行 duration 时间后执行下一条
  QUEUE_ADD: (servoId: number, angle: number, duration: number) =>
    `QUEUE_ADD:${servoId}:${angle}:${duration}`,
  // 队列命令：清空队列
  QUEUE_CLEAR: () => 'QUEUE_CLEAR',
};
