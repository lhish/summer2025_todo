"""
AI功能面板组件 - 纯API版本
"""

from nicegui import ui
from typing import Dict, List, Callable, Optional
import asyncio


class AIPanelComponent:
    def __init__(self, ai_assistant, task_manager, statistics_manager, current_user: Dict):
        self.ai_assistant = ai_assistant
        self.task_manager = task_manager
        self.statistics_manager = statistics_manager
        self.current_user = current_user
        self.current_mode = 'general'  # 当前AI模式
        self.chat_history = []  # 聊天历史
        
    def set_ai_mode(self, mode: str, dialog):
        """设置AI模式"""
        self.current_mode = mode
        mode_names = {
            'task_recommendation': '智能任务推荐',
            'workload_estimation': '工作量预估',
            'efficiency_report': '效能分析',
            'work_pattern': '工作模式分析',
            'general': '通用助手'
        }
        
        if hasattr(dialog, 'mode_label'):
            dialog.mode_label.text = f'当前模式: {mode_names.get(mode, mode)}'
        
        # 添加模式切换消息到聊天记录
        self.add_message_to_chat(dialog, f"🤖 已切换到{mode_names.get(mode, mode)}模式", 'ai')
        
        # 根据模式添加相应的系统提示
        system_prompts = {
            'task_recommendation': '我是一个智能任务推荐助手。我可以分析您的待完成任务，根据优先级、截止日期、工作量等因素为您推荐最适合当前处理的任务。请告诉我您想要什么样的任务推荐。',
            'workload_estimation': '我是一个工作量预估专家。我可以根据任务描述预估完成该任务所需的番茄钟数量。请描述您要完成的任务，我会为您预估时间。',
            'efficiency_report': '我是一个效能分析专家。我可以分析您的工作效能数据，提供个性化的效能报告和改进建议。请告诉我您想了解哪个方面的效能分析。',
            'work_pattern': '我是一个工作模式分析专家。我可以分析您的工作习惯和效率模式，帮助您了解自己的最佳工作时间段和工作特点。请告诉我您想了解哪个方面的工作模式。',
            'general': '我是一个AI助手，可以帮助您进行任务管理、时间规划、效能分析等工作。请告诉我您需要什么帮助。'
        }
        
        if mode in system_prompts:
            self.add_message_to_chat(dialog, system_prompts[mode], 'ai')
    
    def add_message_to_chat(self, dialog, message: str, sender: str):
        """添加消息到聊天记录"""
        if hasattr(dialog, 'chat_area'):
            # 添加新消息到历史记录
            self.chat_history.append({'message': message, 'sender': sender})
            
            # 清空聊天区域并重新显示所有消息
            dialog.chat_area.clear()
            
            # 重新显示所有消息
            with dialog.chat_area:
                for msg in self.chat_history:
                    if msg['sender'] == 'user':
                        with ui.row().classes('w-full justify-end mb-2'):
                            ui.label(msg['message']).classes('bg-blue-100 p-2 rounded-lg text-sm max-w-3/4')
                    else:
                        with ui.row().classes('w-full justify-start mb-2'):
                            ui.label(msg['message']).classes('bg-grey-100 p-2 rounded-lg text-sm max-w-3/4')
    
    def send_message(self, dialog):
        """发送消息给AI"""
        if not hasattr(dialog, 'message_input'):
            return
        
        message = dialog.message_input.value.strip()
        if not message:
            return
        
        # 清空输入框
        dialog.message_input.value = ''
        
        # 添加用户消息到聊天记录
        self.add_message_to_chat(dialog, message, 'user')
        
        # 根据当前模式处理消息
        self.process_message_with_mode(dialog, message)
    
    def process_message_with_mode(self, dialog, message: str):
        """根据当前模式处理消息"""
        try:
            if self.current_mode == 'task_recommendation':
                self.handle_task_recommendation(dialog, message)
            elif self.current_mode == 'workload_estimation':
                self.handle_workload_estimation(dialog, message)
            elif self.current_mode == 'efficiency_report':
                self.handle_efficiency_report(dialog, message)
            elif self.current_mode == 'work_pattern':
                self.handle_work_pattern(dialog, message)
            else:
                self.handle_general_chat(dialog, message)
        except Exception as e:
            self.add_message_to_chat(dialog, f'处理消息时出错: {str(e)}', 'ai')
    
    def get_user_data(self) -> Dict:
        """获取用户数据"""
        try:
            from datetime import datetime, timedelta
            
            user_id = self.current_user['user_id']
            current_time = datetime.now()
            
            # 获取最近7天的数据
            end_date = current_time
            start_date = end_date - timedelta(days=7)
            
            # 获取所有任务数据
            all_tasks = self.task_manager.get_tasks(
                user_id=user_id,
                sort_by='created_at',
                sort_order='DESC'
            )
            
            # 获取效能数据
            productivity_data = self.statistics_manager.get_productivity_overview(
                user_id, 
                days=7
            )
            
            # 获取专注时长数据
            focus_data = self.statistics_manager.get_focus_duration_by_period(
                user_id,
                'daily',
                start_date,
                end_date
            )
            
            # 获取任务完成数据
            completed_tasks = self.statistics_manager.get_tasks_completed_by_period(
                user_id,
                'daily',
                start_date,
                end_date
            )
            
            return {
                'current_time': current_time.strftime('%Y-%m-%d %H:%M'),
                'all_tasks': all_tasks,
                'productivity_data': productivity_data,
                'focus_data': focus_data,
                'completed_tasks': completed_tasks
            }
            
        except Exception as e:
            return {
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'all_tasks': [],
                'productivity_data': {},
                'focus_data': [],
                'completed_tasks': []
            }
    
    def handle_task_recommendation(self, dialog, message: str):
        """处理任务推荐模式的消息"""
        try:
            # 获取用户数据
            user_data = self.get_user_data()
            
            # 构建AI角色和任务数据
            system_prompt = """你是一个智能任务推荐助手。根据用户的待完成任务、工作习惯和当前需求，推荐最适合的任务。

分析因素：
1. 任务优先级（high/medium/low）
2. 截止日期紧迫性
3. 预估工作量
4. 任务类型和标签
5. 用户当前时间和精力状态

请提供：
1. 推荐的任务列表（最多5个）
2. 每个任务的推荐理由
3. 建议的处理顺序
4. 时间安排建议

用中文回答，语调友好专业。"""
            
            # 构建包含任务数据的提示
            prompt = f"""用户数据：
当前时间：{user_data['current_time']}

待完成任务：
{self.format_tasks_for_ai(user_data['all_tasks'])}

用户需求：{message}

请根据以上数据推荐最适合的任务。"""
            
            # 调用AI
            response = self.ai_assistant.call_llm_api(prompt, system_prompt)
            
            if response:
                self.add_message_to_chat(dialog, response, 'ai')
            else:
                self.add_message_to_chat(dialog, "抱歉，无法生成任务推荐，请稍后再试。", 'ai')
            
        except Exception as e:
            self.add_message_to_chat(dialog, f'生成任务推荐时出错: {str(e)}', 'ai')
    
    def handle_workload_estimation(self, dialog, message: str):
        """处理工作量预估模式的消息"""
        try:
            # 获取用户数据
            user_data = self.get_user_data()
            
            # 构建AI角色和任务数据
            system_prompt = """你是一个工作量预估专家。根据任务描述和用户的历史工作数据，预估完成该任务所需的番茄钟数量。

预估原则：
- 简单任务（邮件、整理）：1-2个番茄钟
- 中等任务（文档、学习）：3-6个番茄钟
- 复杂任务（编程、研究）：6-12个番茄钟
- 考虑用户的工作效率和专注时长

请提供：
1. 预估的番茄钟数量
2. 预估理由
3. 时间安排建议
4. 可能的挑战和应对策略

用中文回答，语调专业。"""
            
            # 构建包含任务数据的提示
            prompt = f"""用户数据：
当前时间：{user_data['current_time']}

待完成任务：
{self.format_tasks_for_ai(user_data['all_tasks'])}

效能数据：
{user_data['productivity_data']}

专注时长数据：
{user_data['focus_data']}

需要预估的任务：{message}

请根据以上数据预估工作量。"""
            
            # 调用AI
            response = self.ai_assistant.call_llm_api(prompt, system_prompt)
            
            if response:
                self.add_message_to_chat(dialog, response, 'ai')
            else:
                self.add_message_to_chat(dialog, "抱歉，无法预估工作量，请稍后再试。", 'ai')
            
        except Exception as e:
            self.add_message_to_chat(dialog, f'预估工作量时出错: {str(e)}', 'ai')
    
    def handle_efficiency_report(self, dialog, message: str):
        """处理效能分析模式的消息"""
        try:
            # 获取用户数据
            user_data = self.get_user_data()
            
            # 构建AI角色和任务数据
            system_prompt = """你是一个效能分析专家。根据用户的工作数据，分析工作效率并提供改进建议。

分析维度：
1. 任务完成情况
2. 专注时长和效率
3. 时间管理能力
4. 工作模式特点
5. 改进空间

请提供：
1. 效能总结
2. 关键数据分析
3. 优势和不足
4. 具体改进建议
5. 目标设定

用中文回答，语调鼓励专业。"""
            
            # 构建包含任务数据的提示
            prompt = f"""用户数据：
当前时间：{user_data['current_time']}

待完成任务：
{self.format_tasks_for_ai(user_data['all_tasks'])}

效能数据：
{user_data['productivity_data']}

专注时长数据：
{user_data['focus_data']}

用户需求：{message}

请根据以上数据生成效能分析报告。"""
            
            # 调用AI
            response = self.ai_assistant.call_llm_api(prompt, system_prompt)
            
            if response:
                self.add_message_to_chat(dialog, response, 'ai')
            else:
                self.add_message_to_chat(dialog, "抱歉，无法生成效能报告，请稍后再试。", 'ai')
            
        except Exception as e:
            self.add_message_to_chat(dialog, f'生成效能报告时出错: {str(e)}', 'ai')
    
    def handle_work_pattern(self, dialog, message: str):
        """处理工作模式分析模式的消息"""
        try:
            # 获取用户数据
            user_data = self.get_user_data()
            
            # 构建AI角色和任务数据
            system_prompt = """你是一个工作模式分析专家。根据用户的工作数据，分析工作习惯和效率模式。

分析维度：
1. 最佳工作时间段
2. 专注持续时间特点
3. 任务类型偏好
4. 效率模式特征
5. 工作节奏稳定性

请提供：
1. 工作模式总结
2. 效率高峰期分析
3. 个性化建议
4. 时间管理优化
5. 习惯养成建议

用中文回答，语调专业。"""
            
            # 构建包含任务数据的提示
            prompt = f"""用户数据：
当前时间：{user_data['current_time']}

待完成任务：
{self.format_tasks_for_ai(user_data['all_tasks'])}

专注时长数据：
{user_data['focus_data']}

效能数据：
{user_data['productivity_data']}

用户需求：{message}

请根据以上数据分析工作模式。"""
            
            # 调用AI
            response = self.ai_assistant.call_llm_api(prompt, system_prompt)
            
            if response:
                self.add_message_to_chat(dialog, response, 'ai')
            else:
                self.add_message_to_chat(dialog, "抱歉，无法分析工作模式，请稍后再试。", 'ai')
            
        except Exception as e:
            self.add_message_to_chat(dialog, f'分析工作模式时出错: {str(e)}', 'ai')
    
    def handle_general_chat(self, dialog, message: str):
        """处理通用聊天模式的消息"""
        try:
            # 获取用户数据
            user_data = self.get_user_data()
            
            # 构建AI角色和任务数据
            system_prompt = """你是一个友好的AI助手，专门帮助用户进行任务管理、时间规划、效能分析等工作。

你可以帮助用户：
1. 任务管理和优先级排序
2. 时间规划和安排
3. 效能分析和改进
4. 工作习惯优化
5. 目标设定和跟踪

请用中文回答，语调友好专业，提供实用的建议。"""
            
            # 构建包含任务数据的提示
            prompt = f"""用户数据：
当前时间：{user_data['current_time']}

待完成任务：
{self.format_tasks_for_ai(user_data['all_tasks'])}

效能数据：
{user_data['productivity_data']}

专注时长数据：
{user_data['focus_data']}

用户消息：{message}

请根据以上数据提供帮助。"""
            
            # 调用AI
            response = self.ai_assistant.call_llm_api(prompt, system_prompt)
            
            if response:
                self.add_message_to_chat(dialog, response, 'ai')
            else:
                self.add_message_to_chat(dialog, "抱歉，无法处理您的请求，请稍后再试。", 'ai')
                
        except Exception as e:
            self.add_message_to_chat(dialog, f'处理消息时出错: {str(e)}', 'ai')
    
    def format_tasks_for_ai(self, tasks: List[Dict]) -> str:
        """格式化任务数据供AI使用"""
        if not tasks:
            return "暂无任务数据"
        
        formatted_tasks = []
        for task in tasks:
            # 处理标签信息
            tags = task.get('tags', [])
            tag_names = [tag.get('name', '') for tag in tags] if tags else []
            tag_info = ', '.join(tag_names) if tag_names else '无标签'
            
            task_info = f"""任务ID: {task['task_id']}
标题: {task['title']}
状态: {task['status']}
优先级: {task['priority']}
截止日期: {task['due_date'] if task['due_date'] else '无'}
预估番茄钟: {task['estimated_pomodoros']}
已用番茄钟: {task['used_pomodoros']}
标签: {tag_info}
创建时间: {task['created_at']}
更新时间: {task['updated_at']}"""
            
            formatted_tasks.append(task_info)
        
        return "\n\n".join(formatted_tasks)
    

