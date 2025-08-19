"""
主内容区域组件
"""

from nicegui import ui
from typing import Dict, List, Callable


class MainContentComponent:
    def __init__(self, current_user: Dict, user_tags: List[Dict]):
        self.current_user = current_user
        self.user_tags = user_tags
        self.current_view = 'my_day'

    def create_main_content(self, container, current_view: str, task_list_component):
        """创建主内容区域"""
        self.current_view = current_view
        
        container.clear()
        
        with container:
            with ui.column().classes('w-full p-6'):
                # 页面标题
                title = '所有任务'  # 默认标题
                
                if current_view.startswith('tag_'):
                    # 标签视图：显示标签名称
                    tag_id = int(current_view.split('_')[1])
                    for user_tag in self.user_tags:
                        if user_tag['tag_id'] == tag_id:
                            title = user_tag['name']
                            break
                else:
                    # 默认视图
                    view_titles = {
                        'my_day': '今天截止',
                        'planned': '即将截止',
                        'important': '重要',
                        'all': '所有任务'
                    }
                    title = view_titles.get(current_view, '所有任务')
                
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

    def update_user_tags(self, user_tags: List[Dict]):
        """更新用户标签"""
        self.user_tags = user_tags 