"""
任务列表组件
"""

from nicegui import ui
from datetime import date
from typing import Dict, List, Callable, Optional


class TaskListComponent:
    def __init__(self, task_manager, pomodoro_manager, current_user: Dict, on_task_select: Callable, on_start_pomodoro: Callable, on_refresh: Callable):
        self.task_manager = task_manager
        self.pomodoro_manager = pomodoro_manager
        self.current_user = current_user
        self.on_task_select = on_task_select
        self.on_start_pomodoro = on_start_pomodoro
        self.on_refresh = on_refresh
        self.current_tasks: List[Dict] = []
        self.current_view = 'my_day'

    def create_add_task_input(self, container):
        """创建添加任务输入框"""
        def handle_button_add():
            if task_input.value.strip():
                self.create_quick_task(task_input.value.strip())
                task_input.value = ''
        
        def handle_enter_key():
            if task_input.value.strip():
                self.create_quick_task(task_input.value.strip())
                task_input.value = ''
        
        with container:
            with ui.row().classes('w-full mb-6'):
                task_input = ui.input(placeholder='添加任务...').classes('flex-1')
                # 使用action方法处理回车键
                task_input.action = handle_enter_key
                ui.button(icon='add', on_click=handle_button_add).props('flat round color=primary')

    def create_quick_task(self, title: str):
        """快速创建任务"""
        # 根据当前视图设置默认属性
        due_date = None
        priority = 'medium'
        list_id = None
        
        if self.current_view == 'my_day' or self.current_view == 'planned':
            due_date = date.today()
        elif self.current_view == 'important':
            priority = 'high'
        elif self.current_view.startswith('list_'):
            list_id = int(self.current_view.split('_')[1])
        
        task_id = self.task_manager.create_task(
            user_id=self.current_user['user_id'],
            title=title,
            due_date=due_date,
            priority=priority,
            list_id=list_id
        )
        
        if task_id:
            ui.notify('任务创建成功', type='positive')
            self.on_refresh()
        else:
            ui.notify('任务创建失败', type='negative')

    def create_task_list(self, container):
        """创建任务列表"""
        pending_tasks = [task for task in self.current_tasks if task['status'] == 'pending']
        
        with container:
            if not pending_tasks:
                ui.label('暂无待完成任务').classes('text-center text-grey-5 py-8')
                return
            
            with ui.column().classes('w-full gap-2 mb-6'):
                for task in pending_tasks:
                    self.create_task_item(task)

    def create_task_item(self, task: Dict):
        """创建任务项"""
        def toggle_complete():
            self.task_manager.toggle_task_status(task['task_id'], 'completed')
            self.on_refresh()
        
        def start_pomodoro():
            self.on_start_pomodoro(task['task_id'])
        
        def show_task_detail():
            self.on_task_select(task)
        
        with ui.row().classes('task-item w-full p-4 bg-white rounded shadow-sm items-center gap-3'):
            # 完成按钮
            ui.button(icon='radio_button_unchecked', on_click=toggle_complete).props('flat round size=sm')
            
            # 播放按钮
            ui.button(icon='play_arrow', on_click=start_pomodoro).props('flat round size=sm color=green')
            
            # 任务内容
            with ui.column().classes('flex-1 cursor-pointer').on('click', show_task_detail):
                ui.label(task['title']).classes('font-medium')
                
                # 任务详情
                details = []
                if task['due_date']:
                    details.append(f"📅 {task['due_date']}")
                if task['priority'] == 'high':
                    details.append('⭐ 重要')
                if task['list_name']:
                    details.append(f"📂 {task['list_name']}")
                if task.get('tags'):
                    tag_names = [tag['name'] for tag in task['tags']]
                    details.append(f"🏷️ {', '.join(tag_names)}")
                
                if details:
                    ui.label(' • '.join(details)).classes('text-sm text-grey-6')

    def create_completed_tasks_section(self, container):
        """创建已完成任务区域"""
        completed_tasks = [task for task in self.current_tasks if task['status'] == 'completed']
        
        if not completed_tasks:
            return
        
        with container:
            with ui.expansion(f'已完成 ({len(completed_tasks)})', icon='check_circle').classes('w-full'):
                with ui.column().classes('w-full gap-2'):
                    for task in completed_tasks:
                        self.create_completed_task_item(task)

    def create_completed_task_item(self, task: Dict):
        """创建已完成任务项"""
        def toggle_uncomplete():
            self.task_manager.toggle_task_status(task['task_id'], 'pending')
            self.on_refresh()
        
        with ui.row().classes('w-full p-3 items-center gap-3 opacity-60'):
            ui.button(icon='check_circle', on_click=toggle_uncomplete).props('flat round size=sm color=green')
            ui.label(task['title']).classes('line-through text-grey-6')

    def set_current_tasks(self, tasks: List[Dict]):
        """设置当前任务列表"""
        self.current_tasks = tasks

    def set_current_view(self, view: str):
        """设置当前视图"""
        self.current_view = view

    def create_stats_bar(self, container):
        """创建统计栏"""
        stats = self.get_view_stats()
        
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

    def get_view_stats(self) -> Dict:
        """获取当前视图的统计数据"""
        if not self.current_user:
            return {'estimated_time': 0, 'pending_tasks': 0, 'focus_time': 0, 'completed_tasks': 0}
        
        pending_tasks = [task for task in self.current_tasks if task['status'] == 'pending']
        completed_tasks = [task for task in self.current_tasks if task['status'] == 'completed']
        
        # 计算预计时间
        estimated_time = sum((task.get('estimated_pomodoros', 1) - task.get('used_pomodoros', 0)) * 25 for task in pending_tasks)
        
        # 今日专注时间
        focus_time = self.pomodoro_manager.get_today_focus_duration(self.current_user['user_id'])
        
        return {
            'estimated_time': estimated_time,
            'pending_tasks': len(pending_tasks),
            'focus_time': focus_time,
            'completed_tasks': len(completed_tasks)
        } 