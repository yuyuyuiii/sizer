from dataclasses import dataclass
from typing import Optional


@dataclass
class Preset:
    """窗口预设配置数据类"""
    name: str
    width: Optional[int] = None
    height: Optional[int] = None
    position: str = "center"
    hotkey: Optional[str] = None
