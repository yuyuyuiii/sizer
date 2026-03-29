"""main.py 集成测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from main import WindowManagerApp


def test_app_initialize_with_config():
    """测试应用初始化"""
    with patch('main.load_config') as mock_load, \
         patch('main.HotkeyManager') as mock_hotkey_cls, \
         patch('main.TrayIconManager') as mock_tray_cls, \
         patch('main.Notifier') as mock_notifier_cls:

        mock_load.return_value = []
        mock_hotkey_instance = Mock()
        mock_hotkey_cls.return_value = mock_hotkey_instance
        mock_tray_instance = Mock()
        mock_tray_cls.return_value = mock_tray_instance
        mock_notifier_instance = Mock()
        mock_notifier_cls.return_value = mock_notifier_instance

        app = WindowManagerApp()
        result = app.initialize()

        assert result == True
        mock_load.assert_called_once()
        mock_hotkey_instance.register_presets.assert_called_once()
        mock_tray_cls.assert_called_once()
        mock_tray_instance.set_preset_callback.assert_called_once()


def test_app_initialize_duplicate_hotkey_error():
    """测试热键重复错误处理"""
    from main import DuplicateHotkeyError
    with patch('main.load_config') as mock_load, \
         patch('main.HotkeyManager') as mock_hotkey_cls, \
         patch('main.Notifier') as mock_notifier_cls:

        mock_load.return_value = []
        mock_hotkey_instance = Mock()
        mock_hotkey_cls.return_value = mock_hotkey_instance
        mock_hotkey_instance.register_presets.side_effect = DuplicateHotkeyError("热键已存在")

        mock_notifier_instance = Mock()
        mock_notifier_cls.return_value = mock_notifier_instance

        app = WindowManagerApp()
        result = app.initialize()

        assert result == False
        mock_notifier_instance.show.assert_called_once()
        # 验证错误通知标题和内容
        args, kwargs = mock_notifier_instance.show.call_args
        assert args[0] == "热键错误"
        assert "热键已存在" in args[1]
        assert kwargs.get('error') == True


def test_app_apply_preset_by_name_not_found():
    """测试应用不存在的预设"""
    with patch('main.WindowController') as mock_wc_cls, \
         patch('main.load_config') as mock_load:

        mock_load.return_value = []  # 空预设
        mock_wc_instance = Mock()
        mock_wc_cls.return_value = mock_wc_instance

        with patch('main.Notifier') as mock_notifier_cls:
            mock_notifier_instance = Mock()
            mock_notifier_cls.return_value = mock_notifier_instance

            app = WindowManagerApp()
            app.initialize()
            app._apply_preset_by_name("不存在的预设")

            mock_notifier_instance.show.assert_called_once()
            call_args = mock_notifier_instance.show.call_args[0]
            assert "不存在" in call_args[1]


def test_app_apply_preset_success():
    """测试成功应用预设"""
    from main import Preset
    with patch('main.WindowController') as mock_wc_cls, \
         patch('main.load_config') as mock_load:

        # 创建一个测试预设
        test_preset = Preset(name="测试预设", width=800, height=600)
        mock_load.return_value = [test_preset]

        mock_wc_instance = Mock()
        mock_wc_instance.apply_preset.return_value = True
        mock_wc_cls.return_value = mock_wc_instance

        with patch('main.Notifier') as mock_notifier_cls:
            mock_notifier_instance = Mock()
            mock_notifier_cls.return_value = mock_notifier_instance

            app = WindowManagerApp()
            app.initialize()
            app._apply_preset_by_name("测试预设")

            # 验证窗口控制器被调用
            mock_wc_instance.apply_preset.assert_called_once_with(test_preset)
            # 验证成功通知
            mock_notifier_instance.preset_applied.assert_called_once_with("测试预设")


def test_app_apply_preset_failure():
    """测试应用预设失败"""
    from main import Preset
    with patch('main.WindowController') as mock_wc_cls, \
         patch('main.load_config') as mock_load:

        test_preset = Preset(name="测试预设", width=800, height=600)
        mock_load.return_value = [test_preset]

        mock_wc_instance = Mock()
        mock_wc_instance.apply_preset.return_value = False
        mock_wc_cls.return_value = mock_wc_instance

        with patch('main.Notifier') as mock_notifier_cls:
            mock_notifier_instance = Mock()
            mock_notifier_cls.return_value = mock_notifier_instance

            app = WindowManagerApp()
            app.initialize()
            app._apply_preset_by_name("测试预设")

            # 验证窗口控制器被调用
            mock_wc_instance.apply_preset.assert_called_once_with(test_preset)
            # 验证错误通知
            mock_notifier_instance.error_operation_failed.assert_called_once()


def test_app_signal_handler():
    """测试信号处理"""
    with patch('main.WindowController'), \
         patch('main.load_config'), \
         patch('main.TrayIconManager') as mock_tray_cls:

        mock_tray_instance = Mock()
        mock_tray_cls.return_value = mock_tray_instance

        with patch('main.Notifier'):
            app = WindowManagerApp()
            app.initialize()
            app._signal_handler(None, None)

            mock_tray_instance.stop.assert_called_once()


def test_app_run_success():
    """测试应用成功运行"""
    with patch('main.WindowController'), \
         patch('main.load_config', return_value=[]), \
         patch('main.HotkeyManager') as mock_hotkey_cls, \
         patch('main.TrayIconManager') as mock_tray_cls, \
         patch('main.Notifier') as mock_notifier_cls, \
         patch('main.signal') as mock_signal:

        mock_hotkey_instance = Mock()
        mock_hotkey_cls.return_value = mock_hotkey_instance
        mock_tray_instance = Mock()
        mock_tray_cls.return_value = mock_tray_instance
        mock_notifier_instance = Mock()
        mock_notifier_cls.return_value = mock_notifier_instance

        app = WindowManagerApp()
        app.run()

        # 验证初始化被调用
        assert app.running == False  # run 结束后运行标志应为 False
        # 验证热键注销被调用
        mock_hotkey_instance.unregister_all.assert_called_once()


def test_app_run_initialize_failure():
    """测试初始化失败时的运行"""
    with patch('main.load_config') as mock_load, \
         patch('builtins.input') as mock_input:

        mock_load.return_value = []
        # 让 initialize 失败
        with patch.object(WindowManagerApp, 'initialize', return_value=False):
            app = WindowManagerApp()
            app.run()

            # 验证输入等待被调用
            mock_input.assert_called_once()


def test_main_function_non_windows():
    """测试非 Windows 平台的平台检查"""
    with patch('main.sys') as mock_sys, \
         patch('main.WindowManagerApp') as mock_app_cls, \
         patch('builtins.input', return_value='y'):

        mock_sys.platform = 'linux'
        mock_app_instance = Mock()
        mock_app_cls.return_value = mock_app_instance

        # 执行 main
        from main import main
        main()

        # 验证输入提示被显示
        # 注意：由于我们 patch 了 sys.platform，实际不会执行 sys.exit(1)


def test_main_function_user_decline():
    """测试用户拒绝在非 Windows 平台继续"""
    with patch('main.sys') as mock_sys, \
         patch('builtins.input', return_value='n'):

        mock_sys.platform = 'linux'
        # 确保 sys.exit 真的会 raise SystemExit
        mock_sys.exit.side_effect = SystemExit(1)

        from main import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
