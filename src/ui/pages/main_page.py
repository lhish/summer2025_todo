"""
主页面组件
"""

from nicegui import ui, app
from typing import Dict, List, Optional, Callable

from ..components.sidebar import SidebarComponent
from ..components.task_list import TaskListComponent
from ..components.pomodoro_timer import PomodoroTimerComponent
from ..components.statistics_dashboard import StatisticsDashboardComponent
from ..components.task_detail import TaskDetailComponent
from ..components.settings_dialog import SettingsDialogComponent
from ..components.main_content import MainContentComponent


class MainPage:
    def __init__(self, db_manager, user_manager, list_manager, tag_manager, task_manager, 
                 pomodoro_manager, settings_manager, ai_assistant, statistics_manager):
        self.db_manager = db_manager
        self.user_manager = user_manager
        self.list_manager = list_manager
        self.tag_manager = tag_manager
        self.task_manager = task_manager
        self.pomodoro_manager = pomodoro_manager
        self.settings_manager = settings_manager
        self.ai_assistant = ai_assistant
        self.statistics_manager = statistics_manager
        
        # 应用状态
        self.current_user: Optional[Dict] = None
        self.current_view = 'my_day'
        self.current_tasks: List[Dict] = []
        self.user_lists: List[Dict] = []
        self.task_detail_open = False
        self.selected_task: Optional[Dict] = None
        
        # UI组件引用
        self.main_row = None
        self.sidebar_container = None
        self.main_content_container = None
        self.task_detail_container = None
        self.timer_container = None
        
        # 组件实例
        self.sidebar_component = None
        self.task_list_component = None
        self.pomodoro_component = None
        self.stats_component = None
        self.task_detail_component = None
        self.settings_component = None
        self.main_content_component = None

    def create_index_page(self, on_logout: Callable):
        """创建首页路由"""
        def index():
            """首页"""
            # 检查是否有保存的登录状态
            if not self.current_user:
                saved_user_id = app.storage.user.get('user_id')
                if saved_user_id:
                    # 从数据库重新获取用户信息
                    user = self.user_manager.get_user_by_id(saved_user_id)
                    if user:
                        self.current_user = user
            
            if self.current_user:
                self.show_main_app()
            else:
                ui.navigate.to('/login')
        
        return index

    def show_main_app(self):
        """显示主应用界面"""
        ui.page_title('个人任务与效能管理平台')
        
        # 加载用户数据
        self.load_user_data()
        
        # 初始化组件
        self.init_components()
        
        # 主体布局
        with ui.row().classes('w-full h-screen no-wrap') as main_row:
            self.main_row = main_row
            
            # 左侧边栏
            self.sidebar_container = ui.column().classes('sidebar-container')
            self.sidebar_component.create_sidebar(self.sidebar_container)
            
            # 中间主内容区域
            self.main_content_container = ui.column().classes('flex-1 h-full overflow-auto bg-grey-1')
            self.main_content_component.create_main_content(
                self.main_content_container, 
                self.current_view, 
                self.task_list_component
            )
            
            # 右侧任务详情栏（默认隐藏）
            self.task_detail_container = ui.column().classes('task-detail-container task-detail-hidden')
            
        # 底部番茄钟（固定在主内容区域底部）
        self.timer_container = ui.row().classes('timer-mini-container')
        self.pomodoro_component.create_mini_timer(self.timer_container)
        
        # 添加CSS样式
        self.add_css_styles()

    def load_user_data(self):
        """加载用户数据"""
        if self.current_user:
            self.user_lists = self.list_manager.get_user_lists(self.current_user['user_id'])
            self.refresh_current_tasks()

    def init_components(self):
        """初始化组件"""
        # 侧边栏组件
        self.sidebar_component = SidebarComponent(
            self.list_manager, 
            self.current_user, 
            self.on_view_change,
            self.handle_logout,
            self.show_settings
        )
        
        # 任务列表组件
        self.task_list_component = TaskListComponent(
            self.task_manager,
            self.pomodoro_manager,
            self.current_user,
            self.on_task_select,
            self.start_pomodoro_for_task,
            self.refresh_and_update_ui
        )
        
        # 番茄钟组件
        self.pomodoro_component = PomodoroTimerComponent(
            self.pomodoro_manager,
            self.task_manager,
            self.current_user
        )
        
        # 统计组件
        self.stats_component = StatisticsDashboardComponent(
            self.statistics_manager,
            self.pomodoro_manager,
            self.current_user
        )
        
        # 任务详情组件
        self.task_detail_component = TaskDetailComponent(
            self.task_manager,
            self.refresh_and_update_ui,
            self.start_pomodoro_for_task,
            self.close_task_detail
        )
        
        # 设置组件
        self.settings_component = SettingsDialogComponent(
            self.settings_manager,
            self.current_user
        )
        
        # 主内容组件
        self.main_content_component = MainContentComponent(
            self.current_user,
            self.user_lists
        )

    def refresh_current_tasks(self):
        """刷新当前任务列表"""
        if self.current_user:
            if self.current_view.startswith('list_'):
                # 清单视图
                list_id = int(self.current_view.split('_')[1])
                self.current_tasks = self.task_manager.get_tasks(
                    user_id=self.current_user['user_id'],
                    list_id=list_id,
                    sort_by='created_at',
                    sort_order='DESC'
                )
            else:
                # 默认视图
                self.current_tasks = self.task_manager.get_tasks_by_view(self.current_user['user_id'], self.current_view)
            
            # 更新任务列表组件
            if self.task_list_component:
                self.task_list_component.set_current_tasks(self.current_tasks)
                self.task_list_component.set_current_view(self.current_view)

    def on_view_change(self, view_type: str):
        """视图切换回调"""
        self.current_view = view_type
        self.refresh_current_tasks()
        
        # 更新主内容区域
        if self.main_content_component and self.main_content_container:
            self.main_content_component.create_main_content(
                self.main_content_container,
                self.current_view,
                self.task_list_component
            )

    def on_task_select(self, task: Dict):
        """任务选择回调"""
        self.selected_task = task
        self.task_detail_open = True
        
        # 显示任务详情容器
        self.task_detail_container.classes(remove='task-detail-hidden')
        
        self.task_detail_component.show_task_detail(task, self.task_detail_container)

    def start_pomodoro_for_task(self, task_id: int):
        """为特定任务开始番茄工作法"""
        self.pomodoro_component.start_pomodoro_for_task(task_id)

    def close_task_detail(self):
        """关闭任务详情面板"""
        self.task_detail_open = False
        self.selected_task = None
        
        # 隐藏任务详情容器
        self.task_detail_container.classes(add='task-detail-hidden')

    def show_settings(self):
        """显示设置对话框"""
        self.settings_component.show_settings_dialog()

    def handle_logout(self):
        """处理用户退出"""
        # 清除登录状态
        self.current_user = None
        self.current_tasks = []
        
        # 清除本地存储的登录信息
        app.storage.user.clear()
        
        ui.notify('已退出登录', type='info')
        ui.navigate.to('/login')

    def refresh_and_update_ui(self):
        """刷新数据并更新UI"""
        self.refresh_current_tasks()
        self.load_user_data()
        
        # 更新侧边栏
        if self.sidebar_component:
            self.sidebar_component.refresh_user_lists()
        
        # 更新主内容区域
        if self.main_content_component and self.main_content_container:
            self.main_content_component.update_user_lists(self.user_lists)
            self.main_content_component.create_main_content(
                self.main_content_container,
                self.current_view,
                self.task_list_component
            )

    def add_css_styles(self):
        """添加CSS样式"""
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
            .task-detail-hidden {
                display: none !important;
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

    def set_current_user(self, user: Dict):
        """设置当前用户"""
        self.current_user = user 