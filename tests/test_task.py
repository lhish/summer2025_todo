"""
任务管理功能测试
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.task_manager import TaskManager
from src.database.database import DatabaseManager


class TestTaskManager(unittest.TestCase):
    """任务管理器测试类"""
    
    def setUp(self):
        """测试前的设置"""
        self.mock_db = Mock(spec=DatabaseManager)
        self.task_manager = TaskManager(self.mock_db)
        
        # 模拟任务数据
        self.sample_task = {
            'task_id': 1,
            'user_id': 1,
            'title': '测试任务',
            'description': '这是一个测试任务',
            'priority': 'medium',
            'is_completed': False,
            'created_at': datetime.now(),
            'due_date': date.today()
        }
    
    def test_create_task(self):
        """测试创建任务"""
        # 模拟数据库返回
        self.mock_db.execute_query.return_value = 1
        
        # 调用创建任务
        task_id = self.task_manager.create_task(
            user_id=1,
            title='新任务',
            description='任务描述',
            priority='high'
        )
        
        # 验证结果
        self.assertEqual(task_id, 1)
        self.mock_db.execute_query.assert_called_once()
    
    def test_get_user_tasks(self):
        """测试获取用户任务"""
        # 模拟数据库返回
        self.mock_db.fetch_all.return_value = [self.sample_task]
        
        # 调用获取任务
        tasks = self.task_manager.get_user_tasks(user_id=1)
        
        # 验证结果
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], '测试任务')
        self.mock_db.fetch_all.assert_called_once()
    
    def test_complete_task(self):
        """测试完成任务"""
        # 模拟数据库操作
        self.mock_db.execute_query.return_value = 1
        
        # 调用完成任务
        result = self.task_manager.complete_task(task_id=1)
        
        # 验证结果
        self.assertTrue(result)
        self.mock_db.execute_query.assert_called_once()
    
    def test_update_task(self):
        """测试更新任务"""
        # 模拟数据库操作
        self.mock_db.execute_query.return_value = 1
        
        # 调用更新任务
        result = self.task_manager.update_task(
            task_id=1,
            title='更新的任务',
            priority='high'
        )
        
        # 验证结果
        self.assertTrue(result)
        self.mock_db.execute_query.assert_called_once()
    
    def test_delete_task(self):
        """测试删除任务"""
        # 模拟数据库操作
        self.mock_db.execute_query.return_value = 1
        
        # 调用删除任务
        result = self.task_manager.delete_task(task_id=1)
        
        # 验证结果
        self.assertTrue(result)
        self.mock_db.execute_query.assert_called_once()
    
    def test_get_tasks_by_priority(self):
        """测试按优先级获取任务"""
        # 模拟数据库返回
        high_priority_task = self.sample_task.copy()
        high_priority_task['priority'] = 'high'
        self.mock_db.fetch_all.return_value = [high_priority_task]
        
        # 调用获取高优先级任务
        tasks = self.task_manager.get_tasks_by_priority(user_id=1, priority='high')
        
        # 验证结果
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['priority'], 'high')
    
    def test_get_overdue_tasks(self):
        """测试获取过期任务"""
        # 模拟过期任务
        overdue_task = self.sample_task.copy()
        overdue_task['due_date'] = date.today() - timedelta(days=1)
        self.mock_db.fetch_all.return_value = [overdue_task]
        
        # 调用获取过期任务
        tasks = self.task_manager.get_overdue_tasks(user_id=1)
        
        # 验证结果
        self.assertEqual(len(tasks), 1)
        self.mock_db.fetch_all.assert_called_once()
    
    def test_search_tasks(self):
        """测试搜索任务"""
        # 模拟数据库返回
        self.mock_db.fetch_all.return_value = [self.sample_task]
        
        # 调用搜索任务
        tasks = self.task_manager.search_tasks(user_id=1, keyword='测试')
        
        # 验证结果
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], '测试任务')


if __name__ == '__main__':
    unittest.main() 