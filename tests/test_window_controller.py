import pytest
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
