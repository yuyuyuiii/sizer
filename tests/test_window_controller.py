import pytest
import sys
import types
from unittest.mock import Mock, patch
from window_controller import WindowController, PositionCalculator
from models import Preset


def test_position_calculator_center():
    """测试居中位置计算"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("center", (800, 600))
    assert left == 560
    assert top == 240


def test_position_calculator_top_left():
    """测试左上角位置"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("top-left", (800, 600))
    assert left == 0 and top == 0


def test_position_calculator_top_right():
    """测试右上角位置"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("top-right", (800, 600))
    assert left == 1920 - 800
    assert top == 0


def test_position_calculator_bottom_left():
    """测试左下角位置"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("bottom-left", (800, 600))
    assert left == 0
    assert top == 1080 - 600


def test_position_calculator_bottom_right():
    """测试右下角位置"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("bottom-right", (800, 600))
    assert left == 1920 - 800
    assert top == 1080 - 600


def test_position_calculator_left():
    """测试左侧居中"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("left", (800, 600))
    assert left == 0
    assert top == (1080 - 600) // 2


def test_position_calculator_right():
    """测试右侧居中"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("right", (800, 600))
    assert left == 1920 - 800
    assert top == (1080 - 600) // 2


def test_position_calculator_top():
    """测试顶部居中"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("top", (800, 600))
    assert left == (1920 - 800) // 2
    assert top == 0


def test_position_calculator_bottom():
    """测试底部居中"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    left, top = calc.calculate("bottom", (800, 600))
    assert left == (1920 - 800) // 2
    assert top == 1080 - 600


def test_window_controller_apply_preset_with_mock_window():
    """测试应用预设"""
    with patch.object(WindowController, 'get_active_window') as mock_get_active:
        mock_window = Mock()
        mock_window.width = 1000
        mock_window.height = 800
        mock_window.left = 160
        mock_window.top = 90
        mock_window.resizeTo.side_effect = lambda width, height: (
            setattr(mock_window, "width", width),
            setattr(mock_window, "height", height),
        )
        mock_window.moveTo.side_effect = lambda left, top: (
            setattr(mock_window, "left", left),
            setattr(mock_window, "top", top),
        )
        mock_get_active.return_value = mock_window

        controller = WindowController()
        preset = Preset(name="测试", width=1600, height=900, position="center")

        result = controller.apply_preset(preset)

        assert result == True
        mock_window.restore.assert_called_once()
        mock_window.resizeTo.assert_called_once_with(1600, 900)
        mock_window.moveTo.assert_called_once()


def test_window_controller_apply_preset_keep_original_size():
    """测试保持原尺寸"""
    with patch.object(WindowController, 'get_active_window') as mock_get_active:
        mock_window = Mock()
        mock_window.width = 1000
        mock_window.height = 800
        mock_window.left = 460
        mock_window.top = 140
        mock_window.resizeTo.side_effect = lambda width, height: (
            setattr(mock_window, "width", width),
            setattr(mock_window, "height", height),
        )
        mock_window.moveTo.side_effect = lambda left, top: (
            setattr(mock_window, "left", left),
            setattr(mock_window, "top", top),
        )
        mock_get_active.return_value = mock_window

        controller = WindowController()
        preset = Preset(name="测试", position="center")  # 不指定尺寸

        result = controller.apply_preset(preset)

        assert result == True
        mock_window.resizeTo.assert_called_once_with(1000, 800)  # 保持原尺寸


def test_window_controller_no_active_window():
    """测试无活动窗口"""
    with patch.object(WindowController, 'get_active_window') as mock_get_active:
        mock_get_active.return_value = None
        controller = WindowController()
        preset = Preset(name="测试", width=1600, height=900, position="center")
        result = controller.apply_preset(preset)
        assert result == False


def test_position_calculator_size_limit():
    """测试窗口尺寸限制不超过屏幕"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    # 窗口尺寸超过屏幕
    left, top = calc.calculate("center", (3000, 2000))
    # 应该被限制到屏幕尺寸
    assert left == 0  # (1920 - 1920) // 2
    assert top == 0   # (1080 - 1080) // 2


def test_position_calculator_all_positions():
    """测试所有9个位置"""
    calc = PositionCalculator(screen_width=1920, screen_height=1080)
    win_size = (800, 600)

    positions = {
        "center": (560, 240),
        "top-left": (0, 0),
        "top-right": (1120, 0),
        "bottom-left": (0, 480),
        "bottom-right": (1120, 480),
        "left": (0, 240),
        "right": (1120, 240),
        "top": (560, 0),
        "bottom": (560, 480)
    }

    for pos, expected in positions.items():
        result = calc.calculate(pos, win_size)
        assert result == expected, f"位置 {pos} 计算错误: 期望 {expected}, 实际 {result}"


def test_detect_screen_size_prefers_cursor_monitor():
    """测试屏幕检测优先选择鼠标所在显示器"""
    monitors = [
        ("small", None, None),
        ("large", None, None),
    ]
    fake_win32api = Mock()
    fake_win32api.GetCursorPos.return_value = (2100, 100)
    fake_win32api.EnumDisplayMonitors.return_value = monitors
    fake_win32api.GetSystemMetrics.side_effect = AssertionError("不应回退到系统指标")
    fake_win32api.GetMonitorInfo.side_effect = [
        {"Monitor": (0, 0, 1920, 1080)},
        {"Monitor": (1920, 0, 4480, 1440)},
    ]
    fake_win32gui = Mock()

    with patch.dict(sys.modules, {"win32api": fake_win32api, "win32gui": fake_win32gui, "win32con": Mock()}):
        calc = PositionCalculator()

    assert (calc.screen_width, calc.screen_height) == (2560, 1440)


