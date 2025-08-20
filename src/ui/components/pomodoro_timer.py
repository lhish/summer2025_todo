import asyncio
from datetime import datetime
from typing import Dict, Optional, List
from nicegui import ui, app


class PomodoroTimerComponent:
    def __init__(self, pomodoro_manager, task_manager, current_user, settings_manager: Dict, on_task_update=None):
        self.pomodoro_manager = pomodoro_manager
        self.task_manager = task_manager
        self.current_user = current_user
        self.settings_manager = settings_manager  # 添加设置管理器
        self.on_task_update = on_task_update  # 添加UI更新回调

        self.active_session: Optional[Dict] = None
        self.timer_running = False
        self.selected_task: Optional[Dict] = None
        self.paused_remaining = None

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

        # 主题相关属性
        from src.utils.global_config import AVAILABLE_THEMES, get_current_theme
        self.themes = AVAILABLE_THEMES
        self.current_theme = get_current_theme()
        self.is_sound_on = False

        # 创建通知容器
        self.notification_container = ui.element('div').style('display: none')

        # 通知队列
        self.notification_queue = asyncio.Queue()
        self.setup_notification_handler()

        # 从全局设置中加载番茄钟参数
        self.load_settings()

        # 初始化全局音频控制
        self.audio = None
        self.sound_btn = None

    def load_settings(self):
        """从全局设置中加载番茄钟参数"""
        if not self.settings_manager or not self.current_user:
            print("无法加载设置: 缺少设置管理器或当前用户")
            return

        try:
            settings = self.settings_manager.get_user_settings(self.current_user['user_id'])
            # print(f"加载设置: {settings}")

            # 确保使用正确的键获取值
            self.duration_minutes = settings.get('pomodoro_work_duration', 25)
            self.break_minutes = settings.get('pomodoro_short_break_duration', 5)

            # 确保正确获取专注模式值
            self.focus_mode = bool(settings.get('focus_mode', False))
            
            # 从全局变量加载主题设置
            from src.utils.global_config import get_current_theme
            self.current_theme = get_current_theme()

            # print(
            #    f"加载设置成功: duration={self.duration_minutes}, break={self.break_minutes}, focus_mode={self.focus_mode}")
        except Exception as e:
            print(f"加载设置时出错: {e}")
            # 设置默认值
            self.duration_minutes = 25
            self.break_minutes = 5
            self.focus_mode = False
            from src.utils.global_config import get_current_theme
            self.current_theme = get_current_theme()

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
    
    def update_mini_timer_display(self):
        """更新底部迷你计时器显示"""
        # 更新所有已创建的计时器标签
        for label in self.timer_labels:
            label.text = f'{self.duration_minutes:02d}:00'

    def on_settings_updated(self):
        """当设置更新时调用此方法"""
        old_theme = self.current_theme
        old_duration = self.duration_minutes
        self.load_settings()
        new_theme = self.current_theme
        new_duration = self.duration_minutes
        
        # 如果工作时长发生变化，更新底部迷你计时器显示
        if old_duration != new_duration:
            self.update_mini_timer_display()
        
        if old_theme != new_theme:
            print(f"主题已从 {old_theme} 更新为 {new_theme}")
            # 如果计时器对话框正在显示，立即更新主题
            if hasattr(self, 'dialog_container') and self.dialog_container:
                self.change_theme(new_theme)

    def show_timer_dialog(self):
        """显示计时器对话框"""
        print("显示计时器对话框")
        
        # 始终重新加载设置以确保主题是最新的
        self.load_settings()

        # 获取当前主题的图片
        current_theme_data = next((t for t in self.themes if t['name'] == self.current_theme), self.themes[0])
        theme_image = current_theme_data['image']

        # 创建全屏对话框
        dialog = ui.dialog().classes('fullscreen')

        # 根据专注模式设置属性
        if self.focus_mode:
            dialog.props('no-backdrop-dismiss no-esc-dismiss')
        else:
            dialog.props('no-close-on-outside-click')

        with dialog:
            # 使用全屏列布局，背景设置为当前主题的图片
            self.dialog_container = ui.column().classes('w-full h-full items-center justify-center').style(
                f'background-image: url("/static/image/{theme_image}"); '
                f'background-size: cover; '
                f'background-position: center; '
                f'background-repeat: no-repeat;'
            )
            with self.dialog_container:
                # 创建一个固定大小的容器，带有半透明黑色背景
                with ui.column().classes('items-center justify-center rounded-lg').style(
                    'width: 500px; '
                    'height: 600px; '
                    'background-color: rgba(0, 0, 0, 0.7); '
                    'backdrop-filter: blur(5px); '
                    'padding: 2rem;'
                ):
                    
                    # 显示选中的任务标题
                    if self.selected_task:
                        self.task_title_label = ui.label(self.selected_task['title']).classes('text-h5 mb-4 text-white')
                    else:
                        self.task_title_label = ui.label('专注时间').classes('text-h5 mb-4 text-white')

                    # 状态标签
                    status_text = '休息中' if self.in_break else '专注中'
                    self.status_label = ui.label(status_text).classes('text-h6 mb-2 text-white')

                    # 计时器标签 - 创建新的大字体标签
                    label = ui.label(f'{self.duration_minutes:02d}:00').classes('text-8xl font-mono mb-8 text-white')
                    self.timer_labels.append(label)

                    # 按钮行 - 居中显示
                    with ui.row().classes('gap-4'):
                        ui.button('开始', icon='play_arrow', on_click=lambda: self.start_timer()).props(
                            'size=lg color=white flat')
                        ui.button('暂停', icon='pause', on_click=self.pause_timer).props('size=lg color=white flat')
                        ui.button('重置', icon='refresh', on_click=self.reset_timer).props('size=lg color=white flat')
                        # 调试按钮 - 仅在开发环境中显示
                        ui.button('调试', icon='bug_report', on_click=self.debug_timer).props('size=lg color=red flat')

        dialog.open()
        
        # 立即启动计时器
        self.start_timer()
        
    def show_task_selection_dialog(self):
        """显示任务选择对话框"""
        # 获取当前用户的所有任务
        if not self.current_user or not self.task_manager:
            ui.notify('无法获取任务列表', type='negative')
            return

        tasks = self.task_manager.get_tasks(self.current_user['user_id'], status='pending')

        # 创建任务选择对话框
        dialog = ui.dialog()
        with dialog:
            with ui.card().classes('w-96 bg-gray-900 text-white').style('text-align: center;'):
                ui.label('请选择一个任务开始专注').classes('text-h6 w-full text-center text-white mb-4')

                # 为每个任务创建一个按钮，使用纵向滚动容器
                if tasks:
                    with ui.column().classes('w-full max-h-96 overflow-y-auto'):
                        for task in tasks:
                            task_title = task.get('title', '未命名任务')
                            # 按钮 + tooltip 绑定写法
                            with ui.button(
                                task_title,
                                on_click=lambda t=task: (self.select_task_and_start(t), self.play_ding_sound(), dialog.close())
                            ).classes(
                                'w-full mb-2 bg-gray-800 text-white hover:bg-gray-700 truncate'
                            ).style(
                                'text-align: left; height: auto;'
                            ):
                                ui.tooltip(task_title)
                else:
                    ui.label('暂无可用任务').classes('text-gray-400 w-full text-center')
                    ui.button(
                        '关闭', 
                        on_click=dialog.close
                    ).classes('mt-4 w-full bg-gray-700 text-white hover:bg-gray-600').style('text-align: center;')

        dialog.open()
        
    def select_task_and_start(self, task):
        """选择任务并开始计时"""
        self.selected_task = task
        # 如果计时器对话框中的任务标题标签存在，更新其文本
        if hasattr(self, 'task_title_label') and self.task_title_label:
            self.task_title_label.text = task['title']
        self.play_ding_sound()

        # 启动计时器
        self.start_timer()
        
    def change_theme(self, theme_name):
        """切换主题"""
        print(f"切换主题到: {theme_name}")
        
        # 更新当前主题
        self.current_theme = theme_name
        
        # 更新全局变量中的主题设置
        from src.utils.global_config import set_current_theme
        set_current_theme(theme_name)
        
        # 获取主题数据
        theme = next(t for t in self.themes if t['name'] == theme_name)
        
        # 更新背景图片 - 使用正确的容器对象
        if hasattr(self, 'dialog_container') and self.dialog_container:
            self.dialog_container.style(f'''
                background-image: url("/static/image/{theme["image"]}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            ''')
        
        # 处理音频播放 - 实现重置白噪音功能
        if self.is_sound_on:
            try:
                # 暂停当前音频
                if self.audio:
                    self.audio.pause()
                    print(f"已暂停当前音频: {self.audio.src}")
                
                # 确保音频对象存在
                if not self.audio:
                    self.audio = ui.audio(f"/static/sound/{theme['sound']}").classes('hidden')
                    # 设置循环播放
                    self.audio.on('ended', lambda: self.audio.play())
                else:
                    # 更新音频源
                    self.audio.src = f"/static/sound/{theme['sound']}"
                
                # 通知用户需要手动点击播放按钮
                ui.notify('主题已切换，请点击播放按钮重新开始白噪音', type='info')
                
                # 暂时关闭音频状态，等待用户手动点击播放
                self.is_sound_on = False
                if self.sound_btn:
                    self.sound_btn.props('icon=volume_off')
                
                print(f"主题切换完成，音频源已更新为: {self.audio.src}")
                
            except Exception as e:
                print(f"主题切换时处理音频失败: {e}")
                ui.notify('音频处理失败，请刷新页面重试', type='warning')

    async def _play_theme_audio(self, sound_file):
        """延迟播放主题音频"""
        await asyncio.sleep(0.1)  # 小延迟确保音频对象创建完成
        try:
            if hasattr(self, 'audio') and self.audio:
                self.audio.src = f"/static/sound/{sound_file}"
                self.audio.play()
                print(f"播放新主题音频: {self.audio.src}")
        except Exception as e:
            print(f"延迟播放音频失败: {e}")

    def start_timer(self, task_id: Optional[int] = None):
        """启动计时器"""
        # 每次启动前重新加载设置，确保使用最新配置
        self.load_settings()

        if self.timer_running:
            return  # 避免重复点击

        # 检查是否已选定任务
        if not self.selected_task and task_id is None:
            # 显示任务选择对话框
            self.show_task_selection_dialog()
            return

        # 如果通过任务启动，使用任务提供的task_id
        if task_id is not None:
            task = self.task_manager.get_task_by_id(task_id)
            if task:
                self.selected_task = task
                print(f"🎯 通过参数设置任务: {task['title']} (ID: {task['task_id']})")
        elif self.selected_task:
            # 如果已经有选中的任务，使用其ID
            task_id = self.selected_task.get('task_id')
            print(f"🎯 从已选任务获取ID: {self.selected_task['title']} (ID: {task_id})")

        # 确定当前阶段类型
        phase = "break" if self.in_break else "focus"
        duration = self.break_minutes if self.in_break else self.duration_minutes

        # 检查是否有暂停的会话可以恢复
        if self.active_session and self.paused_remaining is not None:
            # 恢复暂停的会话
            self.active_session['remaining'] = self.paused_remaining
            self.paused_remaining = None
            print(f"恢复计时器: 剩余时间 {self.active_session['remaining']}秒")
        else:
            # 创建新的活动会话
            self.active_session = {
                'task_id': task_id,
                'start_time': datetime.now(),
                'duration': duration * 60,
                'remaining': duration * 60,
                'phase': phase,  # 添加阶段标识
            }
            print(f"创建新计时器: 任务ID={task_id}, 阶段={phase}, 时长={duration}分钟")

        # 启动计时器
        self.timer_running = True
        self.timer_task = asyncio.create_task(self.run_timer())

        # 更新状态标签
        if self.status_label:
            self.status_label.text = '休息中' if self.in_break else '专注中'

        # 发送通知
        ui.notify('计时开始！', type='positive')
        # 播放开始音频
        self.play_ding_sound()
        # print(f"启动计时器: 任务ID={task_id}, 阶段={phase}, 时长={duration}分钟")

    def pause_timer(self):
        """暂停计时器"""
        if self.timer_running and self.active_session:
            self.timer_running = False
            if self.timer_task:
                self.timer_task.cancel()
                self.timer_task = None

            # 保存剩余时间以便恢复
            self.paused_remaining = self.active_session['remaining']
            print(f"计时器已暂停，剩余时间: {self.paused_remaining}秒")
            
            # 更新状态标签
            if self.status_label:
                self.status_label.text = '暂停'

            ui.notify('计时已暂停', type='info')

    def reset_timer(self):
        """重置计时器"""
        # 重新加载设置
        self.load_settings()

        self.timer_running = False
        # if self.timer_task:
        #     self.timer_task.cancel()
        #     self.timer_task = None

        # 清除暂停状态
        self.paused_remaining = None
        self.active_session = None
        self.in_break = False

        self.update_timer_display(self.duration_minutes * 60)
        if self.status_label:
            self.status_label.text = '暂停'

        # 停止白噪音播放并切换声音控制按钮
        if self.is_sound_on:
            self.toggle_sound()

        ui.notify('计时器已重置', type='info')
        print("计时器已重置")

    def debug_timer(self):
        """调试计时器，将当前阶段的剩余时间修改为2秒"""
        if self.active_session:
            self.active_session['remaining'] = 2
            self.update_timer_display(self.active_session['remaining'])
            #ui.notify('调试模式：剩余时间已设置为2秒', type='info')
        else:
            ui.notify('没有活跃的计时器会话', type='warning')

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
                    # 在complete_phase中已经处理了下一阶段的计时器启动，所以这里直接跳出循环
                    break

                # 更新计时器
                await asyncio.sleep(1)
                self.active_session['remaining'] -= 1
                self.update_timer_display(self.active_session['remaining'])

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
        # 获取用户设置
        user_settings = {}
        if self.settings_manager and self.current_user:
            user_settings = self.settings_manager.get_user_settings(self.current_user['user_id']) or {}
        
        # 获取自动开始设置，默认为False
        auto_start_break = user_settings.get('auto_start_break', False)
        auto_start_next_pomodoro = user_settings.get('auto_start_next_pomodoro', False)
        
        if self.active_session and self.active_session['phase'] == "focus":
            # 专注阶段完成
            print(">>> 专注阶段完成")

            # 计算实际专注时长（分钟）
            actual_duration_minutes = max(1, (self.duration_minutes * 60 - self.active_session['remaining']) // 60)

            # 记录专注时长到数据库
            if self.pomodoro_manager and self.current_user:
                task_id = self.active_session.get('task_id')
                print(f">>> 记录专注会话: 用户={self.current_user['user_id']}, 任务={task_id}, 时长={actual_duration_minutes}分钟")
                
                # 使用新的 record_focus_session 方法（会自动增加used_pomodoros）
                session_success = self.pomodoro_manager.record_focus_session(
                    user_id=self.current_user['user_id'],
                    task_id=task_id,
                    duration_minutes=actual_duration_minutes
                )
                print(f">>> 专注会话记录: {'成功' if session_success else '失败'}")
                
                # 如果有任务ID，检查任务完成状态
                if task_id and self.task_manager and session_success:
                    # 获取更新后的任务数据（record_focus_session已经增加了used_pomodoros）
                    updated_task = self.task_manager.get_task_by_id(task_id)
                    if updated_task:
                        print(f">>> 任务状态: {updated_task['title']} - 已用={updated_task['used_pomodoros']}, 预估={updated_task['estimated_pomodoros']}")
                        
                        # 检查是否完成所有预估的番茄数
                        if updated_task['used_pomodoros'] >= updated_task['estimated_pomodoros']:
                            # 自动标记任务为完成
                            completion_success = self.task_manager.toggle_task_status(task_id, 'completed')
                            if completion_success:
                                print(f">>> 🎉 任务 '{updated_task['title']}' 已自动完成！")
                                # 使用安全的通知方式
                                self.safe_notify(f'🎉 任务 "{updated_task["title"]}" 已完成！', 'positive')
                            else:
                                print(">>> ⚠️ 自动完成任务失败")
                        else:
                            remaining = updated_task['estimated_pomodoros'] - updated_task['used_pomodoros']
                            print(f">>> 任务还需要 {remaining} 个番茄")
                            # 使用安全的通知方式
                            self.safe_notify(f'番茄钟完成！还需要 {remaining} 个番茄 🍅', 'positive')
                
                # 调用UI更新回调，刷新任务列表中的番茄显示
                if self.on_task_update:
                    print(">>> 调用UI更新回调")
                    self.on_task_update()
                else:
                    print(">>> ⚠️ 没有UI更新回调")

            # 使用安全通知
            # ui.notify('专注完成！进入休息阶段', type='positive')
            print(">>> 进入休息阶段")
            # 播放结束音频
            self.play_ding_sound()

            # 设置休息阶段
            self.in_break = True
            if self.status_label:
                self.status_label.text = '准备休息（点击按钮开始计时）'

            # 检查是否自动开始休息
            if auto_start_break:
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
                
                # 更新状态标签
                if self.status_label:
                    self.status_label.text = '休息中'
                
                # 重新启动计时器
                self.timer_running = True
                self.timer_task = asyncio.create_task(self.run_timer())
            else:
                # 不自动开始休息，停止计时器
                self.timer_running = False
                self.active_session = None
                self.timer_task = None
                # 提示用户手动点击“开始”按钮开始休息计时
                ui.notify('请手动点击“开始”按钮开始休息计时', type='info')

        elif self.active_session and self.active_session['phase'] == "break":
            # 休息阶段完成
            print(">>> 休息阶段完成")
            # ui.notify('休息完成！准备新一轮专注', type='positive')
            # 播放结束音频
            self.play_ding_sound()

            # 重置状态
            self.in_break = False
            
            # 检查是否自动开始下一个番茄钟
            if auto_start_next_pomodoro:
                # 创建新的专注会话
                self.active_session = {
                    'task_id': self.active_session.get('task_id'),
                    'start_time': datetime.now(),
                    'duration': self.duration_minutes * 60,
                    'remaining': self.duration_minutes * 60,
                    'phase': "focus",
                }
                
                if self.status_label:
                    self.status_label.text = '专注中'
                
                # 更新UI显示专注时间
                self.update_timer_display(self.active_session['remaining'])
                
                # 重新启动计时器
                self.timer_running = True
                self.timer_task = asyncio.create_task(self.run_timer())
            else:
                # 不自动开始下一个番茄钟，停止计时器
                self.active_session = None
                self.timer_running = False
                self.timer_task = None

                # 更新UI显示专注时间
                self.update_timer_display(self.duration_minutes * 60)
                if self.status_label:
                    self.status_label.text = '专注中'
                # 提示用户手动点击“开始”按钮开始下一个番茄钟
                ui.notify('请手动点击“开始”按钮开始下一个番茄钟', type='info')

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
        print(f"🚀 start_pomodoro_for_task 调用，task_id={task_id}")
        
        if self.timer_running:
            print("⚠️ 已有活跃番茄钟运行")
            ui.notify('已有活跃的番茄钟', type='warning')
            return

        task = self.task_manager.get_task_by_id(task_id)
        if task:
            print(f"✅ 获取到任务: {task['title']} (ID: {task['task_id']})")
            self.selected_task = task
            self.show_timer_dialog()
            # 直接启动计时器，而不需要用户再点击开始按钮
            self.start_timer(task_id)
            ui.notify(f'开始专注：{task["title"]}', type='positive')
            print(f"🍅 番茄钟已启动: {task['title']} (ID: {task_id})")
        else:
            print(f"❌ 无法获取任务，task_id={task_id}")
            ui.notify('任务不存在', type='negative')

    def set_selected_task(self, task: Optional[Dict]):
        """设置选中的任务"""
        self.selected_task = task

    def get_active_session(self) -> Optional[Dict]:
        """获取当前活动会话"""
        return self.active_session

    def is_timer_running(self) -> bool:
        """检查计时器是否运行中"""
        return self.timer_running


    def play_ding_sound(self):
        """播放提示音"""
        try:
            # 创建并播放提示音
            self.ding_audio = ui.audio('/static/sound/ding.mp3').classes('hidden')
            self.ding_audio.play()
        except Exception as e:
            print(f"播放提示音失败: {e}")

    def toggle_sound(self):
        """切换白噪音开关"""
        self.is_sound_on = not self.is_sound_on
        
        if self.is_sound_on:
            print("开启白噪音")
            if self.sound_btn:
                self.sound_btn.props('icon=volume_up')
            
            # 获取当前主题
            current_theme = next((t for t in self.themes if t['name'] == self.current_theme), self.themes[0])
            
            # 确保audio对象存在
            if not self.audio:
                self.audio = ui.audio(f"/static/sound/{current_theme['sound']}").classes('hidden')
                # 设置循环播放
                self.audio.on('ended', lambda: self.audio.play())
            else:
                # 更新音频源
                self.audio.src = f"/static/sound/{current_theme['sound']}"
            
            # 尝试播放音频
            try:
                self.audio.play()
                print(f"正在播放音频: {self.audio.src}")
                ui.notify('白噪音已开启', type='positive')
            except Exception as e:
                print(f"播放音频失败: {e}")
                # ui.notify('音频播放失败，请稍后重试', type='warning')
                
        else:
            print("关闭白噪音")
            if self.sound_btn:
                self.sound_btn.props('icon=volume_off')
            if self.audio:
                try:
                    self.audio.pause()
                    print("白噪音已暂停")
                except Exception as e:
                    print(f"暂停音频失败: {e}")
            
            ui.notify('白噪音已关闭', type='info')
        
        print(f"白噪音状态: {'开启' if self.is_sound_on else '关闭'}")

    def create_sound_control(self, container=None, **kwargs):
        """创建全局声音控制按钮
        
        Args:
            container: 容器对象，如果为None则使用默认容器
            **kwargs: 额外的props和classes参数
        """
        if container is None:
            container = ui
            
        # 合并props和classes
        props = kwargs.get('props', 'flat round')
        classes = kwargs.get('classes', 'text-white')
        
        with container:
            self.sound_btn = ui.button(
                icon='volume_up' if self.is_sound_on else 'volume_off',
                on_click=self.toggle_sound
            ).props(props).classes(classes)
        
        return self.sound_btn