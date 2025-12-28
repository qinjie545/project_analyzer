#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号发布脚本
周日执行，将整理好的文章发布到微信公众号
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional
import requests


class WeChatPublisher:
    """微信公众号发布器"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        """
        初始化
        
        Args:
            app_id: 微信公众号 AppID
            app_secret: 微信公众号 AppSecret
        """
        self.app_id = app_id or os.getenv('WECHAT_APP_ID')
        self.app_secret = app_secret or os.getenv('WECHAT_APP_SECRET')
        self.access_token = None
    
    def get_access_token(self) -> Optional[str]:
        """
        获取访问令牌
        
        Returns:
            访问令牌字符串
        """
        if not self.app_id or not self.app_secret:
            print("未配置微信公众号 AppID 或 AppSecret")
            return None
        
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'access_token' in data:
                self.access_token = data['access_token']
                print("成功获取访问令牌")
                return self.access_token
            else:
                print(f"获取访问令牌失败: {data}")
                return None
        except Exception as e:
            print(f"获取访问令牌时出错: {e}")
            return None
    
    def load_latest_article(self) -> Optional[str]:
        """
        加载最新的文章内容
        
        Returns:
            文章内容字符串
        """
        # 文章目录相对于 backend 目录
        articles_dir = os.path.join(os.path.dirname(__file__), '..', 'articles')
        if not os.path.exists(articles_dir):
            print(f"文章目录不存在: {articles_dir}")
            return None
        
        # 查找最新的文章文件
        files = [f for f in os.listdir(articles_dir) if f.startswith('article_') and f.endswith('.md')]
        if not files:
            print("未找到文章文件")
            return None
        
        files.sort(reverse=True)
        latest_file = os.path.join(articles_dir, files[0])
        
        print(f"加载文章文件: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def convert_markdown_to_wechat_format(self, markdown_content: str) -> Dict:
        """
        将 Markdown 转换为微信公众号格式
        
        Args:
            markdown_content: Markdown 格式的内容
            
        Returns:
            微信公众号文章格式字典
        """
        # 简单的 Markdown 到微信公众号格式转换
        # 实际应用中可以使用更完善的转换库
        
        # 提取标题
        lines = markdown_content.split('\n')
        title = ""
        content = ""
        
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
            elif line.startswith('## '):
                content += f"<h2>{line[3:].strip()}</h2>\n"
            elif line.startswith('### '):
                content += f"<h3>{line[4:].strip()}</h3>\n"
            elif line.startswith('**') and line.endswith('**'):
                # 粗体
                text = line.strip('*')
                content += f"<strong>{text}</strong><br/>\n"
            elif line.startswith('- '):
                # 列表项
                text = line[2:].strip()
                content += f"<li>{text}</li>\n"
            elif line.strip().startswith('[') and '](' in line:
                # 链接
                import re
                match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', line.strip())
                if match:
                    link_text = match.group(1)
                    link_url = match.group(2)
                    content += f'<a href="{link_url}">{link_text}</a><br/>\n'
            elif line.strip():
                content += f"{line}<br/>\n"
            else:
                content += "<br/>\n"
        
        if not title:
            title = f"GitHub 一周热门项目分析 - {datetime.now().strftime('%Y年%m月%d日')}"
        
        return {
            "title": title,
            "content": content,
            "author": "GitHub Daily Report",
            "content_source_url": "",
            "digest": "本周 GitHub 热门项目分析"
        }
    
    def create_draft(self, article_data: Dict) -> bool:
        """
        创建草稿
        
        Args:
            article_data: 文章数据
            
        Returns:
            是否创建成功
        """
        if not self.access_token:
            if not self.get_access_token():
                return False
        
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
        
        # 微信公众号 API 需要特定的格式
        payload = {
            "articles": [article_data]
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get('errcode') == 0:
                print("草稿创建成功")
                return True
            else:
                print(f"草稿创建失败: {data}")
                return False
        except Exception as e:
            print(f"创建草稿时出错: {e}")
            return False
    
    def publish(self, article_data: Dict) -> bool:
        """
        发布文章（需要先创建草稿，然后发布）
        
        Args:
            article_data: 文章数据
            
        Returns:
            是否发布成功
        """
        # 注意：实际发布需要先创建草稿，然后使用草稿 ID 发布
        # 这里简化处理，只创建草稿
        print("注意：实际发布需要配置微信公众号的发布权限")
        return self.create_draft(article_data)


def main():
    """主函数"""
    publisher = WeChatPublisher()
    
    # 加载最新文章
    article_content = publisher.load_latest_article()
    if not article_content:
        print("无法加载文章，请先运行 organize_content.py")
        return
    
    # 转换为微信公众号格式
    print("正在转换文章格式...")
    article_data = publisher.convert_markdown_to_wechat_format(article_content)
    
    # 发布文章
    print("正在发布文章...")
    success = publisher.publish(article_data)
    
    if success:
        print("\n文章发布成功！")
    else:
        print("\n文章发布失败，请检查配置")


if __name__ == "__main__":
    # 注意：实际使用时需要配置微信公众号的 AppID 和 AppSecret
    print("提示：请先配置微信公众号的 AppID 和 AppSecret")
    print("可以通过环境变量 WECHAT_APP_ID 和 WECHAT_APP_SECRET 设置")
    main()
