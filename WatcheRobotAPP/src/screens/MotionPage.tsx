import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useBluetooth, BluetoothStatus } from '../modules/bluetooth';
import {
  ACTIONS,
  COMMANDS,
  BLUETOOTH_UUIDS,
} from '../modules/bluetooth/constants/bluetoothConstants';
import { parseBlenderAnimation, generateESP32Commands } from '../utils/animationParser';
import { BlenderAnimation } from '../types/animation';
import thinkAnimationJson from '../assets/思考 - 关键_watcher_animation.json';
import sleepAnimationJson from '../assets/睡觉 - 关键_watcher_animation.json';
import testAnimationJson from '../assets/测试 - X_watcher_animation.json';
import executeAnimationJson from '../assets/Execute30fps8s.json';
import failAnimationJson from '../assets/fail30fps4s.json';
import speakAnimationJson from '../assets/speak30fps7s-2.json';
import successAnimationJson from '../assets/Success30fps3s.json';
import thinkingAnimationJson from '../assets/thinking30fps6s.json';

// 动作类型
interface Motion {
  id: number;
  name: string;
  label: string;
  icon: string;
}

// 可用动作 - 基于嵌入式预设动作
const MOTIONS: Motion[] = [
  { id: 0, name: 'wave', label: '挥手', icon: '👋' },
  { id: 1, name: 'greet', label: '问候', icon: '🙂' },
];

// 动画文件列表
const ANIMATIONS = [
  { id: 'think', name: '思考', json: thinkAnimationJson as BlenderAnimation },
  { id: 'sleep', name: '睡觉', json: sleepAnimationJson as BlenderAnimation },
  { id: 'test', name: '测试', json: testAnimationJson as BlenderAnimation },
  { id: 'execute', name: '执行', json: executeAnimationJson as BlenderAnimation },
  { id: 'fail', name: '失败', json: failAnimationJson as BlenderAnimation },
  { id: 'speak', name: '说话', json: speakAnimationJson as BlenderAnimation },
  { id: 'success', name: '成功', json: successAnimationJson as BlenderAnimation },
  { id: 'thinking', name: '思考2', json: thinkingAnimationJson as BlenderAnimation },
];

