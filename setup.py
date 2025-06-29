#!/usr/bin/env python3
"""
个人任务与效能管理网页平台 - 项目初始化脚本
"""

import os
import sys
import subprocess

def check_requirements():
    """检查Python版本和必要的包"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        return False
    
    print("Python版本检查通过")
    return True

def install_dependencies():
    """安装项目依赖"""
    try:
        print("正在安装项目依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        return False

def create_env_file():
    """创建环境配置文件"""
    env_content = """# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=pomodoro_task_manager

# AI API配置 - Gemini2.5-Flash通过OpenAI格式调用
OPENAI_API_KEY=your_gemini_api_key_here
OPENAI_BASE_URL=https://your-third-party-api-endpoint.com/v1
OPENAI_MODEL=your_model_name_here

# 应用配置
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=8080
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("已创建 .env 配置文件，请根据您的环境修改相关配置")
    else:
        print(".env 文件已存在，跳过创建")

def show_next_steps():
    """显示下一步操作说明"""
    print("\n" + "="*50)
    print("项目初始化完成！")
    print("="*50)
    print("\n接下来的步骤:")
    print("1. 配置MySQL数据库:")
    print("   - 创建数据库: CREATE DATABASE pomodoro_task_manager;")
    print("   - 执行: mysql -u root -p pomodoro_task_manager < src/database/migrations/database_setup.sql")
    print("\n2. 修改 .env 文件中的配置:")
    print("   - 数据库连接信息")
    print("   - AI API密钥和端点")
    print("\n3. 运行应用:")
    print("   python app.py")
    print("\n4. 访问应用:")
    print("   http://localhost:8080")
    print("\n5. 运行测试:")
    print("   python -m pytest tests/")
    print("\n注意: AI功能需要有效的API密钥才能正常工作")

def main():
    """主函数"""
    print("个人任务与效能管理网页平台 - 项目初始化")
    print("="*50)
    
    if not check_requirements():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    create_env_file()
    show_next_steps()

if __name__ == "__main__":
    main() 