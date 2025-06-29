"""
统计功能测试
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, date
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.statistics_manager import StatisticsManager
from src.database.database import DatabaseManager


class TestStatisticsManager(unittest.TestCase):
    """统计管理器测试类"""
    
    def setUp(self):
        """测试前的设置"""
        self.mock_db = Mock(spec=DatabaseManager)
        self.stats_manager = StatisticsManager(self.mock_db)
    
    def test_get_task_completion_stats(self):
        """测试获取任务完成统计"""
        # 模拟数据库返回
        mock_stats = {
            'total_tasks': 100,
            'completed_tasks': 75,
            'completion_rate': 75.0
        }
        self.mock_db.fetch_one.return_value = mock_stats
        
        # 调用获取统计
        stats = self.stats_manager.get_task_completion_stats(user_id=1)
        
        # 验证结果
        self.assertEqual(stats['total_tasks'], 100)
        self.assertEqual(stats['completed_tasks'], 75)
        self.assertEqual(stats['completion_rate'], 75.0)
    
    def test_get_pomodoro_stats(self):
        """测试获取番茄钟统计"""
        # 模拟数据库返回
        mock_stats = {
            'total_sessions': 50,
            'total_focus_time': 1250,  # 分钟
            'average_session_length': 25
        }
        self.mock_db.fetch_one.return_value = mock_stats
        
        # 调用获取统计
        stats = self.stats_manager.get_pomodoro_stats(user_id=1)
        
        # 验证结果
        self.assertEqual(stats['total_sessions'], 50)
        self.assertEqual(stats['total_focus_time'], 1250)
    
    def test_get_productivity_trends(self):
        """测试获取生产力趋势"""
        # 模拟数据库返回
        mock_trends = [
            {'date': '2023-12-01', 'completed_tasks': 5, 'focus_time': 125},
            {'date': '2023-12-02', 'completed_tasks': 7, 'focus_time': 175},
            {'date': '2023-12-03', 'completed_tasks': 3, 'focus_time': 75}
        ]
        self.mock_db.fetch_all.return_value = mock_trends
        
        # 调用获取趋势
        trends = self.stats_manager.get_productivity_trends(user_id=1, days=7)
        
        # 验证结果
        self.assertEqual(len(trends), 3)
        self.assertEqual(trends[0]['completed_tasks'], 5)
    
    def test_get_category_distribution(self):
        """测试获取分类分布"""
        # 模拟数据库返回
        mock_distribution = [
            {'category': '工作', 'count': 40},
            {'category': '个人', 'count': 30},
            {'category': '学习', 'count': 20},
            {'category': '其他', 'count': 10}
        ]
        self.mock_db.fetch_all.return_value = mock_distribution
        
        # 调用获取分布
        distribution = self.stats_manager.get_category_distribution(user_id=1)
        
        # 验证结果
        self.assertEqual(len(distribution), 4)
        self.assertEqual(distribution[0]['category'], '工作')
        self.assertEqual(distribution[0]['count'], 40)
    
    def test_get_time_pattern_analysis(self):
        """测试获取时间模式分析"""
        # 模拟数据库返回
        mock_patterns = [
            {'hour': 9, 'task_count': 5, 'focus_time': 75},
            {'hour': 10, 'task_count': 8, 'focus_time': 100},
            {'hour': 14, 'task_count': 6, 'focus_time': 90}
        ]
        self.mock_db.fetch_all.return_value = mock_patterns
        
        # 调用获取模式分析
        patterns = self.stats_manager.get_time_pattern_analysis(user_id=1)
        
        # 验证结果
        self.assertEqual(len(patterns), 3)
        self.assertEqual(patterns[1]['hour'], 10)
        self.assertEqual(patterns[1]['task_count'], 8)
    
    def test_get_monthly_summary(self):
        """测试获取月度总结"""
        # 模拟数据库返回
        mock_summary = {
            'total_tasks': 150,
            'completed_tasks': 120,
            'total_focus_time': 3000,  # 分钟
            'total_sessions': 120,
            'best_day': '2023-12-15',
            'most_productive_hour': 10
        }
        self.mock_db.fetch_one.return_value = mock_summary
        
        # 调用获取月度总结
        summary = self.stats_manager.get_monthly_summary(user_id=1, year=2023, month=12)
        
        # 验证结果
        self.assertEqual(summary['total_tasks'], 150)
        self.assertEqual(summary['completed_tasks'], 120)
        self.assertEqual(summary['best_day'], '2023-12-15')
    
    def test_get_streak_info(self):
        """测试获取连续记录信息"""
        # 模拟数据库返回
        mock_streak = {
            'current_streak': 7,
            'longest_streak': 15,
            'total_active_days': 45
        }
        self.mock_db.fetch_one.return_value = mock_streak
        
        # 调用获取连续记录
        streak = self.stats_manager.get_streak_info(user_id=1)
        
        # 验证结果
        self.assertEqual(streak['current_streak'], 7)
        self.assertEqual(streak['longest_streak'], 15)
    
    def test_calculate_productivity_score(self):
        """测试计算生产力评分"""
        # 模拟各种统计数据
        with patch.object(self.stats_manager, 'get_task_completion_stats') as mock_task_stats, \
             patch.object(self.stats_manager, 'get_pomodoro_stats') as mock_pomodoro_stats, \
             patch.object(self.stats_manager, 'get_streak_info') as mock_streak:
            
            mock_task_stats.return_value = {'completion_rate': 80.0}
            mock_pomodoro_stats.return_value = {'total_focus_time': 500}
            mock_streak.return_value = {'current_streak': 10}
            
            # 调用计算生产力评分
            score = self.stats_manager.calculate_productivity_score(user_id=1)
            
            # 验证评分在合理范围内
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)


if __name__ == '__main__':
    unittest.main() 