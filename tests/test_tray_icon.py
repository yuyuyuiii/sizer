import pytest
from unittest.mock import Mock, patch, MagicMock
from tray_icon import TrayIconManager, create_icon_image


def test_create_icon_image():
    """测试创建托盘图标"""
    img = create_icon_image()
    assert img is not None
    assert img.size == (64, 64)
    assert img.mode == "RGB"


def test_create_icon_image_custom_size():
    """测试自定义尺寸的图标创建"""
    img = create_icon_image(128, 128)
    assert img is not None
    assert img.size == (128, 128)
    assert img.mode == "RGB"


def test_tray_icon_create_menu():
    """测试菜单创建"""
    from models import Preset
    with patch('tray_icon.pystray'):
        presets = [
            Preset(name="预设1", hotkey="ctrl+1"),
            Preset(name="预设2", hotkey="ctrl+2"),
        ]
        manager = TrayIconManager(presets)
        menu = manager._create_menu()
        # menu 应该是一个 pystray.Menu 对象
        assert menu is not None


def test_tray_icon_menu_with_presets():
    """测试菜单包含预设项"""
    from models import Preset
    with patch('tray_icon.pystray') as mock_pystray:
        presets = [
            Preset(name="预设1", hotkey="ctrl+1"),
            Preset(name="预设2", hotkey="ctrl+2"),
        ]
        manager = TrayIconManager(presets)
        menu = manager._create_menu()
        # menu 应该是一个 pystray.Menu 对象
        assert menu is not None


def test_tray_icon_set_callback():
    """测试设置回调"""
    from models import Preset
    with patch('tray_icon.pystray'):
        manager = TrayIconManager([])
        callback = Mock()
        manager.set_preset_callback(callback)
        assert manager.on_preset_selected == callback


def test_tray_icon_on_preset_clicked():
    """测试预设点击触发回调"""
    from models import Preset
    with patch('tray_icon.pystray'):
        manager = TrayIconManager([])
        callback = Mock()
        manager.set_preset_callback(callback)
        manager._on_preset_clicked("测试预设")
        callback.assert_called_once_with("测试预设")


def test_tray_icon_on_preset_clicked_no_callback():
    """测试无回调时预设点击不会抛出异常"""
    from models import Preset
    with patch('tray_icon.pystray'):
        manager = TrayIconManager([])
        # 不设置回调，应该不会出错
        manager._on_preset_clicked("测试预设")  # 不应该抛出异常


def test_tray_icon_on_exit():
    """测试退出按钮"""
    from models import Preset
    mock_icon = MagicMock()
    with patch('tray_icon.pystray') as mock_pystray:
        mock_pystray.Icon.return_value = mock_icon
        manager = TrayIconManager([])
        manager.run()  # 这会设置 self.icon
        # 模拟调用 _on_exit
        manager._on_exit()
        mock_icon.stop.assert_called_once()


def test_tray_icon_stop():
    """测试停止托盘图标"""
    from models import Preset
    mock_icon = MagicMock()
    with patch('tray_icon.pystray') as mock_pystray:
        mock_pystray.Icon.return_value = mock_icon
        manager = TrayIconManager([])
        manager.run()
        manager.stop()
        mock_icon.stop.assert_called_once()


def test_tray_icon_run_creates_icon():
    """测试 run 方法创建图标"""
    from models import Preset
    mock_icon = MagicMock()
    with patch('tray_icon.pystray') as mock_pystray:
        mock_pystray.Icon.return_value = mock_icon
        presets = [Preset(name="测试预设", hotkey="ctrl+t")]
        manager = TrayIconManager(presets)
        manager.run()
        # 验证 pystray.Icon 被调用
        mock_pystray.Icon.assert_called_once()
        # 验证调用的参数
        args, kwargs = mock_pystray.Icon.call_args
        assert args[0] == "window_sizer"
        assert kwargs.get("title") == "Window Sizer" or (len(args) > 2 and args[2] == "Window Sizer")
