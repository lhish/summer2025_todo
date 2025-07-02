DROP DATABASE IF EXISTS pomodoro_task_manager;
-- 创建数据库
CREATE DATABASE IF NOT EXISTS pomodoro_task_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pomodoro_task_manager;
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 清单表
CREATE TABLE lists (
    list_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#2196F3',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 标签表
CREATE TABLE tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#757575',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_tag (user_id, name),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 任务表
CREATE TABLE tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    list_id INT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,
    priority ENUM('high', 'medium', 'low') DEFAULT 'medium',
    status ENUM('pending', 'completed') DEFAULT 'pending',
    repeat_cycle ENUM('none', 'daily', 'weekly', 'monthly') DEFAULT 'none',
    reminder_time TIME,
    estimated_pomodoros INT DEFAULT 1,
    used_pomodoros INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (list_id) REFERENCES lists(list_id) ON DELETE SET NULL
);

-- 任务标签关联表
CREATE TABLE task_tags (
    task_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

-- 用户设置表
CREATE TABLE user_settings (
    user_id INT PRIMARY KEY,
    pomodoro_work_duration INT DEFAULT 25,
    pomodoro_short_break_duration INT DEFAULT 5,
    pomodoro_long_break_duration INT DEFAULT 15,
    pomodoro_long_break_interval INT DEFAULT 4,
    notification_sound VARCHAR(50) DEFAULT 'default',
    auto_start_next_pomodoro BOOLEAN DEFAULT FALSE,
    auto_start_break BOOLEAN DEFAULT FALSE,
    daily_focus_target_minutes INT DEFAULT 120,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 专注记录表
CREATE TABLE focus_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_id INT,
    session_type ENUM('work', 'short_break', 'long_break') NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_minutes INT NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE SET NULL
);

-- 插入默认数据
-- 为每个用户创建默认清单的触发器
DELIMITER //
CREATE TRIGGER create_default_list AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO lists (user_id, name, color) VALUES (NEW.user_id, '默认清单', '#2196F3');
END//
DELIMITER ; 