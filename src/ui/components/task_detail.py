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
        self.task_detail_open = False
        
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

    def create_task_detail_panel(self, container):
        """创建任务详情面板"""
        if not self.selected_task:
            return
        
        container.clear()
        
        with container:
            # 使用响应式设计的主容器，添加滚动支持
            with ui.scroll_area().classes('h-full').style('height: calc(100vh - 60px);'):
                with ui.column().classes('w-full min-w-80 max-w-md p-4 mx-auto').style('min-height: 100%;'):
                    # 顶部操作按钮行
                    with ui.row().classes('w-full gap-2 sm:gap-4 mb-4 sm:mb-6 justify-center'):
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
                        complete_text = '标记完成' if self.selected_task['status'] == 'pending' else '已完成'
                        
                        with ui.column().classes('items-center'):
                            ui.button(icon=complete_icon, on_click=toggle_complete).props(f'flat round size=lg color={complete_color}')
                            ui.label(complete_text).classes('text-xs text-center mt-1')
                        
                        # 播放按钮（番茄钟）
                        def start_pomodoro():
                            self.on_start_pomodoro(self.selected_task['task_id'])
                        
                        with ui.column().classes('items-center'):
                            ui.button(icon='play_arrow', on_click=start_pomodoro).props('flat round size=lg color=primary')
                            ui.label('开始专注').classes('text-xs text-center mt-1')
                    
                    # 任务标题（可编辑）和操作按钮
                    with ui.row().classes('w-full items-center gap-2 mb-4'):
                        self.title_input = ui.input(
                            placeholder='输入任务标题...',
                            value=self.selected_task['title']
                        ).classes('flex-1 text-base sm:text-lg font-medium').props('borderless')
                        
                        # 操作按钮
                        ui.button(icon='refresh', on_click=self.reset_form).props('flat round size=sm color=grey').tooltip('重置表单')
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
                                ).classes('flex-shrink-0 w-32').props('dense borderless')
                                # 添加回车键支持
                                self.new_tag_input.on('keydown', self.handle_tag_enter_key)
                                
                                # 添加按钮
                                ui.button(
                                    icon='add',
                                    on_click=self.add_new_tag
                                ).props('round dense flat color=primary size=sm')
                        
                        # 番茄数
                        with ui.row().classes('w-full items-center gap-2 sm:gap-3'):
                            ui.icon('timer').classes('text-grey-6 flex-shrink-0')
                            ui.label('预估番茄钟:').classes('min-w-fit text-sm sm:text-base')
                            self.estimated_pomodoros_input = ui.number(
                                value=self.selected_task.get('estimated_pomodoros', 1),
                                min=1,
                                max=20
                            ).classes('w-16 sm:w-20').props('borderless dense')
                            ui.label('个').classes('text-sm sm:text-base')
                            
                            # 显示已使用数量
                            used_pomodoros = self.selected_task.get('used_pomodoros', 0)
                            if used_pomodoros > 0:
                                ui.label(f'(已用 {used_pomodoros} 个)').classes('text-xs sm:text-sm text-grey-6')
                        
                        # 到期日
                        with ui.row().classes('w-full items-center gap-2 sm:gap-3'):
                            ui.icon('event').classes('text-grey-6 flex-shrink-0')
                            due_date_value = self.selected_task.get('due_date')
                            if due_date_value and isinstance(due_date_value, str):
                                due_date_value = due_date_value.split()[0]
                            self.due_date_input = ui.input(
                                placeholder='设置到期日',
                                value=due_date_value or ''
                            ).props('type=date borderless').classes('flex-1 min-w-0')
                        
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
                        
                        # 备注
                        with ui.column().classes('w-full gap-2'):
                            with ui.row().classes('w-full items-center gap-2 sm:gap-3'):
                                ui.icon('notes').classes('text-grey-6 flex-shrink-0')
                                ui.label('备注').classes('text-sm sm:text-base')
                            
                            self.description_input = ui.textarea(
                                placeholder='添加备注...',
                                value=self.selected_task.get('description', '') or ''
                            ).classes('w-full min-h-20').props('borderless auto-grow')
                    
                    # 底部区域
                    ui.space().classes('flex-grow min-h-4')
                    
                    # 进度显示
                    estimated = self.selected_task.get('estimated_pomodoros', 1)
                    used = self.selected_task.get('used_pomodoros', 0)
                    if used > 0:
                        progress = (used / estimated * 100) if estimated > 0 else 0
                        progress_value = progress / 100
                        with ui.row().classes('w-full items-center mb-4 p-3 bg-grey-1 rounded'):
                            ui.icon('trending_up').classes('text-primary flex-shrink-0')
                            ui.label(f'进度: {used}/{estimated} 番茄钟').classes('text-xs sm:text-sm flex-shrink-0')
                            with ui.linear_progress(value=progress_value, color='primary', show_value=False, size='1.5em').classes('flex-1 mx-2 sm:mx-3').props('instant-feedback'):
                                ui.label(f'{progress:.2f}%').classes('text-xs text-black absolute-center font-medium')
                    
                    # 分隔线
                    ui.separator().classes('my-4')
                    
                    # 底部操作区
                    with ui.column().classes('w-full gap-3'):
                        # 保存和取消按钮
                        with ui.row().classes('w-full gap-2'):
                            ui.button('保存', icon='save', on_click=self.save_task_changes).props('color=primary').classes('flex-1')
                            ui.button('取消', icon='close', on_click=self.close_with_unsaved_check).props('color=grey').classes('flex-1')
                        
                        # 创建日期
                        with ui.row().classes('w-full justify-center mt-2'):
                            created_at = self.selected_task.get('created_at', '未知')
                            if isinstance(created_at, str) and len(created_at) > 10:
                                created_at = created_at[:10]  # 只显示日期部分
                            ui.label(f'创建于 {created_at}').classes('text-xs text-grey-6')

    def close_task_detail(self):
        """关闭任务详情面板"""
        self.task_detail_open = False
        self.selected_task = None
        
        # 清理UI组件引用
        self.title_input = None
        self.description_input = None
        self.due_date_input = None
        self.priority_select = None
        self.estimated_pomodoros_input = None
        self.tags_input = None
        self.repeat_select = None
        
        self.on_close()

    def validate_form_data(self) -> bool:
        """验证表单数据"""
        if not self.title_input or not self.title_input.value.strip():
            ui.notify('任务标题不能为空', type='negative')
            return False
        
        if self.estimated_pomodoros_input and self.estimated_pomodoros_input.value < 1:
            ui.notify('预估番茄钟数量至少为1', type='negative')
            return False
        
        return True

    def reset_form(self):
        """重置表单到任务原始数据"""
        if not self.selected_task:
            return
        
        if self.title_input:
            self.title_input.value = self.selected_task['title']
        
        if self.description_input:
            self.description_input.value = self.selected_task.get('description', '') or ''
        
        if self.due_date_input:
            due_date_value = self.selected_task.get('due_date')
            if due_date_value and isinstance(due_date_value, str):
                due_date_value = due_date_value.split()[0]
            self.due_date_input.value = due_date_value or ''
        
        if self.estimated_pomodoros_input:
            self.estimated_pomodoros_input.value = self.selected_task.get('estimated_pomodoros', 1)
        
        if self.tags_input:
            current_tags = self.selected_task.get('tags', [])
            tag_names = [tag['name'] for tag in current_tags] if current_tags else []
            self.tags_input.value = ', '.join(tag_names)
        
        if self.repeat_select:
            self.repeat_select.value = self.selected_task.get('repeat_cycle', 'none')
        
        if self.priority_select:
            self.priority_select.value = self.selected_task.get('priority', 'medium')

    def show_task_detail(self, task: Dict, container):
        """显示任务详情"""
        self.selected_task = task
        self.task_detail_open = True
        self.create_task_detail_panel(container)

    def is_open(self) -> bool:
        """检查详情面板是否打开"""
        return self.task_detail_open

    def get_selected_task(self) -> Optional[Dict]:
        """获取选中的任务"""
        return self.selected_task

    def save_task_changes(self) -> bool:
        """保存任务更改到数据库"""
        if not self.selected_task or not all([
            self.title_input, self.description_input, self.due_date_input,
            self.estimated_pomodoros_input, self.tags_input, self.priority_select, self.repeat_select
        ]):
            ui.notify('表单未正确初始化', type='negative')
            return False
        
        # 验证表单数据
        if not self.validate_form_data():
            return False
        
        try:
            # 获取表单数据
            title = self.title_input.value.strip() if self.title_input.value else ''
            description = self.description_input.value.strip() if self.description_input.value else None
            due_date_value = self.due_date_input.value
            priority = self.priority_select.value if self.priority_select else 'medium'
            repeat_cycle = self.repeat_select.value if self.repeat_select else 'none'
            estimated_pomodoros = int(self.estimated_pomodoros_input.value)
            # 标签现在由chip组件管理，不需要从input获取
            tags_str = ''
            
            # 处理截止日期 - 修复类型错误
            due_date = None
            if due_date_value:
                if isinstance(due_date_value, str):
                    due_date_str = due_date_value.strip()
                    if due_date_str:
                        try:
                            due_date = date.fromisoformat(due_date_str)
                        except ValueError:
                            ui.notify('日期格式不正确', type='negative')
                            return False
                elif isinstance(due_date_value, date):
                    due_date = due_date_value
                else:
                    # 处理其他可能的日期类型
                    try:
                        due_date = date.fromisoformat(str(due_date_value))
                    except (ValueError, TypeError):
                        ui.notify('日期格式不正确', type='negative')
                        return False
            
            # 处理标签
            tags = []
            if tags_str:
                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            # 检查是否有实际更改
            has_changes = (
                title != self.selected_task['title'] or
                description != self.selected_task.get('description') or
                due_date != self.selected_task.get('due_date') or
                priority != self.selected_task.get('priority', 'medium') or
                repeat_cycle != self.selected_task.get('repeat_cycle', 'none') or
                estimated_pomodoros != self.selected_task.get('estimated_pomodoros', 1) or
                self._tags_changed(tags)
            )
            
            if not has_changes:
                ui.notify('没有检测到更改', type='info')
                return True
            
            # 更新任务到数据库
            success = self.task_manager.update_task(
                task_id=self.selected_task['task_id'],
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                repeat_cycle=repeat_cycle,
                estimated_pomodoros=estimated_pomodoros,
                tags=tags
            )
            
            if success:
                ui.notify('任务更新成功', type='positive')
                
                # 更新本地任务数据
                self.selected_task.update({
                    'title': title,
                    'description': description,
                    'due_date': due_date,
                    'priority': priority,
                    'repeat_cycle': repeat_cycle,
                    'estimated_pomodoros': estimated_pomodoros,
                })
                
                # 刷新任务数据以获取最新的标签信息
                self.refresh_task_data()
                
                # 通知父组件更新
                self.on_task_update()
                
                return True
            else:
                ui.notify('任务更新失败，请检查网络连接或重试', type='negative')
                return False
                
        except ValueError as e:
            ui.notify(f'数据格式错误: {str(e)}', type='negative')
            return False
        except Exception as e:
            ui.notify(f'保存失败: {str(e)}', type='negative')
            return False

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
    
    def _tags_changed(self, new_tags: List[str]) -> bool:
        """检查标签是否有更改"""
        try:
            current_tags = self.selected_task.get('tags', [])
            current_tag_names = set([tag['name'] for tag in current_tags] if current_tags else [])
            new_tag_names = set(new_tags)
            
            return current_tag_names != new_tag_names
        except:
            return True  # 如果比较出错，认为有更改
    
    def has_unsaved_changes(self) -> bool:
        """检查是否有未保存的更改"""
        if not self.selected_task:
            return False
            
        # 检查必要的组件是否存在
        if not all([
            self.title_input, self.description_input, self.due_date_input,
            self.estimated_pomodoros_input
        ]):
            return False
        
        # 检查可选组件
        if not self.priority_select or not self.repeat_select:
            return False
        
        try:
            # 获取当前表单数据
            title = self.title_input.value.strip() if self.title_input.value else ''
            
            # 处理描述字段
            description = self.description_input.value.strip() if self.description_input.value else ''
            original_description = self.selected_task.get('description', '') or ''
            
            # 处理截止日期
            due_date_str = self.due_date_input.value.strip() if self.due_date_input.value else ''
            due_date = None
            if due_date_str:
                try:
                    due_date = date.fromisoformat(due_date_str)
                except ValueError:
                    # 日期格式错误，认为有更改
                    return True
            
            # 处理原始截止日期
            original_due_date = self.selected_task.get('due_date')
            if isinstance(original_due_date, str):
                try:
                    original_due_date = date.fromisoformat(original_due_date.split()[0])
                except:
                    original_due_date = None
            
            # 获取优先级和重复周期
            priority = self.priority_select.value if self.priority_select.value else 'medium'
            repeat_cycle = self.repeat_select.value if self.repeat_select.value else 'none'
            
            # 获取番茄钟数量
            try:
                estimated_pomodoros = int(self.estimated_pomodoros_input.value)
            except:
                estimated_pomodoros = 1
            
            # 标签现在由chip组件管理，直接从selected_task获取
            current_tags = self.selected_task.get('tags', [])
            tags = [tag['name'] for tag in current_tags]
            
            # 比较各个字段是否有更改
            title_changed = title != (self.selected_task.get('title', '') or '')
            description_changed = description != original_description
            due_date_changed = due_date != original_due_date
            priority_changed = priority != self.selected_task.get('priority', 'medium')
            repeat_changed = repeat_cycle != self.selected_task.get('repeat_cycle', 'none')
            pomodoros_changed = estimated_pomodoros != self.selected_task.get('estimated_pomodoros', 1)
            tags_changed = self._tags_changed(tags)
            
            # 调试输出（可以在开发时启用）
            # print(f"Debug - Title: '{title}' vs '{self.selected_task.get('title', '')}' = {title_changed}")
            # print(f"Debug - Description: '{description}' vs '{original_description}' = {description_changed}")
            # print(f"Debug - Due date: {due_date} vs {original_due_date} = {due_date_changed}")
            # print(f"Debug - Priority: '{priority}' vs '{self.selected_task.get('priority', 'medium')}' = {priority_changed}")
            # print(f"Debug - Repeat: '{repeat_cycle}' vs '{self.selected_task.get('repeat_cycle', 'none')}' = {repeat_changed}")
            # print(f"Debug - Pomodoros: {estimated_pomodoros} vs {self.selected_task.get('estimated_pomodoros', 1)} = {pomodoros_changed}")
            # print(f"Debug - Tags: {tags_changed}")
            
            return (
                title_changed or
                description_changed or
                due_date_changed or
                priority_changed or
                repeat_changed or
                pomodoros_changed or
                tags_changed
            )
            
        except Exception as e:
            # 如果检查过程中出现错误，为了安全起见认为没有更改
            print(f"Error in has_unsaved_changes: {e}")
            return False

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
                ).classes('flex-shrink-0 w-32').props('dense borderless')
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
                ui.notify(f'已添加标签: {tag_name}', type='positive')
        else:
            ui.notify('添加标签失败', type='negative')

    def close_with_unsaved_check(self):
        """关闭前检查是否有未保存的更改"""
        if self.has_unsaved_changes():
            def save_and_close():
                if self.save_task_changes():
                    self.close_task_detail()
                dialog.close()
            
            def close_without_save():
                self.close_task_detail()
                dialog.close()
            
            def cancel_close():
                dialog.close()
            
            with ui.dialog() as dialog:
                with ui.card().classes('w-96'):
                    with ui.column().classes('w-full gap-4'):
                        ui.label('有未保存的更改').classes('text-h6 font-bold text-orange-600')
                        ui.label('您有未保存的更改。您想要保存这些更改吗？')
                        
                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            ui.button('取消', on_click=cancel_close).props('flat')
                            ui.button('不保存', on_click=close_without_save).props('flat color=negative')
                            ui.button('保存并关闭', on_click=save_and_close).props('color=primary')
            
            dialog.open()
        else:
            self.close_task_detail()

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