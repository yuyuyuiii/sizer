"""主程序入口 - Window Manager"""
import signal
import sys
import logging
from pathlib import Path
from config import load_config
from models import Preset
from window_controller import WindowController
from hotkey_manager import HotkeyManager, DuplicateHotkeyError
from tray_icon import TrayIconManager
from notifier import Notifier


class WindowManagerApp:
    """窗口管理器应用类"""

    def __init__(self):
        """初始化应用组件"""
        self.logger = None
        self._setup_logging()
        self.presets = []
        self.window_controller = WindowController()
        self.hotkey_manager = HotkeyManager()
        self.tray_icon = None
        self.notifier = Notifier(enabled=True)
        self.running = False

    def initialize(self) -> bool:
        """
        初始化应用

        Returns:
            bool: 初始化成功返回 True，失败返回 False
        """
        try:
            # 1. 加载配置
            self.presets = load_config()

            # 打印并通知加载数量
            count = len(self.presets)
            print(f"已加载 {count} 个预设")
            # 不再显示加载成功的通知,避免打扰

            # 2. 注册热键
            self.hotkey_manager.register_presets(self.presets, self._on_hotkey_triggered)

            # 3. 初始化托盘
            self.tray_icon = TrayIconManager(self.presets)
            self.tray_icon.set_preset_callback(self._on_preset_selected)

            return True

        except DuplicateHotkeyError as e:
            # 热键重复错误
            if self.logger:
                self.logger.error(f"热键注册失败: {e}")
            else:
                print(f"热键注册失败: {e}")
            self.notifier.show("热键错误", str(e), error=True)
            return False

        except Exception as e:
            # 其他初始化错误
            if self.logger:
                self.logger.error(f"启动失败: {e}")
            else:
                print(f"启动失败: {e}")
            self.notifier.show("启动失败", str(e), error=True)
            return False

    def _on_hotkey_triggered(self, preset_name: str) -> None:
        """
        热键触发回调

        Args:
            preset_name: 预设名称
        """
        self._apply_preset_by_name(preset_name)

    def _on_preset_selected(self, preset_name: str) -> None:
        """
        托盘预设选择回调

        Args:
            preset_name: 预设名称
        """
        self._apply_preset_by_name(preset_name)

    def _apply_preset_by_name(self, preset_name: str) -> None:
        """
        根据预设名称应用预设

        Args:
            preset_name: 预设名称
        """
        if self.logger:
            self.logger.debug(f"收到预设选择请求: '{preset_name}'")
            self.logger.debug(f"可用预设列表: {[p.name for p in self.presets]}")
        else:
            print(f"[调试] 收到预设选择请求: '{preset_name}'")
            print(f"[调试] 可用预设列表: {[p.name for p in self.presets]}")

        # 查找预设(支持去除空格的模糊匹配)
        preset = None
        preset_name_clean = preset_name.strip()
        for p in self.presets:
            if p.name.strip() == preset_name_clean:
                preset = p
                break

        if preset is None:
            self.notifier.show("错误", f"预设 '{preset_name}' 不存在", error=True)
            if self.logger:
                self.logger.error(f"未找到预设: '{preset_name}' (清理后: '{preset_name_clean}')")
            else:
                print(f"[错误] 未找到预设: '{preset_name}' (清理后: '{preset_name_clean}')")
            return

        # 打印应用信息
        if self.logger:
            self.logger.info(f"应用预设: {preset_name}")
        else:
            print(f"应用预设: {preset_name}")

        # 应用预设
        success = self.window_controller.apply_preset(preset)

        # 显示通知(只有失败时才弹窗)
        if success:
            if self.logger:
                self.logger.info(f"预设 '{preset_name}' 应用成功")
        else:
            self.notifier.error_operation_failed()
            if self.logger:
                self.logger.error(f"预设 '{preset_name}' 应用失败")

    def _setup_logging(self) -> None:
        """配置日志系统"""
        # 创建日志目录 (用户 AppData 目录)
        log_dir = Path.home() / "AppData" / "Local" / "window-manager"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "app.log"

        # 配置根 logger (捕获所有)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # 文件处理器 - 所有级别
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 控制台处理器 - 只显示 INFO 及以上
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 清除已有的 handlers (避免重复)
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # 测试日志
        self.logger = logging.getLogger("WindowManager")
        self.logger.info("=" * 50)
        self.logger.info("Window Manager 启动")
        self.logger.info(f"日志文件: {log_file}")

    def run(self) -> None:
        """运行应用"""
        # 初始化
        if not self.initialize():
            print("初始化失败，按 Enter 键退出...")
            input()
            return

        # 打印启动信息
        if self.logger:
            self.logger.info("Window Manager 已启动")
            self.logger.info("提示：可以通过托盘图标或热键触发窗口预设")
        else:
            print("Window Manager 已启动")
            print("提示：可以通过托盘图标或热键触发窗口预设")

        # 不显示启动通知,避免打扰
        pass

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)

        # 运行托盘图标（阻塞）
        self.running = True
        try:
            self.tray_icon.run()
        finally:
            self.running = False

        # 退出清理
        if self.logger:
            self.logger.info("正在退出...")
        else:
            print("正在退出...")
        self.hotkey_manager.unregister_all()

        if self.logger:
            self.logger.info("已退出")
            self.logger.info("=" * 50)

    def _signal_handler(self, signum, frame) -> None:
        """
        信号处理函数

        Args:
            signum: 信号编号
            frame: 当前帧
        """
        if self.logger:
            self.logger.info("收到退出信号")
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()


def main() -> None:
    """主函数"""
    # 检查平台
    if sys.platform != "win32":
        print("警告：此程序针对 Windows 平台设计")
        print("将在 WSL/Linux 环境下无法使用托盘功能")
        print("建议在 Windows 原生环境运行")

    # 创建并运行应用
    app = WindowManagerApp()
    app.run()


if __name__ == "__main__":
    main()
