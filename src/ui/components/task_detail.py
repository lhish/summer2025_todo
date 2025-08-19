"""
任务详情组件
"""

from nicegui import ui
from typing import Dict, Optional, Callable, List
from datetime import date
from .tag_edit_dialog import TagEditDialog


class TaskDetailComponent:
    def __init__(self, task_manager, on_task_update: Callable, on_start_pomodoro: Callable, on_close: Callable, user_id: int = 1):
        self.task_manager = task_manager
        self.on_task_update = on_task_update
        self.on_start_pomodoro = on_start_pomodoro
        self.on_close = on_close
        self.user_id = user_id
        self.selected_task: Optional[Dict] = None
        self.initial_task_state: Optional[Dict] = None  # 保存初始状态
        self.task_detail_open = False
        self.current_view = None  # 跟踪当前视图
        
        # UI 组件引用
        self.title_input = None
        self.description_input = None
        self.due_date_input = None
        self.priority_select = None
        self.estimated_pomodoros_input = None
        self.tags_container = None
        self.new_tag_input = None
        self.repeat_select = None
        
        # 初始化标签编辑对话框组件
        self.tag_edit_dialog = TagEditDialog(
            tag_manager=task_manager.tag_manager,
            on_success=self._on_tag_dialog_success,
            user_id=user_id
        )

    def set_current_view(self, view_type: str):
        """设置当前视图类型"""
        self.current_view = view_type

    def create_task_detail_panel(self, container):
        """创建任务详情面板"""
        if not self.selected_task:
            return
        
        container.clear()
        
        with container.classes('relative h-full'):
            # 主内容区（可滚动）
            with ui.scroll_area().classes('h-full').style('height: calc(100vh - 60px);'):
                with ui.column().classes('w-full min-w-80 max-w-md p-4 mx-auto').style('min-height: 100%; padding-bottom: 80px;'):
                    # 任务标题（可编辑）和操作按钮
                    with ui.row().classes('w-full items-center gap-2 mb-4'):
                        # 完成按钮
                        def toggle_complete():
                            new_status = 'completed' if self.selected_task['status'] == 'pending' else 'pending'
                            self.task_manager.toggle_task_status(self.selected_task['task_id'], new_status)
                            self.selected_task['status'] = new_status
                            self.on_task_update()
                            self.create_task_detail_panel(container)  # 刷新面板
                        
                        # 反转图标显示逻辑：未完成时显示空心圆，已完成时显示实心勾选
                        complete_icon = 'radio_button_unchecked' if self.selected_task['status'] == 'pending' else 'check_circle'
                        complete_color = 'grey' if self.selected_task['status'] == 'pending' else 'green'
                        
                        ui.button(icon=complete_icon, on_click=toggle_complete).props(f'flat round size=md color={complete_color}')
                        
                        # 播放按钮（番茄钟）
                        def start_pomodoro():
                            self.on_start_pomodoro(self.selected_task['task_id'])
                        
                        ui.button(icon='play_arrow', on_click=start_pomodoro).props('flat round size=md color=primary')
                        
                        self.title_input = ui.input(
                            placeholder='输入任务标题...',
                            value=self.selected_task['title']
                        ).classes('flex-1 text-base sm:text-lg font-medium').props('borderless')
                        # 添加失去焦点时自动保存
                        self.title_input.on('blur', lambda: self.auto_save_field('title'))
                        
                        # 删除按钮
                        ui.button(icon='delete', on_click=self.delete_task).props('flat round size=sm color=negative').tooltip('删除任务')
                        

                    
                    # 分隔线
                    ui.separator().classes('mb-4')
                    
                    # 任务属性编辑区域
                    with ui.column().classes('w-full gap-3 sm:gap-4'):
                        
                        # 标签编辑区域
                        with ui.column().classes('w-full gap-2'):
                            # 标签标题行
                            with ui.row().classes('w-full items-center gap-2'):
                                ui.icon('local_offer').classes('text-grey-6 flex-shrink-0')
                                ui.label('标签').classes('text-sm font-medium')
                            
                            # 标签chip显示和编辑区域
                            current_tags = self.selected_task.get('tags', [])
                            self.tags_container = ui.row().classes('w-full gap-1 flex-wrap items-center')
                            
                            with self.tags_container:
                                # 显示现有标签
                                for tag in current_tags:
                                    def edit_tag(tag_data=tag):
                                        # 调用标签编辑对话框
                                        self.show_edit_tag_dialog(tag_data)
                                    
                                    def remove_tag(tag_data=tag):
                                        # 从任务中移除标签
                                        updated_tags = [t for t in current_tags if t['tag_id'] != tag_data['tag_id']]
                                        tag_names = [t['name'] for t in updated_tags]
                                        # 更新任务标签
                                        if self.task_manager.update_task(
                                            task_id=self.selected_task['task_id'],
                                            tags=tag_names
                                        ):
                                            self.selected_task['tags'] = updated_tags
                                            self.refresh_tags_display()
                                            # 通知主界面更新
                                            self.on_task_update()
                                            ui.notify(f'已移除标签: {tag_data["name"]}', type='positive')
                                        else:
                                            ui.notify('移除标签失败', type='negative')
                                    
                                    ui.chip(
                                        text=tag['name'], 
                                        icon='label', 
                                        color=tag.get('color', '#757575'),
                                        text_color='white',
                                        removable=True,
                                        on_click=lambda t=tag: edit_tag(t)
                                    ).on('remove', lambda t=tag: remove_tag(t))
                                
                                # 添加新标签的输入框
                                self.new_tag_input = ui.input(
                                    placeholder='添加标签'
                                ).classes('flex-shrink-0 w-32').props('dense borderless maxlength=15')
                                # 添加回车键支持
                                self.new_tag_input.on('keydown', self.handle_tag_enter_key)
                                
                                # 添加按钮
                                ui.button(
                                    icon='add',
                                    on_click=self.add_new_tag
                                ).props('round dense flat color=primary size=sm')
                        
                        # 番茄数
                        with ui.row().classes('w-full items-center gap-1 sm:gap-2'):
                            ui.icon('timer').classes('text-grey-6 flex-shrink-0 text-sm')
                            ui.label('预估番茄钟:').classes('min-w-fit text-xs sm:text-sm')
                            self.estimated_pomodoros_input = ui.number(
                                value=self.selected_task.get('estimated_pomodoros', 1),
                                min=1,
                                max=20
                            ).classes('w-12 sm:w-16').props('borderless dense')
                            # 添加失去焦点时自动保存
                            self.estimated_pomodoros_input.on('blur', lambda: self.auto_save_field('estimated_pomodoros'))
                            ui.label('个').classes('text-xs sm:text-sm')
                            
                            # 显示已使用数量
                            used_pomodoros = self.selected_task.get('used_pomodoros', 0)
                            if used_pomodoros > 0:
                                ui.label(f'(已完成 {used_pomodoros} 个)').classes('text-xs text-grey-6')
                        
                        # 到期日
                        with ui.row().classes('w-full items-center gap-2 sm:gap-3'):
                            ui.icon('event').classes('text-grey-6 flex-shrink-0')
                            ui.label('截止日期:').classes('min-w-fit text-xs sm:text-sm')
                            due_date_value = self.selected_task.get('due_date')
                            if due_date_value and isinstance(due_date_value, str):
                                due_date_value = due_date_value.split()[0]
                            self.due_date_input = ui.input(
                                placeholder='设置到期日',
                                value=due_date_value or ''
                            ).props('type=date borderless').classes('flex-1 min-w-0')
                            # 添加失去焦点时自动保存
                            self.due_date_input.on('blur', lambda: self.auto_save_field('due_date'))
                            
                            # 添加清除截止日期按钮
                            ui.button(icon='clear', on_click=self.clear_due_date).props('flat round dense color=grey size=sm').tooltip('清除截止日期')
                        
                        # 重复周期（可编辑）
                        with ui.row().classes('w-full items-center gap-2 sm:gap-3'):
                            ui.icon('repeat').classes('text-grey-6 flex-shrink-0')
                            
                            # 重复周期选择框
                            repeat_options = {
                                'none': '不重复',
                                'daily': '每天',
                                'weekly': '每周',
                                'monthly': '每月'
                            }
                            
                            current_repeat = self.selected_task.get('repeat_cycle', 'none')
                            self.repeat_select = ui.select(
                                options=repeat_options,
                                value=current_repeat,
                                label='重复周期'
                            ).classes('flex-1 min-w-0').props('borderless')
                            # 添加值改变时自动保存
                            def on_repeat_change():
                                if self.repeat_select:
                                    current_value = self.repeat_select.value
                                    self.auto_save_field('repeat_cycle', new_value=current_value)
                            self.repeat_select.on('update:model-value', on_repeat_change)
                        
                        # 优先级（可编辑）
                        with ui.row().classes('w-full items-center gap-2 sm:gap-3'):
                            ui.icon('flag').classes('text-grey-6 flex-shrink-0')
                            
                            # 优先级选择框
                            priority_options = {
                                'low': '低优先级',
                                'medium': '中优先级',
                                'high': '高优先级'
                            }
                            
                            current_priority = self.selected_task.get('priority', 'medium')
                            self.priority_select = ui.select(
                                options=priority_options,
                                value=current_priority,
                                label='优先级'
                            ).classes('flex-1 min-w-0').props('borderless')
                            # 添加值改变时自动保存
                            def on_priority_change():
                                if self.priority_select:
                                    current_value = self.priority_select.value
                                    self.auto_save_field('priority', new_value=current_value)
                            self.priority_select.on('update:model-value', on_priority_change)
                        
                        # 备注
                        with ui.column().classes('w-full gap-2'):
                            self.description_input = ui.textarea(
                                placeholder='添加备注...',
                                value=self.selected_task.get('description', '') or ''
                            ).classes('w-full min-h-20').props('borderless auto-grow')
                            # 添加失去焦点时自动保存
                            self.description_input.on('blur', lambda: self.auto_save_field('description'))
                    
                    # 底部区域
                    ui.space().classes('flex-grow min-h-4')
                                        
                    # 分隔线
                    ui.separator().classes('my-4')
                    
                    # 创建日期
                    with ui.row().classes('w-full justify-center mt-2'):
                        created_at = self.selected_task.get('created_at', '未知')
                        if isinstance(created_at, str) and len(created_at) > 10:
                            created_at = created_at[:10]  # 只显示日期部分
                        ui.label(f'创建于 {created_at}').classes('text-xs text-grey-6')
            # 详情栏底部按钮条（绝对定位，靠左，无背景无阴影）
            with ui.row().classes('absolute left-0 bottom-0 w-full p-3 z-10 justify-start mb-4'):
                ui.button('关闭', icon='close', on_click=self.close_task_detail).props('flat color=grey size=md').tooltip('关闭详情面板')
                # ui.button('重置', icon='refresh', on_click=self.reset_form).props('flat color=grey size=md').tooltip('重置到初始状态')

    def close_task_detail(self):
        """关闭任务详情面板"""
        self.task_detail_open = False
        self.selected_task = None
        self.initial_task_state = None  # 清理初始状态
        
        # 清理UI组件引用
        self.title_input = None
        self.description_input = None
        self.due_date_input = None
        self.priority_select = None
        self.estimated_pomodoros_input = None
        self.tags_container = None
        self.new_tag_input = None
        self.repeat_select = None
        
        self.on_close()

    def clear_due_date(self):
        """清除截止日期"""
        if not self.selected_task or not self.task_detail_open:
            ui.notify('无法清除截止日期：没有选中的任务', type='warning')
            return
        
        try:
            # 清空输入框
            if self.due_date_input:
                self.due_date_input.value = ''
            
            # 保存到数据库，传递当前视图信息
            task_id = self.selected_task['task_id']
            result = self.task_manager.update_task(
                task_id=task_id,
                due_date=None,
                current_view=self.current_view
            )
            
            if result.get('success', False):
                self.selected_task['due_date'] = None
                ui.notify('截止日期已清除', type='positive', timeout=1500)
                
                # 检查是否需要显示视图变更通知
                view_change = result.get('view_change')
                if view_change and view_change.get('should_remove'):
                    ui.notify(view_change['notification'], type='info', timeout=3000)
                
                self.on_task_update()
            else:
                ui.notify('清除截止日期失败：数据库更新失败', type='negative')
                
        except Exception as e:
            ui.notify(f'清除截止日期失败：{str(e)}', type='negative')



    # def reset_form(self):
    #     """重置表单到初始状态"""
    #     if not self.initial_task_state:
    #         ui.notify('无法重置：没有初始状态数据', type='warning')
    #         return
    #     try:
    #         # 重置各个字段到初始状态
    #         if self.title_input:
    #             self.title_input.value = self.initial_task_state['title']
    #         if self.description_input:
    #             self.description_input.value = self.initial_task_state['description']
    #         if self.due_date_input:
    #             due_date_value = self.initial_task_state['due_date']
    #             if due_date_value and isinstance(due_date_value, str):
    #                 due_date_value = due_date_value.split()[0]
    #             self.due_date_input.value = due_date_value or ''
    #         if self.estimated_pomodoros_input:
    #             self.estimated_pomodoros_input.value = self.initial_task_state['estimated_pomodoros']
    #         if self.repeat_select:
    #             self.repeat_select.value = self.initial_task_state['repeat_cycle']
    #         if self.priority_select:
    #             self.priority_select.value = self.initial_task_state['priority']
    #         # 重置标签到初始状态
    #         initial_tag_names = [tag['name'] for tag in self.initial_task_state['tags']]
    #         # 更新任务标签到初始状态
    #         success = self.task_manager.update_task(
    #             task_id=self.selected_task['task_id'],
    #             title=self.initial_task_state['title'],
    #             description=self.initial_task_state['description'],
    #             due_date=self.initial_task_state['due_date'],
    #             priority=self.initial_task_state['priority'],
    #             estimated_pomodoros=self.initial_task_state['estimated_pomodoros'],
    #             repeat_cycle=self.initial_task_state['repeat_cycle'],
    #             tags=initial_tag_names
    #         )
    #         if success:
    #             # 重新获取任务数据以更新标签显示
    #             updated_task = self.task_manager.get_task_by_id(self.selected_task['task_id'])
    #             if updated_task:
    #                 self.selected_task = updated_task
    #                 self.refresh_tags_display()
    #             ui.notify('已重置到初始状态', type='positive')
    #             # 触发界面更新
    #             self.on_task_update()
    #         else:
    #             ui.notify('重置失败', type='negative')
    #     except Exception as e:
    #         ui.notify(f'重置失败: {str(e)}', type='negative')

    def show_task_detail(self, task: Dict, container):
        """显示任务详情"""
        self.selected_task = task
        # 保存初始状态，用于重置功能
        self.initial_task_state = {
            'title': task.get('title', ''),
            'description': task.get('description', '') or '',
            'due_date': task.get('due_date'),
            'priority': task.get('priority', 'medium'),
            'estimated_pomodoros': task.get('estimated_pomodoros', 1),
            'repeat_cycle': task.get('repeat_cycle', 'none'),
            'tags': [tag.copy() for tag in task.get('tags', [])]  # 深拷贝标签
        }
        self.task_detail_open = True
        self.create_task_detail_panel(container)

    def is_open(self) -> bool:
        """检查详情面板是否打开"""
        return self.task_detail_open

    def get_selected_task(self) -> Optional[Dict]:
        """获取选中的任务"""
        return self.selected_task



    def delete_task(self):
        """删除任务（带确认对话框）"""
        if not self.selected_task:
            ui.notify('没有选中的任务', type='warning')
            return
        
        def confirm_delete():
            try:
                success = self.task_manager.delete_task(self.selected_task['task_id'])
                if success:
                    ui.notify('任务删除成功', type='positive')
                    # 通知父组件更新任务列表
                    self.on_task_update()
                    # 关闭详情面板
                    self.close_task_detail()
                else:
                    ui.notify('任务删除失败，请重试', type='negative')
            except Exception as e:
                ui.notify(f'删除失败: {str(e)}', type='negative')
            finally:
                dialog.close()
        
        def cancel_delete():
            dialog.close()
        
        # 创建确认对话框
        with ui.dialog() as dialog:
            with ui.card().classes('w-96'):
                with ui.column().classes('w-full gap-4'):
                    # 标题
                    ui.label('确认删除任务').classes('text-h6 font-bold text-red-600')
                    
                    # 任务信息
                    with ui.column().classes('w-full gap-2 p-4 bg-grey-1 rounded'):
                        ui.label(f'任务标题: {self.selected_task["title"]}').classes('font-medium')
                        if self.selected_task.get('description'):
                            ui.label(f'描述: {self.selected_task["description"][:50]}...').classes('text-sm text-grey-6')
                        if self.selected_task.get('due_date'):
                            ui.label(f'到期日: {self.selected_task["due_date"]}').classes('text-sm text-grey-6')
                    
                    # 警告信息
                    ui.label('此操作不可撤销，确定要删除这个任务吗？').classes('text-grey-8')
                    
                    # 按钮行
                    with ui.row().classes('w-full justify-end gap-2 mt-4'):
                        ui.button('取消', on_click=cancel_delete).props('flat')
                        ui.button('确认删除', on_click=confirm_delete).props('color=negative')
        
        dialog.open()

    def refresh_task_data(self):
        """从数据库刷新任务数据"""
        if not self.selected_task:
            return False
            
        try:
            updated_task = self.task_manager.get_task_by_id(self.selected_task['task_id'])
            if updated_task:
                self.selected_task = updated_task
                return True
            else:
                ui.notify('无法获取最新任务数据', type='warning')
                return False
        except Exception as e:
            ui.notify(f'刷新任务数据失败: {str(e)}', type='negative')
            return False

    def get_priority_color(self, priority: str) -> str:
        """根据优先级获取颜色"""
        color_map = {
            'high': 'red',
            'medium': 'orange', 
            'low': 'green'
        }
        return color_map.get(priority, 'grey')

    def format_date(self, date_value) -> str:
        """格式化日期显示"""
        if not date_value:
            return '未设置'
        
        if isinstance(date_value, str):
            try:
                date_obj = date.fromisoformat(date_value.split()[0])
                return date_obj.strftime('%Y年%m月%d日')
            except:
                return date_value
        elif isinstance(date_value, date):
            return date_value.strftime('%Y年%m月%d日')
        
        return str(date_value)

    def calculate_time_remaining(self) -> str:
        """计算剩余时间"""
        if not self.selected_task:
            return '0分钟'
        
        estimated = self.selected_task.get('estimated_pomodoros', 1)
        used = self.selected_task.get('used_pomodoros', 0)
        remaining = max(0, estimated - used)
        
        return f'{remaining * 25}分钟'
    


    def refresh_tags_display(self):
        """刷新标签显示"""
        if self.tags_container and self.selected_task:
            self.tags_container.clear()
            current_tags = self.selected_task.get('tags', [])
            
            with self.tags_container:
                # 显示现有标签
                for tag in current_tags:
                    def edit_tag(tag_data=tag):
                        # 调用标签编辑对话框
                        self.show_edit_tag_dialog(tag_data)
                    
                    def remove_tag(tag_data=tag):
                        updated_tags = [t for t in current_tags if t['tag_id'] != tag_data['tag_id']]
                        tag_names = [t['name'] for t in updated_tags]
                        if self.task_manager.update_task(
                            task_id=self.selected_task['task_id'],
                            tags=tag_names
                        ):
                            self.selected_task['tags'] = updated_tags
                            self.refresh_tags_display()
                            # 通知主界面更新
                            self.on_task_update()
                            ui.notify(f'已移除标签: {tag_data["name"]}', type='positive')
                        else:
                            ui.notify('移除标签失败', type='negative')
                    
                    ui.chip(
                        text=tag['name'], 
                        icon='label', 
                        color=tag.get('color', '#757575'),
                        text_color='white',
                        removable=True,
                        on_click=lambda t=tag: edit_tag(t)
                    ).on('remove', lambda t=tag: remove_tag(t))
                
                # 重新创建输入框
                self.new_tag_input = ui.input(
                    placeholder='添加标签'
                ).classes('flex-shrink-0 w-32').props('dense borderless maxlength=15')
                # 添加回车键支持
                self.new_tag_input.on('keydown', self.handle_tag_enter_key)
                
                ui.button(
                    icon='add',
                    on_click=self.add_new_tag
                ).props('round dense flat color=primary size=sm')
    
    def handle_tag_enter_key(self, e):
        """处理标签输入框的回车键事件"""
        # 检查是否按下了Enter键
        if e.args.get('key') == 'Enter' and self.new_tag_input.value.strip():
            self.add_new_tag()
            # 重新聚焦到输入框
            ui.run_javascript('''
                setTimeout(() => {
                    const input = document.querySelector('input[placeholder="添加标签"]');
                    if (input) input.focus();
                }, 100);
            ''')
    
    def add_new_tag(self):
        """添加新标签"""
        if not self.new_tag_input or not self.new_tag_input.value.strip():
            return
        
        tag_name = self.new_tag_input.value.strip()
        
        # 检查标签长度
        if len(tag_name) > 15:
            ui.notify('标签名称不能超过15个字符', type='warning')
            return
        
        current_tags = self.selected_task.get('tags', [])
        
        # 检查标签是否已存在
        if any(tag['name'] == tag_name for tag in current_tags):
            ui.notify(f'标签 "{tag_name}" 已存在', type='warning')
            # 清空输入框
            self.new_tag_input.value = ''
            return
        
        # 添加标签到任务
        tag_names = [tag['name'] for tag in current_tags] + [tag_name]
        if self.task_manager.update_task(
            task_id=self.selected_task['task_id'],
            tags=tag_names
        ):
            # 重新获取任务数据以获取更新后的标签信息
            updated_task = self.task_manager.get_task_by_id(self.selected_task['task_id'])
            if updated_task:
                self.selected_task = updated_task
                # 清空输入框
                self.new_tag_input.value = ''
                self.refresh_tags_display()
                # 通知主界面更新
                self.on_task_update()
                ui.notify(f'已添加标签: {tag_name}', type='positive')
        else:
            ui.notify('添加标签失败', type='negative')



    def _on_tag_dialog_success(self):
        """标签对话框成功后的回调"""
        # 重新获取任务数据以获取更新后的标签信息
        updated_task = self.task_manager.get_task_by_id(self.selected_task['task_id'])
        if updated_task:
            self.selected_task = updated_task
            self.refresh_tags_display()
            # 触发任务更新回调
            self.on_task_update()

    def show_edit_tag_dialog(self, user_tag: Dict):
        """显示编辑标签对话框"""
        self.tag_edit_dialog.show_edit_dialog(user_tag)

    def auto_save_field(self, field_name: str, new_value: any = None):
        """自动保存单个字段。可以接收来自事件的值，也可以自己从组件获取。"""
        if not self.selected_task or not self.task_detail_open:
            return

        try:
            current_value = None
            original_value = self.selected_task.get(field_name)

            # 优先使用事件传递过来的新值 (new_value)
            if new_value is not None:
                current_value = new_value
            # 否则，从对应的UI组件读取值 (用于 on('blur') 事件)
            else:
                if field_name == 'title':
                    if not self.title_input: return
                    current_value = self.title_input.value.strip() if self.title_input.value else ''
                    if not current_value:
                        ui.notify('任务标题不能为空', type='warning')
                        return
                elif field_name == 'description':
                    if not self.description_input: return
                    current_value = self.description_input.value.strip() if self.description_input.value else None
                elif field_name == 'due_date':
                    if not self.due_date_input: return
                    due_date_str = self.due_date_input.value
                    if due_date_str and due_date_str.strip():
                        try:
                            current_value = date.fromisoformat(due_date_str.strip())
                        except ValueError:
                            ui.notify('日期格式不正确', type='warning')
                            return
                    else:
                        current_value = None  # 空值表示清除截止日期
                elif field_name == 'estimated_pomodoros':
                    if not self.estimated_pomodoros_input: return
                    try:
                        current_value = int(self.estimated_pomodoros_input.value)
                        if current_value < 1:
                            ui.notify('预估番茄钟数量至少为1', type='warning')
                            return
                    except (ValueError, TypeError):
                        ui.notify('请输入有效的数字', type='warning')
                        return
            
            # 对原始值进行适配，以便比较
            # (例如，数据库里存的是'medium'，但get出来可能是None，需要修正)
            if field_name in ['priority', 'repeat_cycle'] and original_value is None:
                original_value = 'medium' if field_name == 'priority' else 'none'
            
            # 检查是否有变化
            if current_value == original_value:
                return  # 没有变化，不需要保存

            # 构建并执行更新
            update_params = {
                'task_id': self.selected_task['task_id'],
                field_name: current_value,
                'current_view': self.current_view  # 传递当前视图信息
            }
            
            result = self.task_manager.update_task(**update_params)
            
            if result.get('success', False):
                self.selected_task[field_name] = current_value
                field_display_names = {
                    'title': '标题', 'description': '描述', 'due_date': '到期日',
                    'priority': '优先级', 'estimated_pomodoros': '预估番茄钟', 'repeat_cycle': '重复周期'
                }
                field_display = field_display_names.get(field_name, field_name)
                ui.notify(f'{field_display}已保存', type='info', timeout=1500, position='top')
                
                # 检查是否需要显示视图变更通知
                view_change = result.get('view_change')
                if view_change and view_change.get('should_remove'):
                    ui.notify(view_change['notification'], type='info', timeout=3000)
                
                self.on_task_update()
            else:
                ui.notify(f'保存失败', type='negative')

        except (ValueError, TypeError) as e:
            ui.notify(f'输入值无效: {e}', type='warning')
        except Exception as e:
            ui.notify(f'保存失败: {str(e)}', type='negative')