"""舵机控制器 - 读取JSON动画文件并按时间戳发送舵机数据"""
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ServoKeyframe:
    """单帧舵机数据（关键帧版本）"""
    frame_number: int  # 帧号
    time: float  # 时间戳（秒）
    angle: float  # 角度


@dataclass
class ServoFrame:
    """单帧数据（顺序帧格式）"""
    x: int  # X 轴角度
    y: int  # Y 轴角度


@dataclass
class ServoAnimation:
    """单个动画数据"""
    name: str
    fps: int
    # 关键帧数据（用于按时间戳播放）
    x_keyframes: list[ServoKeyframe]  # X 轴关键帧列表
    y_keyframes: list[ServoKeyframe]  # Y 轴关键帧列表
    duration: float  # 动画总时长（秒）
    max_frame: int  # 最大帧号


class ServoController:
    """舵机控制器 - 管理JSON动画文件并发送舵机指令"""

    def __init__(self, json_dir: str = None):
        """初始化舵机控制器

        Args:
            json_dir: JSON动画文件目录
        """
        self.json_dir = json_dir or settings.servo_json_dir

        # 存储所有动画数据 {state_name: ServoAnimation}
        self.animations: dict[str, ServoAnimation] = {}

        # 当前播放状态
        self._current_task: Optional[asyncio.Task] = None
        self._is_playing: bool = False

        # 独占播放状态（一次性播放，优先级更高，不能被中断）
        self._is_exclusive: bool = False
        self._exclusive_lock: asyncio.Lock = asyncio.Lock()

        # 回调函数：发送舵机数据到客户端
        self._send_callback: Optional[callable] = None

        logger.info(f"舵机控制器初始化: json_dir={self.json_dir}")

    def set_send_callback(self, callback: callable):
        """设置发送回调函数

        Args:
            callback: 回调函数，接收 frames 参数，frames 是一个包含帧数据的列表
                      每帧格式: {"id": "x"/"y", "Angle": angle, "time": interval}
        """
        self._send_callback = callback

    async def load_animations(self):
        """加载所有JSON动画文件"""
        json_path = Path(self.json_dir)

        if not json_path.exists():
            logger.warning(f"舵机动画目录不存在: {json_path}")
            return

        # 查找所有JSON文件
        json_files = list(json_path.glob("*.json"))
        logger.info(f"找到 {len(json_files)} 个舵机动画文件")

        for json_file in json_files:
            state_name = json_file.stem  # 文件名不带扩展名
            try:
                animation = self._load_json(json_file)
                if animation:
                    self.animations[state_name] = animation
                    logger.info(f"加载动画: {state_name} - fps={animation.fps}, duration={animation.duration:.2f}s, x_keyframes={len(animation.x_keyframes)}, y_keyframes={len(animation.y_keyframes)}")
                else:
                    logger.warning(f"动画文件为空: {json_file}")
            except Exception as e:
                logger.error(f"加载动画失败 {json_file}: {e}")

    def _load_json(self, json_path: Path) -> Optional[ServoAnimation]:
        """加载单个JSON文件

        Args:
            json_path: JSON文件路径

        Returns:
            ServoAnimation: 动画数据
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        fps = data.get('fps', 30)
        frame_start = data.get('frame_start', 1)
        frame_end = data.get('frame_end', 150)
        animated_objects = data.get('animated_objects', [])

        # 分离 x 和 y 轴的关键帧数据
        x_keyframes: list[ServoKeyframe] = []  # X 轴关键帧列表
        y_keyframes: list[ServoKeyframe] = []  # Y 轴关键帧列表

        for obj in animated_objects:
            object_name = obj.get('object_name', '')

            # 根据 object_name 映射到 x 或 y 轴
            # "头轴" -> y轴, "底部轴" -> x轴
            if '头轴' in object_name:
                axis = 'y'
            elif '底部轴' in object_name:
                axis = 'x'
            else:
                continue

            keyframe_data = obj.get('keyframe_data', [])
            for kf in keyframe_data:
                frame_number = kf.get('frame_number', 0)
                rotation_angle = kf.get('rotation_angle', 0)

                # 计算时间戳（秒）
                time = (frame_number - frame_start) / fps

                keyframe = ServoKeyframe(
                    frame_number=frame_number,
                    time=time,
                    angle=rotation_angle
                )

                if axis == 'y':
                    y_keyframes.append(keyframe)
                elif axis == 'x':
                    x_keyframes.append(keyframe)

        # 按时间排序
        x_keyframes.sort(key=lambda k: k.time)
        y_keyframes.sort(key=lambda k: k.time)

        # 计算总时长
        max_frame = frame_end
        duration = (max_frame - frame_start + 1) / fps if fps > 0 else 0.0

        return ServoAnimation(
            name=json_path.stem,
            fps=fps,
            x_keyframes=x_keyframes,
            y_keyframes=y_keyframes,
            duration=duration,
            max_frame=max_frame
        )

    async def start(self, state: str, loop: bool = True):
        """开始播放指定状态的动画

        Args:
            state: 状态名称 (对应JSON文件名)
            loop: 是否循环播放
        """
        if state not in self.animations:
            logger.warning(f"动画状态不存在: {state}")
            return

        # 如果当前有独占播落在进行，等待其完成
        if self._is_exclusive:
            logger.info(f"等待独占播放完成后开始循环动画: {state}")
            await self._exclusive_lock.acquire()
            self._exclusive_lock.release()

        # 如果正在播放，先停止
        if self._is_playing:
            await self.stop()

        self._is_playing = True
        logger.info(f"开始播放舵机动画: {state}, loop={loop}")

        # 创建播放任务
        self._current_task = asyncio.create_task(
            self._play_animation(state, loop)
        )

    async def stop(self):
        """停止播放"""
        # 独占播放模式下不允许停止
        if self._is_exclusive:
            logger.warning("独占播放中，无法停止")
            return

        if not self._is_playing:
            return

        self._is_playing = False

        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass

        logger.info("舵机动画已停止")

    async def play_once(self, state: str):
        """独占播放一次（优先级更高，不循环，不可中断）
        一次性发送所有帧数据，按顺序发送

        Args:
            state: 状态名称 (对应JSON文件名)
        """
        if state not in self.animations:
            logger.warning(f"动画状态不存在: {state}")
            return

        # 获取独占锁，如果当前有独占播放在进行，则等待
        async with self._exclusive_lock:
            # 标记为独占播放模式
            self._is_exclusive = True
            logger.info(f"开始独占播放舵机动画: {state}")

            # 停止当前的循环播放
            if self._is_playing and self._current_task:
                self._is_playing = False
                if not self._current_task.done():
                    self._current_task.cancel()
                    try:
                        await self._current_task
                    except asyncio.CancelledError:
                        pass

            # 开始独占播放
            self._is_playing = True

            try:
                animation = self.animations[state]
                await self._play_animation_by_timestamp(animation)

                logger.info(f"独占播放完成: {state}")
            except asyncio.CancelledError:
                logger.info(f"独占播放被取消: {state}")
            finally:
                self._is_playing = False
                self._is_exclusive = False

    async def _play_animation_by_timestamp(self, animation: ServoAnimation):
        """按关键帧播放动画（用于独占播放）
        一次性发送所有帧数据，按顺序发送

        Args:
            animation: 动画数据
        """
        x_keyframes = animation.x_keyframes
        y_keyframes = animation.y_keyframes

        # 构建 X 轴帧数据列表
        x_frames = []
        prev_time = 0.0
        for kf in x_keyframes:
            delay = kf.time - prev_time
            delay_ms = round(delay * 1000)  # 转换为毫秒并四舍五入
            x_frames.append({"id": "x", "Angle": kf.angle, "time": delay_ms})
            prev_time = kf.time

        # 构建 Y 轴帧数据列表
        y_frames = []
        prev_time = 0.0
        for kf in y_keyframes:
            delay = kf.time - prev_time
            delay_ms = round(delay * 1000)  # 转换为毫秒并四舍五入
            y_frames.append({"id": "y", "Angle": kf.angle, "time": delay_ms})
            prev_time = kf.time

        # 合并 X 和 Y，按时间排序
        all_frames = x_frames + y_frames
        all_frames.sort(key=lambda f: f["time"])

        # 一次性发送所有帧
        if self._send_callback:
            try:
                await self._send_callback(frames=all_frames)
            except Exception as e:
                logger.error(f"发送舵机数据失败: {e}")

    def _get_angle_at_time(self, keyframes: list[ServoKeyframe], target_time: float) -> float:
        """获取指定时间点的角度（精确匹配关键帧）

        Args:
            keyframes: 关键帧列表（已按时间排序）
            target_time: 目标时间（秒）

        Returns:
            float: 角度
        """
        if not keyframes:
            return 90.0

        # 找到最接近目标时间的关键帧
        closest_kf = min(keyframes, key=lambda k: abs(k.time - target_time))
        return closest_kf.angle

    async def _play_animation(self, state: str, loop: bool):
        """播放动画的协程（循环播放模式）
        一次性发送所有帧数据，按顺序发送

        Args:
            state: 状态名称
            loop: 是否循环
        """
        animation = self.animations[state]
        x_keyframes = animation.x_keyframes
        y_keyframes = animation.y_keyframes

        while self._is_playing:
            # 构建 X 轴帧数据列表
            x_frames = []
            prev_time = 0.0
            for kf in x_keyframes:
                delay = kf.time - prev_time
                delay_ms = round(delay * 1000)  # 转换为毫秒并四舍五入
                x_frames.append({"id": "x", "Angle": kf.angle, "time": delay_ms})
                prev_time = kf.time

            # 构建 Y 轴帧数据列表
            y_frames = []
            prev_time = 0.0
            for kf in y_keyframes:
                delay = kf.time - prev_time
                delay_ms = round(delay * 1000)  # 转换为毫秒并四舍五入
                y_frames.append({"id": "y", "Angle": kf.angle, "time": delay_ms})
                prev_time = kf.time

            # 合并 X 和 Y，按时间排序
            all_frames = x_frames + y_frames
            all_frames.sort(key=lambda f: f["time"])

            # 一次性发送所有帧
            if self._send_callback:
                try:
                    await self._send_callback(frames=all_frames)
                except Exception as e:
                    logger.error(f"发送舵机数据失败: {e}")

            # 如果不循环，等待总时长后退出
            if not loop:
                break

            # 等待动画完成
            await asyncio.sleep(animation.duration)

        self._is_playing = False

    def get_available_states(self) -> list[str]:
        """获取所有可用的动画状态

        Returns:
            list[str]: 状态名称列表
        """
        return list(self.animations.keys())

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self._is_playing
