# Window Manager

一个 Windows 窗口大小和位置管理工具。

## 功能

- 通过系统托盘控制窗口位置和大小
- 全局热键快速应用预设
- JSON 配置文件自定义预设

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

1. 编辑 `presets.json` 配置预设
2. 在 Windows 上运行：
```bash
python main.py
```

## 配置格式

```json
{
  "presets": [
    {
      "name": "居中 1920x1080",
      "width": 1920,
      "height": 1080,
      "position": "center",
      "hotkey": "ctrl+shift+1"
    }
  ]
}
```

## 支持的位置

- `center`: 屏幕居中
- `top-left`, `top-right`, `bottom-left`, `bottom-right`: 四角
- `left`, `right`, `top`, `bottom`: 靠边居中

## 注意事项

此工具需要在 Windows 原生环境运行，WSL 无法控制 Windows 窗口。