def test_detect_screen_size_uses_win32api_get_monitor_info_when_win32gui_missing():
    """测试 win32gui 缺少 GetMonitorInfo 时仍可通过 win32api 正常检测"""
    fake_win32api = Mock()
    fake_win32api.GetCursorPos.return_value = (100, 100)
    fake_win32api.EnumDisplayMonitors.return_value = [("primary", None, None)]
    fake_win32api.GetMonitorInfo.return_value = {"Monitor": (0, 0, 2560, 1440)}
    fake_win32gui = types.SimpleNamespace()

    with patch.dict(sys.modules, {"win32api": fake_win32api, "win32gui": fake_win32gui, "win32con": Mock()}):
        calc = PositionCalculator()

    assert (calc.screen_width, calc.screen_height) == (2560, 1440)


def test_detect_screen_size_prefers_physical_resolution_from_display_settings():
    """测试显示器 rect 是缩放后的逻辑坐标时，优先读取物理分辨率"""
    fake_win32api = Mock()
    fake_win32api.GetCursorPos.return_value = (100, 100)
    fake_win32api.EnumDisplayMonitors.return_value = [("primary", None, None)]
    fake_win32api.GetMonitorInfo.return_value = {
        "Monitor": (0, 0, 2048, 1152),
        "Device": r"\\\\.\\DISPLAY1",
    }
    fake_settings = types.SimpleNamespace(dmPelsWidth=2560, dmPelsHeight=1440)
    fake_win32api.EnumDisplaySettings.return_value = fake_settings
    fake_win32con = types.SimpleNamespace(ENUM_CURRENT_SETTINGS=-1)
    fake_win32gui = types.SimpleNamespace()

    with patch.dict(
        sys.modules,
        {"win32api": fake_win32api, "win32gui": fake_win32gui, "win32con": fake_win32con},
    ):
        calc = PositionCalculator()

    assert (calc.screen_width, calc.screen_height) == (2560, 1440)


def test_window_controller_skips_own_active_window():
    """测试活动窗口是工具自身时会回退到其他活动窗口"""
    own_window = Mock()
    own_window.isActive = True
    own_window._hWnd = 100
    target_window = Mock()
    target_window.isActive = True
    target_window._hWnd = 200

    fake_gw = types.SimpleNamespace(
        getActiveWindow=lambda: own_window,
        getAllWindows=lambda: [own_window, target_window],
    )
    fake_win32process = types.SimpleNamespace(
        GetWindowThreadProcessId=Mock(side_effect=[(1, 9999), (1, 9999), (1, 8888)])
    )

    with patch("window_controller.os.getpid", return_value=9999), \
         patch.dict(sys.modules, {"pygetwindow": fake_gw, "win32process": fake_win32process}):
        controller = WindowController()
        result = controller.get_active_window()

    assert result is target_window


def test_apply_preset_returns_false_when_window_state_mismatch():
    """测试窗口调整后尺寸明显不匹配时返回失败"""
    with patch.object(WindowController, "get_active_window") as mock_get_active:
        mock_window = Mock()
        mock_window.width = 1000
        mock_window.height = 800
        mock_window.left = 0
        mock_window.top = 0
        mock_window.resizeTo.side_effect = lambda width, height: None
        mock_window.moveTo.side_effect = lambda left, top: None
        mock_get_active.return_value = mock_window

        controller = WindowController()
        preset = Preset(name="测试", width=1600, height=900, position="center")

        result = controller.apply_preset(preset)

        assert result is False


def test_apply_preset_prefers_win32_api_when_hwnd_available():
    """测试有 hwnd 时优先使用 Win32 API 调整窗口"""
    fake_win32gui = Mock()
    fake_win32con = types.SimpleNamespace(
        SW_RESTORE=9,
        SWP_NOZORDER=0x0004,
        SWP_NOACTIVATE=0x0010,
    )
    fake_win32gui.GetWindowRect.return_value = (160, 90, 1760, 990)

    with patch.object(WindowController, "get_active_window") as mock_get_active, \
         patch.dict(sys.modules, {"win32gui": fake_win32gui, "win32con": fake_win32con}):
        mock_window = Mock()
        mock_window.width = 1600
        mock_window.height = 900
        mock_window.left = 160
        mock_window.top = 90
        mock_window._hWnd = 999
        mock_get_active.return_value = mock_window

        controller = WindowController()
        preset = Preset(name="测试", width=1600, height=900, position="center")

        result = controller.apply_preset(preset)

        assert result is True
        fake_win32gui.ShowWindow.assert_called_once_with(999, fake_win32con.SW_RESTORE)
        fake_win32gui.SetWindowPos.assert_called_once_with(
            999,
            None,
            160,
            90,
            1600,
            900,
            fake_win32con.SWP_NOZORDER | fake_win32con.SWP_NOACTIVATE,
        )


def test_apply_preset_reads_final_rect_from_win32_api():
    """测试结果校验优先读取 Win32 API 的真实窗口矩形"""
    fake_win32gui = Mock()
    fake_win32con = types.SimpleNamespace(
        SW_RESTORE=9,
        SWP_NOZORDER=0x0004,
        SWP_NOACTIVATE=0x0010,
    )
    fake_win32gui.GetWindowRect.return_value = (360, 140, 1560, 940)

    with patch.object(WindowController, "get_active_window") as mock_get_active, \
         patch.dict(sys.modules, {"win32gui": fake_win32gui, "win32con": fake_win32con}):
        mock_window = Mock()
        mock_window.width = 500
        mock_window.height = 400
        mock_window.left = 0
        mock_window.top = 0
        mock_window._hWnd = 888
        mock_get_active.return_value = mock_window

        controller = WindowController()
        preset = Preset(name="测试", width=1200, height=800, position="center")

        result = controller.apply_preset(preset)

        assert result is True
