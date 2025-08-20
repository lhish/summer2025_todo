"""
AI助手服务 - 简化版本
提供与外部AI API的通信功能
"""

import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI, AsyncOpenAI
from config import AI_CONFIG

logger = logging.getLogger(__name__)


class AIAssistant:
    def __init__(self):
        """初始化AI助手，使用OpenAI格式调用外部API"""
        self.client = AsyncOpenAI(
            api_key=AI_CONFIG['api_key'],
            base_url=AI_CONFIG['base_url']
        )
        self.model = AI_CONFIG['model']
        self.max_tokens = AI_CONFIG['max_tokens']
        self.temperature = AI_CONFIG['temperature']
    
    async def call_llm_api(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """封装与第三方大型语言模型API的底层通信"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # 检查响应类型
            if hasattr(response, 'choices') and response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                content = choice.message.content
                finish_reason = choice.finish_reason
                
                # 检查是否因为token限制而被截断
                if finish_reason == 'length' and not content:
                    return None
                
                # 检查是否有内容过滤
                if finish_reason == 'content_filter':
                    return None
                
                # 检查是否有其他问题
                if not content and finish_reason != 'stop':
                    return None
                
                return content if content else None
            elif isinstance(response, str):
                # 如果响应直接是字符串，检查是否是HTML
                if response.strip().startswith('<!doctype html>') or response.strip().startswith('<html'):
                    return None
                return response
            else:
                return None
            
        except Exception as e:
            logger.error(f"调用AI API时发生错误: {e}")
            return None

    async def estimate_pomodoro_count(self, task_title: str, task_description: Optional[str], pomodoro_duration: int = 25) -> Optional[int]:
        """
        使用AI预估完成任务所需的番茄钟数量。
        :param task_title: 任务标题
        :param task_description: 任务描述
        :param pomodoro_duration: 每个番茄钟的时长（分钟），默认为25
        :return: 预估的番茄钟数量（整数）或 None
        """
        prompt = (
            f"请根据以下任务的标题和描述，预估完成该任务所需的番茄钟数量（每个番茄钟时长为 {pomodoro_duration} 分钟）。\n"
            f"任务标题: {task_title}\n"
            f"任务描述: {task_description if task_description else '无'}\n\n"
            f"请直接返回一个整数数字，不要包含任何其他文字或解释。"
        )
        system_prompt = f"你是一个任务工作量预估AI，专门根据任务描述预估番茄钟数量。每个番茄钟时长为 {pomodoro_duration} 分钟。请只返回数字。"

        response = await self.call_llm_api(prompt=prompt, system_prompt=system_prompt)

        if response and response.strip().isdigit():
            return int(response.strip())
        else:
            logger.warning(f"AI未能给出有效预估或返回非数字内容: {response}")
            return None