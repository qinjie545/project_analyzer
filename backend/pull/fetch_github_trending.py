#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 趋势项目拉取脚本
每周五自动拉取最近一周 star 增长最快的项目
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time


class GitHubTrendingFetcher:
    """GitHub 趋势项目获取器"""
    
    def __init__(self, github_token: str = None):
        """
        初始化
        
        Args:
            github_token: GitHub Personal Access Token（可选，但建议使用以提高 API 限制）
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
    
    def get_trending_repos(self, days: int = 7, limit: int = 20) -> List[Dict]:
        """
        获取最近 N 天 star 增长最快的项目
        
        Args:
            days: 查询天数，默认 7 天
            limit: 返回项目数量，默认 20 个
            
        Returns:
            项目列表，按 star 增长数排序
        """
        # 计算时间范围
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 使用 GitHub Search API 搜索最近创建或更新的仓库
        # 注意：GitHub API 不直接提供按 star 增长排序，我们需要获取数据后自己排序
        query = f"created:>{since_date} OR pushed:>{since_date}"
        
        repos = []
        page = 1
        per_page = 100
        
        print(f"开始拉取最近 {days} 天的 GitHub 项目...")
        
        while len(repos) < limit * 2:  # 多拉取一些以便后续筛选
            try:
                url = f"{self.base_url}/search/repositories"
                params = {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                # 检查 API 限制
                if response.status_code == 403:
                    rate_limit = response.headers.get('X-RateLimit-Remaining', '0')
                    reset_time = response.headers.get('X-RateLimit-Reset', '0')
                    print(f"API 限制达到，剩余请求数: {rate_limit}")
                    if reset_time != '0':
                        reset_datetime = datetime.fromtimestamp(int(reset_time))
                        print(f"重置时间: {reset_datetime}")
                    break
                
                response.raise_for_status()
                data = response.json()
                
                if not data.get('items'):
                    break
                
                # 获取每个仓库的详细信息，包括 star 增长情况
                for repo in data['items']:
                    repo_detail = self._get_repo_detail(repo['full_name'])
                    if repo_detail:
                        repos.append(repo_detail)
                    
                    # 避免触发 API 限制
                    time.sleep(0.1)
                
                page += 1
                
                # 避免触发 API 限制
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"请求错误: {e}")
                break
        
        # 按 star 增长数排序（这里简化处理，使用当前 star 数）
        # 实际应用中，可以记录历史数据来比较增长
        repos.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)
        
        return repos[:limit]
    
    def _get_repo_detail(self, full_name: str) -> Dict:
        """
        获取仓库详细信息
        
        Args:
            full_name: 仓库全名，格式：owner/repo
            
        Returns:
            仓库详细信息字典
        """
        try:
            url = f"{self.base_url}/repos/{full_name}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            repo_data = response.json()
            
            return {
                'name': repo_data.get('name'),
                'full_name': repo_data.get('full_name'),
                'description': repo_data.get('description', ''),
                'url': repo_data.get('html_url'),
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'language': repo_data.get('language', ''),
                'created_at': repo_data.get('created_at'),
                'updated_at': repo_data.get('updated_at'),
                'pushed_at': repo_data.get('pushed_at'),
                'topics': repo_data.get('topics', []),
                'owner': {
                    'login': repo_data.get('owner', {}).get('login'),
                    'avatar_url': repo_data.get('owner', {}).get('avatar_url')
                }
            }
        except Exception as e:
            print(f"获取仓库 {full_name} 详情失败: {e}")
            return None
    
    def save_to_file(self, repos: List[Dict], filename: str = None):
        """
        保存项目数据到文件
        
        Args:
            repos: 项目列表
            filename: 文件名，默认为当前日期
        """
        if filename is None:
            filename = f"repos_{datetime.now().strftime('%Y%m%d')}.json"
        
        # 数据目录相对于 backend 目录
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, filename)
        
        output = {
            'fetch_date': datetime.now().isoformat(),
            'repos': repos
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {filepath}")
        return filepath


def main():
    """主函数"""
    # 从环境变量或配置文件读取 GitHub Token
    github_token = os.getenv('GITHUB_TOKEN')
    
    fetcher = GitHubTrendingFetcher(github_token=github_token)
    
    # 拉取最近一周 star 增长最快的项目
    repos = fetcher.get_trending_repos(days=7, limit=20)
    
    print(f"\n成功拉取 {len(repos)} 个项目")
    print("\n前 5 个项目:")
    for i, repo in enumerate(repos[:5], 1):
        print(f"{i}. {repo['full_name']} - ⭐ {repo['stars']} - {repo['language']}")
    
    # 保存到文件
    fetcher.save_to_file(repos)
    
    return repos


if __name__ == "__main__":
    main()
