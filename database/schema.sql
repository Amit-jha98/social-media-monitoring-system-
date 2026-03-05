-- schema.sql
CREATE DATABASE IF NOT EXISTS ncb_projectv3;
USE ncb_projectv3;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keywords table
CREATE TABLE keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL UNIQUE,
    added_by INT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Raw Data table
CREATE TABLE raw_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    platform VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,  -- Store encrypted content
    timestamp DATETIME NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clean_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255),
    platform VARCHAR(255),
    user_id VARCHAR(255) DEFAULT NULL,
    user_name VARCHAR(255) DEFAULT NULL,
    link TEXT DEFAULT NULL,
    caption TEXT DEFAULT NULL,
    tags TEXT DEFAULT NULL,
    comments TEXT DEFAULT NULL,
    likes INT DEFAULT NULL,
    post_time DATETIME DEFAULT NULL,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Honeypots table
CREATE TABLE honeypots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform ENUM('Telegram', 'WhatsApp', 'Instagram') NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL UNIQUE,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Platforms table
CREATE TABLE platforms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Monitored Channels table
CREATE TABLE monitored_channels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform_id INT,
    channel_name VARCHAR(255) NOT NULL,
    channel_id VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (platform_id) REFERENCES platforms(id)
);

-- Logs table
CREATE TABLE logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(255),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Alerts table
CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type ENUM('keyword_match', 'suspicious_activity', 'honeypot_interaction') NOT NULL,
    description TEXT,
    related_user INT,
    channel_id INT,
    platform_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (related_user) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (channel_id) REFERENCES monitored_channels(id) ON DELETE SET NULL,
    FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE SET NULL
);

-- Reports table
CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_title VARCHAR(255) NOT NULL,
    report_content TEXT,
    generated_by INT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Suspicious Activity table
CREATE TABLE suspicious_activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    keyword_id INT,
    keyword_text VARCHAR(255) DEFAULT NULL,
    platform_id INT,
    channel_id INT,
    detected_text TEXT,
    text_hash VARCHAR(64) DEFAULT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE SET NULL,
    FOREIGN KEY (channel_id) REFERENCES monitored_channels(id) ON DELETE SET NULL
);


