"""
标签编辑对话框组件
"""

from nicegui import ui
from typing import Dict, Callable, Optional


class TagEditDialog:
    """标签编辑对话框组件"""
    
    def __init__(self, tag_manager, on_success: Callable = None, user_id: int = None):
        self.tag_manager = tag_manager
        self.on_success = on_success  # 成功回调函数
        self.user_id = user_id  # 用户ID
        
        # 预设颜色选项
        self.colors = [
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
    
    def show_create_dialog(self):
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
                    user_id=self.user_id,
                    name=dialog_result['tag_name'].strip(),
                    color=dialog_result['tag_color']
                )
                
                if new_tag:
                    ui.notify(f'标签 "{dialog_result["tag_name"]}" 创建成功！', type='positive')
                    dialog.close()
                    if self.on_success:
                        self.on_success()
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
                
                # 颜色选择区域
                self._create_color_picker(dialog_result['tag_color'], on_color_change)
                
                # 操作按钮
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('取消', on_click=dialog.close).props('flat')
                    ui.button('创建', on_click=create_tag).props('color=primary')
    
    def show_edit_dialog(self, user_tag: Dict, user_id: int = None):
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
                    ui.notify(f'标签 "{dialog_result["tag_name"]}" 更新成功！', type='positive')
                    dialog.close()
                    if self.on_success:
                        self.on_success()
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
                
                # 颜色选择区域
                self._create_color_picker(dialog_result['tag_color'], on_color_change)
                
                # 操作按钮
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('取消', on_click=dialog.close).props('flat')
                    ui.button('保存', on_click=update_tag).props('color=primary')
    
    def _create_color_picker(self, selected_color: str, on_color_change: Callable):
        """创建颜色选择器"""
        # 颜色选择
        with ui.row().classes('w-full items-center gap-3'):
            ui.label('颜色:').classes('text-sm')
            
            with ui.row().classes('gap-2') as color_container:
                self.color_container = color_container
                self.selected_color = selected_color
                self.color_change_callback = on_color_change
                
                for color in self.colors:
                    self._create_color_button(color)
    
    def _create_color_button(self, color: str):
        """创建单个颜色按钮"""
        # 判断是否为选中状态
        is_selected = color == self.selected_color
        
        # 设置按钮样式 - 选中时有边框和阴影
        button_style = f'background-color: {color}; min-width: 28px; height: 28px;'
        if is_selected:
            button_style += ' border: 3px solid #1976d2; box-shadow: 0 0 8px rgba(25, 118, 210, 0.5);'
        else:
            button_style += ' border: 2px solid #e0e0e0;'
        
        button_props = 'flat round size=sm'
        if is_selected:
            button_props += ' unelevated'
        
        color_button = ui.button().props(button_props).style(button_style)
        color_button.on('click', lambda c=color: self._handle_color_click(c))
        
        return color_button
    
    def _handle_color_click(self, color: str):
        """处理颜色点击事件"""
        # 更新选中颜色
        self.selected_color = color
        
        # 调用外部回调函数
        if hasattr(self, 'color_change_callback'):
            self.color_change_callback(color)
        
        # 重新创建颜色选择器以更新视觉状态
        self._update_color_selection()
    
    def _update_color_selection(self):
        """更新颜色选择的视觉反馈"""
        # 重新创建颜色选择器以更新视觉状态
        if hasattr(self, 'color_container'):
            # 清空容器并重新创建按钮
            self.color_container.clear()
            
            with self.color_container:
                for color in self.colors:
                    self._create_color_button(color) 