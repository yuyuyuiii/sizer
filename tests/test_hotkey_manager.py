import pytest
from unittest.mock import Mock, patch
from hotkey_manager import HotkeyManager, DuplicateHotkeyError


def test_hotkey_manager_register():
    """测试注册热键"""
    with patch('hotkey_manager.keyboard') as mock_keyboard:
        manager = HotkeyManager()
        callback = Mock()
        manager.register("ctrl+shift+c", callback)
        mock_keyboard.add_hotkey.assert_called_once()
        registered_callback = mock_keyboard.add_hotkey.call_args[0][1]
        assert callable(registered_callback)
        registered_callback()
        callback.assert_called_once_with()
        assert "ctrl+shift+c" in manager.registered_hotkeys


def test_hotkey_manager_duplicate_error():
    """测试重复热键注册会抛出 DuplicateHotkeyError"""
    with patch('hotkey_manager.keyboard'):
        manager = HotkeyManager()
        callback1 = Mock()
        callback2 = Mock()
        manager.register("ctrl+shift+c", callback1)
        with pytest.raises(DuplicateHotkeyError):
            manager.register("ctrl+shift+c", callback2)


def test_hotkey_manager_unregister():
    """测试注销热键"""
    with patch('hotkey_manager.keyboard') as mock_keyboard:
        manager = HotkeyManager()
        callback = Mock()
        manager.register("ctrl+shift+c", callback)
        result = manager.unregister("ctrl+shift+c")
        assert result == True
        mock_keyboard.remove_hotkey.assert_called_once_with("ctrl+shift+c")
        assert "ctrl+shift+c" not in manager.registered_hotkeys


def test_hotkey_manager_unregister_nonexistent():
    """测试注销未注册的热键返回 False"""
    with patch('hotkey_manager.keyboard'):
        manager = HotkeyManager()
        result = manager.unregister("ctrl+shift+c")
        assert result == False


def test_hotkey_manager_register_presets():
    """测试批量注册预设热键"""
    from models import Preset
    with patch('hotkey_manager.keyboard') as mock_keyboard:
        manager = HotkeyManager()
        presets = [
            Preset(name="居中", hotkey="ctrl+shift+c"),
            Preset(name="靠左", hotkey="ctrl+shift+l"),
            Preset(name="仅位置", hotkey=None),  # 无热键应跳过
        ]
        callback = Mock()
        manager.register_presets(presets, callback)

        # 验证只注册了有热键的预设
        assert mock_keyboard.add_hotkey.call_count == 2
        calls = mock_keyboard.add_hotkey.call_args_list
        # 第一个热键：args=("居中",)
        assert calls[0][1]['args'] == ("居中",)
        # 第二个热键：args=("靠左",)
        assert calls[1][1]['args'] == ("靠左",)


def test_hotkey_manager_unregister_all():
    """测试注销所有热键"""
    with patch('hotkey_manager.keyboard') as mock_keyboard:
        manager = HotkeyManager()
        manager.registered_hotkeys = {"hk1": Mock(), "hk2": Mock(), "hk3": Mock()}
        manager.unregister_all()
        assert mock_keyboard.remove_hotkey.call_count == 3
        assert len(manager.registered_hotkeys) == 0
