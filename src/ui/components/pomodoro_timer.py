"""
番茄钟组件
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
from nicegui import ui


class PomodoroTimerComponent:
    def __init__(self, pomodoro_manager, task_manager, current_user: Dict):
        self.pomodoro_manager = pomodoro_manager
        self.task_manager = task_manager
        self.current_user = current_user
        self.active_session: Optional[Dict] = None
        self.timer_running = False
        self.selected_task: Optional[Dict] = None
        self.timer_container = None
        self.pomodoro_fullscreen = None
    
    def create_mini_timer(self, container):
        """创建迷你番茄钟"""
        self.timer_container = container
        
        container.clear()
        
        with container:
            with ui.row().classes('items-center gap-3'):
                ui.label('25:00').classes('font-mono text-lg')
                ui.button(icon='play_arrow', on_click=self.show_fullscreen_timer).props('flat round size=sm')
    
    def create_fullscreen_timer(self, task: Optional[dict] = None) -> ui.column:
        """创建全屏计时器"""
        with ui.column().classes('w-full h-full items-center justify-center bg-primary text-white') as container:
            if task:
                ui.label(f'专注任务: {task["title"]}').classes('text-h5 mb-4')
            
            self.timer_label = ui.label('25:00').classes('text-h1 font-mono mb-8')
            
            with ui.row().classes('gap-4'):
                ui.button(
                    '开始',
                    icon='play_arrow',
                    on_click=self.start_timer
                ).props('size=lg color=white flat')
                
                ui.button(
                    '暂停',
                    icon='pause',
                    on_click=self.pause_timer
                ).props('size=lg color=white flat')
                
                ui.button(
                    '重置',
                    icon='refresh',
                    on_click=self.reset_timer
                ).props('size=lg color=white flat')
            
            ui.button(
                '退出全屏',
                icon='fullscreen_exit',
                on_click=lambda: container.delete()
            ).classes('absolute top-4 right-4').props('flat color=white')
        
        return container
    
    def toggle_timer(self):
        """切换计时器状态"""
        if self.timer_running:
            self.pause_timer()
        else:
            self.start_timer()
    
    def start_timer(self, task_id: Optional[int] = None):
        """开始计时"""
        if not self.timer_running:
            if not self.active_session:
                # 创建新的番茄钟会话
                self.active_session = {
                    'task_id': task_id,
                    'start_time': datetime.now(),
                    'duration': 25 * 60,  # 25分钟
                    'remaining': 25 * 60
                }
            
            self.timer_running = True
            self.timer_task = asyncio.create_task(self.run_timer())
            ui.notify('番茄钟开始！', type='positive')
    
    def pause_timer(self):
        """暂停计时"""
        if self.timer_running:
            self.timer_running = False
            if self.timer_task:
                self.timer_task.cancel()
            ui.notify('番茄钟已暂停', type='info')
    
    def reset_timer(self):
        """重置计时器"""
        self.timer_running = False
        if self.timer_task:
            self.timer_task.cancel()
        
        self.active_session = None
        self.update_timer_display(25 * 60)
        ui.notify('番茄钟已重置', type='info')
    
    async def run_timer(self):
        """运行计时器"""
        try:
            while self.timer_running and self.active_session and self.active_session['remaining'] > 0:
                await asyncio.sleep(1)
                self.active_session['remaining'] -= 1
                self.update_timer_display(self.active_session['remaining'])
            
            if self.active_session and self.active_session['remaining'] <= 0:
                await self.complete_session()
        except asyncio.CancelledError:
            pass
    
    def update_timer_display(self, seconds: int):
        """更新计时器显示"""
        minutes = seconds // 60
        seconds = seconds % 60
        time_str = f'{minutes:02d}:{seconds:02d}'
        
        if self.timer_label:
            self.timer_label.text = time_str
    
    async def complete_session(self):
        """完成番茄钟会话"""
        self.timer_running = False
        
        if self.active_session:
            # 保存会话到数据库
            if self.pomodoro_manager and self.active_session.get('task_id'):
                self.pomodoro_manager.complete_session(
                    self.active_session['task_id'],
                    self.active_session['start_time'],
                    25  # 25分钟
                )
        
        ui.notify('番茄钟完成！休息一下吧 🎉', type='positive')
        
        # 重置会话
        self.active_session = None
        self.update_timer_display(25 * 60)
    
    def show_fullscreen_timer(self):
        """显示全屏番茄钟"""
        with ui.dialog().classes('fullscreen') as dialog:
            with ui.column().classes('w-full h-full items-center justify-center bg-primary text-white'):
                ui.button(icon='close', on_click=dialog.close).classes('absolute top-4 left-4').props('flat round text-white')
                
                if self.selected_task:
                    ui.label(self.selected_task['title']).classes('text-h5 mb-8')
                
                ui.label('25:00').classes('text-8xl font-mono mb-8')
                
                with ui.row().classes('gap-4'):
                    ui.button('开始', icon='play_arrow').props('size=lg color=white flat')
                    ui.button('暂停', icon='pause').props('size=lg color=white flat')
                    ui.button('重置', icon='refresh').props('size=lg color=white flat')
        
        dialog.open()

    def start_pomodoro_for_task(self, task_id: int):
        """为特定任务开始番茄工作法"""
        if self.timer_running:
            ui.notify('已有活跃的番茄钟', type='warning')
            return
        
        # 获取任务信息
        task = self.task_manager.get_task_by_id(task_id)
        if task:
            self.selected_task = task
            self.show_fullscreen_timer()
            ui.notify(f'开始专注：{task["title"]}', type='positive')

    def set_selected_task(self, task: Optional[Dict]):
        """设置选中的任务"""
        self.selected_task = task

    def get_active_session(self) -> Optional[Dict]:
        """获取活跃会话"""
        return self.active_session

    def is_timer_running(self) -> bool:
        """检查计时器是否正在运行"""
        return self.timer_running 