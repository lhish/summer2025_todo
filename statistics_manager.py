from database import DatabaseManager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class StatisticsManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_focus_duration_by_period(self, user_id: int, period_type: str, 
                                   start_date: datetime, end_date: datetime) -> List[Dict]:
        """按指定周期聚合用户的专注时长数据，用于图表展示"""
        if period_type == 'daily':
            date_group = 'DATE(start_time)'
            date_format = '%Y-%m-%d'
        elif period_type == 'weekly':
            date_group = 'YEARWEEK(start_time, 1)'  # ISO周
            date_format = '%Y-%u'
        elif period_type == 'monthly':
            date_group = 'DATE_FORMAT(start_time, "%Y-%m")'
            date_format = '%Y-%m'
        else:
            logger.error(f"不支持的周期类型: {period_type}")
            return []
        
        query = f"""
        SELECT {date_group} as period, 
               SUM(duration_minutes) as total_minutes,
               COUNT(*) as session_count,
               AVG(duration_minutes) as avg_duration
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' AND is_completed = TRUE
        AND start_time >= %s AND start_time <= %s
        GROUP BY {date_group}
        ORDER BY period
        """
        
        result = self.db.execute_query(query, (user_id, start_date, end_date))
        return result if result else []
    
    def get_tasks_completed_by_period(self, user_id: int, period_type: str, 
                                    start_date: datetime, end_date: datetime) -> List[Dict]:
        """按指定周期聚合用户完成的任务数量，用于图表展示"""
        if period_type == 'daily':
            date_group = 'DATE(updated_at)'
        elif period_type == 'weekly':
            date_group = 'YEARWEEK(updated_at, 1)'
        elif period_type == 'monthly':
            date_group = 'DATE_FORMAT(updated_at, "%Y-%m")'
        else:
            logger.error(f"不支持的周期类型: {period_type}")
            return []
        
        query = f"""
        SELECT {date_group} as period,
               COUNT(*) as completed_count,
               SUM(used_pomodoros) as total_pomodoros_used
        FROM tasks 
        WHERE user_id = %s AND status = 'completed'
        AND updated_at >= %s AND updated_at <= %s
        GROUP BY {date_group}
        ORDER BY period
        """
        
        result = self.db.execute_query(query, (user_id, start_date, end_date))
        return result if result else []
    
    def get_productivity_overview(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """获取用户生产力概览数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        overview = {}
        
        # 专注时长统计
        query = """
        SELECT 
            SUM(CASE WHEN DATE(start_time) = CURDATE() THEN duration_minutes ELSE 0 END) as today_minutes,
            SUM(CASE WHEN start_time >= %s THEN duration_minutes ELSE 0 END) as period_minutes,
            COUNT(CASE WHEN DATE(start_time) = CURDATE() THEN 1 END) as today_sessions,
            COUNT(CASE WHEN start_time >= %s THEN 1 END) as period_sessions
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' AND is_completed = TRUE
        """
        result = self.db.execute_query(query, (start_date, start_date, user_id))
        if result:
            overview.update({
                'today_focus_minutes': result[0]['today_minutes'] or 0,
                'period_focus_minutes': result[0]['period_minutes'] or 0,
                'today_focus_sessions': result[0]['today_sessions'] or 0,
                'period_focus_sessions': result[0]['period_sessions'] or 0
            })
        
        # 任务完成统计
        query = """
        SELECT 
            COUNT(CASE WHEN DATE(updated_at) = CURDATE() THEN 1 END) as today_completed,
            COUNT(CASE WHEN updated_at >= %s THEN 1 END) as period_completed,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
            SUM(CASE WHEN DATE(updated_at) = CURDATE() THEN used_pomodoros ELSE 0 END) as today_pomodoros_used
        FROM tasks 
        WHERE user_id = %s
        """
        result = self.db.execute_query(query, (start_date, user_id))
        if result:
            overview.update({
                'today_completed_tasks': result[0]['today_completed'] or 0,
                'period_completed_tasks': result[0]['period_completed'] or 0,
                'pending_tasks': result[0]['pending_tasks'] or 0,
                'today_pomodoros_used': result[0]['today_pomodoros_used'] or 0
            })
        
        return overview
    
    def get_task_completion_rate(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """计算任务完成率"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
            AVG(CASE WHEN status = 'completed' THEN used_pomodoros END) as avg_pomodoros_per_task,
            AVG(CASE WHEN status = 'completed' 
                THEN used_pomodoros / NULLIF(estimated_pomodoros, 0) END) as estimation_accuracy
        FROM tasks 
        WHERE user_id = %s AND created_at >= %s
        """
        
        result = self.db.execute_query(query, (user_id, start_date))
        if result and result[0]['total_tasks']:
            data = result[0]
            completion_rate = (data['completed_tasks'] / data['total_tasks']) * 100
            return {
                'total_tasks': data['total_tasks'],
                'completed_tasks': data['completed_tasks'],
                'completion_rate': round(completion_rate, 1),
                'avg_pomodoros_per_task': round(data['avg_pomodoros_per_task'] or 0, 1),
                'estimation_accuracy': round((data['estimation_accuracy'] or 1) * 100, 1)
            }
        
        return {
            'total_tasks': 0,
            'completed_tasks': 0,
            'completion_rate': 0,
            'avg_pomodoros_per_task': 0,
            'estimation_accuracy': 100
        }
    
    def get_priority_distribution(self, user_id: int) -> List[Dict]:
        """获取任务优先级分布"""
        query = """
        SELECT 
            priority,
            COUNT(*) as task_count,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count
        FROM tasks 
        WHERE user_id = %s
        GROUP BY priority
        ORDER BY FIELD(priority, 'high', 'medium', 'low')
        """
        
        result = self.db.execute_query(query, (user_id,))
        return result if result else []
    
    def get_tag_performance(self, user_id: int, days: int = 30) -> List[Dict]:
        """获取标签相关的任务表现"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            COALESCE(tag, '无标签') as tag,
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
            SUM(CASE WHEN status = 'completed' THEN used_pomodoros ELSE 0 END) as total_pomodoros,
            AVG(CASE WHEN status = 'completed' THEN used_pomodoros END) as avg_pomodoros
        FROM tasks 
        WHERE user_id = %s AND created_at >= %s
        GROUP BY tag
        HAVING total_tasks > 0
        ORDER BY completed_tasks DESC
        """
        
        result = self.db.execute_query(query, (user_id, start_date))
        if result:
            for row in result:
                if row['total_tasks'] > 0:
                    row['completion_rate'] = round((row['completed_tasks'] / row['total_tasks']) * 100, 1)
                else:
                    row['completion_rate'] = 0
                row['avg_pomodoros'] = round(row['avg_pomodoros'] or 0, 1)
        
        return result if result else []
    
    def get_daily_pattern_analysis(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """分析用户的日常工作模式"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 按小时统计专注时间
        query = """
        SELECT 
            HOUR(start_time) as hour,
            COUNT(*) as session_count,
            SUM(duration_minutes) as total_minutes,
            AVG(duration_minutes) as avg_duration
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' AND is_completed = TRUE
        AND start_time >= %s
        GROUP BY HOUR(start_time)
        ORDER BY hour
        """
        
        hourly_data = self.db.execute_query(query, (user_id, start_date))
        
        # 按星期几统计
        query = """
        SELECT 
            DAYOFWEEK(start_time) as day_of_week,
            COUNT(*) as session_count,
            SUM(duration_minutes) as total_minutes
        FROM focus_sessions 
        WHERE user_id = %s AND session_type = 'work' AND is_completed = TRUE
        AND start_time >= %s
        GROUP BY DAYOFWEEK(start_time)
        ORDER BY day_of_week
        """
        
        weekly_data = self.db.execute_query(query, (user_id, start_date))
        
        # 转换星期几的数字为中文
        day_names = {1: '周日', 2: '周一', 3: '周二', 4: '周三', 5: '周四', 6: '周五', 7: '周六'}
        if weekly_data:
            for item in weekly_data:
                item['day_name'] = day_names.get(item['day_of_week'], '未知')
        
        return {
            'hourly_pattern': hourly_data if hourly_data else [],
            'weekly_pattern': weekly_data if weekly_data else []
        }
    
    def get_efficiency_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取效率趋势数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 每日效率数据
        query = """
        SELECT 
            DATE(fs.start_time) as date,
            COUNT(DISTINCT fs.session_id) as focus_sessions,
            SUM(fs.duration_minutes) as focus_minutes,
            COUNT(DISTINCT t.task_id) as tasks_worked_on,
            COUNT(CASE WHEN t.status = 'completed' 
                  AND DATE(t.updated_at) = DATE(fs.start_time) THEN 1 END) as tasks_completed
        FROM focus_sessions fs
        LEFT JOIN tasks t ON fs.task_id = t.task_id
        WHERE fs.user_id = %s AND fs.session_type = 'work' AND fs.is_completed = TRUE
        AND fs.start_time >= %s
        GROUP BY DATE(fs.start_time)
        ORDER BY date
        """
        
        daily_trends = self.db.execute_query(query, (user_id, start_date))
        
        # 计算效率指标
        if daily_trends:
            for day in daily_trends:
                # 每分钟完成任务数（简单的效率指标）
                if day['focus_minutes'] and day['focus_minutes'] > 0:
                    day['efficiency_score'] = round((day['tasks_completed'] / day['focus_minutes']) * 100, 2)
                else:
                    day['efficiency_score'] = 0
        
        return {
            'daily_trends': daily_trends if daily_trends else []
        }
    
    def generate_summary_report(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """生成综合汇总报告数据"""
        report = {}
        
        # 基础概览
        report['overview'] = self.get_productivity_overview(user_id, days)
        
        # 完成率分析
        report['completion_analysis'] = self.get_task_completion_rate(user_id, days)
        
        # 优先级分布
        report['priority_distribution'] = self.get_priority_distribution(user_id)
        
        # 标签表现
        report['tag_performance'] = self.get_tag_performance(user_id, days)
        
        # 工作模式分析
        report['pattern_analysis'] = self.get_daily_pattern_analysis(user_id, days)
        
        # 效率趋势
        report['efficiency_trends'] = self.get_efficiency_trends(user_id, days)
        
        # 报告生成时间
        report['generated_at'] = datetime.now().isoformat()
        report['period_days'] = days
        
        return report 