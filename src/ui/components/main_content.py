"""
主内容区域组件
"""

from nicegui import ui
from typing import Dict, List, Callable, Optional


class MainContentComponent:
    def __init__(self, current_user: Dict, user_tags: List[Dict], 
                 statistics_component=None, ai_assistant=None, 
                 task_manager=None, statistics_manager=None):
        self.current_user = current_user
        self.user_tags = user_tags
        self.current_view = 'my_day'
        self.statistics_component = statistics_component
        self.ai_assistant = ai_assistant
        self.task_manager = task_manager
        self.statistics_manager = statistics_manager

    def create_main_content(self, container, current_view: str, task_list_component):
        """创建主内容区域"""
        self.current_view = current_view
        
        container.clear()
        
        with container:
            # 特殊处理统计视图
            if current_view == 'statistics':
                self.create_statistics_view(container)
            else:
                # 原有的任务视图逻辑
                with ui.column().classes('w-full p-6'):
                    # 页面标题
                    title = '任务'  # 默认标题
                    
                    if current_view.startswith('tag_'):
                        # 标签视图：显示标签名称
                        tag_id = int(current_view.split('_')[1])
                        for user_tag in self.user_tags:
                            if user_tag['tag_id'] == tag_id:
                                title = user_tag['name']
                                break
                    else:
                        # 默认视图
                        view_titles = {
                            'my_day': '今天截止',
                            'planned': '即将截止',
                            'important': '重要',
                            'all': '所有任务'
                        }
                        title = view_titles.get(current_view, '任务')
                    
                    ui.label(title).classes('text-h4 font-bold mb-4')
                    
                    # 统计栏
                    stats_container = ui.column().classes('w-full')
                    task_list_component.create_stats_bar(stats_container)
                    
                    # 添加任务输入框
                    task_input_container = ui.column().classes('w-full')
                    task_list_component.create_add_task_input(task_input_container)
                    
                    # 任务列表
                    task_list_container = ui.column().classes('w-full')
                    task_list_component.create_task_list(task_list_container)
                    
                    # 已完成任务（可展开）
                    completed_tasks_container = ui.column().classes('w-full')
                    task_list_component.create_completed_tasks_section(completed_tasks_container)

    def create_statistics_view(self, container):
        """创建统计视图（左侧统计面板，右侧AI面板）"""
        from .ai_panel import AIPanelComponent
        
        with ui.column().classes('w-full h-full p-6'):
            # 页面标题
            ui.label('统计分析').classes('text-h4 font-bold mb-4')
            
            # 主容器：横向布局
            with ui.row().classes('w-full h-full gap-4'):
                # 左侧：统计面板
                with ui.card().classes('flex-1 p-4'):
                    ui.label('统计分析').classes('text-h6 mb-4')
                    if self.statistics_component and self.current_user:
                        self.statistics_component.create_stats_overview(self.current_user['user_id'])
                    else:
                        ui.label('统计组件未初始化')
                
                # 右侧：AI面板
                with ui.card().classes('flex-1 p-4'):
                    ui.label('效能分析').classes('text-h6 mb-4')
                    if self.ai_assistant and self.task_manager and self.statistics_manager and self.current_user:
                        ai_panel = AIPanelComponent(
                            self.ai_assistant, 
                            self.task_manager, 
                            self.statistics_manager, 
                            self.current_user
                        )
                        # 创建AI聊天界面
                        self.create_ai_chat_interface(ai_panel)
                    else:
                        ui.label('AI助手未初始化')
    
    def create_ai_chat_interface(self, ai_panel):
        """创建AI功能界面"""
        # 模式选择器
        # 效能分析按钮
        with ui.column().classes('w-full gap-4'):
            self.execute_button = ui.button(
                '分析',
                on_click=lambda: self.execute_ai_analysis(ai_panel, 'efficiency_report')
            ).classes('bg-primary')
            
            # 结果显示区域
            self.ai_result_container = ui.column().classes('w-full mt-4 p-4 bg-grey-1 rounded')
            # 初始状态为空，等待分析结果

    async def execute_ai_analysis(self, ai_panel, mode: str):
        """执行AI分析"""
        # 禁用按钮防止重复点击
        if hasattr(self, 'execute_button'):
            self.execute_button.props('loading')
        
        # 清空结果容器
        self.ai_result_container.clear()
        
        with self.ai_result_container:
            # 显示加载状态
            with ui.row().classes('items-center gap-2'):
                ui.spinner('dots', size='lg', color='primary')
                ui.label('正在分析，请稍候...').classes('text-blue-6')
            
            # 根据模式执行相应的分析
            try:
                # 只执行效能分析
                await self.show_efficiency_report(ai_panel)
            except Exception as e:
                self.ai_result_container.clear()
                with self.ai_result_container:
                    with ui.card().classes('w-full p-4 bg-red-50'):
                        ui.label(f'分析出错: {str(e)}').classes('text-red-6')
            finally:
                # 恢复按钮状态
                if hasattr(self, 'execute_button'):
                    self.execute_button.props(remove='loading')
    
    async def show_task_recommendations(self, ai_panel):
        """显示任务推荐结果"""
        # 获取用户数据
        user_data = ai_panel.get_user_data()
        
        # 构建提示
        system_prompt = """你是一个智能任务推荐助手。根据用户的待完成任务、工作习惯和当前需求，推荐最适合的任务。

分析因素：
1. 任务优先级（high/medium/low）
2. 截止日期紧迫性
3. 预估工作量
4. 任务类型和标签

请提供：
1. 推荐的任务列表（最多5个）
2. 每个任务的推荐理由
3. 建议的处理顺序

用中文回答，语调友好专业。"""
        
        prompt = f"""用户数据：
当前时间：{user_data['current_time']}

待完成任务：
{ai_panel.format_tasks_for_ai(user_data['all_tasks'])}

请根据以上数据推荐最适合现在处理的任务。"""
        
        # 调用AI
        response = await ai_panel.ai_assistant.call_llm_api(prompt, system_prompt)
        
        # 清空加载状态并显示结果
        self.ai_result_container.clear()
        with self.ai_result_container:
            with ui.card().classes('w-full p-4'):
                ui.label('任务推荐结果').classes('text-h6 mb-2 text-primary')
                ui.separator()
                ui.markdown(response).classes('w-full mt-2')
    
    async def show_workload_estimation(self, ai_panel):
        """显示工作量预估结果"""
        # 获取用户数据
        user_data = ai_panel.get_user_data()
        
        # 构建提示
        system_prompt = """你是一个工作量预估专家。根据用户的待完成任务分析工作量。
            
预估原则：
- 简单任务（邮件、整理）：1-2个番茄钟
- 中等任务（文档、学习）：3-6个番茄钟
- 复杂任务（编程、研究）：6-12个番茄钟
            
请提供：
1. 各任务的预估番茄钟数量
2. 总工作量统计
3. 时间安排建议
            
用中文回答，语调专业。"""
        
        prompt = f"""用户数据：
当前时间：{user_data['current_time']}
            
待完成任务：
{ai_panel.format_tasks_for_ai(user_data['all_tasks'])}
            
请分析所有待完成任务的工作量。"""
        
        # 调用AI
        response = await ai_panel.ai_assistant.call_llm_api(prompt, system_prompt)
        
        # 清空加载状态并显示结果
        self.ai_result_container.clear()
        with self.ai_result_container:
            with ui.card().classes('w-full p-4'):
                ui.label('工作量预估结果').classes('text-h6 mb-2 text-primary')
                ui.separator()
                ui.markdown(response).classes('w-full mt-2')
    
    async def show_efficiency_report(self, ai_panel):
        """显示效能分析结果"""
        # 获取用户数据
        user_data = ai_panel.get_user_data()
        
        # 构建提示
        system_prompt = """你是一个效能分析专家。根据用户的工作数据，分析工作效率并提供改进建议。

分析维度：
1. 任务完成情况
2. 专注时长和效率
3. 时间管理能力
4. 改进空间

请提供：
1. 效能总结
2. 关键数据分析
3. 优势和不足
4. 具体改进建议

用中文回答，语调鼓励专业。"""
        
        prompt = f"""用户数据：
当前时间：{user_data['current_time']}

效能数据：
{user_data['productivity_data']}

专注时长数据：
{user_data['focus_data']}

请生成效能分析报告。不要使用md。"""
        
        # 调用AI
        response = await ai_panel.ai_assistant.call_llm_api(prompt, system_prompt)
        
        # 清空加载状态并显示结果
        self.ai_result_container.clear()
        with self.ai_result_container:
            with ui.card().classes('w-full p-4'):
                ui.label('效能分析报告').classes('text-h6 mb-2 text-primary')
                ui.separator()
                ui.markdown(response).classes('w-full mt-2')

    def update_user_tags(self, user_tags: List[Dict]):
        """更新用户标签"""
        self.user_tags = user_tags 