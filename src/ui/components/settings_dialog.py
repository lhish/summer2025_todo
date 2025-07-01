"""
设置对话框组件
"""

from nicegui import ui, app
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
                                        value=settings.get('pomodoro_work_duration', 25),
                                        min=1, max=60).classes('w-full')
                short_break = ui.number(label='短休息时长(分钟)',
                                      value=settings.get('pomodoro_short_break_duration', 5),
                                      min=1, max=30).classes('w-full')
                # 添加专注模式开关
                #focus_mode = ui.switch('专注模式（阻止退出计时器）',
                #                     value=settings.get('focus_mode', False)).classes('w-full mt-2')

                # 目标设置
                ui.label('目标设置').classes('text-subtitle1 mb-2 mt-4')
                daily_target = ui.number(label='每日专注目标(分钟)',
                                       value=settings.get('daily_focus_target_minutes', 120),
                                       min=1).classes('w-full')

                def save_settings():
                    settings_data = {
                        'pomodoro_work_duration': int(work_duration.value),
                        'pomodoro_short_break_duration': int(short_break.value),
                        #'focus_mode': focus_mode.value,  # 确保保存专注模式
                        'daily_focus_target_minutes': int(daily_target.value)
                    }

                    # 添加调试日志
                    print(f"保存设置: {settings_data}")

                    success = self.settings_manager.update_user_settings(
                        self.current_user['user_id'],
                        settings_data
                    )

                    if success:
                        ui.notify('设置已保存', type='positive')
                        # 通知所有组件设置已更新
                        app.storage.user['settings_updated'] = True
                        dialog.close()
                    else:
                        ui.notify('保存失败', type='negative')

                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('取消', on_click=dialog.close).props('flat')
                    ui.button('保存', on_click=save_settings).props('color=primary')

        dialog.open()