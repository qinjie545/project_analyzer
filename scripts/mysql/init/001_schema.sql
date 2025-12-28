-- Schema initialization for github_daily_report
-- Generated at 2025-12-15T08:40:03.636Z

CREATE DATABASE IF NOT EXISTS `github_daily_report` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `github_daily_report`;

-- 抓取配置
CREATE TABLE IF NOT EXISTS `pull_config` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `sources` JSON NULL,
  `keywords` VARCHAR(1024) NULL,
  `keywords_list` JSON NULL,
  `rule` VARCHAR(64) NULL,
  `frequency` ENUM('daily','weekly') NULL,
  `weekday` TINYINT NULL,
  `times_per_week` TINYINT NULL,
  `start_time` TIME NULL,
  `concurrency` INT NULL,
  `per_project_delay` INT NULL,
  `batch` INT NULL,
  `updated_at` DATETIME NULL,
  INDEX `idx_pull_config_rule` (`rule`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 抓取任务
CREATE TABLE IF NOT EXISTS `pull_task` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `task_id` VARCHAR(64) NOT NULL UNIQUE,
  `config_snapshot` JSON NULL,
  `status` VARCHAR(32) NULL,
  `created_at` DATETIME NULL,
  `started_at` DATETIME NULL,
  `finished_at` DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 抓取记录
CREATE TABLE IF NOT EXISTS `pull_record` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `task_id` VARCHAR(64) NULL,
  `repo_full_name` VARCHAR(255) NULL,
  `url` VARCHAR(512) NULL,
  `pull_time` DATETIME NULL,
  `stars` INT NULL,
  `forks` INT NULL,
  `save_path` VARCHAR(512) NULL,
  `result_status` VARCHAR(32) NULL,
  `rule` VARCHAR(64) NULL,
  INDEX `idx_pull_task` (`task_id`),
  INDEX `idx_repo_full_name` (`repo_full_name`),
  INDEX `idx_pull_time` (`pull_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 制作配置
CREATE TABLE IF NOT EXISTS `make_config` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `provider` VARCHAR(64) NULL,
  `base_url` VARCHAR(255) NULL,
  `model` VARCHAR(128) NULL,
  `external_api_key` VARBINARY(4096) NULL,
  `updated_at` DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 制作任务
CREATE TABLE IF NOT EXISTS `make_task` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `task_id` VARCHAR(64) NOT NULL UNIQUE,
  `input_ref` VARCHAR(512) NULL,
  `status` VARCHAR(32) NULL,
  `created_at` DATETIME NULL,
  `started_at` DATETIME NULL,
  `finished_at` DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 制作记录
CREATE TABLE IF NOT EXISTS `make_record` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `task_id` VARCHAR(64) NULL,
  `artifact_ref` VARCHAR(512) NULL,
  `status` VARCHAR(32) NULL,
  `summary` TEXT NULL,
  `created_at` DATETIME NULL,
  INDEX `idx_make_task` (`task_id`),
  INDEX `idx_make_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 发布配置
CREATE TABLE IF NOT EXISTS `publish_config` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `platforms` JSON NULL,
  `account` VARCHAR(128) NULL,
  `api_key` VARBINARY(4096) NULL,
  `publish_time` TIME NULL,
  `updated_at` DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 发布历史
CREATE TABLE IF NOT EXISTS `publish_history` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NULL,
  `platform` VARCHAR(64) NULL,
  `time` DATETIME NULL,
  `status` VARCHAR(32) NULL,
  `url` VARCHAR(512) NULL,
  INDEX `idx_publish_time` (`time`),
  INDEX `idx_publish_platform` (`platform`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
