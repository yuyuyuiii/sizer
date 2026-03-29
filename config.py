import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from models import Preset


class ConfigValidationError(Exception):
    """配置验证错误异常"""
    pass


VALID_POSITIONS = {
    "center", "top-left", "top-right", "bottom-left", "bottom-right",
    "left", "right", "top", "bottom"
}


class ConfigLoader:
    """配置加载器和验证器"""

    def __init__(self, config_dict: Dict[str, Any]):
        """
        初始化配置加载器

        Args:
            config_dict: 配置字典，应包含 'presets' 键
        """
        self.config_dict = config_dict
        self._validated = False

    def _validate_dimension(self, value: Any, field_name: str, preset_idx: int) -> None:
        """验证宽高度字段"""
        if not isinstance(value, int):
            raise ConfigValidationError(
                f"第 {preset_idx+1} 个预设的 '{field_name}' 必须是整数"
            )
        if value < 1 or value > 7680:
            raise ConfigValidationError(
                f"第 {preset_idx+1} 个预设的 '{field_name}' 必须在 1-7680 之间，当前值: {value}"
            )

    def _validate_preset_fields(self, preset: Dict[str, Any], idx: int) -> None:
        """验证预设字段"""
        # 验证 position 字段
        position = preset.get("position", "center")
        if position not in VALID_POSITIONS:
            raise ConfigValidationError(
                f"第 {idx+1} 个预设的 'position' 无效: '{position}'。"
                f"有效值为: {', '.join(sorted(VALID_POSITIONS))}"
            )

        # 验证 width 字段
        if "width" in preset:
            self._validate_dimension(preset["width"], "width", idx)

        # 验证 height 字段
        if "height" in preset:
            self._validate_dimension(preset["height"], "height", idx)

        # 验证 hotkey 字段
        hotkey = preset.get("hotkey")
        if hotkey is not None and not isinstance(hotkey, str):
            raise ConfigValidationError(
                f"第 {idx+1} 个预设的 'hotkey' 必须是字符串"
            )

    def _validate_preset_structure(self, preset: Dict[str, Any], idx: int) -> None:
        """验证单个预设结构"""
        if not isinstance(preset, dict):
            raise ConfigValidationError(f"第 {idx+1} 个预设必须是字典类型")

        # 验证 name 字段
        if "name" not in preset:
            raise ConfigValidationError(f"第 {idx+1} 个预设缺少 'name' 字段")
        if not isinstance(preset["name"], str):
            raise ConfigValidationError(f"第 {idx+1} 个预设的 'name' 必须是字符串")
        if not preset["name"].strip():
            raise ConfigValidationError(f"第 {idx+1} 个预设的 'name' 不能为空")

    def _validate_structure(self, config_dict: Dict[str, Any]) -> None:
        """验证配置文件结构"""
        if not isinstance(config_dict, dict):
            raise ConfigValidationError("配置必须是字典类型")

        if "presets" not in config_dict:
            raise ConfigValidationError("配置缺少 'presets' 字段")

        presets = config_dict["presets"]
        if not isinstance(presets, list):
            raise ConfigValidationError("'presets' 必须是列表类型")

    def validate(self) -> None:
        """
        验证配置格式

        Raises:
            ConfigValidationError: 当配置无效时
        """
        self._validate_structure(self.config_dict)

        for i, preset in enumerate(self.config_dict["presets"]):
            self._validate_preset_structure(preset, i)
            self._validate_preset_fields(preset, i)

        self._validated = True

    def parse_presets(self) -> List[Preset]:
        """
        将配置解析为 Preset 对象列表

        Returns:
            Preset 对象列表

        Raises:
            ConfigValidationError: 如果未先调用 validate 方法
        """
        if not self._validated:
            raise ConfigValidationError("必须先调用 validate() 方法验证配置")

        presets = []
        for preset_dict in self.config_dict["presets"]:
            preset = Preset(
                name=preset_dict["name"],
                width=preset_dict.get("width"),
                height=preset_dict.get("height"),
                position=preset_dict.get("position", "center"),
                hotkey=preset_dict.get("hotkey")
            )
            presets.append(preset)

        return presets


def load_config(filepath: str = "presets.json") -> List[Preset]:
    """
    从 JSON 文件加载并验证配置

    Args:
        filepath: 配置文件路径

    Returns:
        Preset 对象列表。如果文件不存在或为空，返回空列表。

    Raises:
        ConfigValidationError: 当配置内容无效时
        json.JSONDecodeError: 当 JSON 格式错误时（文件存在但格式错误）
    """
    path = Path(filepath)

    if not path.exists():
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            config_dict = json.loads(content)
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"JSON 解析错误: {e}") from e

    loader = ConfigLoader(config_dict)
    loader.validate()
    return loader.parse_presets()
