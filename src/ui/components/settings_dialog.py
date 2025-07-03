"""
设置对话框组件
"""

from nicegui import ui, app
from typing import Dict, Callable


class SettingsDialogComponent:
    def __init__(self, settings_manager, current_user: Dict, on_logout: Callable = None, on_settings_updated: Callable = None):
        self.settings_manager = settings_manager
        self.current_user = current_user
        self.on_logout = on_logout
        self.on_settings_updated = on_settings_updated
        self.current_section = '番茄钟'  # 默认选中的分类
        self.navigation_container = None  # 存储导航容器的引用

    def show_settings_dialog(self):
        """显示设置对话框"""
        settings = self.settings_manager.get_user_settings(self.current_user['user_id'])

        with ui.dialog().classes('w-4xl max-w-4xl') as dialog:
            with ui.card().classes('w-full gap-0').style('height: 600px; padding: 0; border-radius: 8px; overflow: hidden;'):
                # 标题栏
                with ui.row().classes('w-full items-center bg-primary text-white').style('margin: 0; padding: 16px; position: relative;'):
                    ui.button(icon='close', on_click=dialog.close).props('flat color=white size=sm').style('position: absolute; right: 16px;')
                    ui.label('设置').classes('text-h5 font-bold w-full text-center')

                # 主体内容区域
                with ui.row().classes('w-full').style('height: 540px; margin: 0;'):
                    # 左侧导航栏
                    with ui.column().classes('').style('width: 200px; min-width: 200px; height: 100%; padding: 16px; margin: 0; background: #f5f5f5;') as nav_container:
                        self.navigation_container = nav_container
                        self.create_navigation()

                    # 右侧内容区域
                    with ui.column().classes('flex-1').style('height: 100%; padding: 0; margin: 0; overflow-y: auto; background: transparent;') as content_area:
                        self.content_area = content_area
                        self.render_content(settings)

        dialog.open()

    def create_navigation(self):
        """创建左侧导航栏"""
        sections = [
            {'name': '番茄钟', 'icon': 'timer'},
            {'name': '通知设置', 'icon': 'notifications'},
            {'name': '目标设置', 'icon': 'flag'},
            {'name': '账户操作', 'icon': 'settings'}
        ]

        for section in sections:
            is_active = self.current_section == section['name']
            
            # 根据是否选中设置不同的样式
            if is_active:
                button_style = 'background: #5898d4 !important; color: white !important; border-radius: 6px; margin-bottom: 8px; padding: 8px 12px;'
                button_props = 'flat no-caps'
            else:
                button_style = 'background: transparent; color: #424242; border-radius: 6px; margin-bottom: 8px; padding: 8px 12px;'
                button_props = 'flat no-caps'

            ui.button(
                section['name'],
                icon=section['icon'],
                on_click=lambda s=section['name']: self.switch_section(s)
            ).classes('w-full justify-start').style(button_style).props(button_props)

    def switch_section(self, section_name: str):
        """切换设置分类"""
        self.current_section = section_name
        
        # 重新渲染导航栏以更新选中状态
        self.navigation_container.clear()
        with self.navigation_container:
            self.create_navigation()
        
        # 获取设置并渲染内容
        settings = self.settings_manager.get_user_settings(self.current_user['user_id'])
        self.content_area.clear()
        with self.content_area:
            self.render_content(settings)

    def render_content(self, settings: Dict):
        """渲染右侧内容区域"""
        if self.current_section == '番茄钟':
            self.render_pomodoro_settings(settings)
        elif self.current_section == '通知设置':
            self.render_notification_settings(settings)
        elif self.current_section == '目标设置':
            self.render_goal_settings(settings)
        elif self.current_section == '账户操作':
            self.render_account_actions()

    def render_pomodoro_settings(self, settings: Dict):
        """渲染番茄钟设置"""
        ui.label('番茄钟设置').classes('text-h6 mt-4 mb-0 text-primary')
        ui.separator().classes('mb-4')

        with ui.column().classes('gap-4').style('max-width: 400px;'):
            work_duration = ui.number(
                label='工作时长（分钟）',
                value=settings.get('pomodoro_work_duration', 25),
                min=1, max=60
            ).classes('w-full')

            short_break = ui.number(
                label='短休息时长（分钟）',
                value=settings.get('pomodoro_short_break_duration', 5),
                min=1, max=30
            ).classes('w-full')

            long_break = ui.number(
                label='长休息时长（分钟）',
                value=settings.get('pomodoro_long_break_duration', 15),
                min=1, max=60
            ).classes('w-full')

            long_break_interval = ui.number(
                label='长休息间隔（工作轮数）',
                value=settings.get('pomodoro_long_break_interval', 4),
                min=1, max=10
            ).classes('w-full')

            ui.button(
                '保存番茄钟设置',
                icon='save',
                on_click=lambda: self.save_pomodoro_settings({
                    'pomodoro_work_duration': int(work_duration.value),
                    'pomodoro_short_break_duration': int(short_break.value),
                    'pomodoro_long_break_duration': int(long_break.value),
                    'pomodoro_long_break_interval': int(long_break_interval.value)
                })
            ).props('color=primary').classes('mt-4')

    def render_notification_settings(self, settings: Dict):
        """渲染通知设置"""
        ui.label('通知设置').classes('text-h6 mt-4 mb-1 text-primary')
        ui.separator().classes('mb-4')

        with ui.column().classes('gap-4').style('max-width: 400px;'):
            notification_sound = ui.select(
                label='通知声音',
                options={
                    'default': '默认',
                    'bell': '铃声',
                    'chime': '钟声',
                    'none': '静音'
                },
                value=settings.get('notification_sound', 'default')
            ).classes('w-full')

            auto_start_next = ui.checkbox(
                '自动开始下一个番茄钟',
                value=bool(settings.get('auto_start_next_pomodoro', False))
            ).classes('w-full')

            auto_start_break = ui.checkbox(
                '自动开始休息',
                value=bool(settings.get('auto_start_break', False))
            ).classes('w-full')

            ui.button(
                '保存通知设置',
                icon='save',
                on_click=lambda: self.save_notification_settings({
                    'notification_sound': notification_sound.value,
                    'auto_start_next_pomodoro': auto_start_next.value,
                    'auto_start_break': auto_start_break.value
                })
            ).props('color=primary').classes('mt-4')

    def render_goal_settings(self, settings: Dict):
        """渲染目标设置"""
        ui.label('目标设置').classes('text-h6 mt-4 mb-1 text-primary')
        ui.separator().classes('mb-4')

        with ui.column().classes('gap-4').style('max-width: 400px;'):
            daily_target = ui.number(
                label='每日专注目标（分钟）',
                value=settings.get('daily_focus_target_minutes', 120),
                min=1
            ).classes('w-full')

            # 显示今日进度
            progress_data = self.settings_manager.get_daily_focus_goal_progress(self.current_user['user_id'])
            progress_value = progress_data['progress_percentage'] / 100
            
            ui.label(f"今日进度：{progress_data['completed_minutes']}/{progress_data['target_minutes']} 分钟").classes('text-body1 mt-2')
            
            with ui.linear_progress(value=progress_value, show_value=False, size='1.5em').classes('w-full').props('instant-feedback'):
                ui.label(f'{progress_data["progress_percentage"]:.2f}%').classes('text-sm text-black absolute-center font-medium')

            ui.button(
                '保存目标设置',
                icon='save', 
                on_click=lambda: self.save_goal_settings({
                    'daily_focus_target_minutes': int(daily_target.value)
                })
            ).props('color=primary').classes('mt-4')

    def render_account_actions(self):
        """渲染账户操作"""
        ui.label('账户操作').classes('text-h6 mt-4 mb-1 text-primary')
        ui.separator().classes('mb-4')

        with ui.column().classes('gap-4').style('max-width: 400px;'):
            ui.button(
                '修改密码',
                icon='lock',
                on_click=self.show_change_password_dialog
            ).props('color=secondary').classes('w-full')

            #ui.button(
            #    '导出数据',
            #    icon='download',
            #    on_click=self.export_user_data
            #).props('color=accent').classes('w-full')

            ui.button(
                '退出登录',
                icon='logout',
                on_click=self.handle_logout
            ).props('color=negative').classes('w-full')

    def save_pomodoro_settings(self, settings_data: Dict):
        """保存番茄钟设置"""
        success = self.settings_manager.update_user_settings(
            self.current_user['user_id'],
            settings_data
        )

        if success:
            ui.notify('番茄钟设置已保存', type='positive', icon='check')
            app.storage.user['settings_updated'] = True
            # 通知主页面刷新任务列表
            if self.on_settings_updated:
                self.on_settings_updated()
        else:
            ui.notify('保存失败', type='negative', icon='error')

    def save_notification_settings(self, settings_data: Dict):
        """保存通知设置"""
        success = self.settings_manager.update_user_settings(
            self.current_user['user_id'],
            settings_data
        )

        if success:
            ui.notify('通知设置已保存', type='positive', icon='check')
            app.storage.user['settings_updated'] = True
        else:
            ui.notify('保存失败', type='negative', icon='error')

    def save_goal_settings(self, settings_data: Dict):
        """保存目标设置"""
        success = self.settings_manager.update_user_settings(
            self.current_user['user_id'],
            settings_data
        )

        if success:
            ui.notify('目标设置已保存', type='positive', icon='check')
            app.storage.user['settings_updated'] = True
            # 刷新进度显示
            settings = self.settings_manager.get_user_settings(self.current_user['user_id'])
            self.content_area.clear()
            with self.content_area:
                self.render_content(settings)
        else:
            ui.notify('保存失败', type='negative', icon='error')

    def show_change_password_dialog(self):
        """显示修改密码对话框"""
        with ui.dialog() as password_dialog:
            with ui.card().classes('w-96').style('padding: 24px;'):
                ui.label('修改密码').classes('text-h6 mb-4')

                old_password = ui.input('当前密码', password=True).classes('w-full mb-4')
                new_password = ui.input('新密码', password=True).classes('w-full mb-4')
                confirm_password = ui.input('确认新密码', password=True).classes('w-full mb-4')

                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('取消', on_click=password_dialog.close).props('flat')
                    ui.button('确认', on_click=lambda: self.change_password(
                        old_password.value, new_password.value, confirm_password.value, password_dialog
                    )).props('color=primary')

        password_dialog.open()

    def change_password(self, old_password: str, new_password: str, confirm_password: str, dialog):
        """修改密码"""
        if not old_password or not new_password or not confirm_password:
            ui.notify('请填写所有字段', type='warning')
            return

        if new_password != confirm_password:
            ui.notify('新密码与确认密码不匹配', type='warning')
            return

        if len(new_password) < 6:
            ui.notify('新密码长度至少为6位', type='warning')
            return

        # 这里需要实现密码修改逻辑
        ui.notify('密码修改功能需要额外实现', type='info')
        dialog.close()

    def export_user_data(self):
        """导出用户数据"""
        ui.notify('数据导出功能开发中...', type='info')

    def handle_logout(self):
        """处理退出登录"""
        if self.on_logout:
            self.on_logout()
        ui.notify('已退出登录', type='info')