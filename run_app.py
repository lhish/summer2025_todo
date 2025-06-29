#!/usr/bin/env python3
"""
项目启动脚本
运行个人任务与效能管理网页平台
"""

import os
import sys
from main import *

if __name__ in {"__main__", "__mp_main__"}:
    print("正在启动个人任务与效能管理网页平台...")
    print("请在浏览器中访问: http://localhost:8080")
    print("按 Ctrl+C 停止服务器")
    
    try:
        # 运行应用
        ui.run(
            host=APP_CONFIG['host'],
            port=APP_CONFIG['port'],
            title='个人任务与效能管理平台',
            favicon='🍅',
            show=True,  # 自动打开浏览器
            reload=APP_CONFIG['debug'],
            storage_secret=APP_CONFIG['secret_key']
        )
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1) 