"""
侧边栏组件
"""

from nicegui import ui
from typing import Dict, List, Callable, Optional


class SidebarComponent:
    def __init__(self, list_manager, current_user: Dict, on_view_change: Callable, on_logout: Callable, on_settings: Callable, on_statistics: Callable = None):
        self.list_manager = list_manager
        self.current_user = current_user
        self.on_view_change = on_view_change
        self.on_logout = on_logout
        self.on_settings = on_settings
        self.on_statistics = on_statistics
        self.sidebar_collapsed = True
        self.current_view = 'my_day'
        self.user_lists: List[Dict] = []
        self.sidebar_container = None
        self.sidebar_lists_container = None
        
        # 加载用户清单
        self.refresh_user_lists()

    def create_sidebar(self, container):
        """创建左侧边栏"""
        self.sidebar_container = container
        
        # 根据初始状态应用CSS类
        if self.sidebar_collapsed:
            container.classes(add='sidebar-collapsed')
        
        with container:
            # 顶部：折叠/展开按钮
            with ui.row().classes('w-full p-4 justify-center'):
                ui.button(icon='menu', on_click=self.toggle_sidebar).props('flat round')
            
            ui.separator()
            
            # 第一部分：默认视图
            with ui.column().classes('w-full p-2'):
                self.create_sidebar_item('我的一天', 'sunny', 'my_day')
                self.create_sidebar_item('计划内', 'event', 'planned')
                self.create_sidebar_item('重要', 'star', 'important')
                self.create_sidebar_item('任务', 'list', 'all')
            
            ui.separator()
            
            # 第二部分：清单
            self.sidebar_lists_container = ui.column().classes('w-full p-2')
            self.refresh_sidebar_lists()
            
            ui.separator()

            # 占据剩余空间
            ui.element('div').style('margin-top: auto')
            
            # 底部区域
            with ui.column().classes('w-full'):
                # 已登录状态 - 只在展开时显示
                if not self.sidebar_collapsed:
                    with ui.column().classes('w-full p-4'):
                        with ui.column().classes('gap-1'):
                            ui.label(self.current_user['email']).classes('text-sm font-medium')
                            ui.label('已登录').classes('text-xs text-grey-6')
                
                # 操作按钮 - 始终显示，根据展开/收起状态调整布局
                with ui.column().classes('w-full p-4 pb-6'):
                    if self.sidebar_collapsed:
                        # 收起时：竖直排列居中
                        with ui.column().classes('w-full items-center gap-3'):
                            ui.button(icon='analytics', on_click=self.on_statistics).props('flat round size=sm')
                            ui.button(icon='settings', on_click=self.on_settings).props('flat round size=sm')
                            ui.button(icon='logout', on_click=self.on_logout).props('flat round size=sm')
                    else:
                        # 展开时：水平排列靠右
                        with ui.row().classes('w-full justify-end gap-2'):
                            ui.button(icon='analytics', on_click=self.on_statistics).props('flat round size=sm')
                            ui.button(icon='settings', on_click=self.on_settings).props('flat round size=sm')
                            ui.button(icon='logout', on_click=self.on_logout).props('flat round size=sm')

    def create_sidebar_item(self, label: str, icon: str, view_type: str):
        """创建侧边栏项目"""
        def select_view():
            self.current_view = view_type
            self.on_view_change(view_type)
            # 更新active状态
            self.update_sidebar_active_state()
        
        classes = 'sidebar-item w-full p-3 rounded cursor-pointer flex items-center'
        if self.current_view == view_type:
            classes += ' active'
        if self.sidebar_collapsed:
            classes += ' justify-center'
        else:
            classes += ' gap-3'

        
        with ui.row().classes(classes).on('click', select_view):
            ui.icon(icon).classes('text-xl text-grey-7')
            if not self.sidebar_collapsed:
                ui.label(label).classes('text-sm')

    def refresh_sidebar_lists(self):
        """刷新侧边栏清单列表"""
        # 清空列表容器内容
        if self.sidebar_lists_container:
            self.sidebar_lists_container.clear()
        
        # 重新获取用户清单
        self.refresh_user_lists()
        
        # 为每个清单创建侧边栏项目
        with self.sidebar_lists_container:
            for user_list in self.user_lists:
                def select_list(list_data=user_list):
                    def inner_select():
                        view_type = f'list_{list_data["list_id"]}'
                        self.current_view = view_type
                        self.on_view_change(view_type)
                        self.update_sidebar_active_state()
                    return inner_select
                
                classes = 'sidebar-item w-full p-3 rounded cursor-pointer flex items-center'
                if self.current_view == f'list_{user_list["list_id"]}':
                    classes += ' active'
                if self.sidebar_collapsed:
                    classes += ' justify-center'
                else:
                    classes += ' gap-3'
                
                with ui.row().classes(classes).on('click', select_list(user_list)):
                    ui.icon('folder', color=user_list.get('color', '#2196F3')).classes('text-xl text-grey-7')
                    if not self.sidebar_collapsed:
                        ui.label(user_list['name']).classes('text-sm')
                        if user_list.get('task_count', 0) > 0:
                            ui.badge(str(user_list['task_count'])).props('color=grey-5')

    def toggle_sidebar(self):
        """切换侧边栏展开/折叠状态"""
        self.sidebar_collapsed = not self.sidebar_collapsed
        
        if self.sidebar_collapsed:
            self.sidebar_container.classes(add='sidebar-collapsed')
        else:
            self.sidebar_container.classes(remove='sidebar-collapsed')
        
        # 重新创建侧边栏以更新显示状态
        self.update_sidebar_active_state()

    def update_sidebar_active_state(self):
        """更新侧边栏激活状态"""
        # 重新创建侧边栏以更新active状态
        if self.sidebar_container:
            self.sidebar_container.clear()
            self.create_sidebar(self.sidebar_container)

    def refresh_user_lists(self):
        """刷新用户清单"""
        if self.current_user:
            self.user_lists = self.list_manager.get_user_lists(self.current_user['user_id'])

    def set_current_view(self, view: str):
        """设置当前视图"""
        self.current_view = view
        self.update_sidebar_active_state()

    def get_user_lists(self) -> List[Dict]:
        """获取用户清单列表"""
        return self.user_lists 