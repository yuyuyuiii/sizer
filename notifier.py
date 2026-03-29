from plyer import notification


class Notifier:
    """通知器类，用于显示系统通知"""

    def __init__(self, enabled: bool = True):
        """
        初始化通知器

        Args:
            enabled: 是否启用通知，默认为 True
        """
        self.enabled = enabled

    def show(self, title: str, message: str, error: bool = False) -> bool:
        """
        显示通知

        Args:
            title: 通知标题
            message: 通知内容
            error: 是否为错误通知，错误通知显示时间更长（5秒）

        Returns:
            bool: 显示成功返回 True，失败或禁用时返回 False
        """
        if not self.enabled:
            return False

        try:
            timeout = 5 if error else 3
            notification.notify(
                title=title,
                message=message,
                timeout=timeout
            )
            return True
        except Exception as e:
            print(f"通知显示失败: {e}")
            return False

    def preset_applied(self, preset_name: str) -> bool:
        """
        显示预设应用成功通知

        Args:
            preset_name: 预设名称

        Returns:
            bool: 显示成功返回 True，失败返回 False
        """
        title = "预设已应用"
        message = f"已应用预设: {preset_name}"
        return self.show(title, message, error=False)

    def error_no_window(self) -> bool:
        """
        显示没有活动窗口的错误通知

        Returns:
            bool: 显示成功返回 True，失败返回 False
        """
        title = "错误"
        message = "没有活动窗口可操作"
        return self.show(title, message, error=True)

    def error_operation_failed(self) -> bool:
        """
        显示窗口操作失败的错误通知

        Returns:
            bool: 显示成功返回 True，失败返回 False
        """
        title = "错误"
        message = "窗口调整失败"
        return self.show(title, message, error=True)
