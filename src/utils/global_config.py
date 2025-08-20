# 全局配置文件

# 番茄钟主题设置
CURRENT_POMODORO_THEME = '森林'

# 可用主题列表
AVAILABLE_THEMES = [
    {'name': '森林', 'image': 'forest.jpg', 'sound': 'forest.mp3'},
    {'name': '火焰', 'image': 'fire.jpg', 'sound': 'fire.mp3'},
    {'name': '海岸', 'image': 'coast.jpg', 'sound': 'coast.mp3'},
    {'name': '烟花', 'image': 'fireworks.jpg', 'sound': 'fireworks.mp3'}
]

def get_current_theme():
    """获取当前主题"""
    return CURRENT_POMODORO_THEME

def set_current_theme(theme_name):
    """设置当前主题"""
    global CURRENT_POMODORO_THEME
    if theme_name in [theme['name'] for theme in AVAILABLE_THEMES]:
        CURRENT_POMODORO_THEME = theme_name
        return True
    return False

def get_theme_data(theme_name=None):
    """获取主题数据"""
    if theme_name is None:
        theme_name = CURRENT_POMODORO_THEME
    
    for theme in AVAILABLE_THEMES:
        if theme['name'] == theme_name:
            return theme
    return AVAILABLE_THEMES[1]  # 默认返回森林主题