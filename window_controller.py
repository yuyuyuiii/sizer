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


class PositionCalculator:
    """位置计算器"""

    def __init__(self, screen_width: Optional[int] = None, screen_height: Optional[int] = None):
        if screen_width is None or screen_height is None:
            screen_width, screen_height = self._detect_screen_size()

        self.screen_width = screen_width
        self.screen_height = screen_height

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

    def _detect_screen_size(self) -> Tuple[int, int]:
        """检测屏幕尺寸，优先选择光标或活动窗口所在显示器。"""
        try:
            import win32api
            import win32con
            import win32gui
        except ImportError:
            logger.warning("未找到 win32api,使用默认值 1920x1080")
            return DEFAULT_SCREEN_SIZE

        try:
            cursor_x, cursor_y = win32api.GetCursorPos()
            monitors = win32api.EnumDisplayMonitors()
            desktop_physical_size = self._get_desktop_physical_size()
            logger.info("检测到 %s 个显示器", len(monitors))
            for idx, (hmonitor, _, _) in enumerate(monitors, start=1):
                info = self._get_monitor_info(hmonitor, win32api, win32gui)
                width, height = self._get_monitor_size(info)
                physical_size = self._get_physical_monitor_size(info, win32api, win32con)
                if physical_size is not None:
                    width, height = physical_size
                elif len(monitors) == 1 and desktop_physical_size is not None:
                    width, height = desktop_physical_size
                rect = info["Monitor"]
                logger.info("显示器%s: %sx%s, rect=%s", idx, width, height, rect)
                if rect[0] <= cursor_x <= rect[2] and rect[1] <= cursor_y <= rect[3]:
                    logger.info("选择鼠标所在显示器: %sx%s", width, height)
                    return (width, height)
        except Exception:
            logger.debug("基于鼠标位置检测显示器失败", exc_info=True)

        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
                info = self._get_monitor_info(monitor, win32api, win32gui)
                width, height = self._get_monitor_size(info)
                physical_size = self._get_physical_monitor_size(info, win32api, win32con)
                if physical_size is not None:
                    width, height = physical_size
                logger.info("选择活动窗口所在显示器: %sx%s", width, height)
                return (width, height)
        except Exception:
            logger.debug("基于活动窗口检测显示器失败", exc_info=True)

        try:
            monitors = win32api.EnumDisplayMonitors()
            largest = None
            max_area = -1
            for hmonitor, _, _ in monitors:
                info = self._get_monitor_info(hmonitor, win32api, win32gui)
                width, height = self._get_monitor_size(info)
                physical_size = self._get_physical_monitor_size(info, win32api, win32con)
                if physical_size is not None:
                    width, height = physical_size
                area = width * height
                if area > max_area:
                    max_area = area
                    largest = (width, height)
            if largest:
                logger.info("选择最大显示器: %sx%s", largest[0], largest[1])
                return largest
        except Exception:
            logger.debug("基于最大显示器回退失败", exc_info=True)

        try:
            width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            logger.info("回退到系统指标: %sx%s", width, height)
            if width > 0 and height > 0:
                return (width, height)
        except Exception:
            logger.debug("使用系统指标获取屏幕尺寸失败", exc_info=True)

        logger.warning("所有检测方法失败,使用默认值 1920x1080")
        return DEFAULT_SCREEN_SIZE

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


