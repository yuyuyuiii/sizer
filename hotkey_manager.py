"""热键管理器模块"""
from typing import Callable, List
import keyboard


class DuplicateHotkeyError(Exception):
    """重复热键异常"""
    pass


class HotkeyManager:
    """热键管理器类"""

    def __init__(self):
        """初始化热键管理器"""
        self.registered_hotkeys = {}
        self._keyboard = keyboard

    def register(self, hotkey: str, callback: Callable, args: tuple = ()) -> bool:
        """
        注册热键

        Args:
            hotkey: 热键字符串，如 "ctrl+shift+c"
            callback: 回调函数
            args: 传递给回调函数的参数元组

        Returns:
            bool: 注册成功返回 True

        Raises:
            DuplicateHotkeyError: 热键已被注册时抛出
        """
        if hotkey in self.registered_hotkeys:
            raise DuplicateHotkeyError(f"热键 '{hotkey}' 已被注册")

        self._keyboard.add_hotkey(hotkey, callback, args=args, suppress=False)
        self.registered_hotkeys[hotkey] = callback
        return True

    def unregister(self, hotkey: str) -> bool:
        """
        注销热键

        Args:
            hotkey: 要注销的热键字符串

        Returns:
            bool: 注销成功返回 True，热键不存在返回 False
        """
        if hotkey not in self.registered_hotkeys:
            return False

        self._keyboard.remove_hotkey(hotkey)
        del self.registered_hotkeys[hotkey]
        return True

    def register_presets(self, presets: List, callback: Callable) -> None:
        """
        批量注册预设热键

        Args:
            presets: Preset 对象列表
            callback: 回调函数，预设名称会作为参数传递
        """
        for preset in presets:
            if preset.hotkey:
                self.register(preset.hotkey, callback, args=(preset.name,))

    def unregister_all(self) -> None:
        """注销所有已注册的热键"""
        for hotkey in list(self.registered_hotkeys.keys()):
            self._keyboard.remove_hotkey(hotkey)
        self.registered_hotkeys.clear()

    def wait(self) -> None:
        """阻塞等待热键事件"""
        self._keyboard.wait()
