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
        print("DEBUG: PomodoroTimerComponent - 初始化完成")

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
        self.timer_dialog = None # 用于存储计时器对话框实例

        # 主题相关属性
        from src.utils.global_config import AVAILABLE_THEMES, get_current_theme
        self.themes = AVAILABLE_THEMES
        self.current_theme = get_current_theme()
        # 移除 is_sound_on 属性，因为背景音乐将始终播放

        # 创建通知容器
        self.notification_container = ui.element('div').style('display: none')

        # 通知队列
        self.notification_queue = asyncio.Queue()
        self.setup_notification_handler()

        # 从全局设置中加载番茄钟参数
        self.load_settings()

        # 初始化全局音频控制
        self.audio = None
        
        # 在初始化时创建提示音对象，并将其放置在通知容器中
        with self.notification_container:
            self.ding_audio = ui.audio('/static/sound/ding.mp3').classes('hidden')
            
        # 创建白噪音播放器（不在通知容器中）
        current_theme_data = next((t for t in self.themes if t['name'] == self.current_theme), self.themes[0])
        self.audio = ui.audio(f"/static/sound/{current_theme_data['sound']}").classes('hidden')
        # 设置循环播放
        self.audio.on('ended', lambda: self.audio.play())

    def load_settings(self):
        """从全局设置中加载番茄钟参数"""
        print("DEBUG: load_settings - 尝试加载设置")
        if not self.settings_manager or not self.current_user:
            print("DEBUG: load_settings - 无法加载设置: 缺少设置管理器或当前用户")
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
            print(f"DEBUG: load_settings - 加载设置时出错: {e}")
            # 设置默认值
            self.duration_minutes = 25
            self.break_minutes = 5
            self.focus_mode = False
            from src.utils.global_config import get_current_theme
            self.current_theme = get_current_theme()
            print(f"DEBUG: load_settings - 已设置默认值: duration={self.duration_minutes}, break={self.break_minutes}, focus_mode={self.focus_mode}")

    def setup_notification_handler(self):
        """设置通知处理程序"""

        async def process_notifications():
            while True:
                message, notify_type = await self.notification_queue.get()

                # 直接调用发送通知方法
                self.send_notification(message, notify_type)

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
        print("DEBUG: on_settings_updated - 设置更新被触发")
        old_theme = self.current_theme
        old_duration = self.duration_minutes
        self.load_settings()
        new_theme = self.current_theme
        new_duration = self.duration_minutes
        
        # 如果工作时长发生变化，更新底部迷你计时器显示
        if old_duration != new_duration:
            print(f"DEBUG: on_settings_updated - 工作时长从 {old_duration} 变为 {new_duration}，更新迷你计时器显示")
            self.update_mini_timer_display()
        
        if old_theme != new_theme:
            print(f"DEBUG: on_settings_updated - 主题已从 {old_theme} 更新为 {new_theme}")
            # 如果计时器对话框正在显示，立即更新主题
            if hasattr(self, 'dialog_container') and self.dialog_container:
                self.change_theme(new_theme)
        print("DEBUG: on_settings_updated - 设置更新处理完成")

    def show_timer_dialog(self):
        """显示计时器对话框"""
        print("显示计时器对话框")
        
        # 始终重新加载设置以确保主题是最新的
        self.load_settings()

        # 获取当前主题的图片
        current_theme_data = next((t for t in self.themes if t['name'] == self.current_theme), self.themes[0])
        theme_image = current_theme_data['image']

        # 创建全屏对话框并存储为实例变量
        self.timer_dialog = ui.dialog().classes('fullscreen')

        # 根据专注模式设置属性
        if self.focus_mode:
            self.timer_dialog.props('no-backdrop-dismiss no-esc-dismiss')
        else:
            self.timer_dialog.props('no-close-on-outside-click')

        with self.timer_dialog:
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

        self.timer_dialog.open()
        
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
        print(f"DEBUG: select_task_and_start - 选中任务: {task['title']} (ID: {task['task_id']})")

        # 启动计时器
        self.start_timer()
        print(f"DEBUG: select_task_and_start - 计时器已尝试启动")
        
    def change_theme(self, theme_name):
        """切换主题"""
        print(f"DEBUG: change_theme - 调用，切换主题到: {theme_name}")
        
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
        try:
            # 暂停当前音频
            if self.audio:
                self.audio.pause()
                print(f"已暂停当前音频: {self.audio.src}")
            
            # 更新音频源
            self.audio.src = f"/static/sound/{theme['sound']}"
            
            # 如果音频之前在播放，则继续播放新主题音频
            if self.timer_running:
                asyncio.create_task(self._play_theme_audio(theme['sound']))
            
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
                print(f"DEBUG: _play_theme_audio - 播放新主题音频: {self.audio.src}")
        except Exception as e:
            print(f"DEBUG: _play_theme_audio - 延迟播放音频失败: {e}")
    
    def start_timer(self, task_id: Optional[int] = None):
        """启动计时器"""
        print(f"DEBUG: start_timer - 开始启动计时器，传入task_id: {task_id}")
        # 每次启动前重新加载设置，确保使用最新配置
        self.load_settings()
        print(f"DEBUG: start_timer - 设置加载完成: duration={self.duration_minutes}, break={self.break_minutes}, focus_mode={self.focus_mode}")

        print(f"DEBUG: start_timer - 调用，当前timer_running={self.timer_running}, selected_task={self.selected_task['title'] if self.selected_task else 'None'}, task_id参数={task_id}")

        if self.timer_running:
            print("DEBUG: start_timer - 计时器已在运行，避免重复点击")
            return  # 避免重复点击

        # 检查是否已选定任务
        if not self.selected_task and task_id is None:
            print("DEBUG: start_timer - 未选定任务，显示任务选择对话框")
            self.show_task_selection_dialog()
            return
        
        # 如果已选任务，检查任务是否已完成
        if self.selected_task:
            current_task_status = self.task_manager.get_task_by_id(self.selected_task['task_id'])['status']
            if current_task_status == 'completed':
                self.safe_notify(f"任务 '{self.selected_task['title']}' 已完成，无法开始新的番茄钟。", notify_type='info')
                print(f"DEBUG: start_timer - 任务 '{self.selected_task['title']}' 已完成，无法开始新的番茄钟。")
                # 关闭计时器对话框
                if self.timer_dialog:
                    print("DEBUG: start_timer - 任务已完成，关闭计时器对话框")
                    self.timer_dialog.close()
                self.selected_task = None # 清除已选任务
                return

        # 如果通过任务启动，使用任务提供的task_id
        if task_id is not None:
            task = self.task_manager.get_task_by_id(task_id)
            if task:
                self.selected_task = task
                print(f"DEBUG: start_timer - 🎯 通过参数设置任务: {task['title']} (ID: {task['task_id']})")
        elif self.selected_task:
            # 如果已经有选中的任务，使用其ID
            task_id = self.selected_task.get('task_id')
            print(f"DEBUG: start_timer - 🎯 从已选任务获取ID: {self.selected_task['title']} (ID: {task_id})")
        else:
            print("DEBUG: start_timer - ⚠️ 没有选中的任务，也未提供task_id参数")
            return # 应该不会走到这里，但以防万一

        # 确定当前阶段类型
        phase = "break" if self.in_break else "focus"
        duration = self.break_minutes if self.in_break else self.duration_minutes
        print(f"DEBUG: start_timer - 当前阶段={phase}, 时长={duration}分钟")

        # 检查是否有暂停的会话可以恢复
        if self.active_session and self.paused_remaining is not None:
            # 恢复暂停的会话
            self.active_session['remaining'] = self.paused_remaining
            self.paused_remaining = None
            print(f"DEBUG: start_timer - 恢复计时器: 剩余时间 {self.active_session['remaining']}秒")
        else:
            # 创建新的活动会话
            self.active_session = {
                'task_id': task_id,
                'start_time': datetime.now(),
                'duration': duration * 60,
                'remaining': duration * 60,
                'phase': phase,  # 添加阶段标识
            }
            print(f"DEBUG: start_timer - 创建新计时器会话: {self.active_session}")

        # 启动计时器
        self.timer_running = True
        self.timer_task = asyncio.create_task(self.run_timer())

        # 更新状态标签
        if self.status_label:
            self.status_label.text = '休息中' if self.in_break else '专注中'

        # 启动白噪音播放
        self.start_background_sound()
        
        # 发送通知
        ui.notify('计时开始！', type='positive')
        # 播放开始音频
        self.play_ding_sound()
        print(f"DEBUG: start_timer - 计时器启动成功")

    def pause_timer(self):
        """暂停计时器"""
        print(f"DEBUG: pause_timer - 调用，当前timer_running={self.timer_running}, active_session={self.active_session}")
        if self.timer_running and self.active_session:
            self.timer_running = False
            if self.timer_task:
                self.timer_task.cancel()
                self.timer_task = None

            # 保存剩余时间以便恢复
            self.paused_remaining = self.active_session['remaining']
            print(f"DEBUG: pause_timer - 计时器已暂停，剩余时间: {self.paused_remaining}秒")
            
            # 更新状态标签
            if self.status_label:
                self.status_label.text = '暂停'

            # 停止白噪音播放
            self.stop_background_sound()
            
            ui.notify('计时已暂停', type='info')
        else:
            print("DEBUG: pause_timer - 计时器未运行或无活跃会话，无法暂停")

    def reset_timer(self):
        """重置计时器"""
        print("DEBUG: reset_timer - 调用")
        # 重新加载设置
        self.load_settings()

        self.timer_running = False
        if self.timer_task: # 确保取消正在运行的任务
            self.timer_task.cancel()
            self.timer_task = None

        # 清除暂停状态
        self.paused_remaining = None
        self.active_session = None
        self.in_break = False

        self.update_timer_display(self.duration_minutes * 60)
        if self.status_label:
            self.status_label.text = '暂停'

        # 停止白噪音播放
        self.stop_background_sound()

        ui.notify('计时器已重置', type='info')
        print("DEBUG: reset_timer - 计时器已重置")

    def debug_timer(self):
        """调试计时器，将当前阶段的剩余时间修改为2秒"""
        print("DEBUG: debug_timer - 调用")
        if self.active_session:
            self.active_session['remaining'] = 2
            self.update_timer_display(self.active_session['remaining'])
            ui.notify('调试模式：剩余时间已设置为2秒', type='info')
            print("DEBUG: debug_timer - 调试模式：剩余时间已设置为2秒")
        else:
            ui.notify('没有活跃的计时器会话', type='warning')
            print("DEBUG: debug_timer - 没有活跃的计时器会话")

    async def run_timer(self):
        """运行计时器循环"""
        try:
            print("DEBUG: run_timer - 计时器开始运行")
            while self.timer_running and self.active_session:
                print(f"DEBUG: run_timer - 循环中，剩余时间: {self.active_session['remaining']}秒")
                # 检查剩余时间
                if self.active_session['remaining'] <= 0:
                    print("DEBUG: run_timer - 时间到，完成阶段")
                    # 完成当前阶段
                    await self.complete_phase()
                    # 在complete_phase中已经处理了下一阶段的计时器启动，所以这里直接跳出循环
                    break

                # 更新计时器
                await asyncio.sleep(1)
                self.active_session['remaining'] -= 1
                self.update_timer_display(self.active_session['remaining'])

        except asyncio.CancelledError:
            print("DEBUG: run_timer - 计时任务被取消")
        except Exception as e:
            print(f"DEBUG: run_timer - 计时器错误: {e}")
        finally:
            # 清理任务引用
            self.timer_task = None
            print("DEBUG: run_timer - 计时器任务结束")

    def update_timer_display(self, seconds: int):
        """更新计时器显示"""
        minutes = seconds // 60
        sec = seconds % 60
        time_str = f'{minutes:02d}:{sec:02d}'
        print(f"DEBUG: update_timer_display - 更新显示为: {time_str}, 剩余秒数: {seconds}")
        for label in self.timer_labels:
            label.text = time_str

    async def complete_phase(self):
        """完成当前阶段（专注或休息）"""
        print(f"DEBUG: complete_phase - 调用，当前阶段: {self.active_session['phase'] if self.active_session else 'None'}")
        # 获取用户设置
        user_settings = {}
        if self.settings_manager and self.current_user:
            user_settings = self.settings_manager.get_user_settings(self.current_user['user_id']) or {}
            print(f"DEBUG: complete_phase - 用户设置: {user_settings}")
        
        # 获取自动开始设置，默认为False
        auto_start_break = user_settings.get('auto_start_break', False)
        auto_start_next_pomodoro = user_settings.get('auto_start_next_pomodoro', False)
        print(f"DEBUG: complete_phase - auto_start_break={auto_start_break}, auto_start_next_pomodoro={auto_start_next_pomodoro}")
        
        if self.active_session and self.active_session['phase'] == "focus":
            # 专注阶段完成
            print("DEBUG: complete_phase - >>> 专注阶段完成")

            # 计算实际专注时长（分钟）
            actual_duration_minutes = max(1, (self.duration_minutes * 60 - self.active_session['remaining']) // 60)
            print(f"DEBUG: complete_phase - 实际专注时长: {actual_duration_minutes}分钟")

            # 记录专注时长到数据库
            if self.pomodoro_manager and self.current_user:
                task_id = self.active_session.get('task_id')
                print(f"DEBUG: complete_phase - >>> 记录专注会话: 用户={self.current_user['user_id']}, 任务={task_id}, 时长={actual_duration_minutes}分钟")
                
                # 使用新的 record_focus_session 方法（会自动增加used_pomodoros）
                session_success = self.pomodoro_manager.record_focus_session(
                    user_id=self.current_user['user_id'],
                    task_id=task_id,
                    duration_minutes=actual_duration_minutes
                )
                print(f"DEBUG: complete_phase - >>> 专注会话记录: {'成功' if session_success else '失败'}")
                
                # 如果有任务ID，检查任务完成状态
                if task_id and self.task_manager and session_success:
                    # 获取更新后的任务数据（record_focus_session已经增加了used_pomodoros）
                    updated_task = self.task_manager.get_task_by_id(task_id)
                    if updated_task:
                        print(f"DEBUG: complete_phase - >>> 任务 '{updated_task['title']}' (ID: {task_id}) 更新后状态: 已用={updated_task['used_pomodoros']}, 预估={updated_task['estimated_pomodoros']}")
                        
                        # 检查是否完成所有预估的番茄数
                        if updated_task['used_pomodoros'] >= updated_task['estimated_pomodoros']:
                            print(f"DEBUG: complete_phase - 任务 '{updated_task['title']}' 达到预估番茄数，尝试自动完成")
                            # 自动标记任务为完成
                            completion_success = self.task_manager.toggle_task_status(task_id, 'completed')
                            if completion_success:
                                print(f"DEBUG: complete_phase - >>> 🎉 任务 '{updated_task['title']}' 已自动完成！")
                                # 使用安全的通知方式
                                self.safe_notify(f'🎉 任务 "{updated_task["title"]}" 已完成！', notify_type='positive')
                                # 任务已完成，但继续进行休息阶段，不立即关闭对话框
                                # 标记任务已完成，以便在休息结束后处理
                                self.task_completed_during_pomodoro = True
                            else:
                                print("DEBUG: complete_phase - >>> ⚠️ 自动完成任务失败")
                        else:
                            remaining = updated_task['estimated_pomodoros'] - updated_task['used_pomodoros']
                            print(f"DEBUG: complete_phase - >>> 任务还需要 {remaining} 个番茄")
                            # 使用安全的通知方式
                            self.safe_notify(f'番茄钟完成！还需要 {remaining} 个番茄 🍅', notify_type='positive')
                    else:
                        print(f"DEBUG: complete_phase - ⚠️ 无法获取更新后的任务 (ID: {task_id})")
                
                # 调用UI更新回调，刷新任务列表中的番茄显示
                if self.on_task_update:
                    print("DEBUG: complete_phase - >>> 调用UI更新回调以刷新任务列表")
                    self.on_task_update()
                else:
                    print("DEBUG: complete_phase - >>> ⚠️ 没有UI更新回调，任务列表可能不会自动刷新")

            # 使用安全通知
            self.safe_notify('专注完成！进入休息阶段', notify_type='positive') # 统一通知方式
            print("DEBUG: complete_phase - >>> 进入休息阶段")
            # 播放结束音频
            self.play_ding_sound()

            # 设置休息阶段
            self.in_break = True
            if self.status_label:
                self.status_label.text = '准备休息（点击按钮开始计时）'
            print("DEBUG: complete_phase - 设置in_break为True, 状态标签更新")

            # 检查是否自动开始休息
            if auto_start_break:
                print("DEBUG: complete_phase - 自动开始休息")
                # 创建休息会话
                self.active_session = {
                    'task_id': None, # 休息阶段不关联任务
                    'start_time': datetime.now(),
                    'duration': self.break_minutes * 60,
                    'remaining': self.break_minutes * 60,
                    'phase': "break",
                }
                print(f"DEBUG: complete_phase - 新休息会话: {self.active_session}")

                # 更新UI显示休息时间
                self.update_timer_display(self.active_session['remaining'])
                
                # 更新状态标签
                if self.status_label:
                    self.status_label.text = '休息中'
                
                # 重新启动计时器
                self.timer_running = True
                self.timer_task = asyncio.create_task(self.run_timer())
                print("DEBUG: complete_phase - 休息计时器已重新启动")
            else:
                print("DEBUG: complete_phase - 不自动开始休息，停止计时器")
                # 不自动开始休息，停止计时器
                self.timer_running = False
                self.active_session = None # 清除活动会话
                if self.timer_task: # 确保取消任务
                    self.timer_task.cancel()
                    self.timer_task = None
                # 如果有对话框，关闭它
                if self.timer_dialog:
                    print("DEBUG: complete_phase - 专注阶段完成，不自动开始休息，关闭计时器对话框")
                    self.timer_dialog.close()
                # 提示用户手动点击“开始”按钮开始休息计时
                self.safe_notify('请手动点击“开始”按钮开始休息计时', notify_type='info') # 统一通知方式

        elif self.active_session and self.active_session['phase'] == "break":
            # 休息阶段完成
            print("DEBUG: complete_phase - >>> 休息阶段完成")
            self.safe_notify('休息完成！准备新一轮专注', notify_type='positive') # 统一通知方式
            # 播放结束音频
            self.play_ding_sound()

            # 重置状态
            self.in_break = False
            print("DEBUG: complete_phase - 设置in_break为False")
            
            # 如果任务在专注阶段完成，则在休息阶段结束后关闭对话框
            if hasattr(self, 'task_completed_during_pomodoro') and self.task_completed_during_pomodoro:
                print("DEBUG: complete_phase - 任务在专注阶段已完成，现在关闭对话框")
                self.safe_notify('任务已完成，番茄钟结束', notify_type='info')
                self.selected_task = None # 清除已选任务
                self.timer_running = False
                self.active_session = None
                if self.timer_task:
                    self.timer_task.cancel()
                    self.timer_task = None
                if self.timer_dialog:
                    print("DEBUG: complete_phase - 任务在专注阶段已完成，休息阶段结束，关闭计时器对话框")
                    self.timer_dialog.close()
                self.task_completed_during_pomodoro = False # 重置标记
                return # 任务已完成，不再自动开始下一个番茄钟

            # 检查是否自动开始下一个番茄钟
            if auto_start_next_pomodoro:
                # 检查 self.selected_task 是否为 None （即任务已完成）
                if self.selected_task is None:
                    print("DEBUG: complete_phase - 任务已完成，不自动开始下一个番茄钟")
                    self.safe_notify('任务已完成，请手动选择新任务开始番茄钟', notify_type='info')
                    # 停止计时器，关闭对话框
                    self.timer_running = False
                    self.active_session = None
                    if self.timer_task:
                        self.timer_task.cancel()
                        self.timer_task = None
                    if self.timer_dialog:
                        print("DEBUG: complete_phase - 休息阶段完成，任务已完成，不自动开始下一个番茄钟，关闭计时器对话框")
                        self.timer_dialog.close()
                    # 更新UI显示专注时间
                    self.update_timer_display(self.duration_minutes * 60)
                    if self.status_label:
                        self.status_label.text = '专注中'
                else:
                    print("DEBUG: complete_phase - 自动开始下一个番茄钟")
                    # 创建新的专注会话
                    # 关键点：这里需要使用 self.selected_task 中的 task_id，而不是 active_session 中的
                    self.active_session = {
                        'task_id': self.selected_task.get('task_id') if self.selected_task else None,
                        'start_time': datetime.now(),
                        'duration': self.duration_minutes * 60,
                        'remaining': self.duration_minutes * 60,
                        'phase': "focus",
                    }
                    print(f"DEBUG: complete_phase - 新专注会话: {self.active_session}")
                    
                    if self.status_label:
                        self.status_label.text = '专注中'
                    
                    # 更新UI显示专注时间
                    self.update_timer_display(self.active_session['remaining'])
                    
                    # 重新启动计时器
                    self.timer_running = True
                    self.timer_task = asyncio.create_task(self.run_timer())
                    print("DEBUG: complete_phase - 专注计时器已重新启动")
            else:
                print("DEBUG: complete_phase - 不自动开始下一个番茄钟，停止计时器")
                # 不自动开始下一个番茄钟，停止计时器
                self.active_session = None # 清除活动会话
                self.timer_running = False
                if self.timer_task: # 确保取消任务
                    self.timer_task.cancel()
                    self.timer_task = None
                # 如果有对话框，关闭它
                if self.timer_dialog:
                    print("DEBUG: complete_phase - 休息阶段完成，不自动开始下一个番茄钟，关闭计时器对话框")
                    self.timer_dialog.close()
                # 更新UI显示专注时间
                self.update_timer_display(self.duration_minutes * 60)
                if self.status_label:
                    self.status_label.text = '专注中'
                # 提示用户手动点击“开始”按钮开始下一个番茄钟
                self.safe_notify('请手动点击“开始”按钮开始下一个番茄钟', notify_type='info') # 统一通知方式

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
        print(f"DEBUG: start_pomodoro_for_task - 调用，task_id={task_id}")
        
        if self.timer_running:
            print("DEBUG: start_pomodoro_for_task - ⚠️ 已有活跃番茄钟运行")
            ui.notify('已有活跃的番茄钟', type='warning')
            return

        task = self.task_manager.get_task_by_id(task_id)
        if task:
            print(f"DEBUG: start_pomodoro_for_task - ✅ 获取到任务: {task['title']} (ID: {task['task_id']})")
            self.selected_task = task
            self.show_timer_dialog()
            # 直接启动计时器，而不需要用户再点击开始按钮
            self.start_timer(task_id)
            ui.notify(f'开始专注：{task["title"]}', type='positive')
            print(f"DEBUG: start_pomodoro_for_task - 🍅 番茄钟已启动: {task['title']} (ID: {task_id})")
        else:
            print(f"DEBUG: start_pomodoro_for_task - ❌ 无法获取任务，task_id={task_id}")
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
            self.ding_audio.play()
        except Exception as e:
            print(f"播放提示音失败: {e}")
            
    def start_background_sound(self):
        """开始播放背景白噪音"""
        if self.audio:
            try:
                # 检查当前主题
                current_theme_data = next((t for t in self.themes if t['name'] == self.current_theme), self.themes[0])
                # 更新音频源确保是当前主题
                self.audio.src = f"/static/sound/{current_theme_data['sound']}"
                self.audio.play()
                print(f"DEBUG: start_background_sound - 开始播放背景音频: {self.audio.src}")
            except Exception as e:
                print(f"DEBUG: start_background_sound - 播放背景音频失败: {e}")
        else:
            print("DEBUG: start_background_sound - 音频未启用或audio对象不存在")
            
    def stop_background_sound(self):
        """停止播放背景白噪音"""
        if self.audio:
            try:
                self.audio.pause()
                print("DEBUG: stop_background_sound - 背景音频已暂停")
            except Exception as e:
                print(f"DEBUG: stop_background_sound - 暂停背景音频失败: {e}")
        else:
            print("DEBUG: stop_background_sound - audio对象不存在")
