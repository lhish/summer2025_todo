"""
番茄钟功能测试
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.pomodoro_manager import PomodoroManager
from src.database.database import DatabaseManager


class TestPomodoroManager(unittest.TestCase):
    """番茄钟管理器测试类"""
    
    def setUp(self):
        """测试前的设置"""
        self.mock_db = Mock(spec=DatabaseManager)
        self.pomodoro_manager = PomodoroManager(self.mock_db)
        
        # 模拟会话数据
        self.sample_session = {
            'session_id': 1,
            'user_id': 1,
            'task_id': 1,
            'start_time': datetime.now(),
            'duration': 25,
            'is_completed': True,
            'session_type': 'work'
        }
    
    def test_start_session(self):
        """测试开始番茄钟会话"""
        # 模拟数据库返回
        self.mock_db.execute_query.return_value = 1
        
        # 调用开始会话
        session_id = self.pomodoro_manager.start_session(
            user_id=1,
            task_id=1,
            duration=25
        )
        
        # 验证结果
        self.assertEqual(session_id, 1)
        self.mock_db.execute_query.assert_called_once()
    
    def test_complete_session(self):
        """测试完成番茄钟会话"""
        # 模拟数据库操作
        self.mock_db.execute_query.return_value = 1
        
        # 调用完成会话
        result = self.pomodoro_manager.complete_session(
            session_id=1,
            actual_duration=25
        )
        
        # 验证结果
        self.assertTrue(result)
        self.mock_db.execute_query.assert_called_once()
    
    def test_get_user_sessions(self):
        """测试获取用户会话"""
        # 模拟数据库返回
        self.mock_db.fetch_all.return_value = [self.sample_session]
        
        # 调用获取会话
        sessions = self.pomodoro_manager.get_user_sessions(user_id=1)
        
        # 验证结果
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]['duration'], 25)
    
    def test_get_daily_stats(self):
        """测试获取每日统计"""
        # 模拟数据库返回
        mock_stats = {
            'total_sessions': 5,
            'total_duration': 125,
            'completed_sessions': 4
        }
        self.mock_db.fetch_one.return_value = mock_stats
        
        # 调用获取统计
        stats = self.pomodoro_manager.get_daily_stats(user_id=1)
        
        # 验证结果
        self.assertEqual(stats['total_sessions'], 5)
        self.assertEqual(stats['total_duration'], 125)
    
    def test_pause_session(self):
        """测试暂停会话"""
        # 模拟数据库操作
        self.mock_db.execute_query.return_value = 1
        
        # 调用暂停会话
        result = self.pomodoro_manager.pause_session(session_id=1)
        
        # 验证结果
        self.assertTrue(result)
        self.mock_db.execute_query.assert_called_once()
    
    def test_resume_session(self):
        """测试恢复会话"""
        # 模拟数据库操作
        self.mock_db.execute_query.return_value = 1
        
        # 调用恢复会话
        result = self.pomodoro_manager.resume_session(session_id=1)
        
        # 验证结果
        self.assertTrue(result)
        self.mock_db.execute_query.assert_called_once()
    
    def test_cancel_session(self):
        """测试取消会话"""
        # 模拟数据库操作
        self.mock_db.execute_query.return_value = 1
        
        # 调用取消会话
        result = self.pomodoro_manager.cancel_session(session_id=1)
        
        # 验证结果
        self.assertTrue(result)
        self.mock_db.execute_query.assert_called_once()
    
    @patch('src.services.pomodoro_manager.datetime')
    def test_get_weekly_stats(self, mock_datetime):
        """测试获取周统计"""
        # 模拟当前时间
        mock_datetime.now.return_value = datetime(2023, 12, 15, 10, 0, 0)
        
        # 模拟数据库返回
        mock_weekly_stats = [
            {'date': '2023-12-11', 'sessions': 3, 'duration': 75},
            {'date': '2023-12-12', 'sessions': 4, 'duration': 100}
        ]
        self.mock_db.fetch_all.return_value = mock_weekly_stats
        
        # 调用获取周统计
        stats = self.pomodoro_manager.get_weekly_stats(user_id=1)
        
        # 验证结果
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['sessions'], 3)


if __name__ == '__main__':
    unittest.main() 