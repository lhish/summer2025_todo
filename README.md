# 个人任务与效能管理网页平台

一个基于NiceGUI框架开发的现代化个人任务管理与效能提升工具，集成了任务清单管理、番茄工作法和AI智能化辅助功能。

## 🍅 核心功能

- **任务清单管理**: 创建、编辑、删除任务，支持优先级、截止日期、标签分类
- **番茄工作法**: 专注计时器，帮助提升工作效率和时间管理能力
- **AI智能辅助**: 智能任务推荐、工作量预估、效能分析报告
- **数据统计**: 专注时长统计、任务完成率、生产力趋势分析
- **个性化设置**: 可配置的番茄钟时长、每日目标等

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- 现代浏览器支持

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd summer2025_todo
   ```

2. **初始化项目**
   ```bash
   python setup.py
   ```

3. **配置数据库**
   ```bash
   # 创建数据库
   mysql -u root -p -e "CREATE DATABASE pomodoro_task_manager;"
   
   # 导入表结构
   mysql -u root -p pomodoro_task_manager < database_setup.sql
   ```

4. **配置环境变量**
   编辑 `.env` 文件，设置数据库连接信息和API密钥

5. **启动应用**
   ```bash
   # 新版本主应用（推荐，包含完整UI设计）
   python run_app.py
   
   # 或者运行其他版本
   python main.py        # 新版本主应用
   python simple_app.py  # 简化版本
   python app.py         # 原始完整版本
   ```

6. **访问应用**
   打开浏览器访问 http://localhost:8080

## 🏗️ 技术架构

- **前端**: NiceGUI (Python Web UI Framework)
- **后端**: Python with asyncio
- **数据库**: MySQL
- **AI服务**: Gemini2.5-Flash (OpenAI兼容接口)
- **部署**: Nginx (生产环境)

## 📁 项目结构

```
summer2025_todo/
├── config.py              # 配置管理
├── database.py             # 数据库连接、用户、清单、标签管理
├── task_manager.py         # 任务管理模块（支持多标签和清单）
├── pomodoro_manager.py     # 番茄工作法管理
├── ai_assistant.py         # AI智能辅助功能
├── statistics_manager.py   # 统计报告生成
├── main.py                # 新版本主应用（完整UI设计）
├── run_app.py             # 项目启动脚本
├── simple_app.py           # 简化版主应用
├── app.py                 # 原始完整版主应用
├── database_setup.sql      # 数据库初始化脚本（包含清单和标签表）
├── setup.py               # 项目初始化脚本
└── requirements.txt        # Python依赖包
```

## 🎯 主要特性

### 新版本UI设计 (main.py)
- ✅ **可收缩左侧边栏**: 包含我的一天、计划内、重要、任务等视图
- ✅ **智能任务分类**: 自动按截止日期和优先级组织任务
- ✅ **清单管理**: 支持创建多个任务清单，彩色标识
- ✅ **多标签系统**: 每个任务支持多个标签分类
- ✅ **任务详情面板**: 点击任务弹出右侧详情编辑面板
- ✅ **迷你番茄钟**: 页面底部固定，可展开全屏模式
- ✅ **统计概览栏**: 实时显示预计时间、待完成任务等数据
- ✅ **快速任务创建**: 输入框支持回车快速创建任务

### 任务管理
- ✅ 创建和编辑任务
- ✅ 优先级设置 (高/中/低)
- ✅ 截止日期和提醒（仅日期，无具体时间）
- ✅ 多标签分类管理
- ✅ 任务状态切换
- ✅ 番茄钟预估

### 番茄工作法
- ✅ 可配置工作时长
- ✅ 自动休息提醒
- ✅ 任务关联专注
- ✅ 专注历史记录
- ✅ 每日目标设置

### AI智能功能
- ✅ 智能任务推荐
- ✅ 工作量预估
- ✅ 效能分析报告
- ✅ 工作模式分析

### 数据统计
- ✅ 实时统计展示
- ✅ 今日/本周/本月数据
- ✅ 完成率分析
- ✅ 生产力趋势

## 🔧 配置说明

### 数据库配置
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=pomodoro_task_manager
```

### AI API配置
```env
OPENAI_API_KEY=your_gemini_api_key
OPENAI_BASE_URL=your_api_endpoint
OPENAI_MODEL=your_model_name
```

## 📖 使用指南

1. **用户注册**: 使用邮箱注册账户
2. **创建任务**: 添加待办事项，设置优先级和截止日期
3. **开始专注**: 选择任务启动番茄钟，专注工作25分钟
4. **查看统计**: 了解您的工作效率和完成情况
5. **AI辅助**: 获取智能任务推荐和效能分析

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- NiceGUI 框架提供了优秀的Python Web UI解决方案
- OpenAI 兼容接口使AI集成变得简单
- 番茄工作法理论为时间管理提供了科学依据

---

**注意**: 本项目为学术作业项目，AI功能需要有效的API密钥才能正常使用。