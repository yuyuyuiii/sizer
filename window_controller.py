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
                # 使用 SM_CXSCREEN 和 SM_CYSCREEN 获取真实屏幕分辨率
                # GetSystemMetrics(0) 返回工作区宽度(不含任务栏)
                # GetSystemMetrics(78) 返回屏幕宽度 SM_CXSCREEN
                # GetSystemMetrics(79) 返回屏幕高度 SM_CYSCREEN
                screen_width = screen_width or win32api.GetSystemMetrics(78)  # SM_CXSCREEN
                screen_height = screen_height or win32api.GetSystemMetrics(79)  # SM_CYSCREEN
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

        # 计算位置（限制窗口在屏幕可见区域内）
        # 即使窗口大于屏幕，也确保至少左上角对齐屏幕左上角
        if position == "center":
            left = max(0, (self.screen_width - win_width) // 2)
            top = max(0, (self.screen_height - win_height) // 2)
        elif position == "top-left":
            left = 0
            top = 0
        elif position == "top-right":
            left = max(0, self.screen_width - win_width)
            top = 0
        elif position == "bottom-left":
            left = 0
            top = max(0, self.screen_height - win_height)
        elif position == "bottom-right":
            left = max(0, self.screen_width - win_width)
            top = max(0, self.screen_height - win_height)
        elif position == "left":
            left = 0
            top = max(0, (self.screen_height - win_height) // 2)
        elif position == "right":
            left = max(0, self.screen_width - win_width)
            top = max(0, (self.screen_height - win_height) // 2)
        elif position == "top":
            left = max(0, (self.screen_width - win_width) // 2)
            top = 0
        elif position == "bottom":
            left = max(0, (self.screen_width - win_width) // 2)
            top = max(0, self.screen_height - win_height)
        else:
            # 未知位置，默认居中
            left = max(0, (self.screen_width - win_width) // 2)
            top = max(0, (self.screen_height - win_height) // 2)

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
        import logging
        logger = logging.getLogger()  # 使用 root logger

        try:
            window = self.get_active_window()
            if window is None:
                logger.warning("WindowController: 未找到活动窗口")
                return False

            # 记录窗口初始状态
            logger.info(f"=== 应用预设: {preset.name} ===")
            logger.info(f"预设参数: width={preset.width}, height={preset.height}, position={preset.position}")
            logger.info(f"屏幕分辨率: {self.calculator.screen_width}x{self.calculator.screen_height}")

            # 记录窗口当前状态
            try:
                current_width = window.width
                current_height = window.height
                logger.info(f"窗口当前尺寸: {current_width}x{current_height}")
                # 尝试获取最大化状态（如果支持）
                try:
                    is_maximized = getattr(window, 'is_maximized', None)
                    if is_maximized is not None:
                        logger.info(f"窗口最大化状态: {is_maximized}")
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"无法获取窗口当前尺寸: {e}")

            # 如果窗口最小化或最大化，先恢复
            try:
                logger.debug("调用 window.restore()")
                window.restore()
                logger.debug("restore() 执行完成")
                # 记录 restore 后的窗口状态
                try:
                    restored_width = window.width
                    restored_height = window.height
                    logger.info(f"restore 后窗口尺寸: {restored_width}x{restored_height}")
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"restore() 失败: {e}")
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

            logger.info(f"目标尺寸: {target_width}x{target_height}")

            # 计算目标位置
            left, top = self.calculator.calculate(preset.position, (target_width, target_height))
            logger.info(f"计算出的位置: left={left}, top={top}")

            # 应用尺寸和位置
            logger.info(f"准备调用: resizeTo({target_width}, {target_height})")
            window.resizeTo(target_width, target_height)
            logger.info(f"resizeTo 完成")

            logger.info(f"准备调用: moveTo({left}, {top})")
            window.moveTo(left, top)
            logger.info(f"moveTo 完成")

            # 验证结果
            try:
                final_width = window.width
                final_height = window.height
                final_left = window.left if hasattr(window, 'left') else None
                final_top = window.top if hasattr(window, 'top') else None
                logger.info(f"最终窗口尺寸: {final_width}x{final_height}")
                if final_left is not None and final_top is not None:
                    logger.info(f"最终窗口位置: left={final_left}, top={final_top}")
                logger.info(f"=== 预设应用完成 ===")
            except Exception as e:
                logger.warning(f"无法获取最终窗口状态: {e}")

            return True
        except Exception as e:
            logger.exception(f"应用预设失败: {e}")
            return False
