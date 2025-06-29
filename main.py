#!/usr/bin/env python3
"""
个人任务与效能管理网页平台 - 主应用
基于用户UI设计要求的完整实现
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

from nicegui import ui, app, events

# 导入自定义模块
from config import APP_CONFIG
from database import DatabaseManager, UserManager, ListManager, TagManager
from task_manager import TaskManager
from pomodoro_manager import PomodoroManager, UserSettingsManager
from ai_assistant import AIAssistant
from statistics_manager import StatisticsManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
current_user: Optional[Dict] = None
db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
list_manager = ListManager(db_manager)
tag_manager = TagManager(db_manager)
task_manager = TaskManager(db_manager)
pomodoro_manager = PomodoroManager(db_manager)
settings_manager = UserSettingsManager(db_manager)
ai_assistant = AIAssistant()
statistics_manager = StatisticsManager(db_manager)

# 应用状态
current_view = 'my_day'
current_tasks: List[Dict] = []
user_lists: List[Dict] = []
active_session: Optional[Dict] = None
timer_running = False
sidebar_collapsed = False
task_detail_open = False
selected_task: Optional[Dict] = None

# UI组件引用
sidebar_container = None
sidebar_lists_container = None
main_content_container = None
task_detail_container = None
timer_container = None
pomodoro_fullscreen = None

@ui.page('/')
def index():
    """首页"""
    global current_user
    
    # 检查是否有保存的登录状态
    if not current_user:
        saved_user_id = app.storage.user.get('user_id')
        if saved_user_id:
            # 从数据库重新获取用户信息
            user = user_manager.get_user_by_id(saved_user_id)
            if user:
                current_user = user
    
    if current_user:
        show_main_app()
    else:
        show_login_page()

@ui.page('/login')
def login_page():
    """登录页面"""
    show_login_page()

def show_login_page():
    """显示登录页面"""
    global current_user
    
    ui.page_title('登录 - 个人任务与效能管理平台')
    
    with ui.column().classes('w-full h-screen flex items-center justify-center bg-grey-1'):
        with ui.card().classes('w-96 p-8 shadow-lg'):
            ui.label('个人任务与效能管理平台').classes('text-h4 text-center mb-6 text-primary')
            
            email_input = ui.input('邮箱', placeholder='输入您的邮箱').classes('w-full mb-4')
            password_input = ui.input('密码', placeholder='输入您的密码', password=True).classes('w-full mb-4')
            
            def handle_login():
                global current_user
                
                email = email_input.value
                password = password_input.value
                
                if not email or not password:
                    ui.notify('请输入邮箱和密码', type='warning')
                    return
                
                user = user_manager.get_user_by_email(email)
                if user and user_manager.verify_password(password, user['password_hash']):
                    current_user = user
                    # 保存登录状态到本地存储
                    app.storage.user['user_id'] = user['user_id']
                    app.storage.user['email'] = user['email']
                    ui.notify('登录成功！', type='positive')
                    ui.navigate.to('/')
                else:
                    ui.notify('邮箱或密码错误', type='negative')
            
            def handle_register():
                email = email_input.value
                password = password_input.value
                
                if not email or not password:
                    ui.notify('请填写所有字段', type='warning')
                    return
                
                if len(password) < 6:
                    ui.notify('密码长度至少为6位', type='warning')
                    return
                
                user_id = user_manager.create_user(email, password)
                if user_id:
                    ui.notify('注册成功！请登录', type='positive')
                else:
                    ui.notify('注册失败，邮箱可能已存在', type='negative')
            
            with ui.row().classes('w-full gap-2'):
                ui.button('登录', on_click=handle_login).classes('flex-1').props('color=primary')
                ui.button('注册', on_click=handle_register).classes('flex-1').props('flat color=primary')

def show_main_app():
    """显示主应用界面"""
    global sidebar_container, main_content_container, task_detail_container, timer_container
    
    ui.page_title('个人任务与效能管理平台')
    
    # 加载用户数据
    load_user_data()
    
    # 主体布局
    with ui.row().classes('w-full h-screen no-wrap'):
        # 左侧边栏
        sidebar_container = ui.column().classes('sidebar-container')
        create_sidebar()
        
        # 中间主内容区域
        main_content_container = ui.column().classes('flex-1 h-full overflow-auto bg-grey-1')
        create_main_content()
        
        # 右侧任务详情栏（默认隐藏）
        task_detail_container = ui.column().classes('task-detail-container hidden')
        
        # 底部番茄钟（固定在主内容区域底部）
        timer_container = ui.row().classes('timer-mini-container')
        create_mini_timer()
    
    # 添加CSS样式
    ui.add_head_html("""
    <style>
        .sidebar-container {
            width: 280px;
            min-width: 280px;
            background: white;
            border-right: 1px solid #e0e0e0;
            transition: all 0.3s ease;
        }
        .sidebar-collapsed {
            width: 60px !important;
            min-width: 60px !important;
        }
        .task-detail-container {
            width: 360px;
            min-width: 360px;
            background: white;
            border-left: 1px solid #e0e0e0;
            transition: all 0.3s ease;
        }
        .task-detail-container.hidden {
            width: 0 !important;
            min-width: 0 !important;
            opacity: 0;
            overflow: hidden;
        }
        .timer-mini-container {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            border-radius: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            padding: 8px 16px;
            z-index: 1000;
        }
        .task-item {
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .task-item:hover {
            background: #f5f5f5;
        }
        .sidebar-item {
            transition: all 0.2s ease;
        }
        .sidebar-item:hover {
            background: #f0f8ff;
        }
        .sidebar-item.active {
            background: #e3f2fd;
            border-right: 3px solid #2196f3;
        }
    </style>
    """)

def load_user_data():
    """加载用户数据"""
    global user_lists, current_tasks
    
    if current_user:
        user_lists = list_manager.get_user_lists(current_user['user_id'])
        refresh_current_tasks()

def create_sidebar():
    """创建左侧边栏"""
    global sidebar_container
    
    with sidebar_container:
        # 顶部：折叠/展开按钮
        with ui.row().classes('w-full p-4 justify-center'):
            ui.button(icon='menu', on_click=toggle_sidebar).props('flat round')
        
        ui.separator()
        
        # 第一部分：默认视图
        with ui.column().classes('w-full p-2'):
            create_sidebar_item('我的一天', 'today', 'my_day')
            create_sidebar_item('计划内', 'event', 'planned')
            create_sidebar_item('重要', 'star', 'important')
            create_sidebar_item('任务', 'list', 'all')
        
        ui.separator()
        
        # 第二部分：清单
        global sidebar_lists_container
        sidebar_lists_container = ui.column().classes('w-full p-2')
        refresh_sidebar_lists()
        
        ui.separator()
        
        # 底部：用户信息
        with ui.column().classes('mt-auto p-4 bg-grey-1'):
            if not sidebar_collapsed:
                ui.label(current_user['email']).classes('text-sm font-medium')
                ui.label('已登录').classes('text-xs text-grey-6')
            
            with ui.row().classes('w-full justify-end'):
                ui.button(icon='settings', on_click=show_settings_dialog).props('flat round size=sm')
                ui.button(icon='logout', on_click=handle_logout).props('flat round size=sm')

def create_sidebar_item(label: str, icon: str, view_type: str):
    """创建侧边栏项目"""
    def select_view():
        global current_view
        current_view = view_type
        refresh_current_tasks()
        create_main_content()
        # 更新active状态
        update_sidebar_active_state()
    
    classes = 'sidebar-item w-full p-3 rounded cursor-pointer flex items-center gap-3'
    if current_view == view_type:
        classes += ' active'
    
    with ui.row().classes(classes).on('click', select_view):
        ui.icon(icon).classes('text-grey-7')
        if not sidebar_collapsed:
            ui.label(label).classes('text-sm')

def refresh_sidebar_lists():
    """刷新侧边栏清单列表"""
    global user_lists, sidebar_lists_container
    
    # 清空列表容器内容
    if sidebar_lists_container:
        sidebar_lists_container.clear()
    
    # 重新获取用户清单
    if current_user:
        user_lists = list_manager.get_user_lists(current_user['user_id'])
        
        # 为每个清单创建侧边栏项目
        with sidebar_lists_container:
            for user_list in user_lists:
                def select_list(list_data=user_list):
                    def inner_select():
                        global current_view
                        current_view = f'list_{list_data["list_id"]}'
                        refresh_current_tasks()
                        create_main_content()
                        update_sidebar_active_state()
                    return inner_select
                
                classes = 'sidebar-item w-full p-3 rounded cursor-pointer flex items-center gap-3'
                if current_view == f'list_{user_list["list_id"]}':
                    classes += ' active'
                
                with ui.row().classes(classes).on('click', select_list(user_list)):
                    ui.icon('folder', color=user_list.get('color', '#2196F3')).classes('text-grey-7')
                    if not sidebar_collapsed:
                        ui.label(user_list['name']).classes('text-sm')
                        if user_list.get('task_count', 0) > 0:
                            ui.badge(str(user_list['task_count'])).props('color=grey-5')

def toggle_sidebar():
    """切换侧边栏展开/折叠状态"""
    global sidebar_collapsed
    sidebar_collapsed = not sidebar_collapsed
    
    if sidebar_collapsed:
        sidebar_container.classes(add='sidebar-collapsed')
    else:
        sidebar_container.classes(remove='sidebar-collapsed')

def create_main_content():
    """创建主内容区域"""
    global main_content_container
    
    main_content_container.clear()
    
    with main_content_container:
        with ui.column().classes('w-full p-6'):
            # 页面标题
            view_titles = {
                'my_day': '我的一天',
                'planned': '计划内',
                'important': '重要',
                'all': '任务'
            }
            
            title = view_titles.get(current_view, '任务')
            
            # 如果是清单视图，显示清单名称
            if current_view.startswith('list_'):
                list_id = int(current_view.split('_')[1])
                for user_list in user_lists:
                    if user_list['list_id'] == list_id:
                        title = user_list['name']
                        break
            
            ui.label(title).classes('text-h4 font-bold mb-4')
            
            # 统计栏
            create_stats_bar()
            
            # 添加任务输入框
            create_add_task_input()
            
            # 任务列表
            create_task_list()
            
            # 已完成任务（可展开）
            create_completed_tasks_section()

def create_stats_bar():
    """创建统计栏"""
    stats = get_view_stats()
    
    with ui.row().classes('w-full gap-6 mb-6 p-4 bg-white rounded shadow-sm'):
        with ui.column().classes('text-center'):
            ui.label(f"{stats['estimated_time']}分钟").classes('text-h6 font-bold text-blue-6')
            ui.label('预计时间').classes('text-sm text-grey-6')
        
        with ui.column().classes('text-center'):
            ui.label(str(stats['pending_tasks'])).classes('text-h6 font-bold text-orange-6')
            ui.label('待完成任务').classes('text-sm text-grey-6')
        
        with ui.column().classes('text-center'):
            ui.label(f"{stats['focus_time']}分钟").classes('text-h6 font-bold text-green-6')
            ui.label('已专注时间').classes('text-sm text-grey-6')
        
        with ui.column().classes('text-center'):
            ui.label(str(stats['completed_tasks'])).classes('text-h6 font-bold text-purple-6')
            ui.label('已完成任务').classes('text-sm text-grey-6')

def create_add_task_input():
    """创建添加任务输入框"""
    def handle_button_add():
        if task_input.value.strip():
            create_quick_task(task_input.value.strip())
            task_input.value = ''
    
    def handle_enter_key():
        if task_input.value.strip():
            create_quick_task(task_input.value.strip())
            task_input.value = ''
    
    with ui.row().classes('w-full mb-6'):
        task_input = ui.input(placeholder='添加任务...').classes('flex-1')
        # 使用action方法处理回车键
        task_input.action = handle_enter_key
        ui.button(icon='add', on_click=handle_button_add).props('flat round color=primary')

def create_quick_task(title: str):
    """快速创建任务"""
    # 根据当前视图设置默认属性
    due_date = None
    priority = 'medium'
    list_id = None
    
    if current_view == 'my_day' or current_view == 'planned':
        due_date = date.today()
    elif current_view == 'important':
        priority = 'high'
    elif current_view.startswith('list_'):
        list_id = int(current_view.split('_')[1])
    
    task_id = task_manager.create_task(
        user_id=current_user['user_id'],
        title=title,
        due_date=due_date,
        priority=priority,
        list_id=list_id
    )
    
    if task_id:
        ui.notify('任务创建成功', type='positive')
        refresh_current_tasks()
        create_main_content()
    else:
        ui.notify('任务创建失败', type='negative')

def create_task_list():
    """创建任务列表"""
    pending_tasks = [task for task in current_tasks if task['status'] == 'pending']
    
    if not pending_tasks:
        ui.label('暂无待完成任务').classes('text-center text-grey-5 py-8')
        return
    
    with ui.column().classes('w-full gap-2 mb-6'):
        for task in pending_tasks:
            create_task_item(task)

def create_task_item(task: Dict):
    """创建任务项"""
    def toggle_complete():
        task_manager.toggle_task_status(task['task_id'], 'completed')
        refresh_current_tasks()
        create_main_content()
    
    def start_pomodoro():
        start_pomodoro_for_task(task['task_id'])
    
    def show_task_detail():
        global selected_task, task_detail_open
        selected_task = task
        task_detail_open = True
        create_task_detail_panel()
    
    with ui.row().classes('task-item w-full p-4 bg-white rounded shadow-sm items-center gap-3'):
        # 完成按钮
        ui.button(icon='radio_button_unchecked', on_click=toggle_complete).props('flat round size=sm')
        
        # 播放按钮
        ui.button(icon='play_arrow', on_click=start_pomodoro).props('flat round size=sm color=green')
        
        # 任务内容
        with ui.column().classes('flex-1 cursor-pointer').on('click', show_task_detail):
            ui.label(task['title']).classes('font-medium')
            
            # 任务详情
            details = []
            if task['due_date']:
                details.append(f"📅 {task['due_date']}")
            if task['priority'] == 'high':
                details.append('⭐ 重要')
            if task['list_name']:
                details.append(f"📂 {task['list_name']}")
            if task.get('tags'):
                tag_names = [tag['name'] for tag in task['tags']]
                details.append(f"🏷️ {', '.join(tag_names)}")
            
            if details:
                ui.label(' • '.join(details)).classes('text-sm text-grey-6')

def create_completed_tasks_section():
    """创建已完成任务区域"""
    completed_tasks = [task for task in current_tasks if task['status'] == 'completed']
    
    if not completed_tasks:
        return
    
    with ui.expansion(f'已完成 ({len(completed_tasks)})', icon='check_circle').classes('w-full'):
        with ui.column().classes('w-full gap-2'):
            for task in completed_tasks:
                create_completed_task_item(task)

def create_completed_task_item(task: Dict):
    """创建已完成任务项"""
    def toggle_uncomplete():
        task_manager.toggle_task_status(task['task_id'], 'pending')
        refresh_current_tasks()
        create_main_content()
    
    with ui.row().classes('w-full p-3 items-center gap-3 opacity-60'):
        ui.button(icon='check_circle', on_click=toggle_uncomplete).props('flat round size=sm color=green')
        ui.label(task['title']).classes('line-through text-grey-6')

def create_task_detail_panel():
    """创建任务详情面板"""
    global task_detail_container
    
    if not selected_task:
        return
    
    task_detail_container.classes(remove='hidden')
    task_detail_container.clear()
    
    with task_detail_container:
        with ui.column().classes('w-full h-full p-6'):
            # 标题栏
            with ui.row().classes('w-full items-center mb-4'):
                ui.button(icon='close', on_click=close_task_detail).props('flat round size=sm')
                ui.space()
            
            # 任务操作按钮
            with ui.row().classes('w-full gap-2 mb-6'):
                def toggle_task():
                    task_manager.toggle_task_status(selected_task['task_id'])
                    refresh_current_tasks()
                    close_task_detail()
                
                def start_task_pomodoro():
                    start_pomodoro_for_task(selected_task['task_id'])
                
                ui.button('完成', icon='check', on_click=toggle_task).props('color=green')
                ui.button('开始', icon='play_arrow', on_click=start_task_pomodoro).props('color=primary')
            
            # 任务标题
            task_title = ui.input('标题', value=selected_task['title']).classes('w-full mb-4')
            
            # 其他字段...
            ui.label('更多详情功能开发中...').classes('text-grey-6')

def close_task_detail():
    """关闭任务详情面板"""
    global task_detail_open, selected_task
    task_detail_open = False
    selected_task = None
    task_detail_container.classes(add='hidden')

def create_mini_timer():
    """创建迷你番茄钟"""
    global timer_container
    
    timer_container.clear()
    
    with timer_container:
        with ui.row().classes('items-center gap-3'):
            ui.label('25:00').classes('font-mono text-lg')
            ui.button(icon='play_arrow', on_click=show_fullscreen_timer).props('flat round size=sm')

def show_fullscreen_timer():
    """显示全屏番茄钟"""
    global pomodoro_fullscreen
    
    with ui.dialog().classes('fullscreen') as dialog:
        with ui.column().classes('w-full h-full items-center justify-center bg-primary text-white'):
            ui.button(icon='close', on_click=dialog.close).classes('absolute top-4 left-4').props('flat round text-white')
            
            if selected_task:
                ui.label(selected_task['title']).classes('text-h5 mb-8')
            
            ui.label('25:00').classes('text-8xl font-mono mb-8')
            
            with ui.row().classes('gap-4'):
                ui.button('开始', icon='play_arrow').props('size=lg color=white flat')
                ui.button('暂停', icon='pause').props('size=lg color=white flat')
                ui.button('重置', icon='refresh').props('size=lg color=white flat')
    
    dialog.open()

def start_pomodoro_for_task(task_id: int):
    """为特定任务开始番茄工作法"""
    global active_session, timer_running, selected_task
    
    if timer_running:
        ui.notify('已有活跃的番茄钟', type='warning')
        return
    
    # 获取任务信息
    task = task_manager.get_task_by_id(task_id)
    if task:
        selected_task = task
        show_fullscreen_timer()
        ui.notify(f'开始专注：{task["title"]}', type='positive')

def refresh_current_tasks():
    """刷新当前任务列表"""
    global current_tasks
    
    if current_user:
        if current_view.startswith('list_'):
            # 清单视图
            list_id = int(current_view.split('_')[1])
            current_tasks = task_manager.get_tasks(
                user_id=current_user['user_id'],
                list_id=list_id,
                sort_by='created_at',
                sort_order='DESC'
            )
        else:
            # 默认视图
            current_tasks = task_manager.get_tasks_by_view(current_user['user_id'], current_view)

def get_view_stats():
    """获取当前视图的统计数据"""
    if not current_user:
        return {'estimated_time': 0, 'pending_tasks': 0, 'focus_time': 0, 'completed_tasks': 0}
    
    pending_tasks = [task for task in current_tasks if task['status'] == 'pending']
    completed_tasks = [task for task in current_tasks if task['status'] == 'completed']
    
    # 计算预计时间
    estimated_time = sum((task['estimated_pomodoros'] - task['used_pomodoros']) * 25 for task in pending_tasks)
    
    # 今日专注时间
    focus_time = pomodoro_manager.get_today_focus_duration(current_user['user_id'])
    
    return {
        'estimated_time': estimated_time,
        'pending_tasks': len(pending_tasks),
        'focus_time': focus_time,
        'completed_tasks': len(completed_tasks)
    }

def update_sidebar_active_state():
    """更新侧边栏激活状态"""
    # 重新创建侧边栏以更新active状态
    sidebar_container.clear()
    create_sidebar()

def show_settings_dialog():
    """显示设置对话框"""
    settings = settings_manager.get_user_settings(current_user['user_id'])
    
    with ui.dialog().classes('w-96') as dialog:
        with ui.card():
            ui.label('系统设置').classes('text-h6 mb-4')
            
            # 番茄工作法设置
            ui.label('番茄工作法设置').classes('text-subtitle1 mb-2')
            work_duration = ui.number(label='工作时长(分钟)', 
                                    value=settings['pomodoro_work_duration'] if settings else 25).classes('w-full')
            short_break = ui.number(label='短休息时长(分钟)', 
                                  value=settings['pomodoro_short_break_duration'] if settings else 5).classes('w-full')
            long_break = ui.number(label='长休息时长(分钟)', 
                                 value=settings['pomodoro_long_break_duration'] if settings else 15).classes('w-full')
            
            # 目标设置
            ui.label('目标设置').classes('text-subtitle1 mb-2 mt-4')
            daily_target = ui.number(label='每日专注目标(分钟)', 
                                   value=settings['daily_focus_target_minutes'] if settings else 120).classes('w-full')
            
            def save_settings():
                settings_data = {
                    'pomodoro_work_duration': int(work_duration.value),
                    'pomodoro_short_break_duration': int(short_break.value),
                    'pomodoro_long_break_duration': int(long_break.value),
                    'daily_focus_target_minutes': int(daily_target.value)
                }
                
                success = settings_manager.update_user_settings(current_user['user_id'], settings_data)
                if success:
                    ui.notify('设置已保存', type='positive')
                    dialog.close()
                else:
                    ui.notify('保存失败', type='negative')
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('保存', on_click=save_settings).props('color=primary')
    
    dialog.open()

def handle_logout():
    """处理用户退出"""
    global current_user, current_tasks, active_session, timer_running
    
    # 清除登录状态
    current_user = None
    current_tasks = []
    active_session = None
    timer_running = False
    
    # 清除本地存储的登录信息
    app.storage.user.clear()
    
    ui.notify('已退出登录', type='info')
    ui.navigate.to('/login')

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