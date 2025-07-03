#!/usr/bin/env python3
"""
任务管理模块
实现任务的创建、查询、更新、删除等核心功能
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import logging

from src.database.database import DatabaseManager, TagManager

logger = logging.getLogger(__name__)

class TaskManager:
    """任务管理类 - 实现文档5.2.1节详细设计"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.tag_manager = TagManager(db_manager)
    
    def create_task(self, 
                   user_id: int, 
                   title: str, 
                   description: str = None,
                   due_date: date = None,
                   priority: str = 'medium',
                   estimated_pomodoros: int = 1,
                   repeat_cycle: str = 'none',
                   tags: List[str] = None) -> Optional[int]:
        """
        创建任务
        
        Args:
            user_id: 用户ID
            title: 任务标题
            description: 任务描述
            due_date: 截止日期（只包含日期，不包含时间）
            priority: 优先级 (high, medium, low)
            estimated_pomodoros: 预估番茄钟数量
            repeat_cycle: 重复周期 (none, daily, weekly, monthly)
            tags: 标签列表
            
        Returns:
            任务ID，创建失败返回None
        """
        try:
            # 创建任务
            query = """
            INSERT INTO tasks (user_id, title, description, due_date, priority, estimated_pomodoros, repeat_cycle)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (user_id, title, description, due_date, priority, estimated_pomodoros, repeat_cycle)
            
            if self.db.execute_update(query, params):
                task_id = self.db.get_last_insert_id()
                
                # 添加标签
                if task_id and tags:
                    self._add_tags_to_task(task_id, user_id, tags)
                
                logger.info(f"任务创建成功: {title}")
                return task_id
            
            return None
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return None
    
    def get_tasks(self, 
                  user_id: int,
                  status: str = None,
                  priority: str = None,
                  tag_id: int = None,
                  due_date_filter: str = None,
                  search_query: str = None,
                  sort_by: str = 'created_at',
                  sort_order: str = 'DESC',
                  limit: int = None) -> List[Dict]:
        """
        查询任务列表
        
        Args:
            user_id: 用户ID
            status: 状态过滤 (pending, completed)
            priority: 优先级过滤 (high, medium, low)
            tag_id: 标签ID过滤
            due_date_filter: 截止日期过滤 (today, overdue, this_week, no_date)
            search_query: 搜索关键词
            sort_by: 排序字段
            sort_order: 排序顺序 (ASC, DESC)
            limit: 限制返回数量
            
        Returns:
            任务列表
        """
        try:
            # 构建基础查询
            query = """
            SELECT t.*
            FROM tasks t
            WHERE t.user_id = %s
            """
            
            params = [user_id]
            
            # 添加过滤条件
            if status:
                query += " AND t.status = %s"
                params.append(status)
            
            if priority:
                query += " AND t.priority = %s"
                params.append(priority)
                
            if tag_id:
                query += " AND t.task_id IN (SELECT task_id FROM task_tags WHERE tag_id = %s)"
                params.append(tag_id)
            
            # 截止日期过滤
            if due_date_filter:
                today = date.today()
                if due_date_filter == 'today':
                    query += " AND t.due_date = %s"
                    params.append(today)
                elif due_date_filter == 'overdue':
                    query += " AND t.due_date < %s AND t.status = 'pending'"
                    params.append(today)
                elif due_date_filter == 'this_week':
                    week_end = today + timedelta(days=7)
                    query += " AND t.due_date BETWEEN %s AND %s"
                    params.extend([today, week_end])
                elif due_date_filter == 'no_date':
                    query += " AND t.due_date IS NULL"
            
            # 搜索功能
            if search_query:
                query += " AND (t.title LIKE %s OR t.description LIKE %s)"
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param])
            
            # 排序
            valid_sort_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'title']
            if sort_by in valid_sort_fields:
                query += f" ORDER BY t.{sort_by} {sort_order}"
            else:
                query += " ORDER BY t.created_at DESC"
            
            # 限制数量
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            tasks = self.db.execute_query(query, tuple(params))
            
            # 为每个任务添加标签信息
            if tasks:
                for task in tasks:
                    task['tags'] = self.tag_manager.get_task_tags(task['task_id'])
            
            return tasks or []
            
        except Exception as e:
            logger.error(f"查询任务失败: {e}")
            return []
    
    def get_tasks_by_view(self, user_id: int, view_type: str) -> List[Dict]:
        """
        根据视图类型获取任务
        
        Args:
            user_id: 用户ID
            view_type: 视图类型 (my_day, planned, important, all)
            
        Returns:
            任务列表
        """
        today = date.today()
        
        if view_type == 'my_day':
            # 我的一天：今天到期的任务 + 过期未完成的任务
            return self.get_tasks(
                user_id=user_id,
                status='pending',
                due_date_filter='today'
            ) + self.get_tasks(
                user_id=user_id,
                status='pending',
                due_date_filter='overdue'
            )
        
        elif view_type == 'planned':
            # 计划内：有截止日期的任务
            query = """
            SELECT t.*
            FROM tasks t
            WHERE t.user_id = %s AND t.due_date IS NOT NULL
            ORDER BY t.due_date ASC
            """
            tasks = self.db.execute_query(query, (user_id,))
            
        elif view_type == 'important':
            # 重要：高优先级任务
            return self.get_tasks(
                user_id=user_id,
                priority='high',
                sort_by='due_date',
                sort_order='ASC'
            )
        
        elif view_type == 'all':
            # 所有任务
            return self.get_tasks(
                user_id=user_id,
                sort_by='created_at',
                sort_order='DESC'
            )
        
        else:
            return []
        
        # 为每个任务添加标签信息
        if tasks:
            for task in tasks:
                task['tags'] = self.tag_manager.get_task_tags(task['task_id'])
        
        return tasks or []
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """根据ID获取任务详情"""
        try:
            query = """
            SELECT t.*
            FROM tasks t
            WHERE t.task_id = %s
            """
            
            results = self.db.execute_query(query, (task_id,))
            if results:
                task = results[0]
                task['tags'] = self.tag_manager.get_task_tags(task_id)
                return task
            
            return None
            
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            return None
    
    def update_task(self, 
                   task_id: int,
                   title: str = None,
                   description: str = None,
                   due_date: date = None,
                   priority: str = None,
                   estimated_pomodoros: int = None,
                   repeat_cycle: str = None,
                   tags: List[str] = None) -> bool:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            title: 任务标题
            description: 任务描述
            due_date: 截止日期
            priority: 优先级
            estimated_pomodoros: 预估番茄钟数量
            repeat_cycle: 重复周期 (none, daily, weekly, monthly)
            tags: 标签列表
            
        Returns:
            更新是否成功
        """
        try:
            # 构建更新语句
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            
            if due_date is not None:
                updates.append("due_date = %s")
                params.append(due_date)
            
            if priority is not None:
                updates.append("priority = %s")
                params.append(priority)
            
            if estimated_pomodoros is not None:
                updates.append("estimated_pomodoros = %s")
                params.append(estimated_pomodoros)
            
