#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度脚本
使用 cron 或 schedule 库来执行定时任务
"""

import schedule
import time
import subprocess
import sys
import os
from datetime import datetime


def run_fetch_script():
    """执行拉取脚本（每周五执行）"""
    print(f"[{datetime.now()}] 开始执行 GitHub 项目拉取任务...")
    try:
        result = subprocess.run(
            [sys.executable, "pull/fetch_github_trending.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"[{datetime.now()}] GitHub 项目拉取任务完成")
    except Exception as e:
        print(f"[{datetime.now()}] 执行拉取任务时出错: {e}")


def run_organize_script():
    """执行内容整理脚本（每周六执行）"""
    print(f"[{datetime.now()}] 开始执行内容整理任务...")
    try:
        result = subprocess.run(
            [sys.executable, "make/organize_content.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"[{datetime.now()}] 内容整理任务完成")
    except Exception as e:
        print(f"[{datetime.now()}] 执行整理任务时出错: {e}")


def run_publish_script():
    """执行发布脚本（每周日执行）"""
    print(f"[{datetime.now()}] 开始执行微信公众号发布任务...")
    try:
        result = subprocess.run(
            [sys.executable, "publish/publish_wechat.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"[{datetime.now()}] 微信公众号发布任务完成")
    except Exception as e:
        print(f"[{datetime.now()}] 执行发布任务时出错: {e}")


def setup_schedule():
    """设置定时任务"""
    # 用户已取消定期拉取，改为手动触发
    # schedule.every().friday.at("09:00").do(run_fetch_script)
    
    # 每周六执行整理任务
    schedule.every().saturday.at("09:00").do(run_organize_script)
    
    # 每周日执行发布任务
    schedule.every().sunday.at("09:00").do(run_publish_script)
    
    print("定时任务已设置：")
    print("- (已禁用) 每周五 09:00: 拉取 GitHub 项目")
    print("- 每周六 09:00: 整理内容")
    print("- 每周日 09:00: 发布微信公众号文章")


def main():
    """主函数"""
    setup_schedule()
    
    print("\n定时任务调度器已启动，按 Ctrl+C 退出")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        print("\n定时任务调度器已停止")


if __name__ == "__main__":
    main()
