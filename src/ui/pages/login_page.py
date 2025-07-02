"""
登录页面组件
"""

from nicegui import ui, app
from typing import Optional, Dict, Callable


class LoginPage:
    def __init__(self, user_manager, on_login_success: Callable = None):
        self.user_manager = user_manager
        self.on_login_success = on_login_success

    def show_login_page(self) -> Optional[Dict]:
        """显示登录页面"""
        current_user = None
        
        ui.page_title('登录 - 个人任务与效能管理平台')
        
        with ui.column().classes('w-full h-screen flex items-center justify-center bg-grey-1'):
            with ui.card().classes('w-96 p-8 shadow-lg'):
                ui.label('个人任务与效能管理平台').classes('text-h4 text-center mb-6 text-primary')
                ui.label('登录您的账户').classes('text-h6 text-center mb-4 text-grey-8')
                
                email_input = ui.input('邮箱', placeholder='输入您的邮箱').classes('w-full mb-4')
                password_input = ui.input('密码', placeholder='输入您的密码', password=True).classes('w-full mb-4')
                
                def handle_login():
                    nonlocal current_user
                    
                    email = email_input.value
                    password = password_input.value
                    
                    if not email or not password:
                        ui.notify('请输入邮箱和密码', type='warning')
                        return
                    
                    user = self.user_manager.get_user_by_email(email)
                    if user and self.user_manager.verify_password(password, user['password_hash']):
                        current_user = user
                        # 保存登录状态到本地存储
                        app.storage.user['user_id'] = user['user_id']
                        app.storage.user['email'] = user['email']
                        ui.notify('登录成功！', type='positive')
                        if self.on_login_success:
                            self.on_login_success(user)
                        ui.navigate.to('/')
                    else:
                        ui.notify('邮箱或密码错误', type='negative')
                
                ui.button('登录', on_click=handle_login).classes('w-full mb-4').props('color=primary')
                
                with ui.row().classes('w-full justify-center'):
                    ui.label('还没有账户？').classes('text-grey-6')
                    ui.link('立即注册', target='/register').classes('text-primary underline ml-1')
        
        return current_user

    def create_login_page_route(self):
        """创建登录页面路由"""
        def login_page():
            """登录页面"""
            self.show_login_page()
        return login_page 