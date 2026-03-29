"""窗口控制器模块"""

from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from models import Preset


class PositionCalculator:
    """位置计算器"""

    def __init__(self, screen_width: Optional[int] = None, screen_height: Optional[int] = None):
        """初始化位置计算器

        Args:
            screen_width: 屏幕宽度，如果不提供则自动检测
            screen_height: 屏幕高度，如果不提供则自动检测
        """
        if screen_width is None or screen_height is None:
            try:
                import win32api
                screen_width = screen_width or win32api.GetSystemMetrics(0)
                screen_height = screen_height or win32api.GetSystemMetrics(1)
            except ImportError:
                # 无法导入 win32api 时使用默认值
                screen_width = screen_width or 1920
                screen_height = screen_height or 1080

        self.screen_width = screen_width
        self.screen_height = screen_height

    def calculate(self, position: str, window_size: Tuple[int, int]) -> Tuple[int, int]:
        """计算窗口位置

        Args:
            position: 位置字符串，支持: center, top-left, top-right, bottom-left, bottom-right, left, right, top, bottom
            window_size: 窗口尺寸 (width, height)

        Returns:
            (left, top) 坐标元组
        """
        win_width, win_height = window_size

        # 计算位置(不限制窗口尺寸,允许窗口大于屏幕)
        if position == "center":
            left = (self.screen_width - win_width) // 2
            top = (self.screen_height - win_height) // 2
        elif position == "top-left":
            left = 0
            top = 0
        elif position == "top-right":
            left = self.screen_width - win_width
            top = 0
        elif position == "bottom-left":
            left = 0
            top = self.screen_height - win_height
        elif position == "bottom-right":
            left = self.screen_width - win_width
            top = self.screen_height - win_height
        elif position == "left":
            left = 0
            top = (self.screen_height - win_height) // 2
        elif position == "right":
            left = self.screen_width - win_width
            top = (self.screen_height - win_height) // 2
        elif position == "top":
            left = (self.screen_width - win_width) // 2
            top = 0
        elif position == "bottom":
            left = (self.screen_width - win_width) // 2
            top = self.screen_height - win_height
        else:
            # 未知位置，默认居中
            left = (self.screen_width - win_width) // 2
            top = (self.screen_height - win_height) // 2

        return (left, top)


class WindowController:
    """窗口控制器"""

    def __init__(self):
        """初始化窗口控制器"""
        self.calculator = PositionCalculator()

    def get_active_window(self):
        """获取当前活动窗口

        Returns:
            活动窗口对象，如果无活动窗口则返回 None
        """
        try:
            import pygetwindow as gw
            return gw.getActiveWindow()
        except Exception:
            return None

    def apply_preset(self, preset: 'Preset') -> bool:
        """应用预设到当前活动窗口

        Args:
            preset: 窗口预设配置

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            window = self.get_active_window()
            if window is None:
                return False

            # 如果窗口最小化或最大化，先恢复
            try:
                window.restore()
            except Exception:
                # 如果 restore 失败，继续尝试
                pass

            # 确定目标尺寸
            if preset.width is not None and preset.height is not None:
                target_width = preset.width
                target_height = preset.height
            else:
                # 保持窗口原尺寸
                target_width = window.width
                target_height = window.height

            # 计算目标位置
            left, top = self.calculator.calculate(preset.position, (target_width, target_height))

            # 应用尺寸和位置
            window.resizeTo(target_width, target_height)
            window.moveTo(left, top)

            return True
        except Exception:
            return False
