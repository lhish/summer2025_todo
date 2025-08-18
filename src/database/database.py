#!/usr/bin/env python3
"""
数据库管理模块
处理数据库连接、用户管理、标签管理等基础操作
"""

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                logger.info("成功连接到MySQL数据库")
        except Error as e:
            logger.error(f"连接数据库时发生错误: {e}")
            self.connection = None
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """执行查询并返回结果"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except Error as e:
            logger.error(f"执行查询时发生错误: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """执行更新操作"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"执行更新时发生错误: {e}")
            self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def get_last_insert_id(self) -> Optional[int]:
        """获取最后插入的ID"""
        if not self.connection or not self.connection.is_connected():
            return None
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT LAST_INSERT_ID()")
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            logger.error(f"获取插入ID时发生错误: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

# 用户管理相关函数
class UserManager:
    """用户管理类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """修改用户密码，返回详细的结果信息"""
        try:
            # 获取用户当前密码哈希
            user = self.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'user_not_found'}
            
            # 验证旧密码
            if not self.verify_password(old_password, user['password_hash']):
                return {'success': False, 'error': 'wrong_old_password'}
            
            # 检查新密码是否与旧密码相同
            if self.verify_password(new_password, user['password_hash']):
                return {'success': False, 'error': 'same_password'}
            
            # 生成新密码哈希
            new_password_hash = self.hash_password(new_password)
            
            # 更新数据库
            query = "UPDATE users SET password_hash = %s WHERE user_id = %s"
            update_success = self.db.execute_update(query, (new_password_hash, user_id))
            
            if update_success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'database_error'}
            
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            return {'success': False, 'error': 'exception', 'message': str(e)}
    
    def create_user(self, email: str, password: str) -> Optional[int]:
        """创建新用户"""
        # 检查邮箱是否已存在
        if self.get_user_by_email(email):
            return None
        
        password_hash = self.hash_password(password)
        query = "INSERT INTO users (email, password_hash) VALUES (%s, %s)"
        if self.db.execute_update(query, (email, password_hash)):
            user_id = self.db.get_last_insert_id()
            # 创建用户默认设置
            if user_id:
                self.create_default_settings(user_id)
            return user_id
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """通过邮箱获取用户信息"""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.db.execute_query(query, (email,))
        return result[0] if result else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """通过ID获取用户信息"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.db.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def create_default_settings(self, user_id: int) -> bool:
        """为新用户创建默认设置"""
        from config import DEFAULT_POMODORO_SETTINGS
        query = """
        INSERT INTO user_settings 
        (user_id, pomodoro_work_duration, pomodoro_short_break_duration, 
         pomodoro_long_break_duration, pomodoro_long_break_interval, 
         notification_sound, auto_start_next_pomodoro, auto_start_break, 
         daily_focus_target_minutes) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            user_id,
            DEFAULT_POMODORO_SETTINGS['work_duration'],
            DEFAULT_POMODORO_SETTINGS['short_break_duration'],
            DEFAULT_POMODORO_SETTINGS['long_break_duration'],
            DEFAULT_POMODORO_SETTINGS['long_break_interval'],
            DEFAULT_POMODORO_SETTINGS['notification_sound'],
            DEFAULT_POMODORO_SETTINGS['auto_start_next_pomodoro'],
            DEFAULT_POMODORO_SETTINGS['auto_start_break'],
            DEFAULT_POMODORO_SETTINGS['daily_focus_target_minutes']
        )
        return self.db.execute_update(query, params)

# ListManager 类已删除 - 功能已整合到 TagManager

class TagManager:
    """标签管理类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_tag(self, user_id: int, name: str, color: str = '#757575') -> Optional[int]:
        """创建标签"""
        # 验证标签名称长度
        if len(name) > 15:
            return None
        
        query = "INSERT INTO tags (user_id, name, color) VALUES (%s, %s, %s)"
        success = self.db.execute_update(query, (user_id, name, color))
        return self.db.get_last_insert_id() if success else None
    
    def get_user_tags(self, user_id: int) -> List[Dict]:
        """获取用户的所有标签"""
        query = "SELECT * FROM tags WHERE user_id = %s ORDER BY name"
        return self.db.execute_query(query, (user_id,))
    
    def get_user_tags_with_count(self, user_id: int) -> List[Dict]:
        """获取用户的所有标签（包含任务数量）"""
        query = """
        SELECT t.*, COUNT(tt.task_id) as task_count 
        FROM tags t 
        LEFT JOIN task_tags tt ON t.tag_id = tt.tag_id 
        LEFT JOIN tasks ts ON tt.task_id = ts.task_id AND ts.status = 'pending'
        WHERE t.user_id = %s 
        GROUP BY t.tag_id
        ORDER BY t.name
        """
        return self.db.execute_query(query, (user_id,))
    
    def get_tag_by_name(self, user_id: int, name: str) -> Optional[Dict]:
        """根据名称获取标签"""
        query = "SELECT * FROM tags WHERE user_id = %s AND name = %s"
        results = self.db.execute_query(query, (user_id, name))
        return results[0] if results else None
    
    def get_or_create_tag(self, user_id: int, name: str, color: str = '#757575') -> Optional[int]:
        """获取或创建标签"""
        # 验证标签名称长度
        if len(name) > 15:
            return None
            
        existing_tag = self.get_tag_by_name(user_id, name)
        if existing_tag:
            return existing_tag['tag_id']
        return self.create_tag(user_id, name, color)
    
    def get_task_tags(self, task_id: int) -> List[Dict]:
        """获取任务的所有标签"""
        query = """
        SELECT t.* FROM tags t
        JOIN task_tags tt ON t.tag_id = tt.tag_id
        WHERE tt.task_id = %s
        ORDER BY t.name
        """
        return self.db.execute_query(query, (task_id,))
    
    def add_task_tag(self, task_id: int, tag_id: int) -> bool:
        """为任务添加标签"""
        query = "INSERT IGNORE INTO task_tags (task_id, tag_id) VALUES (%s, %s)"
        return self.db.execute_update(query, (task_id, tag_id))
    
    def remove_task_tag(self, task_id: int, tag_id: int) -> bool:
        """移除任务标签"""
        query = "DELETE FROM task_tags WHERE task_id = %s AND tag_id = %s"
        return self.db.execute_update(query, (task_id, tag_id))
    
    def clear_task_tags(self, task_id: int) -> bool:
        """清除任务的所有标签"""
        query = "DELETE FROM task_tags WHERE task_id = %s"
        return self.db.execute_update(query, (task_id,))
    
    def update_tag(self, tag_id: int, name: str = None, color: str = None) -> bool:
        """更新标签"""
        updates = []
        params = []
        
        if name is not None:
            # 验证标签名称长度
            if len(name) > 15:
                return False
            updates.append("name = %s")
            params.append(name)
        
        if color is not None:
            updates.append("color = %s")
            params.append(color)
        
        if not updates:
            return True
        
        params.append(tag_id)
        query = f"UPDATE tags SET {', '.join(updates)} WHERE tag_id = %s"
        return self.db.execute_update(query, tuple(params))
    
    def delete_tag(self, tag_id: int) -> bool:
        """删除标签"""
        query = "DELETE FROM tags WHERE tag_id = %s"
        return self.db.execute_update(query, (tag_id,))
    
    def get_tag_by_id(self, tag_id: int) -> Optional[Dict]:
        """根据ID获取标签"""
        query = "SELECT * FROM tags WHERE tag_id = %s"
        results = self.db.execute_query(query, (tag_id,))
        return results[0] if results else None
    
    def complete_tag_tasks(self, tag_id: int) -> bool:
        """完成标签下的所有任务"""
        query = """
        UPDATE tasks 
        SET status = 'completed' 
        WHERE task_id IN (
            SELECT task_id FROM task_tags WHERE tag_id = %s
        ) AND status = 'pending'
        """
        return self.db.execute_update(query, (tag_id,))