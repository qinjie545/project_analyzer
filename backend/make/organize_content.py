#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容整理脚本
周六执行，整理周五拉取的项目数据，生成文章内容
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict


class ContentOrganizer:
    """内容整理器"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化
        
        Args:
            data_dir: 数据文件目录，默认为项目根目录下的 data
        """
        if data_dir is None:
            # 数据目录相对于 backend 目录
            self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        else:
            self.data_dir = data_dir
    
    def load_latest_data(self) -> Dict:
        """
        加载最新的项目数据
        
        Returns:
            项目数据字典
        """
        if not os.path.exists(self.data_dir):
            print(f"数据目录不存在: {self.data_dir}")
            return None
        
        # 查找最新的数据文件
        files = [f for f in os.listdir(self.data_dir) if f.startswith('repos_') and f.endswith('.json')]
        if not files:
            print("未找到数据文件")
            return None
        
        # 按文件名排序，获取最新的
        files.sort(reverse=True)
        latest_file = os.path.join(self.data_dir, files[0])
        
        print(f"加载数据文件: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_article_content(self, data: Dict, top_n: int = 10) -> str:
        """
        生成文章内容
        
        Args:
            data: 项目数据
            top_n: 选择前 N 个项目进行分析
            
        Returns:
            Markdown 格式的文章内容
        """
        if not data or 'repos' not in data:
            return ""
        
        repos = data['repos'][:top_n]
        fetch_date = data.get('fetch_date', datetime.now().isoformat())
        
        # 解析日期
        try:
            date_obj = datetime.fromisoformat(fetch_date.replace('Z', '+00:00'))
            date_str = date_obj.strftime('%Y年%m月%d日')
        except:
            date_str = datetime.now().strftime('%Y年%m月%d日')
        
        # 生成文章标题和开头
        content = f"""# GitHub 一周热门项目分析 - {date_str}

> 本文分析了最近一周 GitHub 上 star 增长最快的 {top_n} 个项目，帮助开发者发现最新的技术趋势和优秀开源项目。

## 📊 数据概览

本次分析基于 {date_str} 拉取的 GitHub 项目数据，筛选出 star 数最高的 {top_n} 个项目进行深入分析。

## 🚀 热门项目分析

"""
        
        # 按语言分类统计
        language_stats = {}
        for repo in repos:
            lang = repo.get('language', 'Unknown')
            language_stats[lang] = language_stats.get(lang, 0) + 1
        
        # 添加语言分布
        if language_stats:
            content += "### 编程语言分布\n\n"
            sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
            for lang, count in sorted_langs:
                content += f"- **{lang}**: {count} 个项目\n"
            content += "\n"
        
        # 详细项目分析
        for i, repo in enumerate(repos, 1):
            content += self._generate_repo_section(repo, i)
        
        # 添加总结
        content += f"""
## 📝 总结

本周 GitHub 热门项目呈现出以下特点：

1. **技术趋势**: 从语言分布可以看出当前热门的技术栈
2. **项目质量**: 这些项目都获得了较高的 star 数，说明其质量和实用性得到了社区的认可
3. **创新方向**: 通过分析这些项目，可以发现当前技术创新的主要方向

---

*数据来源: GitHub API*  
*更新时间: {date_str}*
"""
        
        return content
    
    def _generate_repo_section(self, repo: Dict, index: int) -> str:
        """
        生成单个项目的分析段落
        
        Args:
            repo: 项目数据
            index: 项目序号
            
        Returns:
            Markdown 格式的项目分析段落
        """
        name = repo.get('name', 'Unknown')
        full_name = repo.get('full_name', '')
        description = repo.get('description', '暂无描述')
        url = repo.get('url', '')
        stars = repo.get('stars', 0)
        forks = repo.get('forks', 0)
        language = repo.get('language', 'Unknown')
        topics = repo.get('topics', [])
        
        section = f"""### {index}. {name}

**项目地址**: [{full_name}]({url})

**⭐ Stars**: {stars} | **🍴 Forks**: {forks} | **💻 语言**: {language}

**项目描述**: {description}

"""
        
        if topics:
            topics_str = ', '.join([f"`{topic}`" for topic in topics[:5]])
            section += f"**标签**: {topics_str}\n\n"
        
        # 添加分析内容（这里可以后续接入 AI 分析）
        section += f"**简要分析**: 这是一个使用 {language} 开发的项目，获得了 {stars} 个 star，说明其在社区中受到了广泛关注。\n\n"
        
        section += "---\n\n"
        
        return section
    
    def save_article(self, content: str, filename: str = None):
        """
        保存文章到文件
        
        Args:
            content: 文章内容
            filename: 文件名
        """
        if filename is None:
            filename = f"article_{datetime.now().strftime('%Y%m%d')}.md"
        
        # 文章目录相对于 backend 目录
        articles_dir = os.path.join(os.path.dirname(__file__), '..', 'articles')
        os.makedirs(articles_dir, exist_ok=True)
        filepath = os.path.join(articles_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"文章已保存到: {filepath}")
        return filepath


def main():
    """主函数"""
    organizer = ContentOrganizer()
    
    # 加载最新数据
    data = organizer.load_latest_data()
    if not data:
        print("无法加载数据，请先运行 pull/fetch_github_trending.py")
        return
    
    # 生成文章内容
    print("正在生成文章内容...")
    content = organizer.generate_article_content(data, top_n=10)
    
    # 保存文章
    organizer.save_article(content)
    
    print("\n内容整理完成！")


if __name__ == "__main__":
    main()
