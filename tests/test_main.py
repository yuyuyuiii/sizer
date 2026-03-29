"""main.py 集成测试"""

import importlib
import sys
from unittest.mock import Mock, patch


def import_main():
    sys.modules.pop("main", None)
    sys.modules.pop("tray_icon", None)
    return importlib.import_module("main")


def test_app_initialize_with_config():
    """测试应用初始化"""
    main = import_main()

    with patch.object(main.WindowManagerApp, "_setup_logging") as mock_logging, \
         patch.object(main, "load_config") as mock_load, \
         patch.object(main, "HotkeyManager") as mock_hotkey_cls, \
         patch.object(main, "TrayIconManager") as mock_tray_cls, \
         patch.object(main, "Notifier") as mock_notifier_cls, \
         patch.object(main, "WindowController") as mock_wc_cls:
        mock_load.return_value = []
        mock_hotkey_instance = Mock()
        mock_hotkey_cls.return_value = mock_hotkey_instance
        mock_tray_instance = Mock()
        mock_tray_cls.return_value = mock_tray_instance
        mock_notifier_cls.return_value = Mock()
        mock_wc_cls.return_value = Mock()

        app = main.WindowManagerApp()
        result = app.initialize()

        assert result is True
        mock_logging.assert_called_once()
        mock_load.assert_called_once()
        mock_hotkey_instance.register_presets.assert_called_once()
        mock_tray_cls.assert_called_once()
        mock_tray_instance.set_preset_callback.assert_called_once()


def test_app_init_sets_up_logging_before_window_controller():
    """测试日志初始化先于 WindowController 创建"""
    main = import_main()
    order = []

    with patch.object(main.WindowManagerApp, "_setup_logging", autospec=True) as mock_logging, \
         patch.object(main, "WindowController") as mock_wc_cls, \
         patch.object(main, "HotkeyManager") as mock_hotkey_cls, \
         patch.object(main, "Notifier") as mock_notifier_cls:
        mock_logging.side_effect = lambda self: order.append("logging")
        mock_wc_cls.side_effect = lambda: order.append("window_controller") or Mock()
        mock_hotkey_cls.return_value = Mock()
        mock_notifier_cls.return_value = Mock()

        main.WindowManagerApp()

    assert order[:2] == ["logging", "window_controller"]


def test_app_initialize_duplicate_hotkey_error():
    """测试热键重复错误处理"""
    main = import_main()
    duplicate_error = main.DuplicateHotkeyError("热键已存在")

    with patch.object(main.WindowManagerApp, "_setup_logging"), \
         patch.object(main, "load_config") as mock_load, \
         patch.object(main, "HotkeyManager") as mock_hotkey_cls, \
         patch.object(main, "Notifier") as mock_notifier_cls, \
         patch.object(main, "WindowController") as mock_wc_cls:
        mock_load.return_value = []
        mock_hotkey_instance = Mock()
        mock_hotkey_instance.register_presets.side_effect = duplicate_error
        mock_hotkey_cls.return_value = mock_hotkey_instance
        mock_notifier_instance = Mock()
        mock_notifier_cls.return_value = mock_notifier_instance
        mock_wc_cls.return_value = Mock()

        app = main.WindowManagerApp()
        result = app.initialize()

        assert result is False
        mock_notifier_instance.show.assert_called_once()
        args, kwargs = mock_notifier_instance.show.call_args
        assert args[0] == "热键错误"
        assert "热键已存在" in args[1]
        assert kwargs.get("error") is True


def test_app_apply_preset_by_name_not_found():
    """测试应用不存在的预设"""
    main = import_main()

    with patch.object(main.WindowManagerApp, "_setup_logging"), \
         patch.object(main, "WindowController") as mock_wc_cls, \
         patch.object(main, "load_config") as mock_load, \
         patch.object(main, "Notifier") as mock_notifier_cls:
        mock_load.return_value = []
        mock_wc_cls.return_value = Mock()
        mock_notifier_instance = Mock()
        mock_notifier_cls.return_value = mock_notifier_instance

        app = main.WindowManagerApp()
        app.initialize()
        app._apply_preset_by_name("不存在的预设")

        mock_notifier_instance.show.assert_called_once()
        call_args = mock_notifier_instance.show.call_args[0]
        assert "不存在" in call_args[1]


