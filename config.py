import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'pomodoro_task_manager'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'use_unicode': True
}

# AI API配置 - 按照文档要求使用Gemini2.5-Flash
AI_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY', ''),
    'base_url': os.getenv('OPENAI_BASE_URL', ''),
    'model': os.getenv('OPENAI_MODEL', ''),
    'max_tokens': 2000,  # 增加token限制，避免回复被截断
    'temperature': 0.7
}

# 应用配置
APP_CONFIG = {
    'secret_key': os.getenv('SECRET_KEY', 'your-secret-key-here'),
    'debug': os.getenv('DEBUG', 'True').lower() == 'true',
    'port': int(os.getenv('PORT', 8080)),
    'host': os.getenv('HOST', '0.0.0.0')
}

# 番茄工作法默认配置
DEFAULT_POMODORO_SETTINGS = {
    'work_duration': 25,
    'short_break_duration': 5,
    'long_break_duration': 15,
    'long_break_interval': 4,
    'notification_sound': 'default',
    'auto_start_next_pomodoro': False,
    'auto_start_break': False,
    'daily_focus_target_minutes': 120
} 