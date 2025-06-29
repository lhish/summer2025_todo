"""
通用辅助函数
"""
import re
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_duration(minutes: int) -> str:
    """格式化持续时间为可读字符串"""
    if minutes < 60:
        return f"{minutes}分钟"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}小时"
    else:
        return f"{hours}小时{remaining_minutes}分钟"


def format_relative_time(dt: datetime) -> str:
    """格式化相对时间"""
    now = datetime.now()
    delta = now - dt
    
    if delta.days > 0:
        return f"{delta.days}天前"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours}小时前"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"


def get_week_dates(target_date: Optional[date] = None) -> List[date]:
    """获取指定日期所在周的所有日期"""
    if target_date is None:
        target_date = date.today()
    
    # 找到周一
    monday = target_date - timedelta(days=target_date.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def calculate_completion_rate(completed: int, total: int) -> float:
    """计算完成率"""
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 1)


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    # 移除或替换不安全字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # 移除前后空格和点
    filename = filename.strip('. ')
    
    # 限制长度
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def parse_priority(priority_str: str) -> str:
    """解析优先级字符串"""
    priority_map = {
        'high': 'high',
        'medium': 'medium', 
        'low': 'low',
        '高': 'high',
        '中': 'medium',
        '低': 'low',
        '1': 'high',
        '2': 'medium',
        '3': 'low'
    }
    
    return priority_map.get(priority_str.lower(), 'medium')


def generate_color_from_string(text: str) -> str:
    """根据字符串生成一致的颜色"""
    # 简单的哈希函数生成颜色
    hash_value = hash(text) % 360
    return f"hsl({hash_value}, 70%, 60%)"


def is_today(dt: date) -> bool:
    """检查日期是否为今天"""
    return dt == date.today()


def is_this_week(dt: date) -> bool:
    """检查日期是否在本周"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start <= dt <= week_end


def format_task_due_date(due_date: Optional[date]) -> str:
    """格式化任务截止日期"""
    if due_date is None:
        return ""
    
    today = date.today()
    
    if due_date == today:
        return "今天"
    elif due_date == today + timedelta(days=1):
        return "明天"
    elif due_date == today - timedelta(days=1):
        return "昨天"
    elif is_this_week(due_date):
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        return weekdays[due_date.weekday()]
    else:
        return due_date.strftime('%Y-%m-%d')


def extract_hashtags(text: str) -> List[str]:
    """从文本中提取标签"""
    pattern = r'#(\w+)'
    return re.findall(pattern, text)


def remove_hashtags(text: str) -> str:
    """从文本中移除标签"""
    pattern = r'#\w+\s?'
    return re.sub(pattern, '', text).strip()


def time_until_due(due_date: date) -> Dict[str, Any]:
    """计算距离截止日期的时间"""
    today = date.today()
    delta = due_date - today
    
    return {
        'days': delta.days,
        'is_overdue': delta.days < 0,
        'is_due_today': delta.days == 0,
        'is_due_soon': 0 < delta.days <= 3
    } 