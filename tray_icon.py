"""托盘图标管理器"""
from typing import List, Callable
from functools import partial
from PIL import Image, ImageDraw
import pystray
from models import Preset


def create_icon_image(width: int = 64, height: int = 64) -> Image.Image:
    """
    创建简单的蓝色背景、白色矩形图标的 PIL Image

    Args:
        width: 图标宽度
        height: 图标高度

    Returns:
        PIL Image 对象
    """
    # 创建蓝色背景
    img = Image.new("RGB", (width, height), color=(0, 120, 215))
    draw = ImageDraw.Draw(img)

    # 绘制白色矩形（简化为一个居中的矩形）
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
        """
        初始化托盘图标管理器

        Args:
            presets: 预设列表
        """
        self.presets = presets
        self.icon = None
        self.on_preset_selected = None

    def set_preset_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置预设选择回调函数

        Args:
            callback: 回调函数，接收预设名称作为参数
        """
        self.on_preset_selected = callback

    def _create_menu(self) -> pystray.Menu:
        """
        创建托盘菜单

        Returns:
            pystray.Menu 对象
        """
        menu_items = []

        # 为每个预设创建菜单项
        for preset in self.presets:
            # 使用闭包确保每个MenuItem调用时能正确传递预设名称
            def make_handler(name):
                def handler(item):
                    self._on_preset_clicked(name)
                return handler

            menu_items.append(
                pystray.MenuItem(
                    preset.name,
                    make_handler(preset.name)
                )
            )

        # 添加分隔符
        menu_items.append(pystray.Menu.SEPARATOR)

        # 添加退出菜单项
        menu_items.append(
            pystray.MenuItem("退出", self._on_exit)
        )

        return pystray.Menu(*menu_items)

    def _on_preset_clicked(self, preset_name: str) -> None:
        """
        预设菜单项点击回调

        Args:
            preset_name: 预设名称
        """
        print(f"[调试] 托盘菜单点击预设: '{preset_name}'")
        if self.on_preset_selected:
            self.on_preset_selected(preset_name)

    def _on_exit(self) -> None:
        """退出菜单项点击回调"""
        if self.icon:
            self.icon.stop()

    def run(self) -> None:
        """运行托盘图标（阻塞）"""
        self.icon = pystray.Icon(
            "window_sizer",
            create_icon_image(),
            "Window Sizer",
            self._create_menu()
        )
        self.icon.run()

    def stop(self) -> None:
        """停止托盘图标"""
        if self.icon:
            self.icon.stop()
