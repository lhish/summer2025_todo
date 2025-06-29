from openai import OpenAI
from config import AI_CONFIG
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self):
        """初始化AI助手，使用OpenAI格式调用Gemini2.5-Flash"""
        self.client = OpenAI(
            api_key=AI_CONFIG['api_key'],
            base_url=AI_CONFIG['base_url']
        )
        self.model = AI_CONFIG['model']
        self.max_tokens = AI_CONFIG['max_tokens']
        self.temperature = AI_CONFIG['temperature']
    
    def call_llm_api(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """封装与第三方大型语言模型API的底层通信"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            return None
            
        except Exception as e:
            logger.error(f"调用AI API时发生错误: {e}")
            return None
    
    def recommend_next_task_ai(self, user_id: int, tasks_data: List[Dict]) -> List[Dict]:
        """调用AI模型，根据用户任务情况推荐下一步应处理的任务"""
        if not tasks_data:
            return []
        
        # 构建任务信息的简要描述
        task_info = []
        for task in tasks_data:
            if task['status'] == 'pending':  # 只考虑待完成任务
                info = {
                    'id': task['task_id'],
                    'title': task['title'],
                    'priority': task['priority'],
                    'due_date': str(task['due_date']) if task['due_date'] else '无截止日期',
                    'estimated_pomodoros': task['estimated_pomodoros'],
                    'used_pomodoros': task['used_pomodoros'],
                    'tag': task['tag']
                }
                task_info.append(info)
        
        if not task_info:
            return []
        
        system_prompt = """你是一个专业的任务管理助手，专门帮助用户优化工作效率。
你需要根据任务的优先级、截止日期、预估工作量等因素，为用户推荐最适合当前处理的任务。
考虑因素包括：
1. 紧急程度（截止日期）
2. 重要程度（优先级）
3. 工作量（预估番茄钟数）
4. 任务类型（标签）
请按照推荐顺序返回任务ID列表，最多推荐5个任务。"""
        
        prompt = f"""
当前用户有以下待完成任务：
{json.dumps(task_info, ensure_ascii=False, indent=2)}

请根据任务的优先级、截止日期、工作量等因素，为用户推荐接下来最应该处理的任务。
请按照推荐优先级从高到低排序，并简要说明推荐理由。

请以JSON格式返回推荐结果：
{{
    "recommendations": [
        {{
            "task_id": 任务ID,
            "reason": "推荐理由",
            "priority_score": 1-10的优先级评分
        }}
    ]
}}
"""
        
        response = self.call_llm_api(prompt, system_prompt)
        if not response:
            return []
        
        try:
            # 解析AI响应
            result = json.loads(response)
            recommendations = result.get('recommendations', [])
            
            # 返回推荐的任务信息
            recommended_tasks = []
            for rec in recommendations[:5]:  # 最多5个推荐
                task_id = rec.get('task_id')
                for task in tasks_data:
                    if task['task_id'] == task_id:
                        task_copy = task.copy()
                        task_copy['ai_reason'] = rec.get('reason', '')
                        task_copy['ai_priority_score'] = rec.get('priority_score', 5)
                        recommended_tasks.append(task_copy)
                        break
            
            return recommended_tasks
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"解析AI推荐结果时发生错误: {e}")
            return []
    
    def estimate_pomodoros_ai(self, task_description: str, task_title: str = "") -> int:
        """调用AI模型，根据任务描述预估完成该任务所需的番茄钟数量"""
        system_prompt = """你是一个任务时间预估专家，专门帮助用户预估完成任务所需的番茄钟数量。
一个番茄钟通常为25分钟的专注工作时间。
请根据任务的复杂度、工作量、类型等因素，给出合理的预估。
一般原则：
- 简单任务（如发邮件、简单整理）：1-2个番茄钟
- 中等任务（如写文档、学习新知识）：3-6个番茄钟  
- 复杂任务（如编程项目、深度研究）：6-12个番茄钟
- 大型项目：建议分解为更小的子任务"""
        
        prompt = f"""
任务标题：{task_title}
任务描述：{task_description}

请预估完成这个任务需要多少个番茄钟（每个番茄钟25分钟）。
请只返回数字，如果任务描述不清楚，返回3作为默认值。
考虑因素：
1. 任务的复杂程度
2. 需要的专注时间
3. 可能的中断和思考时间

预估番茄钟数量：
"""
        
        response = self.call_llm_api(prompt, system_prompt)
        if not response:
            return 3  # 默认值
        
        try:
            # 尝试从响应中提取数字
            import re
            numbers = re.findall(r'\d+', response)
            if numbers:
                estimated = int(numbers[0])
                # 限制在合理范围内
                return max(1, min(20, estimated))
            return 3
        except:
            return 3
    
    def generate_efficiency_report_ai(self, user_id: int, period_data: Dict[str, Any]) -> str:
        """调用AI模型，基于用户的效能数据生成个性化的总结报告和改进建议"""
        system_prompt = """你是一个专业的效率分析师，专门帮助用户分析工作效率并提供改进建议。
请基于用户的任务完成情况、专注时间等数据，生成一份简洁而有洞察力的效能报告。
报告应该包括：
1. 效能总结（表现亮点）
2. 数据分析（关键指标解读）
3. 潜在问题识别
4. 具体改进建议
请用友好、鼓励的语调，提供实用的建议。"""
        
        prompt = f"""
用户效能数据：
{json.dumps(period_data, ensure_ascii=False, indent=2)}

请基于以上数据生成一份个性化的效能分析报告，包括：
1. 本期表现总结
2. 关键数据分析
3. 优势和需要改进的地方
4. 具体的优化建议

请用中文回答，语调友好专业，给出实用的建议。
"""
        
        response = self.call_llm_api(prompt, system_prompt)
        return response if response else "抱歉，无法生成效能报告，请稍后再试。"
    
    def suggest_task_breakdown_ai(self, task_title: str, task_description: str) -> List[str]:
        """AI辅助任务分解"""
        system_prompt = """你是一个任务分解专家，帮助用户将复杂任务分解为更小、更具体的子任务。
每个子任务应该：
1. 具体明确，可操作
2. 能在1-3个番茄钟内完成
3. 有清晰的完成标准"""
        
        prompt = f"""
任务标题：{task_title}
任务描述：{task_description}

请将这个任务分解为3-8个具体的子任务，每个子任务应该是具体可执行的行动。
请以JSON数组格式返回：
["子任务1", "子任务2", "子任务3", ...]
"""
        
        response = self.call_llm_api(prompt, system_prompt)
        if not response:
            return []
        
        try:
            subtasks = json.loads(response)
            if isinstance(subtasks, list):
                return subtasks[:8]  # 最多8个子任务
            return []
        except:
            return []
    
    def analyze_work_pattern_ai(self, focus_sessions: List[Dict], completed_tasks: List[Dict]) -> str:
        """AI分析用户工作模式"""
        system_prompt = """你是一个工作模式分析专家，专门分析用户的工作习惯和效率模式。
请基于用户的专注会话记录和任务完成情况，分析用户的工作模式特点。"""
        
        # 简化数据用于分析
        session_summary = []
        for session in focus_sessions[-50:]:  # 最近50次会话
            if session['session_type'] == 'work' and session['is_completed']:
                session_summary.append({
                    'date': str(session['start_time'].date()),
                    'hour': session['start_time'].hour,
                    'duration': session['duration_minutes'],
                    'task_title': session.get('task_title', '未知任务')
                })
        
        task_summary = []
        for task in completed_tasks[-20:]:  # 最近20个完成的任务
            task_summary.append({
                'title': task['title'],
                'priority': task['priority'],
                'used_pomodoros': task['used_pomodoros'],
                'estimated_pomodoros': task['estimated_pomodoros'],
                'tag': task['tag']
            })
        
        data = {
            'recent_sessions': session_summary,
            'completed_tasks': task_summary
        }
        
        prompt = f"""
用户工作数据：
{json.dumps(data, ensure_ascii=False, indent=2)}

请分析用户的工作模式，包括：
1. 最佳工作时间段
2. 专注持续时间特点
3. 任务类型偏好
4. 效率模式特征
5. 个性化建议

请用中文回答，提供有洞察力的分析。
"""
        
        response = self.call_llm_api(prompt, system_prompt)
        return response if response else "暂无足够数据进行工作模式分析。" 