SET NAMES utf8mb4;
USE smart_house;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS action_history, data_sensor, devices, sensors, users;
SET FOREIGN_KEY_CHECKS = 1;

-- User: tài khoản sinh viên
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,          -- hash bcrypt, không lưu mật khẩu gốc
    full_name VARCHAR(255),
    student_id VARCHAR(20),
    class_name VARCHAR(20),
    faculty VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    avatar VARCHAR(255),
    links JSON NULL                          -- {"github": "...", "figma": "...", "report_pdf": "..."}
);

-- Device: thiết bị điều khiển (LED)
CREATE TABLE devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    status ENUM('ON', 'OFF') NOT NULL DEFAULT 'OFF'
);

-- Sensor: danh mục kênh đo, kèm ngưỡng bình thường
CREATE TABLE sensors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    unit VARCHAR(20),
    min_normal DOUBLE NULL,
    max_normal DOUBLE NULL
);

-- DataSensor: giá trị đo theo thời gian
CREATE TABLE data_sensor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    value DOUBLE NOT NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sensor_id INT NOT NULL,
    FOREIGN KEY (sensor_id) REFERENCES sensors(id) ON DELETE CASCADE,
    INDEX idx_sensor_time (sensor_id, recorded_at),
    INDEX idx_time (recorded_at)
);

-- ActionHistory: lịch sử bật/tắt thiết bị
CREATE TABLE action_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action ENUM('ON', 'OFF') NOT NULL,
    status ENUM('PENDING', 'SUCCESS', 'FAILED') NOT NULL DEFAULT 'PENDING',
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INT NULL,                        -- NULL = hệ thống/tự động
    device_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id),
    INDEX idx_action_device_time (device_id, recorded_at),
    INDEX idx_action_status (status),
    INDEX idx_action_time (recorded_at)
);