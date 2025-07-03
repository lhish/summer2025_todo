"""
侧边栏组件
"""

from nicegui import ui
from typing import Dict, List, Callable, Optional


class SidebarComponent:
    def __init__(self, tag_manager, task_manager, current_user: Dict, on_view_change: Callable, on_logout: Callable, 
                 on_settings: Callable, on_statistics: Callable = None, on_refresh_ui: Callable = None):
        self.tag_manager = tag_manager
        self.task_manager = task_manager
        self.current_user = current_user
        self.on_view_change = on_view_change
        self.on_logout = on_logout
        self.on_settings = on_settings
        self.on_statistics = on_statistics
        self.on_refresh_ui = on_refresh_ui
        self.sidebar_collapsed = True
        self.current_view = 'my_day'
        self.user_tags: List[Dict] = []
        self.sidebar_container = None
        self.sidebar_tags_container = None

        
        # 加载用户标签
        self.refresh_user_tags()
        
        # 添加CSS样式隐藏滚动条和去掉白边
        ui.add_head_html('''
            <style>
                .no-scrollbar::-webkit-scrollbar {
                    display: none !important;
                }
                .no-scrollbar {
                    -ms-overflow-style: none !important;
                    scrollbar-width: none !important;
                }
                .no-scrollbar .q-scrollarea__bar {
                    display: none !important;
                }
                .no-scrollbar .q-scrollarea__thumb {
                    display: none !important;
                }
                .no-scrollbar.q-scrollarea {
                    padding: 0 !important;
                    margin: 0 !important;
                }
                .no-scrollbar .q-scrollarea__content {
                    padding: 0 !important;
                    margin: 0 !important;
                }
                .no-scrollbar .q-scrollarea__container {
                    padding: 0 !important;
                    margin: 0 !important;
                }
                .no-scrollbar .q-scrollarea__viewport {
                    padding: 0 !important;
                    margin: 0 !important;
                }
            </style>
        ''')

    def create_sidebar(self, container):
        """创建左侧边栏"""
        self.sidebar_container = container
        
        # 根据初始状态应用CSS类
        if self.sidebar_collapsed:
            container.classes(add='sidebar-collapsed')
        
        with container:
            # 使用flexbox布局，让中间的滚动区域能够自适应
            with ui.column().classes('w-full h-full flex').style('height: 100vh;'):
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
                
                # 第二部分：标签 - 使用flex-1让这部分占据剩余空间
                with ui.column().classes('w-full p-1 flex-1').style('min-height: 0;'):
                    self.sidebar_tags_container = ui.column().classes('w-full h-full')
                    self.refresh_sidebar_tags()

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
                                ui.button(icon='add', on_click=self.show_create_tag_dialog).props('flat round size=sm')
                                ui.button(icon='analytics', on_click=self.on_statistics).props('flat round size=sm')
                                ui.button(icon='settings', on_click=self.on_settings).props('flat round size=sm')
                                ui.button(icon='logout', on_click=self.on_logout).props('flat round size=sm')
                        else:
                            # 展开时：新建标签按钮靠左，其他按钮靠右
                            with ui.row().classes('w-full justify-between items-center gap-2'):
                                ui.button('新建标签', icon='add', on_click=self.show_create_tag_dialog).props('flat').classes('text-sm font-medium')
                                
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

    def refresh_sidebar_tags(self):
        """刷新侧边栏标签列表"""
        # 清空标签容器内容
        if self.sidebar_tags_container:
            self.sidebar_tags_container.clear()
        
        # 重新获取用户标签
        self.refresh_user_tags()
        
        # 为每个标签创建侧边栏项目
        with self.sidebar_tags_container:
            # 始终使用滚动容器，高度自适应，隐藏滚动条
            with ui.scroll_area().classes('w-full h-full no-scrollbar').style('scrollbar-width: none; -ms-overflow-style: none;'):
                with ui.column().classes('w-full gap-1'):
                    for user_tag in self.user_tags:
                        self.create_tag_item(user_tag)
    
    def create_tag_item(self, user_tag: Dict):
        """创建单个标签项"""
        def select_tag(tag_data=user_tag):
            def inner_select():
                view_type = f'tag_{tag_data["tag_id"]}'
                self.current_view = view_type
                self.on_view_change(view_type)
                self.update_sidebar_active_state()
            return inner_select
        
        # 标签项容器
        container_classes = 'tag-item-container w-full p-2 rounded cursor-pointer flex items-center justify-between'
        if self.current_view == f'tag_{user_tag["tag_id"]}':
            container_classes += ' active'
        
        with ui.row().classes(container_classes):
            classes = 'flex-1 items-center'
            if self.sidebar_collapsed:
                classes += ' justify-center'
            else:
                classes += ' gap-3'
            # 左侧：可点击的主要区域
            with ui.row().classes(classes).on('click', select_tag(user_tag)):
                # 使用对应颜色的圆圈图标
                ui.element('div').classes('w-4 h-4 rounded-full').style(f'background-color: {user_tag.get("color", "#757575")}; min-width: 16px; min-height: 16px;')
                if not self.sidebar_collapsed:
                    ui.label(user_tag['name']).classes('text-sm')
                    if user_tag.get('task_count', 0) > 0:
                        ui.badge(str(user_tag['task_count'])).props('color=grey-5')
            
            # 右侧：三个点菜单按钮（hover时显示）
            if not self.sidebar_collapsed:
                with ui.button(icon='more_vert').props('flat round size=xs').classes('tag-menu-button'):
                    with ui.menu():
                        ui.menu_item('编辑标签', on_click=lambda t=user_tag: self.show_edit_tag_dialog(t), auto_close=False)
                        ui.menu_item('删除标签', on_click=lambda t=user_tag: self.show_delete_tag_confirm(t), auto_close=False)
                        ui.menu_item('完成标签任务', on_click=lambda t=user_tag: self.show_complete_tag_confirm(t), auto_close=False)

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

    def refresh_user_tags(self):
        """刷新用户标签"""
        if self.current_user:
            self.user_tags = self.tag_manager.get_user_tags_with_count(self.current_user['user_id'])

    def set_current_view(self, view: str):
        """设置当前视图"""
        self.current_view = view
        self.update_sidebar_active_state()

    def get_user_tags(self) -> List[Dict]:
        """获取用户标签列表"""
        return self.user_tags
    
 
    
    def show_create_tag_dialog(self):
        """显示创建标签对话框"""
        dialog_result = {'tag_name': '', 'tag_color': '#757575'}
        
        def create_tag():
            """创建新标签"""
            if not dialog_result['tag_name'].strip():
                ui.notify('标签名称不能为空', type='warning')
                return
            
            try:
                # 创建新标签
                new_tag = self.tag_manager.create_tag(
                    user_id=self.current_user['user_id'],
                    name=dialog_result['tag_name'].strip(),
                    color=dialog_result['tag_color']
                )
                
                if new_tag:
                    # 刷新侧边栏标签显示
                    self.refresh_sidebar_tags()
                    ui.notify(f'标签 "{dialog_result["tag_name"]}" 创建成功！', type='positive')
                    dialog.close()
                else:
                    ui.notify('创建标签失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'创建标签时出错：{str(e)}', type='negative')
        
        def on_name_change(e):
            """处理标签名称变化"""
            dialog_result['tag_name'] = e.value
        
        def on_color_change(color):
            """处理颜色变化"""
            dialog_result['tag_color'] = color
        
        # 创建对话框
        with ui.dialog(value=True) as dialog, ui.card().classes('w-80 p-6'):
            ui.label('新建标签').classes('text-lg font-medium mb-4')
            
            # 标签名称输入
            with ui.column().classes('w-full gap-4'):
                ui.input(
                    label='标签名称', 
                    placeholder='请输入标签名称',
                    on_change=on_name_change
                ).classes('w-full').props('outlined')
                
                # 颜色选择
                with ui.row().classes('w-full items-center gap-3'):
                    ui.label('颜色:').classes('text-sm')
                    
                    # 预设颜色选项
                    colors = [
                        '#757575',  # 灰色
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
                    ui.button('创建', on_click=create_tag).props('color=primary')
    

    def show_edit_tag_dialog(self, user_tag: Dict):
        """显示编辑标签对话框"""
        dialog_result = {
            'tag_name': user_tag['name'], 
            'tag_color': user_tag.get('color', '#757575')
        }
        
        def update_tag():
            """更新标签"""
            if not dialog_result['tag_name'].strip():
                ui.notify('标签名称不能为空', type='warning')
                return
            
            try:
                success = self.tag_manager.update_tag(
                    tag_id=user_tag['tag_id'],
                    name=dialog_result['tag_name'].strip(),
                    color=dialog_result['tag_color']
                )
                
                if success:
                    # 刷新界面
                    self.refresh_sidebar_tags()
                    if self.on_refresh_ui:
                        self.on_refresh_ui()
                    ui.notify(f'标签 "{dialog_result["tag_name"]}" 更新成功！', type='positive')
                    dialog.close()
                else:
                    ui.notify('更新标签失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'更新标签时出错：{str(e)}', type='negative')
        
        def on_name_change(e):
            """处理标签名称变化"""
            dialog_result['tag_name'] = e.value
        
        def on_color_change(color):
            """处理颜色变化"""
            dialog_result['tag_color'] = color
        
        # 创建对话框
        with ui.dialog(value=True) as dialog, ui.card().classes('w-80 p-6'):
            ui.label('编辑标签').classes('text-lg font-medium mb-4')
            
            # 标签名称输入
            with ui.column().classes('w-full gap-4'):
                name_input = ui.input(
                    label='标签名称', 
                    placeholder='请输入标签名称',
                    value=dialog_result['tag_name'],
                    on_change=on_name_change
                ).classes('w-full').props('outlined')
                
                # 颜色选择
                with ui.row().classes('w-full items-center gap-3'):
                    ui.label('颜色:').classes('text-sm')
                    
                    # 预设颜色选项
                    colors = [
                        '#757575',  # 灰色
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
                    ui.button('保存', on_click=update_tag).props('color=primary')
    
    def show_delete_tag_confirm(self, user_tag: Dict):
        """显示删除标签确认对话框"""
        def delete_tag():
            """删除标签"""
            try:
                # 删除标签
                success = self.tag_manager.delete_tag(user_tag['tag_id'])
                
                if success:
                    # 如果当前正在查看被删除的标签，切换到默认视图
                    if self.current_view == f'tag_{user_tag["tag_id"]}':
                        self.current_view = 'my_day'
                        self.on_view_change('my_day')
                    
                    # 刷新界面
                    self.refresh_sidebar_tags()
                    if self.on_refresh_ui:
                        self.on_refresh_ui()
                    
                    ui.notify(f'标签 "{user_tag["name"]}" 已删除', type='positive')
                    dialog.close()
                else:
                    ui.notify('删除标签失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'删除标签时出错：{str(e)}', type='negative')
        
        # 创建确认对话框
        with ui.dialog(value=True) as dialog, ui.card().classes('w-80 p-6'):
            ui.label('删除标签').classes('text-lg font-medium text-red-600 mb-4')
            ui.label(f'确定要删除标签 "{user_tag["name"]}" 吗？').classes('mb-2')
            ui.label('删除后，该标签将从所有任务中移除。').classes('text-sm text-grey-6 mb-4')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('删除', on_click=delete_tag).props('color=negative')
    
    def show_complete_tag_confirm(self, user_tag: Dict):
        """显示完成标签任务确认对话框"""
        def complete_tag():
            """完成标签下的所有任务"""
            try:
                success = self.tag_manager.complete_tag_tasks(user_tag['tag_id'])
                
                if success:
                    # 刷新界面
                    self.refresh_sidebar_tags()
                    if self.on_refresh_ui:
                        self.on_refresh_ui()
                    
                    ui.notify(f'标签 "{user_tag["name"]}" 下的所有任务已完成', type='positive')
                    dialog.close()
                else:
                    ui.notify('完成任务失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'完成任务时出错：{str(e)}', type='negative')
        
        # 创建确认对话框
        with ui.dialog(value=True) as dialog, ui.card().classes('w-80 p-6'):
            ui.label('完成标签任务').classes('text-lg font-medium text-blue-600 mb-4')
            ui.label(f'确定要完成标签 "{user_tag["name"]}" 下的所有待办任务吗？').classes('mb-2')
            ui.label('此操作将把该标签下的所有未完成任务标记为已完成。').classes('text-sm text-grey-6 mb-4')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('完成', on_click=complete_tag).props('color=positive')