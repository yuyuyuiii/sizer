# 构建 Windows 可执行文件

本工具支持通过 GitHub Actions 自动构建 Windows exe 文件，无需在 Windows 上安装 Python。

## 自动构建（推荐）

### 使用 GitHub Actions

1. 推送代码到 GitHub 仓库的 `main` 或 `master` 分支
2. GitHub Actions 会自动在 Windows 虚拟机上构建
3. 构建完成后，可在 **Actions 标签页** 下载产物：
   - 文件名：`window-manager-windows.zip`
   - 包含：`window-manager.exe`

### 手动触发构建

在 GitHub 仓库的 **Actions** 页面：
1. 选择 "Build Windows Executable" 工作流
2. 点击 "Run workflow"
3. 选择分支（如 main）
4. 点击 "Run workflow" 按钮

### 发布版本时自动构建

当创建一个 Git tag（如 `v1.0.0`）时，Actions 会自动：
- 构建 exe
- 创建 GitHub Release
- 将 exe 附加到 Release

```bash
git tag v1.0.0
git push origin v1.0.0
```

## 本地构建（可选）

如果你在 Windows 上有 Python 环境：

```powershell
# 1. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 2. 打包
pyinstaller --onefile --windowed ^
  --name="window-manager" ^
  --add-data="presets.json;." ^
  main.py

# 3. exe 位置
# dist/window-manager.exe
```

**注意**：
- `--add-data="presets.json;."` 会将配置文件打包到 exe 同目录
- 在 Windows 上，路径分隔符使用分号 `;`
- `--windowed` 表示不显示控制台窗口（后台运行）

## 打包选项说明

| 选项 | 说明 |
|------|------|
| `--onefile` | 打包为单个 exe 文件 |
| `--windowed` | 不显示控制台窗口（GUI 程序） |
| `--name` | 输出文件名 |
| `--add-data` | 附加数据文件（配置文件、图标等） |
| `--icon` | 设置 exe 图标（需要 .ico 文件） |

## 产物使用

1. 下载 `window-manager.exe`
2. 在同目录创建 `presets.json` 配置文件（或使用打包内的默认配置）
3. 双击运行 `window-manager.exe`
4. 系统托盘会出现图标，右键选择预设或使用热键

## 故障排除

### exe 启动失败
- 确保 Windows 版本是 Windows 10/11
- 某些杀毒软件可能会误报，需要添加白名单
- 首次运行可能较慢（Nuitka/PyInstaller 的启动开销）

### 配置文件未找到
如果 exe 找不到 `presets.json`：
- 将 `presets.json` 放在 `window-manager.exe` 同一目录
- 或使用绝对路径配置（需修改代码）

### 热键不工作
- 以管理员权限运行 exe
- 确保热key未被其他程序占用
- 检查 `presets.json` 热键格式是否正确
