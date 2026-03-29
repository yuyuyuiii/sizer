import pytest
from unittest.mock import patch, Mock
from notifier import Notifier


def test_notifier_show_success():
    """测试显示成功通知"""
    with patch('notifier.notification') as mock_notify:
        notifier = Notifier()
        result = notifier.show("操作成功", "窗口已调整")
        assert result == True
        mock_notify.notify.assert_called_once()
        call_args = mock_notify.notify.call_args
        assert "窗口已调整" in call_args[1]['message']


def test_notifier_show_error():
    """测试显示错误通知"""
    with patch('notifier.notification') as mock_notify:
        notifier = Notifier()
        result = notifier.show("错误", "没有活动窗口", error=True)
        assert result == True
        # error=True 应设置 timeout 为 5
        call_args = mock_notify.notify.call_args
        assert call_args[1]['timeout'] == 5


def test_notifier_show_when_disabled():
    """测试禁用状态不显示通知"""
    with patch('notifier.notification') as mock_notify:
        notifier = Notifier(enabled=False)
        result = notifier.show("测试", "消息")
        assert result == False
        mock_notify.notify.assert_not_called()


def test_notifier_show_exception():
    """测试通知异常时返回 False"""
    with patch('notifier.notification') as mock_notify:
        mock_notify.notify.side_effect = Exception("Notification failed")
        notifier = Notifier()
        result = notifier.show("测试", "消息")
        assert result == False


def test_notifier_helper_methods():
    """测试辅助方法"""
    with patch('notifier.notification') as mock_notify:
        notifier = Notifier()

        # preset_applied
        notifier.preset_applied("居中 1920x1080")
        call_args = mock_notify.notify.call_args
        assert "居中 1920x1080" in call_args[1]['message']

        # 重置 mock
        mock_notify.reset_mock()

        # error_no_window
        notifier.error_no_window()
        call_args = mock_notify.notify.call_args
        assert "没有活动窗口" in call_args[1]['message']

        # 重置 mock
        mock_notify.reset_mock()

        # error_operation_failed
        notifier.error_operation_failed()
        call_args = mock_notify.notify.call_args
        assert "窗口调整失败" in call_args[1]['message']
