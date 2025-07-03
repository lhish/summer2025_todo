#!/usr/bin/env python3
"""
个人任务与效能管理网页平台 - 主应用
基于用户UI设计要求的完整实现
"""

import logging
from nicegui import ui, app

# 导入自定义模块
from config import APP_CONFIG
from src.database.database import DatabaseManager, UserManager, TagManager
from src.services.task_manager import TaskManager
from src.services.pomodoro_manager import PomodoroManager, UserSettingsManager
from src.services.ai_assistant import AIAssistant
from src.services.statistics_manager import StatisticsManager

# 导入UI组件
from src.ui.pages.login_page import LoginPage
from src.ui.pages.register_page import RegisterPage
from src.ui.pages.main_page import MainPage
from src.ui.pages.settings_page import SettingsPage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化数据库和服务
db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
tag_manager = TagManager(db_manager)
task_manager = TaskManager(db_manager)
pomodoro_manager = PomodoroManager(db_manager)
settings_manager = UserSettingsManager(db_manager)
ai_assistant = AIAssistant()
statistics_manager = StatisticsManager(db_manager)

# 初始化页面组件
login_page = LoginPage(user_manager)
register_page = RegisterPage(user_manager)
main_page = MainPage(
    db_manager, user_manager, tag_manager, task_manager,
    pomodoro_manager, settings_manager, ai_assistant, statistics_manager
)
settings_page = SettingsPage(settings_manager)

def handle_login_success(user):
    """处理登录成功"""
    main_page.set_current_user(user)

# 设置登录成功回调
login_page.on_login_success = handle_login_success

@ui.page('/')
def index():
    """首页"""
    index_handler = main_page.create_index_page(lambda: None)
    index_handler()

@ui.page('/login')
def login():
    """登录页面"""
    login_handler = login_page.create_login_page_route()
    login_handler()

@ui.page('/register')
def register():
    """注册页面"""
    register_handler = register_page.create_register_page_route()
    register_handler()

if __name__ in {"__main__", "__mp_main__"}:
    # 运行应用
    ui.run(
        host=APP_CONFIG['host'],
        port=APP_CONFIG['port'],
        title='个人任务与效能管理平台',
        favicon='🍅',
        show=False,
        reload=APP_CONFIG['debug'],
        storage_secret=APP_CONFIG['secret_key']
    ) 