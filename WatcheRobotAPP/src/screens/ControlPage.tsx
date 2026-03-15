import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import Slider from '@react-native-community/slider';
import { useBluetooth, BluetoothStatus } from '../modules/bluetooth';
import {
  SERVO_CONFIG,
  ACTIONS,
  COMMANDS,
  BLUETOOTH_UUIDS,
} from '../modules/bluetooth/constants/bluetoothConstants';

// 平滑参数
const SMOOTH_ALPHA = 0.3; // 指数平滑系数：越大响应越快，越小越平滑
const SEND_INTERVAL_MS = 50; // 发送间隔

// 舵机配置
const SERVO_CHANNELS = [
  { id: 0, name: 'X轴 (GPIO 12)', minAngle: SERVO_CONFIG.ANGLE_MIN_X, maxAngle: SERVO_CONFIG.ANGLE_MAX_X },
  { id: 1, name: 'Y轴 (GPIO 15)', minAngle: SERVO_CONFIG.ANGLE_MIN_Y, maxAngle: SERVO_CONFIG.ANGLE_MAX_Y },
];

// 预设姿势
const PRESETS = [
  { name: '初始化', angles: [90, 120] },
  { name: '站立', angles: [90, 95] },
  { name: '低头', angles: [90, 150] },
  { name: '抬头', angles: [90, 95] },
];

