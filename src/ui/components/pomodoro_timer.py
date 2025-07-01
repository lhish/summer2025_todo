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

        # 创建通知容器
        self.notification_container = ui.element('div').style('display: none')

        # 通知队列
        self.notification_queue = asyncio.Queue()
        self.setup_notification_handler()

    def setup_notification_handler(self):
        """设置通知处理程序"""

        async def process_notifications():
            while True:
                message, notify_type = await self.notification_queue.get()

                # 使用 UI 上下文发送通知
                ui.run_coroutine_threadsafe(
                    self.send_notification(message, notify_type)
                )

                self.notification_queue.task_done()

        asyncio.create_task(process_notifications())

    def send_notification(self, message: str, notify_type: str):
        """在通知容器中发送通知"""
        with self.notification_container:
            ui.notify(message, type=notify_type)

    def safe_notify(self, message: str, notify_type: str = "positive"):
        """安全地发送通知（通过队列）"""
        self.notification_queue.put_nowait((message, notify_type))

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
                ui.button(icon='play_arrow', on_click=self.show_timer_dialog).props('flat round size=sm')

    def show_timer_dialog(self):
        """显示计时器对话框"""
        # 创建全屏对话框
        dialog = ui.dialog().classes('fullscreen')
        # 根据专注模式设置属性
        if self.focus_mode:
            dialog.props('no-backdrop-dismiss no-esc-dismiss')
        else:
            dialog.props('no-close-on-outside-click')

        with dialog:
            # 使用全屏列布局
            with ui.column().classes('w-full h-full items-center justify-center bg-primary text-white'):
                # 添加关闭按钮（绝对定位在左上角）
                ui.button(icon='close', on_click=dialog.close).classes('absolute top-4 left-4').props('flat round text-white')

                # 显示选中的任务标题
                if self.selected_task:
                    ui.label(self.selected_task['title']).classes('text-h5 mb-4')
                else:
                    ui.label('专注时间').classes('text-h5 mb-4')

                # 状态标签
                self.status_label = ui.label('专注中').classes('text-h6 mb-2')

                # 计时器标签 - 创建新的大字体标签
                label = ui.label(f'{self.duration_minutes:02d}:00').classes('text-8xl font-mono mb-8')
                # 添加到标签列表
                self.timer_labels.append(label)

                # 按钮行 - 居中显示
                with ui.row().classes('gap-4'):
                    ui.button('开始', icon='play_arrow', on_click=lambda: self.start_timer()).props(
                        'size=lg color=white flat')
                    ui.button('暂停', icon='pause', on_click=self.pause_timer).props('size=lg color=white flat')
                    ui.button('重置', icon='refresh', on_click=self.reset_timer).props('size=lg color=white flat')
                    ui.button('设置', icon='settings', on_click=self.show_settings_dialog).props(
                        'size=lg color=white flat')

        dialog.open()


    def start_timer(self, task_id: Optional[int] = None):
        """启动计时器"""
        if self.timer_running:
            return  # 避免重复点击

        # 如果通过任务启动，使用任务提供的task_id
        if task_id is not None:
            task = self.task_manager.get_task_by_id(task_id)
            if task:
                self.selected_task = task
        elif self.selected_task:
            # 如果已经有选中的任务，使用其ID
            task_id = self.selected_task.get('id')

        # 确定当前阶段类型
        phase = "break" if self.in_break else "focus"
        duration = self.break_minutes if self.in_break else self.duration_minutes

        # 创建活动会话
        self.active_session = {
            'task_id': task_id,
            'start_time': datetime.now(),
            'duration': duration * 60,
            'remaining': duration * 60,
            'phase': phase,  # 添加阶段标识
        }

        # 启动计时器
        self.timer_running = True
        self.timer_task = asyncio.create_task(self.run_timer())

        # 更新状态标签
        if self.status_label:
            self.status_label.text = '休息中' if self.in_break else '专注中'

        # 发送通知
        ui.notify('计时开始！', type='positive')
        print(f"启动计时器: 任务ID={task_id}, 阶段={phase}, 时长={duration}分钟")

    def pause_timer(self):
        """暂停计时器"""
        if self.timer_running:
            self.timer_running = False
            if self.timer_task:
                self.timer_task.cancel()
                self.timer_task = None
            ui.notify('计时已暂停', type='info')
            print("计时器已暂停")

    def reset_timer(self):
        """重置计时器"""
        self.timer_running = False
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
        self.active_session = None
        self.in_break = False
        self.update_timer_display(self.duration_minutes * 60)
        if self.status_label:
            self.status_label.text = '专注中'
        ui.notify('计时器已重置', type='info')
        print("计时器已重置")

    async def run_timer(self):
        """运行计时器循环"""
        try:
            print("计时器开始运行")
            while self.timer_running and self.active_session:
                # 检查剩余时间
                if self.active_session['remaining'] <= 0:
                    print("时间到，完成阶段")
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
                # 每10秒打印一次日志
                if self.active_session['remaining'] % 10 == 0:
                    print(f"剩余时间: {self.active_session['remaining']}秒")

        except asyncio.CancelledError:
            print("计时任务被取消")
        except Exception as e:
            print(f"计时器错误: {e}")
        finally:
            # 清理任务引用
            self.timer_task = None
            print("计时器任务结束")

    def update_timer_display(self, seconds: int):
        """更新计时器显示"""
        minutes = seconds // 60
        sec = seconds % 60
        time_str = f'{minutes:02d}:{sec:02d}'
        for label in self.timer_labels:
            label.text = time_str

    async def complete_phase(self):
        """完成当前阶段（专注或休息）"""
        if self.active_session and self.active_session['phase'] == "focus":
            # 专注阶段完成
            print(">>> 专注阶段完成")

            if self.pomodoro_manager and self.active_session.get('task_id'):
                self.pomodoro_manager.complete_session(
                    self.active_session['task_id'],
                    self.active_session['start_time'],
                    self.duration_minutes
                )

            # 使用安全通知
            # ui.notify('专注完成！进入休息阶段', type='positive')
            print(">>> 进入休息阶段")

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

        elif self.active_session and self.active_session['phase'] == "break":
            # 休息阶段完成
            print(">>> 休息阶段完成")
            #ui.notify('休息完成！准备新一轮专注', type='positive')

            # 重置状态
            self.in_break = False
            self.active_session = None
            self.timer_running = False

            # 更新UI显示专注时间
            self.update_timer_display(self.duration_minutes * 60)
            if self.status_label:
                self.status_label.text = '专注中'

    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = ui.dialog().classes('w-1/2')

        with dialog:
            with ui.card().classes('w-full p-6'):
                ui.label('番茄钟设置').classes('text-h6 mb-4 text-center')

                with ui.row().classes('items-center mb-4 w-full justify-between'):
                    ui.label('专注时长（分钟）').classes('text-lg')
                    input_duration = ui.number(min=1, value=self.duration_minutes).classes('w-32')

                with ui.row().classes('items-center mb-4 w-full justify-between'):
                    ui.label('休息时长（分钟）').classes('text-lg')
                    input_break = ui.number(min=1, value=self.break_minutes).classes('w-32')

                with ui.row().classes('items-center mb-4 w-full justify-between'):
                    ui.label('专注模式').classes('text-lg')
                    focus_switch = ui.switch(value=self.focus_mode)

                def save():
                    try:
                        self.set_duration(int(input_duration.value))
                        self.set_break_duration(int(input_break.value))
                        self.set_focus_mode(focus_switch.value)
                        self.update_timer_display(self.duration_minutes * 60)
                        ui.notify('设置已保存', type='positive')
                        dialog.close()
                    except Exception as e:
                        ui.notify(f'保存失败: {e}', type='negative')

                with ui.row().classes('w-full justify-center'):
                    ui.button('保存设置', on_click=save).classes('mt-4')

        dialog.open()

    def save_settings(self):
        """保存设置"""
        try:
            new_duration = int(self.input_duration.value)
            new_break = int(self.input_break.value)
            new_focus_mode = self.focus_mode_switch.value

            self.set_duration(new_duration)
            self.set_break_duration(new_break)
            self.set_focus_mode(new_focus_mode)

            self.update_timer_display(self.duration_minutes * 60)
            ui.notify('设置已保存', type='positive')
            self.settings_dialog.close()
        except Exception as e:
            ui.notify(f'设置保存失败: {e}', type='negative')

    def start_pomodoro_for_task(self, task_id: int):
        """为特定任务启动番茄钟"""
        if self.timer_running:
            ui.notify('已有活跃的番茄钟', type='warning')
            return

        task = self.task_manager.get_task_by_id(task_id)
        if task:
            self.selected_task = task
            self.show_timer_dialog()
            # 直接启动计时器，而不需要用户再点击开始按钮
            self.start_timer(task_id)
            ui.notify(f'开始专注：{task["title"]}', type='positive')
            print(f"为任务启动番茄钟: {task['title']} (ID: {task_id})")

    def set_selected_task(self, task: Optional[Dict]):
        """设置选中的任务"""
        self.selected_task = task

    def get_active_session(self) -> Optional[Dict]:
        """获取当前活动会话"""
        return self.active_session

    def is_timer_running(self) -> bool:
        """检查计时器是否运行中"""
        return self.timer_running