"""
统计仪表板UI组件
"""
from datetime import datetime, date, timedelta
from typing import Dict, List
from nicegui import ui
import json


class StatisticsDashboardComponent:
    """统计仪表板组件"""
    
    def __init__(self, statistics_manager, pomodoro_manager, current_user: Dict):
        self.statistics_manager = statistics_manager
        self.pomodoro_manager = pomodoro_manager
        self.current_user = current_user
    
    def create_stats_overview(self, user_id: int) -> ui.column:
        """创建统计概览"""
        stats = self.get_today_detailed_stats(user_id)
        
        with ui.column().classes('w-full gap-4') as container:
            # 今日统计标题
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label('今日统计').classes('text-h6 text-primary font-bold')
                ui.label(datetime.now().strftime('%Y年%m月%d日')).classes('text-sm text-grey-6')
            
            # 今日任务统计卡片
            with ui.row().classes('w-full gap-3 mb-4'):
                # 应完成任务
                self.create_detailed_stat_card(
                    '应完成任务', 
                    stats['today_due_tasks'], 
                    'event', 
                    'blue',
                    '截止今天的任务'
                )
                # 实际完成
                self.create_detailed_stat_card(
                    '实际完成', 
                    stats['today_completed_due'], 
                    'check_circle', 
                    'positive',
                    f"完成率 {stats['completion_rate']:.1f}%"
                )
                # 额外完成
                self.create_detailed_stat_card(
                    '额外完成', 
                    stats['extra_completed'], 
                    'add_task', 
                    'purple',
                    '其他任务'
                )
            
            # 工作效率统计
            with ui.row().classes('w-full gap-3 mb-4'):
                self.create_detailed_stat_card(
                    '专注时长', 
                    f"{stats['focus_hours']:.1f}h", 
                    'schedule', 
                    'orange',
                    f"{stats['pomodoro_sessions']} 个番茄钟"
                )
                self.create_detailed_stat_card(
                    '完成率', 
                    f"{stats['avg_efficiency']:.1f}%", 
                    'trending_up', 
                    'teal',
                    '应完成任务的完成率'
                )
            
            # 图表区域
            self.create_charts_section(user_id)
        
        return container
    
    def create_detailed_stat_card(self, title: str, value, icon: str, color: str, subtitle: str = ''):
        """创建详细统计卡片"""
        with ui.card().classes('flex-1 p-4 min-h-28'):
            with ui.column().classes('w-full h-full justify-between gap-2'):
                # 顶部图标和标题
                with ui.row().classes('w-full items-center justify-between'):
                    ui.icon(icon).classes(f'text-xl text-{color}')
                    ui.label(title).classes('text-sm text-grey-7 font-medium')
                
                # 数值
                ui.label(str(value)).classes(f'text-2xl font-bold text-{color}')
                
                # 副标题
                if subtitle:
                    ui.label(subtitle).classes('text-xs text-grey-5')
    
    def create_charts_section(self, user_id: int):
        """创建图表区域"""
        ui.label('数据分析').classes('text-h6 text-primary font-bold mb-3')
        
        # 图表容器
        with ui.row().classes('w-full gap-4'):
            # 左列：本周完成趋势
            with ui.column().classes('flex-1'):
                self.create_weekly_completion_chart(user_id)
            
            # 右列：任务优先级分布
            with ui.column().classes('flex-1'):
                self.create_priority_distribution_chart(user_id)
        
        # 第二行图表
        with ui.row().classes('w-full gap-4 mt-4'):
            # 专注时长趋势
            with ui.column().classes('flex-1'):
                self.create_focus_time_chart(user_id)
            
            # 任务状态分布
            with ui.column().classes('flex-1'):
                self.create_task_status_chart(user_id)
        
        # 第三行图表：每月任务趋势和每日任务创建与完成
        with ui.row().classes('w-full gap-4 mt-4'):
            with ui.column().classes('flex-1'):
                self.create_monthly_task_chart(user_id)
            
            with ui.column().classes('flex-1'):
                self.create_daily_creation_completion_chart(user_id)
    
    def create_weekly_completion_chart(self, user_id: int):
        """创建本周完成趋势图"""
        weekly_data = self.get_weekly_completion_data(user_id)
        
        with ui.card().classes('w-full p-4'):
            ui.label('本周完成趋势').classes('text-h6 mb-3')
            
            # 使用 ECharts 创建折线图
            chart_data = {
                'xAxis': {
                    'type': 'category',
                    'data': [item['day'] for item in weekly_data]
                },
                'yAxis': {
                    'type': 'value'
                },
                'series': [
                    {
                        'name': '应完成',
                        'type': 'line',
                        'data': [item['due_tasks'] for item in weekly_data],
                        'itemStyle': {'color': '#1976d2'}
                    },
                    {
                        'name': '实际完成',
                        'type': 'line',
                        'data': [item['completed_tasks'] for item in weekly_data],
                        'itemStyle': {'color': '#388e3c'}
                    }
                ],
                'legend': {
                    'data': ['应完成', '实际完成']
                },
                'tooltip': {
                    'trigger': 'axis'
                }
            }
            
            ui.echart(chart_data).classes('w-full h-48')
    
    def create_priority_distribution_chart(self, user_id: int):
        """创建任务优先级分布图"""
        priority_data = self.get_priority_distribution_data(user_id)
        
        with ui.card().classes('w-full p-4'):
            ui.label('任务优先级分布').classes('text-h6 mb-3')
            
            chart_data = {
                'tooltip': {
                    'trigger': 'item'
                },
                'series': [
                    {
                        'type': 'pie',
                        'radius': '60%',
                        'data': [
                            {'value': priority_data['high'], 'name': '高优先级', 'itemStyle': {'color': '#f44336'}},
                            {'value': priority_data['medium'], 'name': '中优先级', 'itemStyle': {'color': '#ff9800'}},
                            {'value': priority_data['low'], 'name': '低优先级', 'itemStyle': {'color': '#4caf50'}}
                        ]
                    }
                ]
            }
            
            ui.echart(chart_data).classes('w-full h-48')
    
    def create_focus_time_chart(self, user_id: int):
        """创建专注时长趋势图"""
        focus_data = self.get_weekly_focus_data(user_id)
        
        with ui.card().classes('w-full p-4'):
            ui.label('本周专注时长').classes('text-h6 mb-3')
            
            chart_data = {
                'xAxis': {
                    'type': 'category',
                    'data': [item['day'] for item in focus_data]
                },
                'yAxis': {
                    'type': 'value',
                    'name': '小时'
                },
                'series': [
                    {
                        'type': 'bar',
                        'data': [item['hours'] for item in focus_data],
                        'itemStyle': {'color': '#2196f3'}
                    }
                ],
                'tooltip': {
                    'trigger': 'axis',
                    'formatter': '{b}: {c} 小时'
                }
            }
            
            ui.echart(chart_data).classes('w-full h-48')
    
    def create_task_status_chart(self, user_id: int):
        """创建任务状态分布图"""
        status_data = self.get_task_status_data(user_id)
        
        with ui.card().classes('w-full p-4'):
            ui.label('任务状态分布').classes('text-h6 mb-3')
            
            chart_data = {
                'tooltip': {
                    'trigger': 'item'
                },
                'series': [
                    {
                        'type': 'pie',
                        'radius': ['40%', '70%'],
                        'data': [
                            {'value': status_data['completed'], 'name': '已完成', 'itemStyle': {'color': '#4caf50'}},
                            {'value': status_data['pending'], 'name': '待完成', 'itemStyle': {'color': '#ff9800'}},
                            {'value': status_data['in_progress'], 'name': '进行中', 'itemStyle': {'color': '#2196f3'}}
                        ]
                    }
                ]
            }
            
            ui.echart(chart_data).classes('w-full h-48')

    def get_today_detailed_stats(self, user_id: int) -> Dict:
        """获取今日详细统计数据"""
        if not self.statistics_manager:
            return self._get_default_stats()
        
        try:
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # 查询今日应完成的任务（截止日期是今天或之前且还未完成）
            today_due_query = """
            SELECT COUNT(*) as count
            FROM tasks 
            WHERE user_id = %s 
            AND due_date IS NOT NULL
            AND DATE(due_date) <= %s
            AND (status = 'pending' OR status = 'in_progress' OR 
                 (status = 'completed' AND DATE(updated_at) = %s))
            """
            today_due_result = self.statistics_manager.db.execute_query(
                today_due_query, (user_id, today, today)
            )
            today_due_tasks = today_due_result[0]['count'] if today_due_result else 0
            
            # 查询今日完成的应完成任务（截止日期是今天或之前，且今天完成）
            today_completed_due_query = """
            SELECT COUNT(*) as count
            FROM tasks 
            WHERE user_id = %s 
            AND due_date IS NOT NULL
            AND DATE(due_date) <= %s
            AND status = 'completed'
            AND DATE(updated_at) = %s
            """
            completed_due_result = self.statistics_manager.db.execute_query(
                today_completed_due_query, (user_id, today, today)
            )
            today_completed_due = completed_due_result[0]['count'] if completed_due_result else 0
            
            # 查询今日额外完成的任务（没有截止日期或截止日期在今天之后，但今天完成的）
            extra_completed_query = """
            SELECT COUNT(*) as count
            FROM tasks 
            WHERE user_id = %s 
            AND status = 'completed'
            AND DATE(updated_at) = %s
            AND (due_date IS NULL OR DATE(due_date) > %s)
            """
            extra_completed_result = self.statistics_manager.db.execute_query(
                extra_completed_query, (user_id, today, today)
            )
            extra_completed = extra_completed_result[0]['count'] if extra_completed_result else 0
            
            # 重新计算应完成任务数（只计算截止日期是今天或之前的未完成任务）
            actual_due_query = """
            SELECT COUNT(*) as count
            FROM tasks 
            WHERE user_id = %s 
            AND due_date IS NOT NULL
            AND DATE(due_date) <= %s
            AND status != 'completed'
            """
            actual_due_result = self.statistics_manager.db.execute_query(
                actual_due_query, (user_id, today)
            )
            actual_due_tasks = actual_due_result[0]['count'] if actual_due_result else 0
            
            # 总的应完成任务数 = 未完成的 + 今天完成的
            total_due_tasks = actual_due_tasks + today_completed_due
            
            # 计算完成率
            completion_rate = (today_completed_due / max(total_due_tasks, 1)) * 100 if total_due_tasks > 0 else 0
            
            # 获取专注时长数据
            focus_minutes = self.pomodoro_manager.get_today_focus_duration(user_id)
            focus_hours = focus_minutes / 60
            
            # 获取番茄钟数量
            pomodoro_sessions = self._get_today_pomodoro_sessions(user_id)
            
            # 计算平均效率
            avg_efficiency = self._calculate_avg_efficiency(user_id, today)
            
            return {
                'today_due_tasks': total_due_tasks,
                'today_completed_due': today_completed_due,
                'extra_completed': extra_completed,
                'completion_rate': completion_rate,
                'focus_hours': focus_hours,
                'pomodoro_sessions': pomodoro_sessions,
                'avg_efficiency': avg_efficiency
            }
            
        except Exception as e:
            print(f"Error getting today stats: {e}")
            return self._get_default_stats()
    
    def _get_default_stats(self) -> Dict:
        """获取默认统计数据"""
        return {
            'today_due_tasks': 0,
            'today_completed_due': 0,
            'extra_completed': 0,
            'completion_rate': 0.0,
            'focus_hours': 0.0,
            'pomodoro_sessions': 0,
            'avg_efficiency': 0.0
        }
    
    def _get_today_pomodoro_sessions(self, user_id: int) -> int:
        """获取今日番茄钟数量"""
        try:
            # 检查表是否存在
            check_table_query = """
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'pomodoro_sessions'
            """
            table_result = self.statistics_manager.db.execute_query(check_table_query)
            
            if not table_result or table_result[0]['count'] == 0:
                # 表不存在，返回0
                return 0
            
            today = date.today()
            query = """
            SELECT COUNT(*) as count
            FROM pomodoro_sessions 
            WHERE user_id = %s 
            AND DATE(start_time) = %s
            AND status = 'completed'
            """
            result = self.statistics_manager.db.execute_query(query, (user_id, today))
            return result[0]['count'] if result else 0
        except Exception as e:
            print(f"Error getting pomodoro sessions: {e}")
            return 0
    
    def _calculate_avg_efficiency(self, user_id: int, target_date: date) -> float:
        """计算平均效率"""
        try:
            # 获取今日应完成任务总数
            total_due_query = """
            SELECT COUNT(*) as count
            FROM tasks 
            WHERE user_id = %s 
            AND due_date IS NOT NULL
            AND DATE(due_date) <= %s
            AND (status != 'completed' OR 
                 (status = 'completed' AND DATE(updated_at) = %s))
            """
            total_due_result = self.statistics_manager.db.execute_query(
                total_due_query, (user_id, target_date, target_date)
            )
            total_due_tasks = total_due_result[0]['count'] if total_due_result else 0
            
            # 获取今日完成的应完成任务数
            completed_due_query = """
            SELECT COUNT(*) as count
            FROM tasks 
            WHERE user_id = %s 
            AND due_date IS NOT NULL
            AND DATE(due_date) <= %s
            AND status = 'completed'
            AND DATE(updated_at) = %s
            """
            completed_due_result = self.statistics_manager.db.execute_query(
                completed_due_query, (user_id, target_date, target_date)
            )
            completed_due_tasks = completed_due_result[0]['count'] if completed_due_result else 0
            
            # 效率 = 完成的应完成任务数 / 总应完成任务数 * 100%
            if total_due_tasks == 0:
                return 0.0
            
            efficiency = (completed_due_tasks / total_due_tasks) * 100
            return round(efficiency, 1)
        except Exception as e:
            print(f"Error calculating efficiency: {e}")
            return 0.0

    def get_weekly_completion_data(self, user_id: int) -> List[Dict]:
        """获取本周完成趋势数据"""
        weekly_data = []
        today = date.today()
        
        for i in range(7):
            target_date = today - timedelta(days=6-i)
            day_name = target_date.strftime('%m/%d')
            
            try:
                # 获取该日应完成任务数（截止日期是该日或之前的总任务数）
                # 如果是历史日期，包括当天完成和未完成的
                # 如果是今天或未来，只计算未完成的
                if target_date <= today:
                    due_query = """
                    SELECT COUNT(*) as count
                    FROM tasks 
                    WHERE user_id = %s 
                    AND due_date IS NOT NULL
                    AND DATE(due_date) <= %s
                    AND (status != 'completed' OR 
                         (status = 'completed' AND DATE(updated_at) = %s))
                    """
                    due_result = self.statistics_manager.db.execute_query(
                        due_query, (user_id, target_date, target_date)
                    )
                else:
                    due_query = """
                    SELECT COUNT(*) as count
                    FROM tasks 
                    WHERE user_id = %s 
                    AND due_date IS NOT NULL
                    AND DATE(due_date) <= %s
                    AND status != 'completed'
                    """
                    due_result = self.statistics_manager.db.execute_query(
                        due_query, (user_id, target_date)
                    )
                
                due_tasks = due_result[0]['count'] if due_result else 0
                
                # 获取该日完成的应完成任务数（截止日期是该日或之前，且该日完成）
                completed_due_query = """
                SELECT COUNT(*) as count
                FROM tasks 
                WHERE user_id = %s 
                AND due_date IS NOT NULL
                AND DATE(due_date) <= %s
                AND status = 'completed'
                AND DATE(updated_at) = %s
                """
                completed_result = self.statistics_manager.db.execute_query(
                    completed_due_query, (user_id, target_date, target_date)
                )
                completed_tasks = completed_result[0]['count'] if completed_result else 0
                
                weekly_data.append({
                    'day': day_name,
                    'due_tasks': due_tasks,
                    'completed_tasks': completed_tasks
                })
            except Exception as e:
                print(f"Error getting weekly data for {target_date}: {e}")
                weekly_data.append({
                    'day': day_name,
                    'due_tasks': 0,
                    'completed_tasks': 0
                })
        
        return weekly_data

    def get_priority_distribution_data(self, user_id: int) -> Dict:
        """获取任务优先级分布数据"""
        try:
            query = """
            SELECT priority, COUNT(*) as count
            FROM tasks 
            WHERE user_id = %s AND status != 'completed'
            GROUP BY priority
            """
            result = self.statistics_manager.db.execute_query(query, (user_id,))
            
            priority_data = {'high': 0, 'medium': 0, 'low': 0}
            for row in result:
                priority_data[row['priority']] = row['count']
            
            return priority_data
        except:
            return {'high': 0, 'medium': 0, 'low': 0}

    def get_weekly_focus_data(self, user_id: int) -> List[Dict]:
        """获取本周专注时长数据"""
        weekly_data = []
        today = date.today()
        
        # 检查表是否存在
        try:
            check_table_query = """
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'pomodoro_sessions'
            """
            table_result = self.statistics_manager.db.execute_query(check_table_query)
            table_exists = table_result and table_result[0]['count'] > 0
        except:
            table_exists = False
        
        for i in range(7):
            target_date = today - timedelta(days=6-i)
            day_name = target_date.strftime('%m/%d')
            
            if table_exists:
                try:
                    query = """
                    SELECT COALESCE(SUM(actual_duration), 0) as total_minutes
                    FROM pomodoro_sessions 
                    WHERE user_id = %s 
                    AND DATE(start_time) = %s
                    AND status = 'completed'
                    """
                    result = self.statistics_manager.db.execute_query(
                        query, (user_id, target_date)
                    )
                    total_minutes = result[0]['total_minutes'] if result else 0
                    hours = round(total_minutes / 60, 1)
                except:
                    hours = 0
            else:
                # 表不存在，使用番茄钟管理器的方法
                try:
                    if target_date == today:
                        minutes = self.pomodoro_manager.get_today_focus_duration(user_id)
                        hours = round(minutes / 60, 1)
                    else:
                        hours = 0  # 历史数据无法获取
                except:
                    hours = 0
            
            weekly_data.append({
                'day': day_name,
                'hours': hours
            })
        
        return weekly_data

    def get_task_status_data(self, user_id: int) -> Dict:
        """获取任务状态分布数据"""
        try:
            query = """
            SELECT status, COUNT(*) as count
            FROM tasks 
            WHERE user_id = %s
            GROUP BY status
            """
            result = self.statistics_manager.db.execute_query(query, (user_id,))
            
            status_data = {'completed': 0, 'pending': 0, 'in_progress': 0}
            for row in result:
                if row['status'] in status_data:
                    status_data[row['status']] = row['count']
            
            return status_data
        except:
            return {'completed': 0, 'pending': 0, 'in_progress': 0}

    def get_monthly_task_data(self, user_id: int) -> List[Dict]:
        """获取每月任务创建和完成数据"""
        monthly_data = []
        today = date.today()
        # 获取过去12个月的数据
        for i in range(12):
            target_month = today.replace(day=1) - timedelta(days=30 * i) # 近似一个月
            month_start = target_month.replace(day=1)
            next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = next_month - timedelta(days=1)

            month_label = target_month.strftime('%Y年%m月')

            try:
                # 查询当月创建的任务数
                created_query = """
                SELECT COUNT(*) as count
                FROM tasks
                WHERE user_id = %s
                AND DATE(created_at) >= %s
                AND DATE(created_at) <= %s
                """
                created_result = self.statistics_manager.db.execute_query(
                    created_query, (user_id, month_start, month_end)
                )
                created_tasks = created_result[0]['count'] if created_result else 0

                # 查询当月完成的任务数
                completed_query = """
                SELECT COUNT(*) as count
                FROM tasks
                WHERE user_id = %s
                AND status = 'completed'
                AND DATE(updated_at) >= %s
                AND DATE(updated_at) <= %s
                """
                completed_result = self.statistics_manager.db.execute_query(
                    completed_query, (user_id, month_start, month_end)
                )
                completed_tasks = completed_result[0]['count'] if completed_result else 0

                monthly_data.append({
                    'month': month_label,
                    'created_tasks': created_tasks,
                    'completed_tasks': completed_tasks
                })
            except Exception as e:
                print(f"Error getting monthly data for {month_label}: {e}")
                monthly_data.append({
                    'month': month_label,
                    'created_tasks': 0,
                    'completed_tasks': 0
                })
        return list(reversed(monthly_data)) # 反转列表，使月份按时间顺序排列

    def create_monthly_task_chart(self, user_id: int):
        """创建每月任务创建和完成趋势图"""
        monthly_data = self.get_monthly_task_data(user_id)

        with ui.card().classes('w-full p-4'):
            ui.label('每月任务趋势').classes('text-h6 mb-3')

            chart_data = {
                'xAxis': {
                    'type': 'category',
                    'data': [item['month'] for item in monthly_data]
                },
                'yAxis': {
                    'type': 'value',
                    'name': '任务数'
                },
                'series': [
                    {
                        'name': '创建任务',
                        'type': 'line',
                        'data': [item['created_tasks'] for item in monthly_data],
                        'itemStyle': {'color': '#673ab7'} # Deep Purple
                    },
                    {
                        'name': '完成任务',
                        'type': 'line',
                        'data': [item['completed_tasks'] for item in monthly_data],
                        'itemStyle': {'color': '#009688'} # Teal
                    }
                ],
                'legend': {
                    'data': ['创建任务', '完成任务']
                },
                'tooltip': {
                    'trigger': 'axis'
                }
            }

            ui.echart(chart_data).classes('w-full h-48')

    def get_weekly_data(self, user_id: int) -> List[Dict]:
        """获取本周数据"""
        weekly_data = []
        today = date.today()
        
        for i in range(7):
            day = today - timedelta(days=6-i)
            day_name = day.strftime('%m/%d')
            
            if self.statistics_manager:
                # 使用 get_tasks_completed_by_period 方法获取每日数据
                start_date = datetime.combine(day, datetime.min.time())
                end_date = datetime.combine(day, datetime.max.time())
                
                completed_data = self.statistics_manager.get_tasks_completed_by_period(
                    user_id, 'daily', start_date, end_date
                )
                
                # 获取总任务数（需要单独查询）
                total_query = """
                SELECT COUNT(*) as total_count
                FROM tasks
                WHERE user_id = %s AND DATE(created_at) = %s
                """
                total_result = self.statistics_manager.db.execute_query(total_query, (user_id, day))
                total_tasks = total_result[0]['total_count'] if total_result else 0
                
                completed_tasks = completed_data[0]['completed_count'] if completed_data else 0
            else:
                completed_tasks = 0
                total_tasks = 0
            
            weekly_data.append({
                'day': day_name,
                'completed_tasks': completed_tasks,
                'total_tasks': total_tasks
            })
        
        return weekly_data

    def create_daily_creation_completion_chart(self, user_id: int):
        """创建每日任务创建和完成对比图"""
        daily_data = self.get_weekly_data(user_id) # 复用 get_weekly_data

        with ui.card().classes('w-full p-4'):
            ui.label('每日任务创建与完成').classes('text-h6 mb-3')

            chart_data = {
                'xAxis': {
                    'type': 'category',
                    'data': [item['day'] for item in daily_data]
                },
                'yAxis': {
                    'type': 'value',
                    'name': '任务数'
                },
                'series': [
                    {
                        'name': '创建任务',
                        'type': 'bar',
                        'data': [item['total_tasks'] for item in daily_data],
                        'itemStyle': {'color': '#42a5f5'} # Blue
                    },
                    {
                        'name': '完成任务',
                        'type': 'bar',
                        'data': [item['completed_tasks'] for item in daily_data],
                        'itemStyle': {'color': '#66bb6a'} # Green
                    }
                ],
                'legend': {
                    'data': ['创建任务', '完成任务']
                },
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {
                        'type': 'shadow'
                    }
                }
            }

            ui.echart(chart_data).classes('w-full h-48')

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
            'focus_time': focus_time,  # 这里返回分钟数
            'completed_tasks': len(completed_tasks)
        }