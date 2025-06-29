"""
主内容区域组件
"""

from nicegui import ui
from typing import Dict, List, Callable


class MainContentComponent:
    def __init__(self, current_user: Dict, user_lists: List[Dict]):
        self.current_user = current_user
        self.user_lists = user_lists
        self.current_view = 'my_day'

    def create_main_content(self, container, current_view: str, task_list_component):
        """创建主内容区域"""
        self.current_view = current_view
        
        container.clear()
        
        with container:
            with ui.column().classes('w-full p-6'):
                # 页面标题
                view_titles = {
                    'my_day': '我的一天',
                    'planned': '计划内',
                    'important': '重要',
                    'all': '任务'
                }
                
                title = view_titles.get(current_view, '任务')
                
                # 如果是清单视图，显示清单名称
                if current_view.startswith('list_'):
                    list_id = int(current_view.split('_')[1])
                    for user_list in self.user_lists:
                        if user_list['list_id'] == list_id:
                            title = user_list['name']
                            break
                
                ui.label(title).classes('text-h4 font-bold mb-4')
                
                # 统计栏
                stats_container = ui.column().classes('w-full')
                task_list_component.create_stats_bar(stats_container)
                
                # 添加任务输入框
                task_input_container = ui.column().classes('w-full')
                task_list_component.create_add_task_input(task_input_container)
                
                # 任务列表
                task_list_container = ui.column().classes('w-full')
                task_list_component.create_task_list(task_list_container)
                
                # 已完成任务（可展开）
                completed_tasks_container = ui.column().classes('w-full')
                task_list_component.create_completed_tasks_section(completed_tasks_container)

    def update_user_lists(self, user_lists: List[Dict]):
        """更新用户清单"""
        self.user_lists = user_lists 