import asyncio
from datetime import datetime
from typing import Dict, Optional, List
from nicegui import ui, app


class PomodoroTimerComponent:
    def __init__(self, pomodoro_manager, task_manager, current_user: Dict):
        self.pomodoro_manager = pomodoro_manager
        self.task_manager = task_manager
        self.current_user = current_user

        self.active_session: Optional[Dict] = None
        self.timer_running = False
        self.selected_task: Optional[Dict] = None

        self.timer_labels: List[ui.label] = []
        self.timer_task = None

        self.duration_minutes = 25
        self.break_minutes = 5
        self.focus_mode = False
        self.in_break = False

        self.status_label = None
        self.settings_dialog = None
        self.input_duration = None
        self.input_break = None
        self.focus_mode_switch = None
        # 存储客户端引用
        self.client = None
        # 通知队列
        self.notification_queue = asyncio.Queue()
        self.setup_notification_handler()

    def setup_notification_handler(self):
        """设置通知处理程序"""

        async def process_notifications():
            while True:
                message, notify_type = await self.notification_queue.get()

                #  在客户端上下文中运行通知
                if self.client:
                    self.client.run(lambda: ui.notify(message, type=notify_type))
                else:
                    print(f"[警告] 无法显示通知：{message}，未设置 client")

                self.notification_queue.task_done()

        asyncio.create_task(process_notifications())

    def safe_notify(self, message: str, notify_type: str = "positive"):
        """安全地发送通知（通过队列）"""
        self.notification_queue.put_nowait((message, notify_type))
    # 在创建UI时设置客户端引用

    def set_client(self, client):
        self.client = client

    def set_focus_mode(self, enabled: bool):
        self.focus_mode = enabled

    def set_duration(self, minutes: int):
        self.duration_minutes = minutes

    def set_break_duration(self, minutes: int):
        self.break_minutes = minutes

    def create_mini_timer(self, container):
        self.timer_labels.clear()
        container.clear()

        with container:
            with ui.row().classes('items-center gap-3'):
                label = ui.label(f'{self.duration_minutes:02d}:00').classes('font-mono text-lg')
                self.timer_labels.append(label)
                ui.button(icon='play_arrow', on_click=self.show_fullscreen_timer).props('flat round size=sm')

    def show_fullscreen_timer(self):
        dialog = ui.dialog().classes('fullscreen')
        dialog.props('no-close-on-outside-click')

        with dialog:
            with ui.column().classes('w-full h-full items-center justify-center bg-primary text-white'):
                ui.button(icon='close', on_click=dialog.close).classes('absolute top-4 left-4').props(
                    'flat round text-white')

                if self.selected_task:
                    ui.label(self.selected_task['title']).classes('text-h5 mb-4')

                self.status_label = ui.label('专注中').classes('text-h6 mb-2')

                label = ui.label(f'{self.duration_minutes:02d}:00').classes('text-8xl font-mono mb-8')
                self.timer_labels.append(label)

                with ui.row().classes('gap-4'):
                    ui.button('开始', icon='play_arrow', on_click=self.start_timer).props('size=lg color=white flat')
                    ui.button('暂停', icon='pause', on_click=self.pause_timer).props('size=lg color=white flat')
                    ui.button('重置', icon='refresh', on_click=self.reset_timer).props('size=lg color=white flat')
                    ui.button('设置', icon='settings', on_click=self.show_settings_dialog).props(
                        'size=lg color=white flat')

        dialog.open()

    def start_timer(self, task_id: Optional[int] = None):
        if self.timer_running:
            return  # 避免重复点击

        # 确定当前阶段类型
        phase = "break" if self.in_break else "focus"
        duration = self.break_minutes if self.in_break else self.duration_minutes

        self.active_session = {
            'task_id': task_id or (self.selected_task['id'] if self.selected_task else None),
            'start_time': datetime.now(),
            'duration': duration * 60,
            'remaining': duration * 60,
            'phase': phase,  # 添加阶段标识
        }

        self.timer_running = True
        self.timer_task = asyncio.create_task(self.run_timer())

        if self.status_label:
            self.status_label.text = '休息中' if self.in_break else '专注中'

        # 使用安全通知
        self.safe_notify('计时开始！')

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            if self.timer_task:
                self.timer_task.cancel()
                self.timer_task = None
            self.safe_notify('计时已暂停', 'info')

    def reset_timer(self):
        self.timer_running = False
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
        self.active_session = None
        self.in_break = False
        self.update_timer_display(self.duration_minutes * 60)
        if self.status_label:
            self.status_label.text = '专注中'
        self.safe_notify('计时器已重置', 'info')

    async def run_timer(self):
        try:
            while self.timer_running and self.active_session:
                # 检查剩余时间
                if self.active_session['remaining'] <= 0:
                    # 完成当前阶段
                    await self.complete_phase()
                    # 如果进入休息阶段，继续计时
                    if self.in_break and self.active_session:
                        continue
                    else:
                        break

                # 更新计时器
                await asyncio.sleep(1)
                self.active_session['remaining'] -= 1
                self.update_timer_display(self.active_session['remaining'])

        except asyncio.CancelledError:
            print("计时任务被取消")
        finally:
            # 清理任务引用
            self.timer_task = None

    def update_timer_display(self, seconds: int):
        minutes = seconds // 60
        sec = seconds % 60
        time_str = f'{minutes:02d}:{sec:02d}'
        for label in self.timer_labels:
            label.text = time_str

    async def complete_phase(self):
        """完成当前阶段（专注或休息）"""
        if self.active_session['phase'] == "focus":
            # 专注阶段完成
            print(">>> 专注阶段完成")

            if self.pomodoro_manager and self.active_session.get('task_id'):
                self.pomodoro_manager.complete_session(
                    self.active_session['task_id'],
                    self.active_session['start_time'],
                    self.duration_minutes
                )

            # 使用安全通知
            self.safe_notify('专注完成！进入休息阶段')
            print(">>> ui 被调用了")

            # 设置休息阶段
            self.in_break = True
            if self.status_label:
                self.status_label.text = '休息中'

            # 创建休息会话
            self.active_session = {
                'task_id': None,
                'start_time': datetime.now(),
                'duration': self.break_minutes * 60,
                'remaining': self.break_minutes * 60,
                'phase': "break",
            }

            # 更新UI显示休息时间
            self.update_timer_display(self.active_session['remaining'])

        else:
            # 休息阶段完成
            print(">>> 休息阶段完成")
            self.safe_notify('休息完成！准备新一轮专注')

            # 重置状态
            self.in_break = False
            self.active_session = None
            self.timer_running = False

            # 更新UI显示专注时间
            self.update_timer_display(self.duration_minutes * 60)
            if self.status_label:
                self.status_label.text = '专注中'

    def show_settings_dialog(self):
        dialog = ui.dialog()

        with dialog:
            with ui.card().classes('w-80'):
                ui.label('番茄钟设置').classes('text-h6 mb-4')

                with ui.row().classes('items-center mb-4'):
                    ui.label('专注时长（分钟）')
                    input_duration = ui.number(min=1, value=self.duration_minutes)

                with ui.row().classes('items-center mb-4'):
                    ui.label('休息时长（分钟）')
                    input_break = ui.number(min=1, value=self.break_minutes)

                with ui.row().classes('items-center mb-4'):
                    ui.label('专注模式')
                    focus_switch = ui.switch(value=self.focus_mode)

                def save():
                    try:
                        self.set_duration(int(input_duration.value))
                        self.set_break_duration(int(input_break.value))
                        self.set_focus_mode(focus_switch.value)
                        self.update_timer_display(self.duration_minutes * 60)
                        self.safe_notify('设置已保存')
                        dialog.close()
                    except Exception as e:
                        self.safe_notify(f'保存失败: {e}', 'negative')

                ui.button('保存设置', on_click=save).classes('w-full')

        dialog.open()

    def save_settings(self):
        try:
            new_duration = int(self.input_duration.value)
            new_break = int(self.input_break.value)
            new_focus_mode = self.focus_mode_switch.value

            self.set_duration(new_duration)
            self.set_break_duration(new_break)
            self.set_focus_mode(new_focus_mode)

            self.update_timer_display(self.duration_minutes * 60)
            self.safe_notify('设置已保存')
            self.settings_dialog.close()
        except Exception as e:
            self.safe_notify(f'设置保存失败: {e}', 'negative')

    def start_pomodoro_for_task(self, task_id: int):
        if self.timer_running:
            self.safe_notify('已有活跃的番茄钟', 'warning')
            return

        task = self.task_manager.get_task_by_id(task_id)
        if task:
            self.selected_task = task
            self.show_fullscreen_timer()
            self.safe_notify(f'开始专注：{task["title"]}')

    def set_selected_task(self, task: Optional[Dict]):
        self.selected_task = task

    def get_active_session(self) -> Optional[Dict]:
        return self.active_session

    def is_timer_running(self) -> bool:
        return self.timer_running
