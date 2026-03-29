# Windows 窗口管理器 Bug 修复设计文档

**项目名称**: window-manager
**目标平台**: Windows (需在 Windows 上运行，可在 WSL 中开发)
**编程语言**: Python
**设计日期**: 2026-03-29
**设计类型**: Bug 修复与改进

---

## 一、问题概述

用户报告了两个主要问题：

### 1.1 分辨率检测错误
- **现象**: 外接显示器分辨率为 2560x1440，但程序检测为 1920x1080
- **影响**: 窗口位置计算错误，无法正确居中或对齐
- **日志表现**: 启动时无显示器检测日志，直接显示"屏幕分辨率: 1920x1080"

### 1.2 托盘调整窗口不生效
- **现象**: 托盘菜单点击后有响应（有日志输出），但目标窗口无变化
- **附加问题**: 任务栏出现工具图标关不掉
- **影响**: 核心功能失效，用户只能使用热键

### 1.3 问题关联性
1. 分辨率检测失败导致位置计算错误
2. 日志系统初始化顺序问题导致调试信息缺失
3. 窗口选择可能受工具自身窗口干扰
4. 任务栏图标问题影响用户体验

---

## 二、根因分析

### 2.1 分辨率检测问题
1. **初始化顺序**: `WindowController` 在日志配置前初始化，`PositionCalculator` 检测屏幕时日志系统未就绪
2. **检测逻辑**: `_detect_screen_size()` 方法可能未正确枚举外接显示器
3. **回退机制**: 检测失败时静默回退到默认值 1920x1080

### 2.2 托盘操作无效问题
1. **窗口选择**: `getActiveWindow()` 可能获取到工具自身窗口
2. **操作验证**: `resizeTo()` 和 `moveTo()` 调用可能失败但无异常
3. **进程干扰**: pystray 可能创建隐藏窗口用于消息循环

### 2.3 任务栏图标问题
1. **pystray 行为**: pystray 可能创建任务栏可见的隐藏窗口
2. **窗口属性**: 未正确设置窗口属性以隐藏任务栏图标

---

## 三、解决方案设计

### 3.1 初始化顺序重构
**目标**: 确保日志系统在组件初始化前就绪

**修改内容**:
1. 修改 `WindowManagerApp.__init__`:
   ```python
   def __init__(self):
       # 先配置日志
       self._setup_logging()

       # 再初始化组件
       self.presets = []
       self.window_controller = WindowController()
       self.hotkey_manager = HotkeyManager()
       self.tray_icon = None
       self.notifier = Notifier(enabled=True)
       self.running = False
   ```

2. 或添加 `initialize()` 方法到 `WindowController`:
   ```python
   class WindowController:
       def __init__(self):
           self.calculator = None  # 延迟初始化

       def initialize(self):
           self.calculator = PositionCalculator()
   ```

### 3.2 屏幕检测增强
**目标**: 正确检测多显示器配置，优先选择活动显示器

**修改内容**:
1. 改进 `_detect_screen_size()` 方法:
   ```python
   def _detect_screen_size(self) -> Tuple[int, int]:
       # 方法1: 获取包含鼠标光标的显示器
       try:
           cursor_x, cursor_y = win32api.GetCursorPos()
           monitors = win32api.EnumDisplayMonitors()
           for hmonitor, _, _ in monitors:
               info = win32gui.GetMonitorInfo(hmonitor)
               rc = info['Monitor']
               if (rc[0] <= cursor_x <= rc[2] and rc[1] <= cursor_y <= rc[3]):
                   w = rc[2] - rc[0]
                   h = rc[3] - rc[1]
                   return (w, h)
       except Exception as e:
           logger.debug(f"光标位置检测失败: {e}")

       # 方法2: 获取包含活动窗口的显示器
       try:
           hwnd = win32gui.GetForegroundWindow()
           if hwnd:
               monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
               info = win32gui.GetMonitorInfo(monitor)
               rc = info['Monitor']
               w = rc[2] - rc[0]
               h = rc[3] - rc[1]
               return (w, h)
       except Exception as e:
           logger.debug(f"活动窗口检测失败: {e}")

       # 方法3: 选择面积最大的显示器（原逻辑）
       # ... 保留现有逻辑
   ```

2. 添加配置选项（可选）:
   ```python
   # 可在配置中添加 display_index 或 display_selection 字段
   ```

### 3.3 窗口选择与操作修复
**目标**: 确保操作正确的窗口并验证结果

**修改内容**:
1. 过滤工具自身窗口:
   ```python
   def get_active_window(self):
       import pygetwindow as gw
       import os

       windows = gw.getAllWindows()
       current_pid = os.getpid()

       for window in windows:
           # 排除工具自身进程的窗口
           if hasattr(window, '_hWnd'):
               try:
                   window_pid = win32process.GetWindowThreadProcessId(window._hWnd)[1]
                   if window_pid == current_pid:
                       continue
               except:
                   pass

           # 检查是否为活动窗口
           if window.isActive:
               return window

       return None
   ```

2. 添加操作验证:
   ```python
   def apply_preset(self, preset: 'Preset') -> bool:
       # ... 现有代码

       # 验证操作结果
       try:
           new_width = window.width
           new_height = window.height
           new_left = window.left if hasattr(window, 'left') else None
           new_top = window.top if hasattr(window, 'top') else None

           success = True
           if preset.width is not None and abs(new_width - target_width) > 5:  # 允许5像素误差
               logger.warning(f"窗口宽度调整不匹配: 目标={target_width}, 实际={new_width}")
               success = False
           # ... 类似检查高度和位置

           return success
       except Exception as e:
           logger.error(f"验证窗口操作失败: {e}")
           return False
   ```

