"""窗口控制器模块"""

from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING
import ctypes
import logging
import os

if TYPE_CHECKING:
    from models import Preset


logger = logging.getLogger("WindowController")
DEFAULT_SCREEN_SIZE = (1920, 1080)
WINDOW_TOLERANCE = 5
IGNORED_WINDOW_CLASSES = {
    "Shell_TrayWnd",
    "NotifyIconOverflowWindow",
    "Progman",
    "WorkerW",
}


class PositionCalculator:
    """位置计算器"""

    def __init__(self, screen_width: Optional[int] = None, screen_height: Optional[int] = None):
        if screen_width is None or screen_height is None:
            screen_width, screen_height, logical_width, logical_height = self._detect_screen_size()
        else:
            logical_width, logical_height = screen_width, screen_height

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.logical_screen_width = logical_width
        self.logical_screen_height = logical_height

    def _get_monitor_size(self, monitor_info) -> Tuple[int, int]:
        rect = monitor_info["Monitor"]
        return (rect[2] - rect[0], rect[3] - rect[1])

    def _get_monitor_info(self, monitor_handle, win32api, win32gui):
        get_monitor_info = getattr(win32api, "GetMonitorInfo", None)
        if callable(get_monitor_info):
            return get_monitor_info(monitor_handle)

        get_monitor_info = getattr(win32gui, "GetMonitorInfo", None)
        if callable(get_monitor_info):
            return get_monitor_info(monitor_handle)

        raise AttributeError("win32api/win32gui 都不支持 GetMonitorInfo")

    def _get_desktop_physical_size(self) -> Optional[Tuple[int, int]]:
        """读取 Windows 桌面 DC 的物理像素尺寸，作为单显示器缩放场景兜底。"""
        try:
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
        except Exception:
            return None

        desktop_hwnd = 0
        hdc = None
        try:
            hdc = user32.GetDC(desktop_hwnd)
            if not hdc:
                return None

            desktop_horzres = 118
            desktop_vertres = 117
            width = gdi32.GetDeviceCaps(hdc, desktop_horzres)
            height = gdi32.GetDeviceCaps(hdc, desktop_vertres)
            if width > 0 and height > 0:
                return (width, height)
        except Exception:
            logger.debug("读取桌面物理像素尺寸失败", exc_info=True)
        finally:
            try:
                if hdc:
                    user32.ReleaseDC(desktop_hwnd, hdc)
            except Exception:
                logger.debug("释放桌面 DC 失败", exc_info=True)

        return None

    def _get_physical_monitor_size(self, monitor_info, win32api, win32con) -> Optional[Tuple[int, int]]:
        device_name = monitor_info.get("Device")
        if not device_name:
            return None

        enum_display_settings = getattr(win32api, "EnumDisplaySettings", None)
        if not callable(enum_display_settings):
            return None

        try:
            settings = enum_display_settings(device_name, win32con.ENUM_CURRENT_SETTINGS)
        except Exception:
            logger.debug("读取显示设备物理分辨率失败: device=%s", device_name, exc_info=True)
            return None

        width = getattr(settings, "dmPelsWidth", 0)
        height = getattr(settings, "dmPelsHeight", 0)
        if width > 0 and height > 0:
            return (width, height)
        return None

    def _detect_screen_size(self) -> Tuple[int, int, int, int]:
        """检测屏幕尺寸，返回物理和逻辑分辨率。"""
        try:
            import win32api
            import win32con
            import win32gui
        except ImportError:
            logger.warning("未找到 win32api,使用默认值 1920x1080")
            return DEFAULT_SCREEN_SIZE + DEFAULT_SCREEN_SIZE

        try:
            cursor_x, cursor_y = win32api.GetCursorPos()
            monitors = win32api.EnumDisplayMonitors()
            desktop_physical_size = self._get_desktop_physical_size()
            logger.info("检测到 %s 个显示器", len(monitors))
            for idx, (hmonitor, _, _) in enumerate(monitors, start=1):
                info = self._get_monitor_info(hmonitor, win32api, win32gui)
                logical_width, logical_height = self._get_monitor_size(info)
                physical_size = self._get_physical_monitor_size(info, win32api, win32con)
                if physical_size is not None:
                    width, height = physical_size
                elif len(monitors) == 1 and desktop_physical_size is not None:
                    width, height = desktop_physical_size
                else:
                    width, height = logical_width, logical_height
                rect = info["Monitor"]
                logger.info("显示器%s: %sx%s, rect=%s", idx, width, height, rect)
                if rect[0] <= cursor_x <= rect[2] and rect[1] <= cursor_y <= rect[3]:
                    logger.info("选择鼠标所在显示器: %sx%s", width, height)
                    return (width, height, logical_width, logical_height)
        except Exception:
            logger.debug("基于鼠标位置检测显示器失败", exc_info=True)

        try:
            width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            logger.info("回退到系统指标: %sx%s", width, height)
            if width > 0 and height > 0:
                return (width, height, width, height)
        except Exception:
            logger.debug("使用系统指标获取屏幕尺寸失败", exc_info=True)

        logger.warning("所有检测方法失败,使用默认值 1920x1080")
        return DEFAULT_SCREEN_SIZE + DEFAULT_SCREEN_SIZE

    def calculate(self, position: str, window_size: Tuple[int, int]) -> Tuple[int, int]:
        win_width, win_height = window_size

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
            left = max(0, (self.screen_width - win_width) // 2)
            top = max(0, (self.screen_height - win_height) // 2)

        return (left, top)

    def _scale_x(self) -> float:
        if self.screen_width <= 0 or self.logical_screen_width <= 0:
            return 1.0
        return self.logical_screen_width / self.screen_width

    def _scale_y(self) -> float:
        if self.screen_height <= 0 or self.logical_screen_height <= 0:
            return 1.0
        return self.logical_screen_height / self.screen_height

    def to_logical_width(self, width: int) -> int:
        return int(round(width * self._scale_x()))

    def to_logical_height(self, height: int) -> int:
        return int(round(height * self._scale_y()))

    def to_logical_x(self, left: int) -> int:
        return int(round(left * self._scale_x()))

    def to_logical_y(self, top: int) -> int:
        return int(round(top * self._scale_y()))

    def to_physical_width(self, width: int) -> int:
        scale = self._scale_x()
        if scale == 0:
            return width
        return int(round(width / scale))

    def to_physical_height(self, height: int) -> int:
        scale = self._scale_y()
        if scale == 0:
            return height
        return int(round(height / scale))

    def to_physical_x(self, left: int) -> int:
        scale = self._scale_x()
        if scale == 0:
            return left
        return int(round(left / scale))

    def to_physical_y(self, top: int) -> int:
        scale = self._scale_y()
        if scale == 0:
            return top
        return int(round(top / scale))


class WindowController:
    """窗口控制器"""

    def __init__(self):
        self.calculator = PositionCalculator()
        self.last_active_hwnd: Optional[int] = None

    def _matches_target(self, actual: Optional[int], expected: Optional[int]) -> bool:
        if actual is None or expected is None:
            return True
        return abs(actual - expected) <= WINDOW_TOLERANCE

    def _is_own_window(self, hwnd: int) -> bool:
        try:
            import win32process
        except ImportError:
            return False

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return pid == os.getpid()
        except Exception:
            logger.debug("获取窗口进程信息失败: hwnd=%s", hwnd, exc_info=True)
            return False

    def _is_candidate_window(self, hwnd: int, win32gui, win32con) -> bool:
        try:
            if not hwnd or self._is_own_window(hwnd):
                return False
            if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
                return False
            if win32gui.IsIconic(hwnd):
                return False

            class_name = win32gui.GetClassName(hwnd)
            if class_name in IGNORED_WINDOW_CLASSES:
                return False

            title = win32gui.GetWindowText(hwnd)
            if not title.strip():
                return False

            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if ex_style & getattr(win32con, "WS_EX_TOOLWINDOW", 0):
                return False
            return True
        except Exception:
            logger.debug("判断候选窗口失败: hwnd=%s", hwnd, exc_info=True)
            return False

    def _find_fallback_window_handle(self, win32gui, win32con) -> Optional[int]:
        candidates = []

        def callback(hwnd, _):
            if self._is_candidate_window(hwnd, win32gui, win32con):
                candidates.append(hwnd)
                return False
            return True

        try:
            win32gui.EnumWindows(callback, None)
        except Exception:
            logger.debug("枚举窗口失败", exc_info=True)

        return candidates[0] if candidates else None

    def get_active_window_handle(self) -> Optional[int]:
        try:
            import win32con
            import win32gui
        except ImportError:
            return None

        hwnd = None
        try:
            foreground = win32gui.GetForegroundWindow()
            if self._is_candidate_window(foreground, win32gui, win32con):
                hwnd = foreground
        except Exception:
            logger.debug("获取前台窗口失败", exc_info=True)

        if hwnd is None:
            fallback = self._find_fallback_window_handle(win32gui, win32con)
            if fallback is not None:
                logger.info("前台窗口不可用，回退到枚举窗口: hwnd=%s", fallback)
                hwnd = fallback

        if hwnd is None and self.last_active_hwnd is not None:
            try:
                if win32gui.IsWindow(self.last_active_hwnd):
                    logger.info("前台窗口不可用，回退到最近窗口: hwnd=%s", self.last_active_hwnd)
                    hwnd = self.last_active_hwnd
            except Exception:
                logger.debug("检查最近窗口失败", exc_info=True)

        if hwnd is not None:
            self.last_active_hwnd = hwnd
        return hwnd

    def get_active_window(self):
        """兼容旧接口，返回当前活动窗口句柄。"""
        return self.get_active_window_handle()

    def _restore_window(self, hwnd: int) -> None:
        import win32con
        import win32gui

        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    def _read_window_rect(self, hwnd: int) -> Tuple[int, int, int, int]:
        import win32gui

        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return (left, top, right - left, bottom - top)

    def apply_preset(self, preset: "Preset") -> bool:
        root_logger = logging.getLogger()

        try:
            hwnd = self.get_active_window_handle()
            if hwnd is None:
                root_logger.warning("WindowController: 未找到活动窗口")
                return False

            current_left, current_top, current_width, current_height = self._read_window_rect(hwnd)
            current_width_physical = self.calculator.to_physical_width(current_width)
            current_height_physical = self.calculator.to_physical_height(current_height)

            root_logger.info("=== 应用预设: %s ===", preset.name)
            root_logger.info(
                "预设参数: width=%s, height=%s, position=%s",
                preset.width,
                preset.height,
                preset.position,
            )
            root_logger.info(
                "屏幕分辨率: %sx%s (logical=%sx%s)",
                self.calculator.screen_width,
                self.calculator.screen_height,
                self.calculator.logical_screen_width,
                self.calculator.logical_screen_height,
            )
            root_logger.info(
                "窗口当前尺寸: %sx%s",
                current_width_physical,
                current_height_physical,
            )

            try:
                self._restore_window(hwnd)
            except Exception:
                root_logger.warning("restore() 失败", exc_info=True)

            if preset.width is not None and preset.height is not None:
                target_width_physical = preset.width
                target_height_physical = preset.height
            else:
                target_width_physical = current_width_physical
                target_height_physical = current_height_physical

            target_left_physical, target_top_physical = self.calculator.calculate(
                preset.position,
                (target_width_physical, target_height_physical),
            )

            target_width = self.calculator.to_logical_width(target_width_physical)
            target_height = self.calculator.to_logical_height(target_height_physical)
            target_left = self.calculator.to_logical_x(target_left_physical)
            target_top = self.calculator.to_logical_y(target_top_physical)

            root_logger.info(
                "目标窗口矩形: physical=(%s,%s,%s,%s), logical=(%s,%s,%s,%s)",
                target_left_physical,
                target_top_physical,
                target_width_physical,
                target_height_physical,
                target_left,
                target_top,
                target_width,
                target_height,
            )

            import win32con
            import win32gui

            flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            win32gui.SetWindowPos(hwnd, None, target_left, target_top, target_width, target_height, flags)

            final_left, final_top, final_width, final_height = self._read_window_rect(hwnd)
            final_left_physical = self.calculator.to_physical_x(final_left)
            final_top_physical = self.calculator.to_physical_y(final_top)
            final_width_physical = self.calculator.to_physical_width(final_width)
            final_height_physical = self.calculator.to_physical_height(final_height)

            root_logger.info(
                "最终窗口矩形: physical=(%s,%s,%s,%s), logical=(%s,%s,%s,%s)",
                final_left_physical,
                final_top_physical,
                final_width_physical,
                final_height_physical,
                final_left,
                final_top,
                final_width,
                final_height,
            )

            size_ok = self._matches_target(final_width_physical, target_width_physical) and self._matches_target(
                final_height_physical, target_height_physical
            )
            position_ok = self._matches_target(final_left_physical, target_left_physical) and self._matches_target(
                final_top_physical, target_top_physical
            )

            if not size_ok:
                root_logger.warning(
                    "窗口尺寸调整不匹配: 目标=%sx%s, 实际=%sx%s",
                    target_width_physical,
                    target_height_physical,
                    final_width_physical,
                    final_height_physical,
                )
            if not position_ok:
                root_logger.warning(
                    "窗口位置调整不匹配: 目标=(%s, %s), 实际=(%s, %s)",
                    target_left_physical,
                    target_top_physical,
                    final_left_physical,
                    final_top_physical,
                )

            root_logger.info("=== 预设应用完成 ===")
            return size_ok and position_ok
        except Exception:
            root_logger.exception("应用预设失败")
            return False
