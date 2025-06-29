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
                
                def handle_register():
                    email = email_input.value
                    password = password_input.value
                    
                    if not email or not password:
                        ui.notify('请填写所有字段', type='warning')
                        return
                    
                    if len(password) < 6:
                        ui.notify('密码长度至少为6位', type='warning')
                        return
                    
                    user_id = self.user_manager.create_user(email, password)
                    if user_id:
                        ui.notify('注册成功！请登录', type='positive')
                    else:
                        ui.notify('注册失败，邮箱可能已存在', type='negative')
                
                with ui.row().classes('w-full gap-2'):
                    ui.button('登录', on_click=handle_login).classes('flex-1').props('color=primary')
                    ui.button('注册', on_click=handle_register).classes('flex-1').props('flat color=primary')
        
        return current_user

    def create_login_page_route(self):
        """创建登录页面路由"""
        def login_page():
            """登录页面"""
            self.show_login_page()
        return login_page 