export const ControlPage: React.FC = () => {
  const { status, writeData, deviceInfo, error, sendCommand } = useBluetooth();
  const [angles, setAngles] = useState<number[]>([90, 120]);
  const [isSending, setIsSending] = useState(false);

  // 检查是否连接（必须在 useRef 之前声明）
  const isConnected = status === BluetoothStatus.Connected;

  // 平滑控制状态
  const [targetAngles, setTargetAngles] = useState<number[]>([90, 120]); // UI显示的角度（立即跟手）
  const smoothAnglesRef = useRef<number[]>([90, 120]); // 平滑后的角度（实际发送）
  const lastSentAngleRef = useRef<number[]>([90, 120]); // 上次发送的角度（避免重复发送）
  const isDraggingRef = useRef<boolean[]>([false, false]); // 追踪各舵机是否正在拖动
  const isConnectedRef = useRef(isConnected); // 保持最新连接状态
  isConnectedRef.current = isConnected;

  // 指数平滑计算
  const smoothValue = (current: number, target: number): number => {
    return Math.round(current * (1 - SMOOTH_ALPHA) + target * SMOOTH_ALPHA);
  };

  // 定时发送平滑后的角度
  useEffect(() => {
    const interval = setInterval(() => {
      const hasActiveDrag = isDraggingRef.current.some(Boolean);

      if (hasActiveDrag && isConnectedRef.current) {
        isDraggingRef.current.forEach((isDragging, servoId) => {
          if (isDragging) {
            // 平滑计算
            const smoothed = smoothValue(
              smoothAnglesRef.current[servoId],
              targetAngles[servoId]
            );
            smoothAnglesRef.current[servoId] = smoothed;

            // 只有角度发生变化时才发送BLE命令
            if (smoothed !== lastSentAngleRef.current[servoId]) {
              const command = COMMANDS.SET_SERVO(servoId, smoothed);
              sendCommand({
                data: command,
                serviceUUID: BLUETOOTH_UUIDS.SERVICE_UUID,
                characteristicUUID: BLUETOOTH_UUIDS.SERVO_CTRL,
                type: 'response',
              }).catch(() => {});
              lastSentAngleRef.current[servoId] = smoothed;
            }
          }
        });
      }
    }, SEND_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [targetAngles, sendCommand]);

  // 发送舵机命令 - 使用 sendCommand 更可靠
  const sendServoCommand = useCallback(async (servoId: number, angle: number) => {
    if (!isConnected) {
      Alert.alert('提示', '请先连接蓝牙设备');
      return;
    }

    setIsSending(true);
    try {
      const command = COMMANDS.SET_SERVO(servoId, angle);
      // 使用 sendCommand，它会自动处理服务发现
      await sendCommand({
        data: command,
        serviceUUID: BLUETOOTH_UUIDS.SERVICE_UUID,
        characteristicUUID: BLUETOOTH_UUIDS.SERVO_CTRL,
        type: 'response',
      });
      console.log('发送命令:', command);
    } catch (err: any) {
      console.error('发送命令失败:', err);
      Alert.alert('错误', err.message || '发送命令失败，请确保已连接到 ESP_ROBOT 设备');
    } finally {
      setIsSending(false);
    }
  }, [isConnected, sendCommand]);

  // 开始拖动
  const handleDragStart = (channel: number) => {
    isDraggingRef.current[channel] = true;
    smoothAnglesRef.current[channel] = angles[channel]; //起始点 重置平滑
  };

  // 拖动中 - 更新目标角度
  const handleValueChange = (channel: number, value: number) => {
    const roundedValue = Math.round(value);
    setTargetAngles(prev => {
      const newTargets = [...prev];
      newTargets[channel] = roundedValue;
      return newTargets;
    });
  };

  // 拖动结束
  const handleDragEnd = (channel: number) => {
    isDraggingRef.current[channel] = false;
    // 释放时立即发送最终目标角度
    sendServoCommand(channel, targetAngles[channel]);
    setAngles(prev => {
      const newAngles = [...prev];
      newAngles[channel] = targetAngles[channel];
      return newAngles;
    });
    smoothAnglesRef.current[channel] = targetAngles[channel];
  };

  // 快速切换角度（不使用平滑，直接发送）
  const quickUpdateAngle = (channel: number, angle: number) => {
    const newAngles = [...angles];
    newAngles[channel] = angle;
    setAngles(newAngles);
    setTargetAngles(prev => {
      const newTargets = [...prev];
      newTargets[channel] = angle;
      return newTargets;
    });
    smoothAnglesRef.current[channel] = angle;
    sendServoCommand(channel, angle);
  };

  const applyPreset = (preset: typeof PRESETS[0]) => {
    const newAngles = [...preset.angles];
    setAngles(newAngles);
    setTargetAngles(newAngles);
    smoothAnglesRef.current = [...newAngles];
    // 依次发送两个舵机的命令
    preset.angles.forEach((angle, index) => {
      sendServoCommand(index, angle);
    });
  };

  // 快速预设角度按钮
  const quickAngles = [30, 60, 90, 120, 150];

  // 发送持续移动命令（摇杆模式）
  const sendMoveCommand = useCallback(async (servoId: number, direction: number) => {
    if (!isConnected) {
      return;
    }
    const command = COMMANDS.SERVO_MOVE(servoId, direction);
    try {
      await sendCommand({
        data: command,
        serviceUUID: BLUETOOTH_UUIDS.SERVICE_UUID,
        characteristicUUID: BLUETOOTH_UUIDS.SERVO_CTRL,
        type: 'response',
      });
    } catch (err) {
      // 静默失败，避免频繁提示
    }
  }, [isConnected, sendCommand]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>舵机控制</Text>
        <View style={[styles.statusBadge, { backgroundColor: isConnected ? '#34C759' : '#FF3B30' }]}>
          <Text style={styles.statusText}>
            {isConnected ? '已连接' : '未连接'}
          </Text>
        </View>
      </View>

      <ScrollView style={styles.content}>
        {/* 连接信息 */}
        {isConnected && deviceInfo && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>设备信息</Text>
            <View style={styles.card}>
              <Text style={styles.deviceName}>{deviceInfo.name || 'ESP_ROBOT'}</Text>
            </View>
          </View>
        )}

        {/* 预设姿势 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>预设姿势</Text>
          <View style={styles.presetGrid}>
            {PRESETS.map((preset) => (
              <TouchableOpacity
                key={preset.name}
                style={[styles.presetButton, !isConnected && styles.buttonDisabled]}
                onPress={() => applyPreset(preset)}
                disabled={!isConnected}
              >
                <Text style={styles.presetText}>{preset.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* 方向控制（上下左右） */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>方向控制</Text>

          {/* 十字方向键 */}
          <View style={styles.dpadContainer}>
            <View style={styles.dpadRow}>
              <View style={styles.dpadEmpty} />
              {/* 上 - Y轴正向（抬头） */}
              <TouchableOpacity
                style={[styles.dpadButton, !isConnected && styles.dpadDisabled]}
                onPressIn={() => sendMoveCommand(1, 1)}
                onPressOut={() => sendMoveCommand(1, 0)}
                disabled={!isConnected}
              >
                <Text style={styles.dpadButtonText}>上</Text>
              </TouchableOpacity>
              <View style={styles.dpadEmpty} />
            </View>

            <View style={styles.dpadRow}>
              {/* 左 - X轴反向（左转） */}
              <TouchableOpacity
                style={[styles.dpadButton, !isConnected && styles.dpadDisabled]}
                onPressIn={() => sendMoveCommand(0, -1)}
                onPressOut={() => sendMoveCommand(0, 0)}
                disabled={!isConnected}
              >
                <Text style={styles.dpadButtonText}>左</Text>
              </TouchableOpacity>

              {/* 中间 - 显示当前角度 */}
              <View style={styles.dpadCenter}>
                <Text style={styles.dpadCenterText}>{targetAngles[0]}°</Text>
                <Text style={styles.dpadCenterText}>{targetAngles[1]}°</Text>
              </View>

              {/* 右 - X轴正向（右转） */}
              <TouchableOpacity
                style={[styles.dpadButton, !isConnected && styles.dpadDisabled]}
                onPressIn={() => sendMoveCommand(0, 1)}
                onPressOut={() => sendMoveCommand(0, 0)}
                disabled={!isConnected}
              >
                <Text style={styles.dpadButtonText}>右</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.dpadRow}>
              <View style={styles.dpadEmpty} />
              {/* 下 - Y轴反向（低头） */}
              <TouchableOpacity
                style={[styles.dpadButton, !isConnected && styles.dpadDisabled]}
                onPressIn={() => sendMoveCommand(1, -1)}
                onPressOut={() => sendMoveCommand(1, 0)}
                disabled={!isConnected}
              >
                <Text style={styles.dpadButtonText}>下</Text>
              </TouchableOpacity>
              <View style={styles.dpadEmpty} />
            </View>
          </View>

          <Text style={styles.dpadHint}>上/下控制Y轴，左/右控制X轴，按住持续移动</Text>
        </View>

        {/* 舵机滑块 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>舵机控制</Text>
          {SERVO_CHANNELS.map((servo) => (
            <View key={servo.id} style={styles.servoControl}>
              <View style={styles.servoHeader}>
                <Text style={styles.servoName}>{servo.name}</Text>
                <Text style={styles.servoAngle}>{targetAngles[servo.id]}°</Text>
              </View>

              {/* 快速角度按钮 */}
              <View style={styles.quickButtons}>
                {quickAngles.map((angle) => (
                  <TouchableOpacity
                    key={angle}
                    style={[
                      styles.quickButton,
                      targetAngles[servo.id] === angle && styles.quickButtonActive,
                      (angle < servo.minAngle || angle > servo.maxAngle) && styles.quickButtonDisabled,
                    ]}
                    onPress={() => quickUpdateAngle(servo.id, angle)}
                    disabled={!isConnected || angle < servo.minAngle || angle > servo.maxAngle}
                  >
                    <Text
                      style={[
                        styles.quickButtonText,
                        targetAngles[servo.id] === angle && styles.quickButtonTextActive,
                      ]}
                    >
                      {angle}°
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* 滑动条 - 带平滑发送 */}
              <View style={styles.sliderContainer}>
                <Text style={styles.sliderLabel}>{servo.minAngle}°</Text>
                <Slider
                  style={styles.slider}
                  minimumValue={servo.minAngle}
                  maximumValue={servo.maxAngle}
                  step={1}
                  value={targetAngles[servo.id]}
                  onSlidingStart={() => handleDragStart(servo.id)}
                  onValueChange={(value) => handleValueChange(servo.id, value)}
                  onSlidingComplete={() => handleDragEnd(servo.id)}
                  minimumTrackTintColor="#007AFF"
                  maximumTrackTintColor="#E5E5EA"
                  thumbTintColor="#007AFF"
                />
                <Text style={styles.sliderLabel}>{servo.maxAngle}°</Text>
              </View>
            </View>
          ))}
        </View>

        {/* 发送按钮 */}
        <View style={styles.section}>
          <TouchableOpacity
            style={[styles.sendButton, !isConnected && styles.sendButtonDisabled]}
            onPress={() => {
              // 发送当前所有舵机角度
              angles.forEach((angle, index) => {
                sendServoCommand(index, angle);
              });
            }}
            disabled={!isConnected}
          >
            <Text style={styles.sendButtonText}>发送当前角度</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#F2F2F7',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#000',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '500',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    color: '#6E6E73',
    textTransform: 'uppercase',
    marginBottom: 12,
    marginLeft: 4,
  },
  card: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
  },
  deviceName: {
    fontSize: 16,
    color: '#000',
    fontWeight: '500',
  },
  presetGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  presetButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  presetText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '500',
  },
  buttonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  servoControl: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  servoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  servoName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#000',
  },
  servoAngle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  quickButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  quickButton: {
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  quickButtonActive: {
    backgroundColor: '#007AFF',
  },
  quickButtonDisabled: {
    opacity: 0.4,
  },
  quickButtonText: {
    fontSize: 12,
    color: '#007AFF',
  },
  quickButtonTextActive: {
    color: '#FFF',
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sliderLabel: {
    fontSize: 12,
    color: '#8E8E93',
    width: 35,
  },
  slider: {
    flex: 1,
    height: 40,
    marginHorizontal: 8,
  },
  sendButton: {
    backgroundColor: '#34C759',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  sendButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  // 十字方向键样式
  dpadContainer: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  dpadRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dpadEmpty: {
    width: 70,
    height: 70,
  },
  dpadButton: {
    width: 70,
    height: 70,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 12,
    margin: 4,
  },
  dpadButtonText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '600',
  },
  dpadCenter: {
    width: 70,
    height: 70,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    margin: 4,
  },
  dpadCenterText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  dpadDisabled: {
    backgroundColor: '#C7C7CC',
  },
  dpadHint: {
    fontSize: 12,
    color: '#8E8E93',
    textAlign: 'center',
    marginTop: 12,
  },
});
