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
                ui.run_javascript('''
                    setTimeout(() => {
                        const input = document.querySelector('input[placeholder="添加任务..."]');
                        if (input) input.focus();
                    }, 100);
                ''')
        
        def handle_enter_key(e):
            # 检查是否按下了Enter键
            if e.args.get('key') == 'Enter' and task_input.value.strip():
                self.create_quick_task(task_input.value.strip())
                task_input.value = ''
                ui.run_javascript('''
                    setTimeout(() => {
                        const input = document.querySelector('input[placeholder="添加任务..."]');
                        if (input) input.focus();
                    }, 100);
                ''')
        
        with container:
            with ui.row().classes('w-full mb-6'):
                task_input = ui.input(placeholder='添加任务...').classes('flex-1')
                # 使用on方法监听键盘事件
                task_input.on('keydown', handle_enter_key)
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
        """创建任务列表（卡片式）"""
        pending_tasks = [task for task in self.current_tasks if task['status'] == 'pending']
        
        with container:
            if not pending_tasks:
                ui.label('暂无待完成任务').classes('text-center text-grey-5 py-8')
                return
            
            with ui.column().classes('w-full gap-2 mb-6'):
                for task in pending_tasks:
                    self.create_task_item(task)

    def create_task_item(self, task: Dict):
        """创建任务项（卡片式）"""
        def toggle_complete():
            self.task_manager.toggle_task_status(task['task_id'], 'completed')
            self.on_refresh()
        
        def start_pomodoro():
            self.on_start_pomodoro(task['task_id'])
        
        def show_task_detail():
            self.on_task_select(task)
        
        # 计算卡片的背景颜色（过期任务用红色背景）
        card_classes = 'task-item w-full p-4 bg-white rounded shadow-sm items-center gap-3'
        if task.get('due_date') and task['due_date'] < date.today():
            card_classes = 'task-item w-full p-4 bg-red-50 rounded shadow-sm items-center gap-3'
        
        with ui.row().classes(card_classes):
            # 完成按钮
            ui.button(icon='radio_button_unchecked', on_click=toggle_complete).props('flat round size=sm')
            
            # 播放按钮
            ui.button(icon='play_arrow', on_click=start_pomodoro).props('flat round size=sm color=green')
            
            # 任务内容
            with ui.column().classes('flex-1 cursor-pointer').on('click', show_task_detail):
                ui.label(task['title']).classes('font-medium hover:text-blue-600')
                
                # 如果有描述，显示简短描述
                if task.get('description'):
                    description = task['description'][:50] + '...' if len(task['description']) > 50 else task['description']
                    ui.label(description).classes('text-sm text-grey-6')
                
                # 任务详情行
                detail_items = []
                
                # 收集文本详情
                if task['due_date']:
                    due_date = task['due_date']
                    if isinstance(due_date, str):
                        due_date_str = due_date.split()[0]  # 只取日期部分
                    else:
                        due_date_str = str(due_date)
                    
                    # 判断是否过期
                    try:
                        due_date_obj = date.fromisoformat(due_date_str) if isinstance(due_date, str) else due_date
                        if due_date_obj < date.today():
                            detail_items.append(f"📅 {due_date_str} (已过期)")
                        elif due_date_obj == date.today():
                            detail_items.append(f"📅 {due_date_str} (今天)")
                        else:
                            detail_items.append(f"📅 {due_date_str}")
                    except:
                        detail_items.append(f"📅 {due_date_str}")
                
                # 重要程度显示（只显示高和低，不显示中等）
                priority = task.get('priority', 'medium')
                if priority == 'high':
                    detail_items.append('⭐ 重要')
                elif priority == 'low':
                    detail_items.append('🔻 低优先级')
                
                # 自定义标签
                if task.get('tags'):
                    tag_names = [tag['name'] for tag in task['tags']]
                    detail_items.append(f"🏷️ {', '.join(tag_names)}")
                
                # 创建详情显示区域（番茄数和文本在同一行）
                estimated = task.get('estimated_pomodoros', 1)
                used = task.get('used_pomodoros', 0)
                
                if detail_items or task['list_name'] or estimated:
                    with ui.row().classes('items-center gap-2 text-sm text-grey-6 flex-wrap'):
                        # 番茄数显示（排在最前面）
                        if estimated > 5:
                            # 超过5个番茄时，只显示一个番茄和数字
                            if used == estimated:
                                # 已完成全部番茄，显示鲜明颜色
                                ui.label('🍅').classes('text-sm leading-none').style('filter: saturate(1.5) brightness(1.1);')
                            else:
                                # 还没完成全部番茄，显示半透明
                                ui.label('🍅').classes('text-sm leading-none opacity-40').style('filter: grayscale(0.3);')
                            ui.label(f'{used}/{estimated}').classes('text-sm text-grey-600 leading-none')
                        else:
                            # 5个或以下时，显示番茄图标
                            for i in range(estimated):
                                if i < used:
                                    # 已使用的番茄（正常显示，鲜明颜色）
                                    ui.label('🍅').classes('text-sm leading-none').style('filter: saturate(1.5) brightness(1.1);')
                                else:
                                    # 未使用的番茄（半透明显示）
                                    ui.label('🍅').classes('text-sm leading-none opacity-40').style('filter: grayscale(0.3);')
                        
                        # 添加分隔符（如果有其他详情的话）
                        if detail_items or task['list_name']:
                            ui.label('•').classes('text-sm text-grey-400 leading-none mx-1')
                        
                        # 显示文本详情（每个项目独立显示）
                        for i, item in enumerate(detail_items):
                            ui.label(item).classes('text-sm leading-none')
                            # 在项目之间添加分隔符（除了最后一个项目）
                            if i < len(detail_items) - 1 or task['list_name']:
                                ui.label('•').classes('text-sm text-grey-400 leading-none mx-1')
                        
                        # 显示清单（彩色圆点）
                        if task['list_name']:
                            list_color = task.get('list_color', '#2196F3')
                            ui.element('div').classes('w-3 h-3 rounded-full self-center').style(f'background-color: {list_color}; min-width: 12px; min-height: 12px;')
                            ui.label(task['list_name']).classes('text-sm leading-none')

    def create_completed_tasks_section(self, container):
        """创建已完成任务区域（卡片式）"""
        completed_tasks = [task for task in self.current_tasks if task['status'] == 'completed']
        
        if not completed_tasks:
            return
        
        with container:
            ui.space().classes('h-4')  # 间距
            with ui.expansion(f'已完成 ({len(completed_tasks)})', icon='check_circle').classes('w-full'):
                with ui.column().classes('w-full gap-2'):
                    for task in completed_tasks:
                        self.create_completed_task_item(task)

    def create_completed_task_item(self, task: Dict):
        """创建已完成任务项（卡片式）"""
        def toggle_uncomplete():
            self.task_manager.toggle_task_status(task['task_id'], 'pending')
            self.on_refresh()
        
        with ui.row().classes('w-full p-3 bg-white rounded shadow-sm items-center gap-3 opacity-70'):
            ui.button(icon='check_circle', on_click=toggle_uncomplete).props('flat round size=sm color=green')
            
            with ui.column().classes('flex-1'):
                ui.label(task['title']).classes('line-through text-grey-600')
                if task.get('description'):
                    description = task['description'][:50] + '...' if len(task['description']) > 50 else task['description']
                    ui.label(description).classes('text-sm text-grey-500 line-through')
                
                # 完成时间显示
                updated_at = task.get('updated_at', '')
                if updated_at:
                    if isinstance(updated_at, str):
                        # 只显示日期部分
                        date_part = updated_at.split()[0] if ' ' in updated_at else updated_at
                        ui.label(f"完成于: {date_part}").classes('text-xs text-grey-500')

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
                with ui.column().classes('text-center items-center'):
                    ui.label(f"{stats['estimated_time']}分钟").classes('text-h6 font-bold text-blue-6')
                    ui.label('预计时间').classes('text-sm text-grey-6')
                
                with ui.column().classes('text-center items-center'):
                    ui.label(str(stats['pending_tasks'])).classes('text-h6 font-bold text-orange-6')
                    ui.label('待完成任务').classes('text-sm text-grey-6')
                
                with ui.column().classes('text-center items-center'):
                    ui.label(f"{stats['focus_time']}分钟").classes('text-h6 font-bold text-green-6')
                    ui.label('已专注时间').classes('text-sm text-grey-6')
                
                with ui.column().classes('text-center items-center'):
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