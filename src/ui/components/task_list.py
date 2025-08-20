"""
任务列表组件
"""

from nicegui import ui
from datetime import date
from typing import Dict, List, Callable, Optional
from src.services.ai_assistant import AIAssistant


class TaskListComponent:
    def __init__(self, task_manager, pomodoro_manager, settings_manager, tag_manager, current_user: Dict, on_task_select: Callable, on_start_pomodoro: Callable, on_refresh: Callable[[Optional[int]], None]):
        self.task_manager = task_manager
        self.pomodoro_manager = pomodoro_manager
        self.settings_manager = settings_manager
        self.tag_manager = tag_manager
        self.current_user = current_user
        self.on_task_select = on_task_select
        self.on_start_pomodoro = on_start_pomodoro
        self.on_refresh = on_refresh
        self.current_tasks: List[Dict] = []
        self.current_view = 'my_day'
        self.ai_assistant = AIAssistant()

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

        async def handle_smart_recommendation():
            # 调用AI服务获取推荐任务
            ui.notify('正在生成智能推荐任务...', type='info', timeout=1) # 显示加载提示
            
            # 获取当前任务列表标题
            current_task_titles = [task['title'] for task in self.current_tasks if task['status'] == 'pending']
            
            if not current_task_titles:
                ui.notify('当前没有待办任务可供推荐', type='warning')
                return

            # 修改提示词，使其旨在从现有任务中选择一个最相关的任务标题
            prompt = f"请从以下任务列表中选择一个你认为最相关或最紧急的任务标题，只返回一个任务标题，不要有其他任何内容。任务列表：{', '.join(current_task_titles)}"
            system_prompt = "你是一个任务推荐助手，只返回一个任务标题，不要有其他任何内容。"
            
            recommended_task_title = await self.ai_assistant.call_llm_api(prompt, system_prompt)
            ui.notify('智能推荐任务生成完毕', type='positive', timeout=1000) # 隐藏加载提示

            if recommended_task_title:
                recommended_task_title = recommended_task_title.strip()
                # 找到对应的现有任务
                found_task = next((task for task in self.current_tasks if task['title'] == recommended_task_title), None)
                
                if found_task:
                    print(f"DEBUG: Calling highlight_task for task_id: {found_task['task_id']} from handle_smart_recommendation")
                    await self.highlight_task(found_task['task_id'])
                    print(f"DEBUG: highlight_task called for task_id: {found_task['task_id']} from handle_smart_recommendation")
                    ui.notify(f'推荐任务: {found_task["title"]}', type='positive')
                else:
                    print(f"DEBUG: Recommended task '{recommended_task_title}' not found in current_tasks.")
                    ui.notify(f'未能找到推荐任务: {recommended_task_title}，请稍后再试', type='warning')
            else:
                print("DEBUG: Failed to get smart recommendation from AI service.")
                ui.notify('未能获取智能推荐任务，请检查AI服务', type='negative')

        with container:
            with ui.row().classes('w-full mb-6 items-center'): # Add items-center for vertical alignment
                task_input = ui.input(placeholder='添加任务...').classes('flex-1')
                # 使用on方法监听键盘事件
                task_input.on('keydown', handle_enter_key)
                ui.button(icon='auto_awesome', on_click=handle_smart_recommendation).props('flat round color=purple').tooltip('智能推荐任务') # New button
                ui.button(icon='add', on_click=handle_button_add).props('flat round color=primary')

    def create_quick_task(self, title: str): # Modified function signature
        """快速创建任务"""
        # 根据当前视图设置默认属性
        due_date = None
        priority = 'medium'
        tags = []
        
        if self.current_view == 'my_day' or self.current_view == 'planned':
            due_date = date.today()
        elif self.current_view == 'important':
            priority = 'high'
        elif self.current_view.startswith('tag_'):
            # 如果是标签视图，获取标签名并添加到任务
            tag_id = int(self.current_view.split('_')[1])
            tag_info = self.tag_manager.get_tag_by_id(tag_id)
            if tag_info:
                tags = [tag_info['name']]
        
        task_id = self.task_manager.create_task(
            user_id=self.current_user['user_id'],
            title=title,
            due_date=due_date,
            priority=priority,
            tags=tags,
        )
        
        if task_id:
            ui.notify('任务创建成功', type='positive')
            # 传递 is_newly_created 标志给 on_refresh，以便高亮新创建的任务
            self.on_refresh(newly_created_task_id=task_id)
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

        card_element = ui.row().classes(card_classes).props(f'data-task-id="{task["task_id"]}"')
        
        # 如果是新创建的任务，添加短暂高亮效果
        if task.get('is_newly_created'):
            # 移除标记，因为高亮是短暂的，不需要持久化
            del task['is_newly_created']
            print(f"DEBUG: Calling highlight_task for newly created task_id: {task['task_id']} from create_task_item")
            ui.timer(0.1, lambda: self.highlight_task(task['task_id']), once=True) # 稍微延迟执行，确保元素已渲染
            print(f"DEBUG: highlight_task timer set for newly created task_id: {task['task_id']} from create_task_item")

        with card_element:
        
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
                
                # 自定义标签（移除，改为在详情行中直接显示彩色圆点）
                
                # 创建详情显示区域（番茄数、标签圆点和文本在同一行）
                estimated = task.get('estimated_pomodoros', 1)
                used = task.get('used_pomodoros', 0)
                
                if detail_items or estimated or task.get('tags'):
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
                        
                        # 显示标签彩色圆点（在番茄数之后）
                        if task.get('tags'):
                            # 添加分隔符（如果有番茄数的话）
                            if estimated:
                                ui.label('•').classes('text-sm text-grey-400 leading-none mx-1')
                            
                            # 显示每个标签的彩色圆点和名称
                            for i, tag in enumerate(task['tags']):
                                tag_color = tag.get('color', '#757575')
                                ui.element('div').classes('w-3 h-3 rounded-full self-center').style(f'background-color: {tag_color}; min-width: 12px; min-height: 12px;')
                                ui.label(tag['name']).classes('text-sm leading-none')
                                # 在标签之间添加分隔符（除了最后一个标签）
                                if i < len(task['tags']) - 1:
                                    ui.label('•').classes('text-sm text-grey-400 leading-none mx-1')
                        
                        # 添加分隔符（如果有其他详情的话）
                        if detail_items and (estimated or task.get('tags')):
                            ui.label('•').classes('text-sm text-grey-400 leading-none mx-1')
                        
                        # 显示文本详情（每个项目独立显示）
                        for i, item in enumerate(detail_items):
                            ui.label(item).classes('text-sm leading-none')
                            # 在项目之间添加分隔符（除了最后一个项目）
                            if i < len(detail_items) - 1:
                                ui.label('•').classes('text-sm text-grey-400 leading-none mx-1')

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
        
        # 获取用户的番茄长度设置
        user_settings = self.settings_manager.get_user_settings(self.current_user['user_id'])
        pomodoro_duration = user_settings.get('pomodoro_work_duration', 25) if user_settings else 25
        
        # 计算预计时间（使用用户设定的番茄长度）
        estimated_time = sum((task.get('estimated_pomodoros', 1) - task.get('used_pomodoros', 0)) * pomodoro_duration for task in pending_tasks)
        
        # 今日专注时间
        focus_time = self.pomodoro_manager.get_today_focus_duration(self.current_user['user_id'])
        
        return {
            'estimated_time': estimated_time,
            'pending_tasks': len(pending_tasks),
            'focus_time': focus_time,
            'completed_tasks': len(completed_tasks)
        }

    async def highlight_task(self, task_id: int):
        """
        短暂高亮指定任务项
        """
        print(f"DEBUG: highlight_task method called for task_id: {task_id}")
        # 添加高亮样式
        await ui.run_javascript(f'''
            const taskElement = document.querySelector('[data-task-id="{task_id}"]');
            if (taskElement) {{
                taskElement.classList.add('highlight-task');
                console.log('DEBUG: Added highlight-task class to element', taskElement);
            }} else {{
                console.log('DEBUG: Task element not found for task_id', {task_id});
            }}
        ''')
        # 延迟后移除高亮样式
        await ui.run_javascript(f'''
            setTimeout(() => {{
                const taskElement = document.querySelector('[data-task-id="{task_id}"]');
                if (taskElement) {{
                    taskElement.classList.remove('highlight-task');
                    console.log('DEBUG: Removed highlight-task class from element', taskElement);
                }} else {{
                    console.log('DEBUG: Task element not found for task_id', {task_id}, 'during removal attempt');
                }}
            }}, 2000); // 2秒后移除高亮
        ''')
        print(f"DEBUG: JavaScript for highlight_task for task_id {task_id} sent.")