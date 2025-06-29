"""
设置对话框组件
"""

from nicegui import ui
from typing import Dict


class SettingsDialogComponent:
    def __init__(self, settings_manager, current_user: Dict):
        self.settings_manager = settings_manager
        self.current_user = current_user

    def show_settings_dialog(self):
        """显示设置对话框"""
        settings = self.settings_manager.get_user_settings(self.current_user['user_id'])
        
        with ui.dialog().classes('w-96') as dialog:
            with ui.card():
                ui.label('系统设置').classes('text-h6 mb-4')
                
                # 番茄工作法设置
                ui.label('番茄工作法设置').classes('text-subtitle1 mb-2')
                work_duration = ui.number(label='工作时长(分钟)', 
                                        value=settings['pomodoro_work_duration'] if settings else 25).classes('w-full')
                short_break = ui.number(label='短休息时长(分钟)', 
                                      value=settings['pomodoro_short_break_duration'] if settings else 5).classes('w-full')
                long_break = ui.number(label='长休息时长(分钟)', 
                                     value=settings['pomodoro_long_break_duration'] if settings else 15).classes('w-full')
                
                # 目标设置
                ui.label('目标设置').classes('text-subtitle1 mb-2 mt-4')
                daily_target = ui.number(label='每日专注目标(分钟)', 
                                       value=settings['daily_focus_target_minutes'] if settings else 120).classes('w-full')
                
                def save_settings():
                    settings_data = {
                        'pomodoro_work_duration': int(work_duration.value),
                        'pomodoro_short_break_duration': int(short_break.value),
                        'pomodoro_long_break_duration': int(long_break.value),
                        'daily_focus_target_minutes': int(daily_target.value)
                    }
                    
                    success = self.settings_manager.update_user_settings(self.current_user['user_id'], settings_data)
                    if success:
                        ui.notify('设置已保存', type='positive')
                        dialog.close()
                    else:
                        ui.notify('保存失败', type='negative')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('取消', on_click=dialog.close).props('flat')
                    ui.button('保存', on_click=save_settings).props('color=primary')
        
        dialog.open() 