"""
侧边栏组件
"""

from nicegui import ui
from typing import Dict, List, Callable, Optional


class SidebarComponent:
    def __init__(self, list_manager, task_manager, current_user: Dict, on_view_change: Callable, on_logout: Callable, 
                 on_settings: Callable, on_statistics: Callable = None, on_refresh_ui: Callable = None):
        self.list_manager = list_manager
        self.task_manager = task_manager
        self.current_user = current_user
        self.on_view_change = on_view_change
        self.on_logout = on_logout
        self.on_settings = on_settings
        self.on_statistics = on_statistics
        self.on_refresh_ui = on_refresh_ui
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
            with ui.row().classes('w-full p-4 justify-center sidebar-toggle-row'):
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
                    ui.separator()
                    with ui.column().classes('w-full p-1'):
                        with ui.column().classes('gap-1'):
                            ui.label(self.current_user['email']).classes('text-sm font-medium')
                            ui.label('已登录').classes('text-xs text-grey-6')
                    ui.separator()
                
                # 操作按钮 - 始终显示，根据展开/收起状态调整布局
                with ui.column().classes('w-full p-4 pb-6'):
                    if self.sidebar_collapsed:
                        # 收起时：竖直排列居中
                        with ui.column().classes('w-full items-center gap-3'):
                            ui.button(icon='add', on_click=self.show_create_list_dialog).props('flat round size=sm')
                            ui.button(icon='analytics', on_click=self.on_statistics).props('flat round size=sm')
                            ui.button(icon='settings', on_click=self.on_settings).props('flat round size=sm')
                            ui.button(icon='logout', on_click=self.on_logout).props('flat round size=sm')
                    else:
                        # 展开时：新建清单按钮靠左，其他按钮靠右
                        with ui.row().classes('w-full justify-between items-center gap-2'):
                            ui.button('新建清单', icon='add', on_click=self.show_create_list_dialog).props('flat').classes('text-sm font-medium')
                            
                            with ui.row().classes('gap-2'):
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
                
                # 清单项容器
                container_classes = 'list-item-container w-full p-3 rounded cursor-pointer flex items-center justify-between'
                if self.current_view == f'list_{user_list["list_id"]}':
                    container_classes += ' active'
                
                with ui.row().classes(container_classes):
                    classes = 'flex-1 items-center'
                    if self.sidebar_collapsed:
                        classes += ' justify-center'
                    else:
                        classes += ' gap-3'
                    # 左侧：可点击的主要区域
                    with ui.row().classes(classes).on('click', select_list(user_list)):
                        # 使用对应颜色的圆圈图标
                        ui.element('div').classes('w-5 h-5 rounded-full').style(f'background-color: {user_list.get("color", "#2196F3")}; min-width: 20px; min-height: 20px;')
                        if not self.sidebar_collapsed:
                            ui.label(user_list['name']).classes('text-sm')
                            if user_list.get('task_count', 0) > 0:
                                ui.badge(str(user_list['task_count'])).props('color=grey-5')
                    
                    # 右侧：三个点菜单按钮（hover时显示）
                    if not self.sidebar_collapsed:
                        with ui.button(icon='more_vert').props('flat round size=xs').classes('list-menu-button'):
                            with ui.menu():
                                ui.menu_item('编辑清单', on_click=lambda l=user_list: self.show_edit_list_dialog(l), auto_close=False)
                                ui.menu_item('删除清单', on_click=lambda l=user_list: self.show_delete_list_confirm(l), auto_close=False)
                                ui.menu_item('完成清单', on_click=lambda l=user_list: self.show_complete_list_confirm(l), auto_close=False)

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
    
    def show_create_list_dialog(self):
        """显示创建清单对话框"""
        dialog_result = {'list_name': '', 'list_color': '#2196F3'}
        
        def create_list():
            """创建新清单"""
            if not dialog_result['list_name'].strip():
                ui.notify('清单名称不能为空', type='warning')
                return
            
            try:
                # 创建新清单
                new_list = self.list_manager.create_list(
                    user_id=self.current_user['user_id'],
                    name=dialog_result['list_name'].strip(),
                    color=dialog_result['list_color']
                )
                
                if new_list:
                    # 刷新侧边栏清单显示
                    self.refresh_sidebar_lists()
                    ui.notify(f'清单 "{dialog_result["list_name"]}" 创建成功！', type='positive')
                    dialog.close()
                else:
                    ui.notify('创建清单失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'创建清单时出错：{str(e)}', type='negative')
        
        def on_name_change(e):
            """处理清单名称变化"""
            dialog_result['list_name'] = e.value
        
        def on_color_change(color):
            """处理颜色变化"""
            dialog_result['list_color'] = color
        
        # 创建对话框
        with ui.dialog(value=True) as dialog, ui.card().classes('w-80 p-6'):
            ui.label('新建清单').classes('text-lg font-medium mb-4')
            
            # 清单名称输入
            with ui.column().classes('w-full gap-4'):
                ui.input(
                    label='清单名称', 
                    placeholder='请输入清单名称',
                    on_change=on_name_change
                ).classes('w-full').props('outlined')
                
                # 颜色选择
                with ui.row().classes('w-full items-center gap-3'):
                    ui.label('颜色:').classes('text-sm')
                    
                    # 预设颜色选项
                    colors = [
                        '#2196F3',  # 蓝色
                        '#4CAF50',  # 绿色  
                        '#FF9800',  # 橙色
                        '#9C27B0',  # 紫色
                        '#F44336',  # 红色
                        '#607D8B',  # 蓝灰色
                        '#795548',  # 棕色
                        '#E91E63'   # 粉色
                    ]
                    
                    with ui.row().classes('gap-2'):
                        for color in colors:
                            color_button = ui.button().props(f'flat round size=sm').style(f'background-color: {color}; min-width: 28px; height: 28px;')
                            color_button.on('click', lambda c=color: on_color_change(c))
                
                # 操作按钮
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('取消', on_click=dialog.close).props('flat')
                    ui.button('创建', on_click=create_list).props('color=primary')
    

    def show_edit_list_dialog(self, user_list: Dict):
        """显示编辑清单对话框"""
        dialog_result = {
            'list_name': user_list['name'], 
            'list_color': user_list.get('color', '#2196F3')
        }
        
        def update_list():
            """更新清单"""
            if not dialog_result['list_name'].strip():
                ui.notify('清单名称不能为空', type='warning')
                return
            
            try:
                success = self.list_manager.update_list(
                    list_id=user_list['list_id'],
                    name=dialog_result['list_name'].strip(),
                    color=dialog_result['list_color']
                )
                
                if success:
                    # 刷新界面
                    self.refresh_sidebar_lists()
                    if self.on_refresh_ui:
                        self.on_refresh_ui()
                    ui.notify(f'清单 "{dialog_result["list_name"]}" 更新成功！', type='positive')
                    dialog.close()
                else:
                    ui.notify('更新清单失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'更新清单时出错：{str(e)}', type='negative')
        
        def on_name_change(e):
            """处理清单名称变化"""
            dialog_result['list_name'] = e.value
        
        def on_color_change(color):
            """处理颜色变化"""
            dialog_result['list_color'] = color
        
        # 创建对话框
        with ui.dialog(value=True) as dialog, ui.card().classes('w-80 p-6'):
            ui.label('编辑清单').classes('text-lg font-medium mb-4')
            
            # 清单名称输入
            with ui.column().classes('w-full gap-4'):
                name_input = ui.input(
                    label='清单名称', 
                    placeholder='请输入清单名称',
                    value=dialog_result['list_name'],
                    on_change=on_name_change
                ).classes('w-full').props('outlined')
                
                # 颜色选择
                with ui.row().classes('w-full items-center gap-3'):
                    ui.label('颜色:').classes('text-sm')
                    
                    # 预设颜色选项
                    colors = [
                        '#2196F3',  # 蓝色
                        '#4CAF50',  # 绿色  
                        '#FF9800',  # 橙色
                        '#9C27B0',  # 紫色
                        '#F44336',  # 红色
                        '#607D8B',  # 蓝灰色
                        '#795548',  # 棕色
                        '#E91E63'   # 粉色
                    ]
                    
                    with ui.row().classes('gap-2'):
                        for color in colors:
                            color_button = ui.button().props(f'flat round size=sm').style(f'background-color: {color}; min-width: 28px; height: 28px;')
                            color_button.on('click', lambda c=color: on_color_change(c))
                
                # 操作按钮
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('取消', on_click=dialog.close).props('flat')
                    ui.button('保存', on_click=update_list).props('color=primary')
    
    def show_delete_list_confirm(self, user_list: Dict):
        """显示删除清单确认对话框"""
        def delete_list():
            """删除清单"""
            try:
                # 1. 解除清单中任务的绑定
                self.task_manager.unlink_list_tasks(user_list['list_id'])
                
                # 2. 删除清单
                success = self.list_manager.delete_list(user_list['list_id'])
                
                if success:
                    # 3. 如果当前正在查看被删除的清单，切换到默认视图
                    if self.current_view == f'list_{user_list["list_id"]}':
                        self.current_view = 'my_day'
                        self.on_view_change('my_day')
                    
                    # 4. 刷新界面
                    self.refresh_sidebar_lists()
                    if self.on_refresh_ui:
                        self.on_refresh_ui()
                    
                    ui.notify(f'清单 "{user_list["name"]}" 已删除', type='positive')
                    dialog.close()
                else:
                    ui.notify('删除清单失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'删除清单时出错：{str(e)}', type='negative')
        
        # 创建确认对话框
        with ui.dialog(value=True) as dialog, ui.card().classes('w-80 p-6'):
            ui.label('删除清单').classes('text-lg font-medium text-red-600 mb-4')
            ui.label(f'确定要删除清单 "{user_list["name"]}" 吗？').classes('mb-2')
            ui.label('清单中的任务将被保留，但会解除与清单的关联。').classes('text-sm text-grey-6 mb-4')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('删除', on_click=delete_list).props('color=negative')
    
    def show_complete_list_confirm(self, user_list: Dict):
        """显示完成清单确认对话框"""
        def complete_list():
            """完成清单"""
            try:
                # 1. 将清单中所有任务标记为完成
                self.task_manager.complete_list_tasks(user_list['list_id'])
                
                # 2. 解除清单中任务的绑定
                self.task_manager.unlink_list_tasks(user_list['list_id'])
                
                # 3. 删除清单
                success = self.list_manager.delete_list(user_list['list_id'])
                
                if success:
                    # 4. 如果当前正在查看被完成的清单，切换到默认视图
                    if self.current_view == f'list_{user_list["list_id"]}':
                        self.current_view = 'my_day'
                        self.on_view_change('my_day')
                    
                    # 5. 刷新界面
                    self.refresh_sidebar_lists()
                    if self.on_refresh_ui:
                        self.on_refresh_ui()
                    
                    ui.notify(f'清单 "{user_list["name"]}" 已完成', type='positive')
                    dialog.close()
                else:
                    ui.notify('完成清单失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'完成清单时出错：{str(e)}', type='negative')
        
        # 创建确认对话框
        with ui.dialog(value=True) as dialog, ui.card().classes('w-80 p-6'):
            ui.label('完成清单').classes('text-lg font-medium text-green-600 mb-4')
            ui.label(f'确定要完成清单 "{user_list["name"]}" 吗？').classes('mb-2')
            ui.label('清单中的所有任务将被标记为完成，然后清单将被删除。').classes('text-sm text-grey-6 mb-4')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('完成', on_click=complete_list).props('color=positive')