### 3.4 任务栏图标问题修复
**目标**: 隐藏工具的任务栏图标

**修改内容**:
1. 检查 pystray 配置:
   ```python
   # 尝试设置 pystray 不显示窗口
   self.icon = pystray.Icon(
       "window_sizer",
       create_icon_image(),
       "Window Sizer",
       self._create_menu(),
       # 可能需要的参数
   )
   ```

2. Windows API 解决方案（备选）:
   ```python
   import win32gui
   import win32con
   import win32process
   import os

   def find_pystray_window():
       """查找 pystray 创建的隐藏窗口"""
       def enum_windows_callback(hwnd, windows):
           if win32gui.IsWindowVisible(hwnd):
               class_name = win32gui.GetClassName(hwnd)
               window_text = win32gui.GetWindowText(hwnd)
               # pystray 通常使用特定类名或窗口标题
               if "pystray" in class_name.lower() or "tray" in window_text.lower():
                   windows.append(hwnd)
               # 或者查找包含进程ID的窗口
               _, pid = win32process.GetWindowThreadProcessId(hwnd)
               if pid == os.getpid():
                   windows.append(hwnd)
           return True

       windows = []
       win32gui.EnumWindows(enum_windows_callback, windows)
       return windows[0] if windows else None

   hwnd = find_pystray_window()
   if hwnd:
       win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
       # 设置窗口扩展样式隐藏任务栏图标
       ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
       ex_style |= win32con.WS_EX_TOOLWINDOW
       win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
   ```

### 3.5 错误处理与日志增强
**目标**: 提供详细的调试信息

**修改内容**:
1. 增加详细日志:
   ```python
   logger.debug(f"检测显示器: 方法1结果={width1}x{height1}")
   logger.info(f"选择显示器: {selected_width}x{selected_height}")
   ```

2. 错误恢复机制:
   ```python
   def apply_preset_with_retry(self, preset: 'Preset', max_retries: int = 2) -> bool:
       for attempt in range(max_retries):
           try:
               return self.apply_preset(preset)
           except Exception as e:
               logger.warning(f"应用预设失败 (尝试 {attempt+1}/{max_retries}): {e}")
               if attempt < max_retries - 1:
                   time.sleep(0.1)
       return False
   ```

---

## 四、实现计划

### 4.1 第一阶段：初始化顺序与日志修复
1. 修改 `WindowManagerApp` 初始化顺序
2. 确保 `PositionCalculator` 在日志就绪后初始化
3. 验证日志输出包含显示器检测信息

### 4.2 第二阶段：屏幕检测增强
1. 实现改进的 `_detect_screen_size()` 方法
2. 添加光标位置和活动窗口检测逻辑
3. 测试多显示器环境下的正确性

### 4.3 第三阶段：窗口选择修复
1. 实现窗口过滤（排除工具自身进程）
2. 添加操作验证逻辑
3. 测试托盘菜单和热键功能

### 4.4 第四阶段：任务栏图标修复
1. 调研 pystray 隐藏窗口选项
2. 实现 Windows API 备选方案
3. 验证任务栏无工具图标

### 4.5 第五阶段：测试与验证
1. 多显示器环境测试
2. 边界情况测试（无活动窗口、最小化窗口等）
3. 性能与稳定性测试

---

## 五、测试计划

### 5.1 功能测试
- [ ] 分辨率检测: 外接显示器正确识别为 2560x1440
- [ ] 托盘操作: 点击托盘菜单成功调整目标窗口
- [ ] 热键功能: 热键操作正常，与托盘菜单一致
- [ ] 任务栏图标: 工具不显示在任务栏（或可关闭）

### 5.2 环境测试
- [ ] 单显示器环境（1920x1080）
- [ ] 多显示器环境（笔记本+外接）
- [ ] 不同DPI设置
- [ ] 管理员/非管理员权限

### 5.3 边界测试
- [ ] 无活动窗口时操作
- [ ] 最小化/最大化窗口
- [ ] 全屏应用程序
- [ ] 系统对话框

### 5.4 回归测试
- [ ] 现有预设配置正常工作
- [ ] 所有热键功能正常
- [ ] 通知系统正常
- [ ] 错误处理正常

---

## 六、风险与缓解

### 6.1 技术风险
- **风险**: Windows API 调用可能在不同系统版本表现不同
- **缓解**: 添加版本检测和回退机制，使用 try-catch 包装

### 6.2 兼容性风险
- **风险**: pystray 隐藏窗口方案可能不兼容某些 Windows 版本
- **缓解**: 提供配置选项，允许用户选择是否显示任务栏图标

### 6.3 性能风险
- **风险**: 窗口过滤和验证增加开销
- **缓解**: 优化窗口选择逻辑，仅在必要时进行完整过滤

### 6.4 用户体验风险
- **风险**: 修改可能影响现有用户的工作流程
- **缓解**: 保持向后兼容性，分阶段发布，提供回滚指南

---

## 七、验收标准

- [ ] 外接显示器分辨率正确检测（2560x1440）
- [ ] 托盘菜单点击成功调整目标窗口
- [ ] 工具不在任务栏显示干扰窗口（或可关闭）
- [ ] 所有现有功能保持正常
- [ ] 错误情况有明确日志和用户提示
- [ ] 多显示器环境下位置计算正确

---

## 八、扩展性考虑

### 8.1 未来改进
- 显示器选择配置（主显示器、外接显示器等）
- 窗口记忆功能（记住特定应用程序的偏好设置）
- 布局配置文件导入/导出

### 8.2 配置增强
- 添加 `display_selection` 字段到预设配置
- 支持按应用程序过滤窗口
- 条件预设（根据显示器数量选择不同布局）

---

**设计完成，待用户批准后进入实现计划阶段。**