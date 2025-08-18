"""
AI助手服务 - 简化版本
提供与外部AI API的通信功能
"""

import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI
from config import AI_CONFIG

logger = logging.getLogger(__name__)


class AIAssistant:
    def __init__(self):
        """初始化AI助手，使用OpenAI格式调用外部API"""
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