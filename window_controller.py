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
            # 尝试使用多种方法获取真实屏幕分辨率
            screen_width, screen_height = self._detect_screen_size()

        self.screen_width = screen_width
        self.screen_height = screen_height

    def _detect_screen_size(self) -> Tuple[int, int]:
        """检测屏幕尺寸,尝试多种方法"""
        import logging
        logger = logging.getLogger("WindowController")

        try:
            import win32api
            import win32con

            # 方法 1: 使用 GetSystemMetrics 和 SM_CXSCREEN/SM_CYSCREEN
            try:
                width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                logger.info(f"方法1 GetSystemMetrics(SM_CXSCREEN/SM_CYSCREEN): {width}x{height}")
                if width > 0 and height > 0:
                    return (width, height)
            except Exception as e:
                logger.debug(f"方法1失败: {e}")

            # 方法 2: 使用枚举显示器 - 寻找最大的显示器
            try:
                import win32gui
                monitors = win32api.EnumDisplayMonitors()
                logger.info(f"检测到 {len(monitors)} 个显示器")
                if monitors:
                    max_area = 0
                    best_monitor = None
                    for idx, (hmonitor, _, _) in enumerate(monitors):
                        info = win32gui.GetMonitorInfo(hmonitor)
                        rc = info['Monitor']
                        w = rc[2] - rc[0]
                        h = rc[3] - rc[1]
                        area = w * h
                        logger.info(f"  显示器{idx+1}: {w}x{h} (面积={area})")
                        if area > max_area:
                            max_area = area
                            best_monitor = (w, h)
                    if best_monitor:
                        logger.info(f"选择最大显示器: {best_monitor[0]}x{best_monitor[1]}")
                        return best_monitor
            except Exception as e:
                logger.debug(f"方法2失败: {e}")

            # 方法 3: 使用 SM_CXFULLSCREEN/SM_CYFULLSCREEN (工作区)
            try:
                width = win32api.GetSystemMetrics(win32con.SM_CXFULLSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYFULLSCREEN)
                logger.info(f"方法3 GetSystemMetrics(SM_CXFULLSCREEN/SM_CYFULLSCREEN): {width}x{height}")
                if width > 0 and height > 0:
                    return (width, height)
            except Exception as e:
                logger.debug(f"方法3失败: {e}")

            # 方法 4: 使用硬编码的默认值
            logger.warning("所有检测方法失败,使用默认值 1920x1080")
            return (1920, 1080)

        except ImportError:
            # 无法导入 win32api 时使用默认值
            logger.warning("未找到 win32api,使用默认值 1920x1080")
            return (1920, 1080)

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
