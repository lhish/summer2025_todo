"""
侧边栏组件
"""

from nicegui import ui
from typing import Dict, List, Callable, Optional
from .tag_edit_dialog import TagEditDialog


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
        
        # 初始化标签编辑对话框组件
        self.tag_edit_dialog = TagEditDialog(
            tag_manager=tag_manager,
            on_success=self._on_tag_dialog_success,
            user_id=current_user['user_id']
        )

        
        # 加载用户标签
        self.refresh_user_tags()
        
        # 添加CSS样式隐藏滚动条和去掉白边
        ui.add_head_html('''
            <link rel="stylesheet" href="/static/sidebar.css">
        ''')

    def create_sidebar(self, container):
        """创建左侧边栏"""
        self.sidebar_container = container
        
        # 根据初始状态应用CSS类
        if self.sidebar_collapsed:
            container.classes(add='sidebar-collapsed')
        else:
            container.classes(add='sidebar-expanded')
        
        with container:
            # 使用flexbox布局，让中间的滚动区域能够自适应
            with ui.column().classes('w-full h-full flex').style('height: 100vh;'):
            # 顶部：折叠/展开按钮
                with ui.row().classes('w-full p-4 justify-center sidebar-toggle-row'):
                    ui.button(icon='menu', on_click=self.toggle_sidebar).props('flat round')
                
                ui.separator()
                
                # 第一部分：默认视图
                with ui.column().classes('w-full p-2'):
                    self.create_sidebar_item('今天截止', 'sunny', 'my_day')
                    self.create_sidebar_item('即将截止', 'event', 'planned')
                    self.create_sidebar_item('重要', 'star', 'important')
                    self.create_sidebar_item('所有任务', 'list', 'all')
                
                ui.separator()
                
                # 第二部分：标签 - 使用flex-1让这部分占据剩余空间
                with ui.column().classes('w-full p-1 flex-1').style('min-height: 0;'):
                    self.sidebar_tags_container = ui.column().classes('w-full h-full')
                    self.refresh_sidebar_tags()

                # 占据剩余空间
                ui.element('div').style('margin-top: auto')
                
                # 底部区域
                with ui.column().classes('w-full'):
                    # 已登录状态 - 根据展开/折叠状态显示不同样式
                    if not self.sidebar_collapsed:
                        ui.separator()
                        with ui.column().classes('w-full p-3 user-info'):
                            with ui.column().classes('gap-1 w-full').style('min-width: 0;'):
                                # 用户邮箱，限制最大宽度避免溢出
                                email = self.current_user['email']
                                # 如果邮箱太长，显示省略号
                                display_email = email if len(email) <= 25 else email[:22] + '...'
                                ui.label(display_email).classes('text-sm font-medium').style('white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;')
                                ui.label('已登录').classes('text-xs text-grey-6')
                        ui.separator()
                    else:
                        # 折叠时显示用户头像或首字母
                        with ui.column().classes('w-full items-center p-2'):
                            ui.separator()
                            # 显示用户邮箱首字母的圆形头像
                            initial = self.current_user['email'][0].upper() if self.current_user['email'] else 'U'
                            with ui.element('div').classes('w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center user-avatar'):
                                ui.label(initial).classes('text-white text-sm font-bold')
                            ui.separator()
                    
                    # 操作按钮 - 始终显示，根据展开/收起状态调整布局
                    with ui.column().classes('w-full p-3 bottom-actions').style('padding-bottom: 12px;'):
                        if self.sidebar_collapsed:
                            # 收起时：竖直排列居中，添加工具提示
                            with ui.column().classes('w-full items-center gap-2'):
                                with ui.button(icon='add', on_click=self.show_create_tag_dialog).props('flat round size=sm color=primary') as add_btn:
                                    add_btn.tooltip('新建标签')
                                with ui.button(icon='analytics', on_click=self.on_statistics).props('flat round size=sm') as stats_btn:
                                    stats_btn.tooltip('统计分析')
                                with ui.button(icon='settings', on_click=self.on_settings).props('flat round size=sm') as settings_btn:
                                    settings_btn.tooltip('设置')
                                with ui.button(icon='logout', on_click=self.on_logout).props('flat round size=sm color=negative') as logout_btn:
                                    logout_btn.tooltip('退出登录')
                        else:
                            # 展开时：新建标签按钮靠左，其他按钮靠右
                            with ui.row().classes('w-full justify-between items-center gap-2'):
                                ui.button('新建标签', icon='add', on_click=self.show_create_tag_dialog).props('flat color=primary').classes('text-sm font-medium flex-shrink-0').style('white-space: nowrap; min-width: 80px;')
                                
                                with ui.row().classes('gap-1 flex-shrink-0'):
                                    with ui.button(icon='analytics', on_click=self.on_statistics).props('flat round size=sm') as stats_btn:
                                        stats_btn.tooltip('统计分析')
                                    with ui.button(icon='settings', on_click=self.on_settings).props('flat round size=sm') as settings_btn:
                                        settings_btn.tooltip('设置')
                                    with ui.button(icon='logout', on_click=self.on_logout).props('flat round size=sm color=negative') as logout_btn:
                                        logout_btn.tooltip('退出登录')

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
            ui.icon(icon).classes('text-xl text-grey-7 flex-shrink-0')
            if not self.sidebar_collapsed:
                ui.label(label).classes('text-sm flex-1 truncate').style('white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0;')

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
            classes = 'flex-1 items-center min-w-0'
            if self.sidebar_collapsed:
                classes += ' justify-center'
            else:
                classes += ' gap-2'
            # 左侧：可点击的主要区域
            with ui.row().classes(classes).on('click', select_tag(user_tag)):
                # 使用对应颜色的圆圈图标
                ui.element('div').classes('w-4 h-4 rounded-full flex-shrink-0').style(f'background-color: {user_tag.get("color", "#757575")}; min-width: 16px; min-height: 16px;')
                if not self.sidebar_collapsed:
                    ui.label(user_tag['name']).classes('text-sm truncate flex-1').style('white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; max-width: 120px;')
                    if user_tag.get('task_count', 0) > 0:
                        ui.badge(str(user_tag['task_count'])).props('color=grey-5').classes('flex-shrink-0')
            
            # 右侧：三个点菜单按钮（hover时显示）
            if not self.sidebar_collapsed:
                with ui.button(icon='more_vert').props('flat round size=xs').classes('tag-menu-button flex-shrink-0'):
                    with ui.menu():
                        ui.menu_item('编辑标签', on_click=lambda t=user_tag: self.show_edit_tag_dialog(t), auto_close=False)
                        ui.menu_item('删除标签', on_click=lambda t=user_tag: self.show_delete_tag_confirm(t), auto_close=False)
                        ui.menu_item('完成标签任务', on_click=lambda t=user_tag: self.show_complete_tag_confirm(t), auto_close=False)

    def toggle_sidebar(self):
        """切换侧边栏展开/折叠状态"""
        self.sidebar_collapsed = not self.sidebar_collapsed
        
        if self.sidebar_collapsed:
            # 折叠：移除所有展开状态类，添加折叠类
            self.sidebar_container.classes(remove='sidebar-expanded sidebar-expanding')
            self.sidebar_container.classes(add='sidebar-collapsed')
            # 折叠时立即更新内容
            ui.timer(0.1, lambda: self.update_sidebar_content(), once=True)
        else:
            # 展开：移除折叠类，添加展开中状态类
            self.sidebar_container.classes(remove='sidebar-collapsed')
            self.sidebar_container.classes(add='sidebar-expanding')
            
            # 展开动画完成后，移除展开中状态，添加完全展开状态
            def on_expand_complete():
                self.sidebar_container.classes(remove='sidebar-expanding')
                self.sidebar_container.classes(add='sidebar-expanded')
                self.update_sidebar_content()
            
            ui.timer(0.35, on_expand_complete, once=True)

    def update_sidebar_active_state(self):
        """更新侧边栏激活状态"""
        # 重新创建侧边栏以更新active状态
        if self.sidebar_container:
            self.sidebar_container.clear()
            self.create_sidebar(self.sidebar_container)
    
    def update_sidebar_content(self):
        """更新侧边栏内容，用于展开/折叠状态切换后"""
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
    
    def _on_tag_dialog_success(self):
        """标签对话框成功后的回调"""
        # 刷新侧边栏标签显示
        self.refresh_sidebar_tags()
        # 刷新整个界面
        if self.on_refresh_ui:
            self.on_refresh_ui()
    
    def show_create_tag_dialog(self):
        """显示创建标签对话框"""
        self.tag_edit_dialog.show_create_dialog()
    

    def show_edit_tag_dialog(self, user_tag: Dict):
        """显示编辑标签对话框"""
        self.tag_edit_dialog.show_edit_dialog(user_tag)
    
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