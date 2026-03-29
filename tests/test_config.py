import pytest
from models import Preset
from config import load_config, ConfigLoader, ConfigValidationError


def test_load_config_with_valid_presets():
    """测试加载有效配置文件"""
    import json
    import tempfile
    import os

    # 创建临时配置文件
    test_data = {
        "presets": [
            {
                "name": "全屏",
                "width": 1920,
                "height": 1080,
                "position": "center",
                "hotkey": "ctrl+shift+f"
            },
            {
                "name": "半屏左",
                "width": 960,
                "height": 1080,
                "position": "left"
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_path = f.name

    try:
        presets = load_config(temp_path)
        assert len(presets) == 2
        assert isinstance(presets[0], Preset)
        assert presets[0].name == "全屏"
        assert presets[0].width == 1920
        assert presets[0].height == 1080
        assert presets[0].position == "center"
        assert presets[0].hotkey == "ctrl+shift+f"
        assert presets[1].name == "半屏左"
        assert presets[1].position == "left"
    finally:
        os.unlink(temp_path)


def test_load_config_with_minimal_presets():
    """测试仅包含必要字段的预设"""
    import json
    import tempfile
    import os

    test_data = {
        "presets": [
            {"name": "最小配置"}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_path = f.name

    try:
        presets = load_config(temp_path)
        assert len(presets) == 1
        assert presets[0].name == "最小配置"
        assert presets[0].width is None
        assert presets[0].height is None
        assert presets[0].position == "center"  # 默认值
        assert presets[0].hotkey is None
    finally:
        os.unlink(temp_path)


def test_load_config_file_not_exists():
    """测试配置文件不存在时应返回空列表"""
    presets = load_config("/nonexistent/path/presets.json")
    assert presets == []


def test_config_validation_invalid_position():
    """测试无效位置时会抛出 ConfigValidationError"""
    invalid_config = {
        "presets": [
            {"name": "测试", "position": "invalid"}
        ]
    }
    with pytest.raises(ConfigValidationError) as exc_info:
        loader = ConfigLoader(invalid_config)
        loader.validate()
    assert "position" in str(exc_info.value).lower()


def test_config_validation_invalid_dimensions():
    """测试无效尺寸时会抛出 ConfigValidationError"""
    invalid_config = {
        "presets": [
            {"name": "测试", "width": -100, "height": 100000}
        ]
    }
    with pytest.raises(ConfigValidationError):
        loader = ConfigLoader(invalid_config)
        loader.validate()


def test_config_validation_missing_name():
    """测试缺少 name 字段时会抛出 ConfigValidationError"""
    invalid_config = {
        "presets": [
            {"width": 100, "height": 100}
        ]
    }
    with pytest.raises(ConfigValidationError):
        loader = ConfigLoader(invalid_config)
        loader.validate()


def test_config_validation_invalid_name_type():
    """测试 name 字段类型错误时会抛出 ConfigValidationError"""
    invalid_config = {
        "presets": [
            {"name": 123}
        ]
    }
    with pytest.raises(ConfigValidationError):
        loader = ConfigLoader(invalid_config)
        loader.validate()


def test_config_validation_hotkey_type():
    """测试 hotkey 必须是字符串"""
    invalid_config = {
        "presets": [
            {"name": "测试", "hotkey": 123}
        ]
    }
    with pytest.raises(ConfigValidationError):
        loader = ConfigLoader(invalid_config)
        loader.validate()


def test_parse_presets_with_valid_data():
    """测试 parse_presets 方法"""
    config_dict = {
        "presets": [
            {
                "name": "测试预设",
                "width": 800,
                "height": 600,
                "position": "top-left",
                "hotkey": "ctrl+alt+t"
            }
        ]
    }
    loader = ConfigLoader(config_dict)
    loader.validate()
    presets = loader.parse_presets()

    assert len(presets) == 1
    assert isinstance(presets[0], Preset)
    assert presets[0].name == "测试预设"
    assert presets[0].width == 800
    assert presets[0].height == 600
    assert presets[0].position == "top-left"
    assert presets[0].hotkey == "ctrl+alt+t"


def test_all_valid_positions():
    """测试所有有效的位置值"""
    valid_positions = ["center", "top-left", "top-right", "bottom-left", "bottom-right",
                      "left", "right", "top", "bottom"]

    for position in valid_positions:
        config_dict = {
            "presets": [
                {"name": f"测试_{position}", "position": position}
            ]
        }
        loader = ConfigLoader(config_dict)
        loader.validate()  # 不应抛出异常
        presets = loader.parse_presets()
        assert presets[0].position == position
