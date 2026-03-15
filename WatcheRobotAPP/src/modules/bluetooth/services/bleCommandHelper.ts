/**
 * BLE 命令发送辅助模块
 * 基于 ESP32 BLE 机器人协议
 */

import { BLECommands } from '../types';
import {
  BLUETOOTH_UUIDS,
  SERVO_CONFIG,
  ACTIONS,
  COMMANDS,
} from '../constants/bluetoothConstants';

/**
 * 发送舵机控制命令
 */
export const sendServoCommand = async (
  writeData: (serviceUUID: string, charUUID: string, data: string) => Promise<void>,
  servoId: number,
  angle: number
): Promise<void> => {
  // 验证角度范围
  const minAngle = servoId === SERVO_CONFIG.SERVO_X
    ? SERVO_CONFIG.ANGLE_MIN_X
    : SERVO_CONFIG.ANGLE_MIN_Y;
  const maxAngle = servoId === SERVO_CONFIG.SERVO_X
    ? SERVO_CONFIG.ANGLE_MAX_X
    : SERVO_CONFIG.ANGLE_MAX_Y;

  if (angle < minAngle || angle > maxAngle) {
    throw new Error(`舵机${servoId}角度范围: ${minAngle}~${maxAngle}`);
  }

  const command = COMMANDS.SET_SERVO(servoId, angle);
  await writeData(BLUETOOTH_UUIDS.SERVICE_UUID, BLUETOOTH_UUIDS.SERVO_CTRL, command);
};

/**
 * 发送动作播放命令
 */
export const sendActionCommand = async (
  writeData: (serviceUUID: string, charUUID: string, data: string) => Promise<void>,
  actionId: number
): Promise<void> => {
  // 验证动作ID
  if (actionId < 0 || actionId >= ACTIONS.length) {
    throw new Error(`无效的动作ID: ${actionId}`);
  }

  const command = COMMANDS.PLAY_ACTION(actionId);
  await writeData(BLUETOOTH_UUIDS.SERVICE_UUID, BLUETOOTH_UUIDS.ACTION_CTRL, command);
};

/**
 * 获取预设动作列表
 */
export const getActionList = () => {
  return ACTIONS;
};

/**
 * 获取舵机配置
 */
export const getServoConfig = () => {
  return SERVO_CONFIG;
};

export { BLUETOOTH_UUIDS, SERVO_CONFIG, ACTIONS, COMMANDS };