def test_app_apply_preset_success():
    """测试成功应用预设"""
    main = import_main()
    test_preset = main.Preset(name="测试预设", width=800, height=600)

    with patch.object(main.WindowManagerApp, "_setup_logging"), \
         patch.object(main, "WindowController") as mock_wc_cls, \
         patch.object(main, "load_config") as mock_load, \
         patch.object(main, "Notifier") as mock_notifier_cls:
        mock_load.return_value = [test_preset]
        mock_wc_instance = Mock()
        mock_wc_instance.apply_preset.return_value = True
        mock_wc_cls.return_value = mock_wc_instance
        mock_notifier_instance = Mock()
        mock_notifier_cls.return_value = mock_notifier_instance

        app = main.WindowManagerApp()
        app.initialize()
        app._apply_preset_by_name("测试预设")

        mock_wc_instance.apply_preset.assert_called_once_with(test_preset)
        mock_notifier_instance.preset_applied.assert_not_called()


def test_app_apply_preset_failure():
    """测试应用预设失败"""
    main = import_main()
    test_preset = main.Preset(name="测试预设", width=800, height=600)

    with patch.object(main.WindowManagerApp, "_setup_logging"), \
         patch.object(main, "WindowController") as mock_wc_cls, \
         patch.object(main, "load_config") as mock_load, \
         patch.object(main, "Notifier") as mock_notifier_cls:
        mock_load.return_value = [test_preset]
        mock_wc_instance = Mock()
        mock_wc_instance.apply_preset.return_value = False
        mock_wc_cls.return_value = mock_wc_instance
        mock_notifier_instance = Mock()
        mock_notifier_cls.return_value = mock_notifier_instance

        app = main.WindowManagerApp()
        app.initialize()
        app._apply_preset_by_name("测试预设")

        mock_wc_instance.apply_preset.assert_called_once_with(test_preset)
        mock_notifier_instance.error_operation_failed.assert_called_once()


def test_app_signal_handler():
    """测试信号处理"""
    main = import_main()

    with patch.object(main.WindowManagerApp, "_setup_logging"), \
         patch.object(main, "WindowController"), \
         patch.object(main, "load_config"), \
         patch.object(main, "TrayIconManager") as mock_tray_cls, \
         patch.object(main, "Notifier"):
        mock_tray_instance = Mock()
        mock_tray_cls.return_value = mock_tray_instance

        app = main.WindowManagerApp()
        app.initialize()
        app._signal_handler(None, None)

        mock_tray_instance.stop.assert_called_once()


def test_app_run_success():
    """测试应用成功运行"""
    main = import_main()

    with patch.object(main.WindowManagerApp, "_setup_logging"), \
         patch.object(main, "WindowController"), \
         patch.object(main, "load_config", return_value=[]), \
         patch.object(main, "HotkeyManager") as mock_hotkey_cls, \
         patch.object(main, "TrayIconManager") as mock_tray_cls, \
         patch.object(main, "Notifier") as mock_notifier_cls, \
         patch.object(main, "signal") as mock_signal:
        mock_hotkey_instance = Mock()
        mock_hotkey_cls.return_value = mock_hotkey_instance
        mock_tray_instance = Mock()
        mock_tray_cls.return_value = mock_tray_instance
        mock_notifier_cls.return_value = Mock()

        app = main.WindowManagerApp()
        app.run()

        assert app.running is False
        mock_hotkey_instance.unregister_all.assert_called_once()
        mock_signal.signal.assert_called_once()


def test_app_run_initialize_failure():
    """测试初始化失败时的运行"""
    main = import_main()

    with patch.object(main.WindowManagerApp, "_setup_logging"), \
         patch.object(main, "WindowController"), \
         patch.object(main, "HotkeyManager"), \
         patch.object(main, "Notifier"), \
         patch("builtins.input") as mock_input, \
         patch.object(main.WindowManagerApp, "initialize", return_value=False):
        app = main.WindowManagerApp()
        app.run()
        mock_input.assert_called_once()


def test_main_function_non_windows():
    """测试非 Windows 平台的平台检查"""
    main = import_main()

    with patch.object(main, "sys") as mock_sys, \
         patch.object(main, "WindowManagerApp") as mock_app_cls:
        mock_sys.platform = "linux"
        mock_app_instance = Mock()
        mock_app_cls.return_value = mock_app_instance
        main.main()
        mock_app_instance.run.assert_called_once()
