from src.database.database import DatabaseManager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PomodoroManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def start_focus_session(self, user_id: int, task_id: Optional[int] = None, 
                           session_type: str = 'work', duration_minutes: int = 25) -> Optional[int]:
        """开始一个新的专注或休息时段，并记录相关信息"""
        if session_type not in ['work', 'short_break', 'long_break']:
            logger.error(f"无效的会话类型: {session_type}")
            return None
        
        start_time = datetime.now()
        
        query = """
        INSERT INTO focus_sessions (user_id, task_id, session_type, start_time, duration_minutes)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (user_id, task_id, session_type, start_time, duration_minutes)
        
        if self.db.execute_update(query, params):
            session_id = self.db.get_last_insert_id()
            logger.info(f"开始{session_type}会话: ID {session_id}, 时长 {duration_minutes} 分钟")
            return session_id
        return None
    
    def complete_focus_session(self, session_id: int, end_time: datetime = None) -> bool:
        """标记一个专注或休息时段已完成，并更新相关数据"""
        if not end_time:
            end_time = datetime.now()
        
        # 更新会话记录
        query = "UPDATE focus_sessions SET end_time = %s, is_completed = TRUE WHERE session_id = %s"
        success = self.db.execute_update(query, (end_time, session_id))
        
        if success:
            # 如果是工作会话，更新关联任务的已使用番茄数
            session_info = self.get_session_by_id(session_id)
            if session_info and session_info['session_type'] == 'work' and session_info['task_id']:
                self.update_task_used_pomodoros(session_info['task_id'])
            
            logger.info(f"完成专注会话: ID {session_id}")
        
        return success
    
    def get_session_by_id(self, session_id: int) -> Optional[Dict]:
        """根据会话ID获取会话信息"""
        query = "SELECT * FROM focus_sessions WHERE session_id = %s"
        result = self.db.execute_query(query, (session_id,))
        return result[0] if result else None
    
    def update_task_used_pomodoros(self, task_id: int) -> bool:
        """更新任务已使用的番茄数"""
        query = "UPDATE tasks SET used_pomodoros = used_pomodoros + 1 WHERE task_id = %s"
        return self.db.execute_update(query, (task_id,))
    
    def get_pomodoro_records(self, user_id: int, date_range_start: datetime = None, 
                           date_range_end: datetime = None) -> List[Dict]:
        """查询并返回用户在指定时间范围内的专注记录"""
        query = """
        SELECT fs.*, t.title as task_title 
        FROM focus_sessions fs 
        LEFT JOIN tasks t ON fs.task_id = t.task_id 
        WHERE fs.user_id = %s
        """
        params = [user_id]
        
        if date_range_start:
            query += " AND fs.start_time >= %s"
            params.append(date_range_start)
        
        if date_range_end:
            query += " AND fs.start_time <= %s"
            params.append(date_range_end)
        
        query += " ORDER BY fs.start_time DESC"
        
        result = self.db.execute_query(query, tuple(params))
        return result if result else []
    
    def get_today_focus_duration(self, user_id: int) -> int:
        """计算用户今日的总专注时长（分钟）"""
        query = """
        SELECT SUM(duration_minutes) as total_minutes 
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' 
        AND DATE(start_time) = CURDATE() AND is_completed = TRUE
        """
        result = self.db.execute_query(query, (user_id,))
        return result[0]['total_minutes'] if result and result[0]['total_minutes'] else 0
    
    def get_weekly_focus_duration(self, user_id: int) -> int:
        """计算用户本周的总专注时长（分钟）"""
        query = """
        SELECT SUM(duration_minutes) as total_minutes 
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' 
        AND WEEK(start_time) = WEEK(CURDATE()) AND YEAR(start_time) = YEAR(CURDATE())
        AND is_completed = TRUE
        """
        result = self.db.execute_query(query, (user_id,))
        return result[0]['total_minutes'] if result and result[0]['total_minutes'] else 0
    
    def get_total_focus_duration(self, user_id: int) -> int:
        """计算用户总的专注时长（分钟）"""
        query = """
        SELECT SUM(duration_minutes) as total_minutes 
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' AND is_completed = TRUE
        """
        result = self.db.execute_query(query, (user_id,))
        return result[0]['total_minutes'] if result and result[0]['total_minutes'] else 0
    
    def get_focus_duration_by_period(self, user_id: int, period_type: str, 
                                   start_date: datetime, end_date: datetime) -> List[Dict]:
        """按指定周期聚合用户的专注时长数据，用于图表展示"""
        if period_type == 'daily':
            date_format = '%Y-%m-%d'
            date_group = 'DATE(start_time)'
        elif period_type == 'weekly':
            date_format = '%Y-%u'
            date_group = 'YEARWEEK(start_time)'
        elif period_type == 'monthly':
            date_format = '%Y-%m'
            date_group = 'DATE_FORMAT(start_time, "%Y-%m")'
        else:
            return []
        
        query = f"""
        SELECT {date_group} as period, 
               SUM(duration_minutes) as total_minutes,
               COUNT(*) as session_count
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' AND is_completed = TRUE
        AND start_time >= %s AND start_time <= %s
        GROUP BY {date_group}
        ORDER BY period
        """
        
        result = self.db.execute_query(query, (user_id, start_date, end_date))
        return result if result else []
    
    def get_completed_pomodoros_today(self, user_id: int) -> int:
        """获取今日完成的番茄钟数量"""
        query = """
        SELECT COUNT(*) as count 
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' 
        AND DATE(start_time) = CURDATE() AND is_completed = TRUE
        """
        result = self.db.execute_query(query, (user_id,))
        return result[0]['count'] if result else 0
    
    def get_completed_pomodoros_this_week(self, user_id: int) -> int:
        """获取本周完成的番茄钟数量"""
        query = """
        SELECT COUNT(*) as count 
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' 
        AND WEEK(start_time) = WEEK(CURDATE()) AND YEAR(start_time) = YEAR(CURDATE())
        AND is_completed = TRUE
        """
        result = self.db.execute_query(query, (user_id,))
        return result[0]['count'] if result else 0
    
    def get_active_session(self, user_id: int) -> Optional[Dict]:
        """获取用户当前活跃的会话"""
        query = """
        SELECT * FROM focus_sessions 
        WHERE user_id = %s AND is_completed = FALSE 
        ORDER BY start_time DESC LIMIT 1
        """
        result = self.db.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def cancel_session(self, session_id: int) -> bool:
        """取消/停止一个会话"""
        query = "UPDATE focus_sessions SET is_completed = TRUE, end_time = %s WHERE session_id = %s"
        success = self.db.execute_update(query, (datetime.now(), session_id))
        if success:
            logger.info(f"取消专注会话: ID {session_id}")
        return success

class UserSettingsManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_user_settings(self, user_id: int) -> Optional[Dict]:
        """获取指定用户的个人化系统设置"""
        query = "SELECT * FROM user_settings WHERE user_id = %s"
        result = self.db.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def update_user_settings(self, user_id: int, settings_data: Dict[str, Any]) -> bool:
        """更新用户的个人化系统设置"""
        valid_fields = [
            'pomodoro_work_duration', 'pomodoro_short_break_duration',
            'pomodoro_long_break_duration', 'pomodoro_long_break_interval',
            'notification_sound', 'auto_start_next_pomodoro',
            'auto_start_break', 'daily_focus_target_minutes'
        ]
        
        set_clauses = []
        params = []
        
        for field, value in settings_data.items():
            if field in valid_fields:
                set_clauses.append(f"{field} = %s")
                params.append(value)
        
        if not set_clauses:
            return False
        
        query = f"UPDATE user_settings SET {', '.join(set_clauses)} WHERE user_id = %s"
        params.append(user_id)
        
        success = self.db.execute_update(query, tuple(params))
        if success:
            logger.info(f"成功更新用户设置: {user_id}")
        return success
    
    def get_daily_focus_goal_progress(self, user_id: int) -> Dict[str, Any]:
        """计算用户每日专注目标的完成进度"""
        # 获取用户目标
        settings = self.get_user_settings(user_id)
        target_minutes = settings['daily_focus_target_minutes'] if settings else 120
        
        # 获取今日专注时长
        pomodoro_manager = PomodoroManager(self.db)
        today_minutes = pomodoro_manager.get_today_focus_duration(user_id)
        
        # 计算进度
        progress_percentage = min(100, (today_minutes / target_minutes * 100)) if target_minutes > 0 else 0
        
        return {
            'target_minutes': target_minutes,
            'completed_minutes': today_minutes,
            'progress_percentage': progress_percentage,
            'remaining_minutes': max(0, target_minutes - today_minutes)
        } 