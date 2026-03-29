"""托盘图标管理器"""

from __future__ import annotations

from typing import Callable, List, Optional
import importlib
import logging
import os
import threading

from PIL import Image, ImageDraw

from models import Preset

logger = logging.getLogger(__name__)


def _load_pystray():
    """按需加载 pystray，避免在无图形环境导入阶段直接失败。"""
    try:
        return importlib.import_module("pystray")
    except Exception as exc:
        logger.warning("加载 pystray 失败: %s", exc)
        return None


def _hide_taskbar_windows_for_current_process() -> None:
    """在 Windows 上尽量把当前进程的工具窗口从任务栏隐藏。"""
    try:
        import win32con
        import win32gui
        import win32process
    except ImportError:
        return

    current_pid = os.getpid()

    def callback(hwnd, _):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid != current_pid:
                return True

            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(
                hwnd,
                win32con.GWL_EXSTYLE,
                ex_style | win32con.WS_EX_TOOLWINDOW,
            )
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
        except Exception:
            logger.debug("隐藏任务栏窗口失败: hwnd=%s", hwnd, exc_info=True)
        return True

    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        logger.debug("枚举当前进程窗口失败", exc_info=True)


def create_icon_image(width: int = 64, height: int = 64) -> Image.Image:
    """
    创建简单的蓝色背景、白色矩形图标的 PIL Image

    Args:
        width: 图标宽度
        height: 图标高度

    Returns:
        PIL Image 对象
    """
    img = Image.new("RGB", (width, height), color=(0, 120, 215))
    draw = ImageDraw.Draw(img)

    margin = width // 4
    rect_x1 = margin
    rect_y1 = margin
    rect_x2 = width - margin
    rect_y2 = height - margin
    draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], fill=(255, 255, 255))

    return img


class TrayIconManager:
    """托盘图标管理器"""

    def __init__(self, presets: List[Preset]):
        self.presets = presets
        self.icon = None
        self.on_preset_selected: Optional[Callable[[str], None]] = None

    def set_preset_callback(self, callback: Callable[[str], None]) -> None:
        self.on_preset_selected = callback

    def _create_menu(self):
        pystray = _load_pystray()
        if pystray is None:
            raise RuntimeError("pystray 不可用，无法创建托盘菜单")

        menu_items = []

        for preset in self.presets:
            def make_handler(name):
                def handler(icon, item):
                    logger.info("托盘菜单点击预设: %s", name)
                    self._on_preset_clicked(name)
                return handler

            menu_items.append(pystray.MenuItem(preset.name, make_handler(preset.name)))

        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem("退出", self._on_exit))

        return pystray.Menu(*menu_items)

    def _schedule_taskbar_hide(self) -> None:
        timer = threading.Timer(0.5, _hide_taskbar_windows_for_current_process)
        timer.daemon = True
        timer.start()

    def _on_preset_clicked(self, preset_name: str) -> None:
        if self.on_preset_selected:
            try:
                self.on_preset_selected(preset_name)
            except Exception:
                logger.exception("托盘预设回调执行失败: %s", preset_name)
                raise
        else:
            logger.warning("托盘预设点击时未设置回调: %s", preset_name)

    def _on_exit(self) -> None:
        if self.icon:
            self.icon.stop()

    def run(self) -> None:
        pystray = _load_pystray()
        if pystray is None:
            raise RuntimeError("pystray 不可用，无法运行托盘图标")

        logger.info("启动托盘图标，预设数量: %s", len(self.presets))
        self.icon = pystray.Icon(
            "window_sizer",
            create_icon_image(),
            "Window Sizer",
            self._create_menu(),
        )
        self._schedule_taskbar_hide()
        self.icon.run()

    def stop(self) -> None:
        if self.icon:
            self.icon.stop()