# list_id 参数已移除
            
            if repeat_cycle is not None:
                updates.append("repeat_cycle = %s")
                params.append(repeat_cycle)
            
            if not updates and tags is None:
                return True
            
            # 更新任务基本信息
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(task_id)
                
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = %s"
                if not self.db.execute_update(query, tuple(params)):
                    return False
            
            # 更新标签
            if tags is not None:
                # 获取任务信息以获取user_id
                task = self.get_task_by_id(task_id)
                if task:
                    self._update_task_tags(task_id, task['user_id'], tags)
            
            logger.info(f"任务更新成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        try:
            query = "DELETE FROM tasks WHERE task_id = %s"
            success = self.db.execute_update(query, (task_id,))
            
            if success:
                logger.info(f"任务删除成功: {task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return False
    
    def toggle_task_status(self, task_id: int, status: str = None) -> bool:
        """切换任务状态"""
        try:
            if status is None:
                # 自动切换状态
                task = self.get_task_by_id(task_id)
                if not task:
                    return False
                
                status = 'completed' if task['status'] == 'pending' else 'pending'
            
            query = "UPDATE tasks SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE task_id = %s"
            success = self.db.execute_update(query, (status, task_id))
            
            if success:
                logger.info(f"任务状态更新成功: {task_id} -> {status}")
            
            return success
            
        except Exception as e:
            logger.error(f"切换任务状态失败: {e}")
            return False
    
    def increment_used_pomodoros(self, task_id: int) -> bool:
        """增加任务已使用的番茄钟数量"""
        try:
            query = """
            UPDATE tasks 
            SET used_pomodoros = used_pomodoros + 1, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = %s
            """
            return self.db.execute_update(query, (task_id,))
            
        except Exception as e:
            logger.error(f"更新番茄钟数量失败: {e}")
            return False
    
# complete_list_tasks 和 unlink_list_tasks 方法已移除 - 标签功能由 TagManager 提供
    
    def get_task_summary_stats(self, user_id: int) -> Dict[str, Any]:
        """获取任务统计摘要"""
        try:
            stats = {}
            
            # 总任务数
            query = "SELECT COUNT(*) as total FROM tasks WHERE user_id = %s"
            result = self.db.execute_query(query, (user_id,))
            stats['total_tasks'] = result[0]['total'] if result else 0
            
            # 待完成任务数
            query = "SELECT COUNT(*) as pending FROM tasks WHERE user_id = %s AND status = 'pending'"
            result = self.db.execute_query(query, (user_id,))
            stats['pending_tasks'] = result[0]['pending'] if result else 0
            
            # 已完成任务数
            query = "SELECT COUNT(*) as completed FROM tasks WHERE user_id = %s AND status = 'completed'"
            result = self.db.execute_query(query, (user_id,))
            stats['completed_tasks'] = result[0]['completed'] if result else 0
            
            # 今日完成任务数
            today = date.today()
            query = """
            SELECT COUNT(*) as today_completed 
            FROM tasks 
            WHERE user_id = %s AND status = 'completed' AND DATE(updated_at) = %s
            """
            result = self.db.execute_query(query, (user_id, today))
            stats['today_completed_tasks'] = result[0]['today_completed'] if result else 0
            
            # 过期任务数
            query = """
            SELECT COUNT(*) as overdue 
            FROM tasks 
            WHERE user_id = %s AND status = 'pending' AND due_date < %s
            """
            result = self.db.execute_query(query, (user_id, today))
            stats['overdue_tasks'] = result[0]['overdue'] if result else 0
            
            # 预计剩余时间（分钟）
            query = """
            SELECT SUM(estimated_pomodoros - used_pomodoros) as remaining_pomodoros
            FROM tasks 
            WHERE user_id = %s AND status = 'pending'
            """
            result = self.db.execute_query(query, (user_id,))
            remaining_pomodoros = result[0]['remaining_pomodoros'] if result and result[0]['remaining_pomodoros'] else 0
            stats['estimated_time_minutes'] = remaining_pomodoros * 25  # 每个番茄钟25分钟
            
            return stats
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}
    
    def _add_tags_to_task(self, task_id: int, user_id: int, tags: List[str]) -> bool:
        """为任务添加标签"""
        try:
            for tag_name in tags:
                if tag_name.strip():
                    tag_id = self.tag_manager.get_or_create_tag(user_id, tag_name.strip())
                    if tag_id:
                        self.tag_manager.add_task_tag(task_id, tag_id)
            return True
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False
    
    def _update_task_tags(self, task_id: int, user_id: int, tags: List[str]) -> bool:
        """更新任务标签"""
        try:
            # 清除现有标签
            self.tag_manager.clear_task_tags(task_id)
            
            # 添加新标签
            return self._add_tags_to_task(task_id, user_id, tags)
            
        except Exception as e:
            logger.error(f"更新标签失败: {e}")
            return False 