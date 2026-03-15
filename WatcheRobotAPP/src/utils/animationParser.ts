/**
 * Blender 动画 JSON 解析工具
 */

import {
  BlenderAnimation,
  ServoCommand,
  AnimationMeta,
  SERVO_MAPPING,
} from '../types/animation';

/**
 * 解析 Blender 导出的动画 JSON
 * 按帧号对齐 X 和 Y 轴命令，确保同一帧的 X 和 Y 命令同时发送
 */
export function parseBlenderAnimation(
  json: BlenderAnimation,
  animationName: string
): AnimationMeta {
  const { fps, animated_objects } = json;

  // 计算每帧对应的时间 (ms)
  const msPerFrame = 1000 / fps;

  // 按帧号分组存储命令
  // key: 帧号, value: 该帧时刻的所有舵机命令
  const frameCommandsMap = new Map<number, ServoCommand[]>();

  // 遍历每个动画对象
  for (const obj of animated_objects) {
    const servoId = SERVO_MAPPING[obj.object_name];

    if (servoId === undefined) {
      console.warn(`Unknown object name: ${obj.object_name}`);
      continue;
    }

    const keyframes = obj.keyframe_data;

    // 遍历关键帧，计算每个关键帧之间的时间差
    for (let i = 1; i < keyframes.length; i++) {
      const prevFrame = keyframes[i - 1];
      const currFrame = keyframes[i];

      // 计算时间差 = 帧差 / fps * 1000
      const frameDiff = currFrame.frame_number - prevFrame.frame_number;
      const durationMs = Math.round(frameDiff * msPerFrame);

      // 目标角度
      const targetAngle = Math.round(currFrame.rotation_angle);

      const cmd: ServoCommand = {
        servoId,
        angle: targetAngle,
        durationMs,
      };

      // 按帧号添加到对应的组
      const frameNum = currFrame.frame_number;
      if (!frameCommandsMap.has(frameNum)) {
        frameCommandsMap.set(frameNum, []);
      }
      frameCommandsMap.get(frameNum)!.push(cmd);
    }
  }

  // 按帧号排序，依次输出所有命令
  const allCommands: ServoCommand[] = [];
  const sortedFrameNumbers = Array.from(frameCommandsMap.keys()).sort((a, b) => a - b);

  for (const frameNum of sortedFrameNumbers) {
    const cmds = frameCommandsMap.get(frameNum)!;
    // 同一帧的 X 和 Y 命令都添加进去
    allCommands.push(...cmds);
  }

  // 计算总时长（取最后一个命令的结束时间）
  const lastCmd = allCommands[allCommands.length - 1];
  const totalDuration = lastCmd
    ? allCommands.reduce((sum, cmd) => sum + cmd.durationMs, 0)
    : 0;

  return {
    name: animationName,
    duration: totalDuration,
    servoCommands: allCommands,
  };
}

/**
 * 生成 ESP32 命令字符串
 */
export function generateESP32Commands(animation: AnimationMeta): string[] {
  const commands: string[] = [];

  // 先清空队列
  commands.push('QUEUE_CLEAR');

  // 添加所有命令到队列
  // 格式: QUEUE_ADD:servoId:angle:duration
  // ESP32 检测到队列有命令会自动开始执行
  for (const cmd of animation.servoCommands) {
    commands.push(
      `QUEUE_ADD:${cmd.servoId}:${cmd.angle}:${cmd.durationMs}`
    );
  }

  return commands;
}
