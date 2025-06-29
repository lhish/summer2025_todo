"""
任务详情组件
"""

from nicegui import ui
from typing import Dict, Optional, Callable


class TaskDetailComponent:
    def __init__(self, task_manager, on_task_update: Callable, on_start_pomodoro: Callable, on_close: Callable):
        self.task_manager = task_manager
        self.on_task_update = on_task_update
        self.on_start_pomodoro = on_start_pomodoro
        self.on_close = on_close
        self.selected_task: Optional[Dict] = None
        self.task_detail_open = False

    def create_task_detail_panel(self, container):
        """创建任务详情面板"""
        if not self.selected_task:
            return
        
        container.clear()
        
        with container:
            with ui.column().classes('w-full h-full p-6'):
                # 标题栏
                with ui.row().classes('w-full items-center mb-4'):
                    ui.button(icon='close', on_click=self.close_task_detail).props('flat round size=sm')
                    ui.space()
                
                # 任务操作按钮
                with ui.row().classes('w-full gap-2 mb-6'):
                    def toggle_task():
                        self.task_manager.toggle_task_status(self.selected_task['task_id'])
                        self.on_task_update()
                        self.close_task_detail()
                    
                    def start_task_pomodoro():
                        self.on_start_pomodoro(self.selected_task['task_id'])
                    
                    ui.button('完成', icon='check', on_click=toggle_task).props('color=green')
                    ui.button('开始', icon='play_arrow', on_click=start_task_pomodoro).props('color=primary')
                
                # 任务标题
                task_title = ui.input('标题', value=self.selected_task['title']).classes('w-full mb-4')
                
                # 其他字段...
                ui.label('更多详情功能开发中...').classes('text-grey-6')

    def close_task_detail(self):
        """关闭任务详情面板"""
        self.task_detail_open = False
        self.selected_task = None
        self.on_close()

    def show_task_detail(self, task: Dict, container):
        """显示任务详情"""
        self.selected_task = task
        self.task_detail_open = True
        self.create_task_detail_panel(container)

    def is_open(self) -> bool:
        """检查详情面板是否打开"""
        return self.task_detail_open

    def get_selected_task(self) -> Optional[Dict]:
        """获取选中的任务"""
        return self.selected_task 