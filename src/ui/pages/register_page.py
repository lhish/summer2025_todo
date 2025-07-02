"""
注册页面组件
"""

from nicegui import ui, app
from typing import Optional, Dict, Callable


class RegisterPage:
    def __init__(self, user_manager, on_register_success: Callable = None):
        self.user_manager = user_manager
        self.on_register_success = on_register_success

    def show_register_page(self) -> Optional[Dict]:
        """显示注册页面"""
        
        ui.page_title('注册 - 个人任务与效能管理平台')
        
        with ui.column().classes('w-full h-screen flex items-center justify-center bg-grey-1'):
            with ui.card().classes('w-96 p-8 shadow-lg'):
                ui.label('个人任务与效能管理平台').classes('text-h4 text-center mb-6 text-primary')
                ui.label('创建新账户').classes('text-h6 text-center mb-4 text-grey-8')
                
                email_input = ui.input('邮箱', placeholder='输入您的邮箱').classes('w-full mb-4')
                password_input = ui.input('密码', placeholder='输入您的密码（至少6位）', password=True).classes('w-full mb-4')
                confirm_password_input = ui.input('确认密码', placeholder='再次输入密码', password=True).classes('w-full mb-4')
                
                def handle_register():
                    email = email_input.value
                    password = password_input.value
                    confirm_password = confirm_password_input.value
                    
                    if not email or not password or not confirm_password:
                        ui.notify('请填写所有字段', type='warning')
                        return
                    
                    if len(password) < 6:
                        ui.notify('密码长度至少为6位', type='warning')
                        return
                    
                    if password != confirm_password:
                        ui.notify('两次输入的密码不一致', type='warning')
                        return
                    
                    user_id = self.user_manager.create_user(email, password)
                    if user_id:
                        ui.notify('注册成功！正在跳转到登录页面', type='positive')
                        if self.on_register_success:
                            self.on_register_success({'user_id': user_id, 'email': email})
                        ui.navigate.to('/login')
                    else:
                        ui.notify('注册失败，邮箱可能已存在', type='negative')
                
                ui.button('注册', on_click=handle_register).classes('w-full mb-4').props('color=primary')
                
                with ui.row().classes('w-full justify-center'):
                    ui.label('已有账户？').classes('text-grey-6')
                    ui.link('立即登录', target='/login').classes('text-primary underline ml-1')

    def create_register_page_route(self):
        """创建注册页面路由"""
        def register_page():
            """注册页面"""
            self.show_register_page()
        return register_page 