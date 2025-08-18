"""
设置页面
"""
from typing import Dict, Callable
from nicegui import ui


class SettingsPage:
    """设置页面类"""
    
    def __init__(self, settings_manager, user_manager, on_logout: Callable = None):
        self.settings_manager = settings_manager
        self.user_manager = user_manager  # 使用传入的用户管理器
        self.on_logout = on_logout
        self.current_user = None
    
    def create(self, user: Dict) -> ui.column:
        """创建设置页面"""
        self.current_user = user
        
        with ui.column().classes('w-full max-w-2xl mx-auto p-6 gap-6') as page:
            ui.label('设置').classes('text-h4 text-primary mb-4')
            
            # 用户信息设置
            self.create_user_settings()
            
            # 番茄钟设置
            self.create_pomodoro_settings()
            
            # 通知设置
            self.create_notification_settings()
            
            # 外观设置
            self.create_appearance_settings()
            
            # 账户操作
            self.create_account_actions()
        
        return page
    
    def create_user_settings(self):
        """创建用户信息设置"""
        with ui.card().classes('w-full p-4'):
            ui.label('用户信息').classes('text-h6 mb-4')
            
            with ui.column().classes('gap-4'):
                ui.input(
                    label='邮箱',
                    value=self.current_user.get('email', ''),
                    readonly=True
                ).classes('w-full')
                
                ui.input(
                    label='昵称',
                    value=self.current_user.get('name', ''),
                    placeholder='设置您的昵称'
                ).classes('w-full')
                
                ui.button('保存用户信息', on_click=self.save_user_info).props('color=primary')
    
    def create_pomodoro_settings(self):
        """创建番茄钟设置"""
        settings = self.get_user_settings()
        
        with ui.card().classes('w-full p-4'):
            ui.label('番茄钟设置').classes('text-h6 mb-4')
            
            with ui.column().classes('gap-4'):
                work_duration = ui.number(
                    label='工作时长（分钟）',
                    value=settings.get('work_duration', 25),
                    min=1,
                    max=60
                ).classes('w-full')
                
                short_break = ui.number(
                    label='短休息时长（分钟）',
                    value=settings.get('short_break', 5),
                    min=1,
                    max=30
                ).classes('w-full')
                
                long_break = ui.number(
                    label='长休息时长（分钟）',
                    value=settings.get('long_break', 15),
                    min=1,
                    max=60
                ).classes('w-full')
                
                sessions_before_long_break = ui.number(
                    label='长休息前的工作轮数',
                    value=settings.get('sessions_before_long_break', 4),
                    min=1,
                    max=10
                ).classes('w-full')
                
                ui.button(
                    '保存番茄钟设置',
                    on_click=lambda: self.save_pomodoro_settings({
                        'work_duration': work_duration.value,
                        'short_break': short_break.value,
                        'long_break': long_break.value,
                        'sessions_before_long_break': sessions_before_long_break.value
                    })
                ).props('color=primary')
    
    def create_notification_settings(self):
        """创建通知设置"""
        settings = self.get_user_settings()
        
        with ui.card().classes('w-full p-4'):
            ui.label('通知设置').classes('text-h6 mb-4')
            
            with ui.column().classes('gap-4'):
                enable_notifications = ui.checkbox(
                    '启用通知',
                    value=settings.get('enable_notifications', True)
                )
                
                enable_sound = ui.checkbox(
                    '启用声音提醒',
                    value=settings.get('enable_sound', True)
                )
                
                enable_desktop_notifications = ui.checkbox(
                    '启用桌面通知',
                    value=settings.get('enable_desktop_notifications', False)
                )
                
                ui.button(
                    '保存通知设置',
                    on_click=lambda: self.save_notification_settings({
                        'enable_notifications': enable_notifications.value,
                        'enable_sound': enable_sound.value,
                        'enable_desktop_notifications': enable_desktop_notifications.value
                    })
                ).props('color=primary')
    
    def create_appearance_settings(self):
        """创建外观设置"""
        settings = self.get_user_settings()
        
        with ui.card().classes('w-full p-4'):
            ui.label('外观设置').classes('text-h6 mb-4')
            
            with ui.column().classes('gap-4'):
                theme_select = ui.select(
                    label='主题',
                    options={'light': '浅色', 'dark': '深色', 'auto': '跟随系统'},
                    value=settings.get('theme', 'light')
                ).classes('w-full')
                
                language_select = ui.select(
                    label='语言',
                    options={'zh-CN': '中文', 'en-US': 'English'},
                    value=settings.get('language', 'zh-CN')
                ).classes('w-full')
                
                ui.button(
                    '保存外观设置',
                    on_click=lambda: self.save_appearance_settings({
                        'theme': theme_select.value,
                        'language': language_select.value
                    })
                ).props('color=primary')
    
    def create_account_actions(self):
        """创建账户操作"""
        with ui.card().classes('w-full p-4'):
            ui.label('账户操作').classes('text-h6 mb-4')
            
            with ui.column().classes('gap-4'):
                ui.button(
                    '修改密码',
                    on_click=self.show_change_password_dialog
                ).props('color=secondary')
                
                ui.button(
                    '导出数据',
                    on_click=self.export_user_data
                ).props('color=accent')
                
                ui.separator()
                
                ui.button(
                    '退出登录',
                    on_click=self.handle_logout
                ).props('color=negative')
    
    def get_user_settings(self) -> Dict:
        """获取用户设置"""
        if not self.settings_manager or not self.current_user:
            return {}
        
        return self.settings_manager.get_user_settings(self.current_user['user_id'])
    
    def save_user_info(self):
        """保存用户信息"""
        ui.notify('用户信息已保存', type='positive')
    
    def save_pomodoro_settings(self, settings: Dict):
        """保存番茄钟设置"""
        if self.settings_manager and self.current_user:
            self.settings_manager.update_user_settings(
                self.current_user['user_id'],
                settings
            )
        ui.notify('番茄钟设置已保存', type='positive')
    
    def save_notification_settings(self, settings: Dict):
        """保存通知设置"""
        if self.settings_manager and self.current_user:
            self.settings_manager.update_user_settings(
                self.current_user['user_id'],
                settings
            )
        ui.notify('通知设置已保存', type='positive')
    
    def save_appearance_settings(self, settings: Dict):
        """保存外观设置"""
        if self.settings_manager and self.current_user:
            self.settings_manager.update_user_settings(
                self.current_user['user_id'],
                settings
            )
        ui.notify('外观设置已保存', type='positive')
    
    def show_change_password_dialog(self):
        """显示修改密码对话框"""
        with ui.dialog() as dialog:
            with ui.card().classes('w-96 p-6'):
                ui.label('修改密码').classes('text-h6 mb-4')
                
                old_password = ui.input('当前密码', password=True).classes('w-full mb-4')
                new_password = ui.input('新密码', password=True).classes('w-full mb-4')
                confirm_password = ui.input('确认新密码', password=True).classes('w-full mb-4')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('取消', on_click=dialog.close).props('flat')
                    ui.button('确认', on_click=lambda: self.change_password(
                        old_password.value, new_password.value, confirm_password.value, dialog
                    )).props('color=primary')
        
        dialog.open()
    
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
        
        try:
            result = self.user_manager.change_password(
                self.current_user['user_id'],
                old_password,
                new_password
            )
            
            if result['success']:
                ui.notify('密码修改成功', type='positive')
                dialog.close()
            else:
                error = result.get('error', 'unknown')
                if error == 'wrong_old_password':
                    ui.notify('当前密码不正确', type='negative')
                elif error == 'same_password':
                    ui.notify('新密码不能与当前密码相同', type='warning')
                elif error == 'user_not_found':
                    ui.notify('用户不存在', type='negative')
                elif error == 'database_error':
                    ui.notify('数据库更新失败，请重试', type='negative')
                else:
                    message = result.get('message', '未知错误')
                    ui.notify(f'密码修改失败: {message}', type='negative')
                
        except Exception as e:
            ui.notify(f'密码修改失败: {str(e)}', type='negative')
    
    def export_user_data(self):
        """导出用户数据"""
        ui.notify('数据导出功能开发中...', type='info')
    
    def handle_logout(self):
        """处理退出登录"""
        if self.on_logout:
            self.on_logout()
        ui.notify('已退出登录', type='info') 