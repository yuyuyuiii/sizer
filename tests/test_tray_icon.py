import importlib
import sys
from unittest.mock import MagicMock, Mock, patch


def import_tray_icon():
    sys.modules.pop("tray_icon", None)
    return importlib.import_module("tray_icon")


def test_create_icon_image():
    """测试创建托盘图标"""
    tray_icon = import_tray_icon()
    img = tray_icon.create_icon_image()
    assert img is not None
    assert img.size == (64, 64)
    assert img.mode == "RGB"


def test_create_icon_image_custom_size():
    """测试自定义尺寸的图标创建"""
    tray_icon = import_tray_icon()
    img = tray_icon.create_icon_image(128, 128)
    assert img is not None
    assert img.size == (128, 128)
    assert img.mode == "RGB"


def test_tray_icon_create_menu():
    """测试菜单创建"""
    from models import Preset

    tray_icon = import_tray_icon()
    fake_pystray = Mock()
    fake_pystray.Menu.return_value = object()
    fake_pystray.MenuItem.side_effect = lambda *args, **kwargs: ("item", args, kwargs)
    fake_pystray.Menu.SEPARATOR = object()

    with patch.object(tray_icon, "_load_pystray", return_value=fake_pystray):
        presets = [
            Preset(name="预设1", hotkey="ctrl+1"),
            Preset(name="预设2", hotkey="ctrl+2"),
        ]
        manager = tray_icon.TrayIconManager(presets)
        menu = manager._create_menu()
        assert menu is not None
        assert fake_pystray.MenuItem.call_count == 3


def test_tray_icon_menu_handler_accepts_icon_and_item_arguments():
    """测试托盘菜单 handler 兼容 pystray 的 (icon, item) 调用签名"""
    from models import Preset

    tray_icon = import_tray_icon()
    fake_pystray = Mock()
    fake_pystray.Menu.return_value = object()
    fake_pystray.MenuItem.side_effect = lambda *args, **kwargs: ("item", args, kwargs)
    fake_pystray.Menu.SEPARATOR = object()

    with patch.object(tray_icon, "_load_pystray", return_value=fake_pystray):
        manager = tray_icon.TrayIconManager([Preset(name="预设1", hotkey="ctrl+1")])
        callback = Mock()
        manager.set_preset_callback(callback)
        manager._create_menu()

        handler = fake_pystray.MenuItem.call_args_list[0][0][1]
        handler(Mock(), Mock())

        callback.assert_called_once_with("预设1")


def test_tray_icon_set_callback():
    """测试设置回调"""
    tray_icon = import_tray_icon()
    manager = tray_icon.TrayIconManager([])
    callback = Mock()
    manager.set_preset_callback(callback)
    assert manager.on_preset_selected == callback


def test_tray_icon_on_preset_clicked():
    """测试预设点击触发回调"""
    tray_icon = import_tray_icon()
    manager = tray_icon.TrayIconManager([])
    callback = Mock()
    manager.set_preset_callback(callback)
    manager._on_preset_clicked("测试预设")
    callback.assert_called_once_with("测试预设")


def test_tray_icon_on_preset_clicked_no_callback():
    """测试无回调时预设点击不会抛出异常"""
    tray_icon = import_tray_icon()
    manager = tray_icon.TrayIconManager([])
    manager._on_preset_clicked("测试预设")


def test_tray_icon_on_exit():
    """测试退出按钮"""
    tray_icon = import_tray_icon()
    mock_icon = MagicMock()
    manager = tray_icon.TrayIconManager([])
    manager.icon = mock_icon
    manager._on_exit()
    mock_icon.stop.assert_called_once()


def test_tray_icon_stop():
    """测试停止托盘图标"""
    tray_icon = import_tray_icon()
    mock_icon = MagicMock()
    manager = tray_icon.TrayIconManager([])
    manager.icon = mock_icon
    manager.stop()
    mock_icon.stop.assert_called_once()


def test_tray_icon_run_creates_icon_and_hides_taskbar_window():
    """测试 run 方法创建图标并调用任务栏隐藏逻辑"""
    from models import Preset

    tray_icon = import_tray_icon()
    mock_icon = MagicMock()
    fake_pystray = Mock()
    fake_pystray.Icon.return_value = mock_icon
    fake_pystray.Menu.return_value = object()
    fake_pystray.MenuItem.side_effect = lambda *args, **kwargs: ("item", args, kwargs)
    fake_pystray.Menu.SEPARATOR = object()

    with patch.object(tray_icon, "_load_pystray", return_value=fake_pystray), \
         patch.object(tray_icon.TrayIconManager, "_schedule_taskbar_hide") as mock_hide:
        presets = [Preset(name="测试预设", hotkey="ctrl+t")]
        manager = tray_icon.TrayIconManager(presets)
        manager.run()
        fake_pystray.Icon.assert_called_once()
        mock_hide.assert_called_once()


def test_load_pystray_returns_none_when_backend_unavailable():
    """测试 pystray 后端不可用时返回 None 而不是在导入阶段崩溃"""
    tray_icon = import_tray_icon()

    with patch("importlib.import_module", side_effect=RuntimeError("backend unavailable")):
        assert tray_icon._load_pystray() is None


def test_hide_taskbar_window_updates_windows_style():
    """测试隐藏任务栏窗口时会更新扩展样式"""
    tray_icon = import_tray_icon()

    fake_win32gui = Mock()
    fake_win32con = Mock(
        GWL_EXSTYLE=-20,
        WS_EX_TOOLWINDOW=0x00000080,
        SW_HIDE=0,
    )
    fake_win32process = Mock()
    fake_win32process.GetWindowThreadProcessId.return_value = (1, 1234)
    fake_win32gui.GetWindowLong.return_value = 0x00040000
    fake_win32gui.EnumWindows.side_effect = lambda callback, arg: callback(99, arg)

    with patch.object(tray_icon.os, "getpid", return_value=1234), \
         patch.dict(
             sys.modules,
             {
                 "win32gui": fake_win32gui,
                 "win32con": fake_win32con,
                 "win32process": fake_win32process,
             },
         ):
        tray_icon._hide_taskbar_windows_for_current_process()

    fake_win32gui.EnumWindows.assert_called_once()
    fake_win32gui.SetWindowLong.assert_called()
    fake_win32gui.ShowWindow.assert_called()
