"""
统计仪表板UI组件
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from nicegui import ui


class StatisticsDashboardComponent:
    """统计仪表板组件"""
    
    def __init__(self, statistics_manager, pomodoro_manager, current_user: Dict):
        self.statistics_manager = statistics_manager
        self.pomodoro_manager = pomodoro_manager
        self.current_user = current_user
    
    def create_stats_overview(self, user_id: int) -> ui.column:
        """创建统计概览"""
        stats = self.get_user_stats(user_id)
        
        with ui.column().classes('w-full gap-4') as container:
            ui.label('今日统计').classes('text-h6 text-primary')
            
            with ui.row().classes('w-full gap-4'):
                self.create_stat_card('完成任务', stats.get('completed_tasks', 0), 'task_alt', 'positive')
                self.create_stat_card('番茄钟', stats.get('pomodoro_sessions', 0), 'timer', 'secondary')
                self.create_stat_card('专注时间', f"{stats.get('focus_hours', 0):.1f}h", 'schedule', 'accent')
            
            # 本周趋势
            self.create_weekly_chart(user_id)
            
            # 任务分布
            self.create_task_distribution(user_id)
        
        return container
    
    def create_stat_card(self, title: str, value: str, icon: str, color: str):
        """创建统计卡片"""
        with ui.card().classes('flex-1 p-4'):
            with ui.row().classes('w-full items-center gap-3'):
                ui.icon(icon).classes(f'text-2xl text-{color}')
                with ui.column().classes('gap-1'):
                    ui.label(str(value)).classes('text-h5 font-bold')
                    ui.label(title).classes('text-caption text-grey-6')
    
    def create_weekly_chart(self, user_id: int):
        """创建本周趋势图表"""
        ui.label('本周趋势').classes('text-h6 text-primary mt-4 mb-2')
        
        # 获取本周数据
        weekly_data = self.get_weekly_data(user_id)
        
        # 使用简单的条形图显示
        with ui.card().classes('w-full p-4'):
            for day_data in weekly_data:
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    ui.label(day_data['day']).classes('w-16 text-sm')
                    
                    # 任务完成进度条
                    with ui.column().classes('flex-1'):
                        ui.linear_progress(
                            value=day_data['completed_tasks'] / max(day_data['total_tasks'], 1),
                            color='positive'
                        ).classes('w-full')
                        ui.label(f"{day_data['completed_tasks']}/{day_data['total_tasks']} 任务").classes('text-xs text-grey-6')
    
    def create_task_distribution(self, user_id: int):
        """创建任务分布图"""
        ui.label('任务分布').classes('text-h6 text-primary mt-4 mb-2')
        
        distribution = self.get_task_distribution(user_id)
        
        with ui.card().classes('w-full p-4'):
            for category, count in distribution.items():
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    ui.label(category).classes('w-20 text-sm')
                    ui.linear_progress(
                        value=count / max(sum(distribution.values()), 1),
                        color='primary'
                    ).classes('flex-1')
                    ui.label(str(count)).classes('text-sm text-grey-6')
    
    def get_user_stats(self, user_id: int) -> Dict:
        """获取用户统计数据"""
        if not self.statistics_manager:
            return {}
        
        today = date.today()
        
        # 获取今日完成的任务数
        completed_tasks = self.statistics_manager.get_completed_tasks_count(user_id, today)
        
        # 获取今日番茄钟会话数
        pomodoro_sessions = self.statistics_manager.get_pomodoro_sessions_count(user_id, today)
        
        # 获取今日专注时间
        focus_hours = self.statistics_manager.get_focus_time_hours(user_id, today)
        
        return {
            'completed_tasks': completed_tasks,
            'pomodoro_sessions': pomodoro_sessions,
            'focus_hours': focus_hours
        }
    
    def get_weekly_data(self, user_id: int) -> List[Dict]:
        """获取本周数据"""
        weekly_data = []
        today = date.today()
        
        for i in range(7):
            day = today - timedelta(days=6-i)
            day_name = day.strftime('%m/%d')
            
            if self.statistics_manager:
                completed = self.statistics_manager.get_completed_tasks_count(user_id, day)
                total = self.statistics_manager.get_total_tasks_count(user_id, day)
            else:
                completed = 0
                total = 0
            
            weekly_data.append({
                'day': day_name,
                'completed_tasks': completed,
                'total_tasks': total
            })
        
        return weekly_data
    
    def get_task_distribution(self, user_id: int) -> Dict[str, int]:
        """获取任务分布数据"""
        if not self.statistics_manager:
            return {'工作': 0, '个人': 0, '学习': 0, '其他': 0}
        
        return self.statistics_manager.get_task_distribution_by_category(user_id)

    def create_stats_bar(self, container, current_tasks: List[Dict]):
        """创建统计栏"""
        stats = self.get_view_stats(current_tasks)
        
        with container:
            with ui.row().classes('w-full gap-6 mb-6 p-4 bg-white rounded shadow-sm'):
                with ui.column().classes('text-center'):
                    ui.label(f"{stats['estimated_time']}分钟").classes('text-h6 font-bold text-blue-6')
                    ui.label('预计时间').classes('text-sm text-grey-6')
                
                with ui.column().classes('text-center'):
                    ui.label(str(stats['pending_tasks'])).classes('text-h6 font-bold text-orange-6')
                    ui.label('待完成任务').classes('text-sm text-grey-6')
                
                with ui.column().classes('text-center'):
                    ui.label(f"{stats['focus_time']}分钟").classes('text-h6 font-bold text-green-6')
                    ui.label('已专注时间').classes('text-sm text-grey-6')
                
                with ui.column().classes('text-center'):
                    ui.label(str(stats['completed_tasks'])).classes('text-h6 font-bold text-purple-6')
                    ui.label('已完成任务').classes('text-sm text-grey-6')

    def get_view_stats(self, current_tasks: List[Dict]) -> Dict:
        """获取当前视图的统计数据"""
        if not self.current_user:
            return {'estimated_time': 0, 'pending_tasks': 0, 'focus_time': 0, 'completed_tasks': 0}
        
        pending_tasks = [task for task in current_tasks if task['status'] == 'pending']
        completed_tasks = [task for task in current_tasks if task['status'] == 'completed']
        
        # 计算预计时间
        estimated_time = sum((task['estimated_pomodoros'] - task['used_pomodoros']) * 25 for task in pending_tasks)
        
        # 今日专注时间
        focus_time = self.pomodoro_manager.get_today_focus_duration(self.current_user['user_id'])
        
        return {
            'estimated_time': estimated_time,
            'pending_tasks': len(pending_tasks),
            'focus_time': focus_time,
            'completed_tasks': len(completed_tasks)
        } 