export const MotionPage: React.FC = () => {
  const { status, writeData, deviceInfo, sendCommand } = useBluetooth();
  const [selectedMotion, setSelectedMotion] = useState<number | null>(null);
  const [selectedAnimation, setSelectedAnimation] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // 检查是否连接
  const isConnected = status === BluetoothStatus.Connected;

  // 发送命令
  const sendBLECommand = useCallback(async (command: string) => {
    try {
      await sendCommand({
        data: command,
        serviceUUID: BLUETOOTH_UUIDS.SERVICE_UUID,
        characteristicUUID: BLUETOOTH_UUIDS.SERVO_CTRL,
        type: 'response',
      });
      console.log('发送命令:', command);
    } catch (err: any) {
      console.error('发送命令失败:', err);
    }
  }, [sendCommand]);

  // 发送动作命令 - 使用 sendCommand 更可靠
  const sendActionCommand = useCallback(async (actionId: number) => {
    if (!isConnected) {
      Alert.alert('提示', '请先连接蓝牙设备');
      return;
    }

    try {
      const command = COMMANDS.PLAY_ACTION(actionId);
      await sendCommand({
        data: command,
        serviceUUID: BLUETOOTH_UUIDS.SERVICE_UUID,
        characteristicUUID: BLUETOOTH_UUIDS.ACTION_CTRL,
        type: 'response',
      });
      console.log('发送动作命令:', command);
    } catch (err: any) {
      console.error('发送动作命令失败:', err);
      Alert.alert('错误', err.message || '发送命令失败，请确保已连接到 ESP_ROBOT 设备');
    }
  }, [isConnected, sendCommand]);

  // 播放动画
  const playAnimation = useCallback(async (animation: typeof ANIMATIONS[0]) => {
    if (!isConnected) {
      Alert.alert('提示', '请先连接蓝牙设备');
      return;
    }

    try {
      // 解析动画
      const parsed = parseBlenderAnimation(animation.json, animation.name);
      console.log('解析动画:', parsed.name, '时长:', parsed.duration, 'ms');
      console.log('命令数量:', parsed.servoCommands.length);

      // 生成 ESP32 命令
      const commands = generateESP32Commands(parsed);

      // 依次发送所有命令
      for (const cmd of commands) {
        await sendBLECommand(cmd);
        // 添加小延迟避免发送过快
        await new Promise<void>(resolve => {
          setTimeout(() => resolve(), 10);
        });
      }

      console.log('动画命令发送完成');
      setIsPlaying(true);

      // 动画完成后重置状态
      setTimeout(() => {
        setIsPlaying(false);
        setSelectedAnimation(null);
      }, parsed.duration);
    } catch (err: any) {
      console.error('播放动画失败:', err);
      Alert.alert('错误', '播放动画失败');
    }
  }, [isConnected, sendBLECommand]);

  const handleMotionPress = (motionId: number) => {
    if (selectedMotion === motionId) {
      setSelectedMotion(null);
      setIsPlaying(false);
    } else {
      setSelectedMotion(motionId);
      setSelectedAnimation(null);
      sendActionCommand(motionId);
      setIsPlaying(true);
    }
  };

  const handleAnimationPress = (animationId: string) => {
    if (selectedAnimation === animationId) {
      setSelectedAnimation(null);
      setIsPlaying(false);
      // 发送停止命令
      sendBLECommand(COMMANDS.QUEUE_CLEAR());
    } else {
      setSelectedAnimation(animationId);
      setSelectedMotion(null);
      const animation = ANIMATIONS.find(a => a.id === animationId);
      if (animation) {
        playAnimation(animation);
      }
    }
  };

  const handlePlayStop = () => {
    if (isPlaying) {
      setIsPlaying(false);
      setSelectedMotion(null);
      setSelectedAnimation(null);
      // 停止动画队列
      sendBLECommand(COMMANDS.QUEUE_CLEAR());
      // 发送初始化角度
      sendBLECommand(COMMANDS.SET_SERVO(0, 90));
      sendBLECommand(COMMANDS.SET_SERVO(1, 120));
    } else if (selectedMotion !== null) {
      setIsPlaying(true);
      sendActionCommand(selectedMotion);
    } else if (selectedAnimation !== null) {
      const animation = ANIMATIONS.find(a => a.id === selectedAnimation);
      if (animation) {
        playAnimation(animation);
      }
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>动作控制</Text>
        <View style={[styles.statusBadge, { backgroundColor: isConnected ? '#34C759' : '#FF3B30' }]}>
          <Text style={styles.statusText}>
            {isPlaying ? '运行中' : (isConnected ? '就绪' : '未连接')}
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

        {/* 动作网格 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>预设动作</Text>
          <View style={styles.motionGrid}>
            {MOTIONS.map((motion) => (
              <TouchableOpacity
                key={motion.id}
                style={[
                  styles.motionCard,
                  selectedMotion === motion.id && styles.motionCardActive,
                  !isConnected && styles.motionCardDisabled,
                ]}
                onPress={() => handleMotionPress(motion.id)}
                disabled={!isConnected}
              >
                <Text style={styles.motionIcon}>{motion.icon}</Text>
                <Text
                  style={[
                    styles.motionName,
                    selectedMotion === motion.id && styles.motionNameActive,
                  ]}
                >
                  {motion.label}
                </Text>
                <Text style={styles.motionDesc}>ID: {motion.id}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Blender 动画 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Blender 动画</Text>
          <View style={styles.motionGrid}>
            {ANIMATIONS.map((animation) => (
              <TouchableOpacity
                key={animation.id}
                style={[
                  styles.motionCard,
                  selectedAnimation === animation.id && styles.motionCardActive,
                  !isConnected && styles.motionCardDisabled,
                ]}
                onPress={() => handleAnimationPress(animation.id)}
                disabled={!isConnected}
              >
                <Text style={styles.motionIcon}>🎬</Text>
                <Text
                  style={[
                    styles.motionName,
                    selectedAnimation === animation.id && styles.motionNameActive,
                  ]}
                >
                  {animation.name}
                </Text>
                <Text style={styles.motionDesc}>JSON 动画</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* 说明 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>说明</Text>
          <View style={styles.card}>
            <Text style={styles.infoText}>
              预设动作：{'\n'}
              • ID 0 - 挥手 (wave){'\n'}
              • ID 1 - 问候 (greet){'\n'}
              {'\n'}Blender 动画：{'\n'}
              • 解析 JSON 关键帧数据{'\n'}
              • 计算时间差并发送队列命令
            </Text>
            <Text style={styles.infoText}>
              {'\n'}命令格式：{'\n'}
              • PLAY_ACTION:{"<动作ID>"}{'\n'}
              • QUEUE_ADD:id:angle:duration:delay{'\n'}
              • QUEUE_START / QUEUE_CLEAR
            </Text>
          </View>
        </View>

        {/* 播放/停止按钮 */}
        <View style={styles.section}>
          <TouchableOpacity
            style={[
              styles.playButton,
              ((!selectedMotion && !selectedAnimation) || !isConnected) && styles.playButtonDisabled,
            ]}
            onPress={handlePlayStop}
            disabled={(!selectedMotion && !selectedAnimation) || !isConnected}
          >
            <Text style={styles.playButtonText}>
              {isPlaying ? '停止' : '播放'}
            </Text>
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
  infoText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
  },
  motionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  motionCard: {
    width: '47%',
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
  },
  motionCardActive: {
    backgroundColor: '#007AFF',
  },
  motionCardDisabled: {
    opacity: 0.5,
  },
  motionIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  motionName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  motionNameActive: {
    color: '#FFF',
  },
  motionDesc: {
    fontSize: 12,
    color: '#8E8E93',
  },
  playButton: {
    backgroundColor: '#34C759',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  playButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  playButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
