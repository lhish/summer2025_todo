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
    def __init__(self, db_manager, user_manager, tag_manager, task_manager, 
                 pomodoro_manager, settings_manager, ai_assistant, statistics_manager):
        self.db_manager = db_manager
        self.user_manager = user_manager
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
        self.user_tags: List[Dict] = []
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
        
        # 初始化组件
        self.init_components()
        
        # 加载用户数据
        self.load_user_data()
        
        # 加载任务数据
        self.refresh_current_tasks()
        
        # 主体布局
        with ui.row().classes('w-full h-screen no-wrap') as main_row:
            self.main_row = main_row
            
            # 左侧边栏
            self.sidebar_container = ui.column().classes('sidebar-container h-full')
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
            
        # 底部番茄钟和声音控制（固定在主内容区域底部）
        self.timer_container = ui.row().style('position: fixed; bottom: 20px; right: 20px; background: white; border-radius: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 8px 16px; z-index: 1000;')
        with self.timer_container:
            # 番茄钟计时器
            self.pomodoro_component.create_mini_timer(ui.element())
            # 添加全局声音控制按钮
        
        # 添加CSS样式
        self.add_css_styles()

    def load_user_data(self):
        """加载用户数据"""
        if self.current_user:
            self.user_tags = self.tag_manager.get_user_tags_with_count(self.current_user['user_id'])

    def init_components(self):
        """初始化组件"""
        # 侧边栏组件
        self.sidebar_component = SidebarComponent(
            self.tag_manager, 
            self.task_manager,
            self.current_user, 
            self.on_view_change,
            self.handle_logout,
            self.show_settings,
            self.show_statistics,
            self.refresh_and_update_ui,
            self.ai_assistant,
            self.statistics_manager
        )
        
        # 任务列表组件
        self.task_list_component = TaskListComponent(
            self.task_manager,
            self.pomodoro_manager,
            self.settings_manager,
            self.tag_manager,
            self.current_user,
            self.on_task_select,
            self.start_pomodoro_for_task,
            self.refresh_and_update_ui
        )
        
        # 番茄钟组件
        self.pomodoro_component = PomodoroTimerComponent(
            self.pomodoro_manager,
            self.task_manager,
            self.current_user,
            self.settings_manager,
            self.refresh_and_update_ui  # 添加UI更新回调
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
            self.close_task_detail,
            self.current_user['user_id']
        )
        
        # 设置组件
        self.settings_component = SettingsDialogComponent(
            self.settings_manager,
            self.current_user,
            self.user_manager,  # 传入用户管理器
            self.handle_logout,
            self.refresh_and_update_ui
        )
        
        # 主内容组件
        self.main_content_component = MainContentComponent(
            self.current_user,
            self.user_tags,
            statistics_component=self.stats_component,
            ai_assistant=self.ai_assistant,
            task_manager=self.task_manager,
            statistics_manager=self.statistics_manager
        )

    def refresh_current_tasks(self, newly_created_task_id: Optional[int] = None):
        """刷新当前任务列表"""
        print(f"\n=== 主页面刷新任务列表 ===")
        print(f"当前视图: {self.current_view}")
        print(f"当前用户: {self.current_user['user_id'] if self.current_user else 'None'}")
        
        if self.current_user:
            if self.current_view.startswith('tag_'):
                # 标签视图
                tag_id = int(self.current_view.split('_')[1])
                print(f"获取标签任务: tag_id={tag_id}")
                self.current_tasks = self.task_manager.get_tasks(
                    user_id=self.current_user['user_id'],
                    tag_id=tag_id,
                    sort_by='created_at',
                    sort_order='DESC'
                )
            else:
                # 默认视图
                print(f"获取视图任务: view={self.current_view}")
                self.current_tasks = self.task_manager.get_tasks_by_view(self.current_user['user_id'], self.current_view)
            
            print(f"从数据库获取到 {len(self.current_tasks)} 个任务")
            
            # 更新任务列表组件
            if self.task_list_component:
                # 如果有新创建的任务ID，在任务数据中标记
                if newly_created_task_id:
                    for task in self.current_tasks:
                        if task['task_id'] == newly_created_task_id:
                            task['is_newly_created'] = True
                            break
                print("调用 task_list_component.set_current_tasks()...")
                self.task_list_component.set_current_tasks(self.current_tasks)
                self.task_list_component.set_current_view(self.current_view)

    def on_view_change(self, view_type: str):
        """视图切换回调"""
        self.current_view = view_type
        
        # 更新任务详情组件的当前视图
        if hasattr(self, 'task_detail_component') and self.task_detail_component:
            self.task_detail_component.set_current_view(view_type)
        
        # 先更新用户数据（包括标签信息）
        self.load_user_data()
        
        # 刷新任务数据
        self.refresh_current_tasks()
        
        # 更新主内容区域
        if self.main_content_component and self.main_content_container:
            # 确保主内容组件有最新的标签数据
            self.main_content_component.update_user_tags(self.user_tags)
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
        print(f"📋 主页面 start_pomodoro_for_task 被调用，task_id: {task_id}")
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

    def show_statistics(self):
        """显示统计窗口"""
        with ui.dialog() as dialog:
            with ui.card().classes('w-96 max-w-full'):
                ui.label('统计分析').classes('text-h6 mb-4')
                if self.current_user:
                    self.stats_component.create_stats_overview(self.current_user['user_id'])
                else:
                    ui.label('未登录用户')
        dialog.open()

    def handle_logout(self):
        """处理用户退出"""
        # 清除登录状态
        self.current_user = None
        self.current_tasks = []
        
        # 清除本地存储的登录信息
        app.storage.user.clear()
        
        ui.notify('已退出登录', type='info')
        ui.navigate.to('/login')

    def refresh_and_update_ui(self, newly_created_task_id: Optional[int] = None):
        """刷新数据并更新UI"""
        self.refresh_current_tasks(newly_created_task_id)
        self.load_user_data()
        
        # 更新侧边栏
        if self.sidebar_component:
            self.sidebar_component.refresh_sidebar_tags()
        
        # 更新番茄钟组件（当设置更新时）
        if hasattr(self, 'pomodoro_component') and self.pomodoro_component:
            self.pomodoro_component.on_settings_updated()
        
        # 更新主内容区域
        if self.main_content_component and self.main_content_container:
            self.main_content_component.update_user_tags(self.user_tags)
            self.main_content_component.create_main_content(
                self.main_content_container,
                self.current_view,
                self.task_list_component
            )
        
        # 更新任务详情组件（如果正在显示）
        if self.task_detail_component and self.task_detail_open and self.selected_task:
            # 重新获取任务数据以获取最新的标签信息
            updated_task = self.task_manager.get_task_by_id(self.selected_task['task_id'])
            if updated_task:
                self.selected_task = updated_task
                self.task_detail_component.show_task_detail(updated_task, self.task_detail_container)

    def add_css_styles(self):
        """添加CSS样式"""
        ui.add_head_html("""
        <link rel="stylesheet" href="/static/main.css">
        <link rel="stylesheet" href="/static/sidebar.css">
        """)

    def set_current_user(self, user: Dict):
        """设置当前用户"""
        self.current_user = user