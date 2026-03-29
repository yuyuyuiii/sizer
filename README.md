# Window Manager

一个 Windows 系统窗口大小和位置管理工具。

## 功能特性

- ✅ 系统托盘图标，右键菜单快速选择预设
- ✅ 全局热键支持，一键应用窗口布局
- ✅ 可配置的预设（尺寸、位置、热键）
- ✅ 操作结果通知提示
- ✅ 支持多种位置：居中、四角、靠边

## 系统要求

- **操作系统**: Windows 10/11 (必须在 Windows 原生环境运行，WSL 不可用)
- **Python**: 3.8+
- **权限**: 可能需要管理员权限（某些热键需要）

## 安装步骤

1. 克隆或下载项目到本地

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 编辑 `presets.json` 配置你想要的自定义预设

## 使用方法

### 启动

在 Windows 命令提示符或 PowerShell 中运行：

```bash
python main.py
```

程序会在系统托盘显示图标（蓝色方块）。

### 配置预设

编辑 `presets.json` 文件：

```json
{
  "presets": [
    {
      "name": "居中 1920x1080",
      "width": 1920,
      "height": 1080,
      "position": "center",
      "hotkey": "ctrl+shift+1"
    },
    {
      "name": "左上 1600x900",
      "width": 1600,
      "height": 900,
      "position": "top-left",
      "hotkey": "ctrl+shift+2"
    },
    {
      "name": "靠右（保持原尺寸）",
      "position": "right",
      "hotkey": "ctrl+shift+r"
    },
    {
      "name": "仅居中",
      "position": "center"
    }
  ]
}
```

配置字段说明：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | 是 | 预设名称（用于菜单显示） |
| width | int | 否 | 窗口宽度（不指定则保持原尺寸） |
| height | int | 否 | 窗口高度（不指定则保持原尺寸） |
| position | string | 否 | 位置，默认为 "center" |
| hotkey | string | 否 | 全局热键，如 "ctrl+shift+c" |

### 支持的位置

- `center`: 屏幕居中
- `top-left`: 左上角
- `top-right`: 右上角
- `bottom-left`: 左下角
- `bottom-right`: 右下角
- `left`: 靠左，垂直居中
- `right`: 靠右，垂直居中
- `top`: 靠上，水平居中
- `bottom`: 靠下，水平居中

### 热键格式

使用 `keyboard` 库的格式：

- `ctrl+shift+c`: Ctrl + Shift + C
- `alt+f12`: Alt + F12
- `win+up`: Win + 上箭头
- 详见 [keyboard 文档](https://github.com/boppreh/keyboard)

### 使用

**托盘菜单**: 右键点击托盘图标，在菜单中选择预设

**热键**: 按下配置的快捷键直接应用

**注意事项**:
- 工具控制当前**活动窗口**
- 确保要操作的窗口处于激活状态
- 如果窗口最小化，工具会自动恢复它

## 故障排除

### 热键不工作

- 某些情况下需要**管理员权限**
- 检查热键是否与其他程序冲突
- 查看控制台是否有错误输出

### 托盘图标不显示

- WSL 环境不支持系统托盘
- 必须在 Windows 原生环境运行

### 窗口位置错误

- 多显示器环境下可能不正确（当前仅支持单显示器）
- 窗口尺寸超过屏幕会被自动限制

## 开发

### 项目结构

```
window-manager/
├── main.py              # 主程序入口
├── config.py            # 配置加载
├── models.py            # 数据模型
├── window_controller.py # 窗口控制
├── hotkey_manager.py    # 热键管理
├── tray_icon.py         # 托盘图标
├── notifier.py          # 通知提示
├── presets.json         # 预设配置
├── requirements.txt     # 依赖
└── tests/               # 测试
```

### 运行测试

```bash
pytest tests/ -v
```

### 打包为 exe

使用 PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

---

## License

MIT