class WindowController:
    """窗口控制器"""

    def __init__(self):
        self.calculator = PositionCalculator()

    def _is_own_window(self, window) -> bool:
        hwnd = getattr(window, "_hWnd", None)
        if hwnd is None:
            return False

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

    def get_active_window(self):
        """获取当前活动窗口，并排除工具自身窗口。"""
        try:
            import pygetwindow as gw
        except Exception:
            return None

        try:
            active_window = gw.getActiveWindow()
            if active_window is not None and not self._is_own_window(active_window):
                return active_window

            for window in gw.getAllWindows():
                if getattr(window, "isActive", False) and not self._is_own_window(window):
                    return window
        except Exception:
            logger.debug("获取活动窗口失败", exc_info=True)

        return None

    def _matches_target(self, actual: Optional[int], expected: Optional[int]) -> bool:
        if actual is None or expected is None:
            return True
        if not isinstance(actual, (int, float)) or not isinstance(expected, (int, float)):
            return True
        return abs(actual - expected) <= WINDOW_TOLERANCE

    def _restore_window(self, window) -> None:
        hwnd = getattr(window, "_hWnd", None)
        if hwnd is not None:
            try:
                import win32con
                import win32gui

                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                return
            except Exception:
                logger.debug("使用 Win32 API 恢复窗口失败: hwnd=%s", hwnd, exc_info=True)

        window.restore()

    def _apply_window_bounds(self, window, left: int, top: int, width: int, height: int) -> None:
        hwnd = getattr(window, "_hWnd", None)
        if hwnd is not None:
            try:
                import win32con
                import win32gui

                flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
                win32gui.SetWindowPos(hwnd, None, left, top, width, height, flags)
                return
            except Exception:
                logger.debug("使用 Win32 API 调整窗口失败: hwnd=%s", hwnd, exc_info=True)

        window.resizeTo(width, height)
        window.moveTo(left, top)

    def _read_window_state(self, window) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
        hwnd = getattr(window, "_hWnd", None)
        if hwnd is not None:
            try:
                import win32gui

                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                return (right - left, bottom - top, left, top)
            except Exception:
                logger.debug("使用 Win32 API 读取窗口矩形失败: hwnd=%s", hwnd, exc_info=True)

        return (
            getattr(window, "width", None),
            getattr(window, "height", None),
            getattr(window, "left", None),
            getattr(window, "top", None),
        )

    def apply_preset(self, preset: "Preset") -> bool:
        """应用预设到当前活动窗口。"""
        root_logger = logging.getLogger()

        try:
            window = self.get_active_window()
            if window is None:
                root_logger.warning("WindowController: 未找到活动窗口")
                return False

            root_logger.info("=== 应用预设: %s ===", preset.name)
            root_logger.info(
                "预设参数: width=%s, height=%s, position=%s",
                preset.width,
                preset.height,
                preset.position,
            )
            root_logger.info(
                "屏幕分辨率: %sx%s",
                self.calculator.screen_width,
                self.calculator.screen_height,
            )

            try:
                root_logger.info("窗口当前尺寸: %sx%s", window.width, window.height)
            except Exception:
                root_logger.warning("无法获取窗口当前尺寸", exc_info=True)

            try:
                self._restore_window(window)
            except Exception:
                root_logger.warning("restore() 失败", exc_info=True)

            if preset.width is not None and preset.height is not None:
                target_width = preset.width
                target_height = preset.height
            else:
                target_width = window.width
                target_height = window.height

            left, top = self.calculator.calculate(preset.position, (target_width, target_height))

            self._apply_window_bounds(window, left, top, target_width, target_height)
            final_width, final_height, final_left, final_top = self._read_window_state(window)

            size_ok = self._matches_target(final_width, target_width) and self._matches_target(
                final_height, target_height
            )
            position_ok = self._matches_target(final_left, left) and self._matches_target(final_top, top)

            if not size_ok:
                root_logger.warning(
                    "窗口尺寸调整不匹配: 目标=%sx%s, 实际=%sx%s",
                    target_width,
                    target_height,
                    final_width,
                    final_height,
                )
            if not position_ok:
                root_logger.warning(
                    "窗口位置调整不匹配: 目标=(%s, %s), 实际=(%s, %s)",
                    left,
                    top,
                    final_left,
                    final_top,
                )

            root_logger.info("=== 预设应用完成 ===")
            return size_ok and position_ok
        except Exception:
            root_logger.exception("应用预设失败")
            return False
