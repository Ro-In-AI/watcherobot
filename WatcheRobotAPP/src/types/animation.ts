/**
 * Blender 动画 JSON 数据类型定义
 */

// 关键帧数据
export interface AnimationKeyframe {
  frame_number: number;
  active_axis: string;
  rotation_angle: number;
}

// 动画对象（每个舵机）
export interface AnimatedObject {
  object_name: string;
  object_type: string;
  action_name: string;
  keyframe_data: AnimationKeyframe[];
}

// Blender 导出的完整动画数据
export interface BlenderAnimation {
  scene_name: string;
  frame_start: number;
  frame_end: number;
  fps: number;
  animated_objects: AnimatedObject[];
}

// 解析后的舵机命令
export interface ServoCommand {
  servoId: number;      // 舵机 ID (0 = 底部轴/X轴, 1 = 头轴/Y轴)
  angle: number;        // 目标角度
  durationMs: number;   // 移动持续时间 (ms)
}

// 动画元数据
export interface AnimationMeta {
  name: string;
  duration: number;     // 总时长 (ms)
  servoCommands: ServoCommand[];
}

// 舵机映射配置
export const SERVO_MAPPING: Record<string, number> = {
  '底部轴': 0,
  '头轴': 1,
};
