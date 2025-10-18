#!/usr/bin/env python3
"""
GitHub Actions HTTP 触发器

使用方法:
1. 设置环境变量 GITHUB_TOKEN (Personal Access Token)
2. 运行脚本: python trigger_action.py <feishu_table_url> <feishu_auth_token> <douyin_url> [max_videos]

示例:
python trigger_action.py "https://xxx.feishu.cn/base/APP_TOKEN?table=TABLE_ID" "auth_token" "https://www.douyin.com/user/MS4wLjABAAAA..." 30
"""

import requests
import sys
import os
import json

def trigger_github_action(feishu_table_url, feishu_auth_token, douyin_url, max_videos=20, github_token=None):
    """
    通过 HTTP API 触发 GitHub Actions
    
    Args:
        feishu_table_url (str): 飞书多维表格链接
        feishu_auth_token (str): 飞书多维表格授权码
        douyin_url (str): 抖音用户主页URL
        max_videos (int): 最大视频数量
        github_token (str): GitHub Personal Access Token
    
    Returns:
        bool: 是否成功触发
    """
    
    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("错误: 请设置 GITHUB_TOKEN 环境变量或传入 github_token 参数")
        return False
    
    # GitHub API 配置
    owner = "k190513120"
    repo = "douyin_to_base"
    url = f"https://api.github.com/repos/{owner}/{repo}/dispatches"
    
    # 请求头
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    
    # 请求体
    payload = {
        "event_type": "douyin-sync",
        "client_payload": {
            "feishu_table_url": feishu_table_url,
            "feishu_auth_token": feishu_auth_token,
            "douyin_url": douyin_url,
            "max_videos": str(max_videos)
        }
    }
    
    try:
        print(f"正在触发 GitHub Actions...")
        print(f"飞书表格链接: {feishu_table_url}")
        print(f"抖音URL: {douyin_url}")
        print(f"最大视频数: {max_videos}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 204:
            print("✅ GitHub Actions 触发成功!")
            print(f"🔗 查看运行状态: https://github.com/{owner}/{repo}/actions")
            return True
        else:
            print(f"❌ 触发失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 4:
        print("用法: python trigger_action.py <feishu_table_url> <feishu_auth_token> <douyin_url> [max_videos]")
        print("示例: python trigger_action.py 'https://xxx.feishu.cn/base/APP_TOKEN?table=TABLE_ID' 'auth_token' 'https://www.douyin.com/user/MS4wLjABAAAA...' 30")
        sys.exit(1)
    
    feishu_table_url = sys.argv[1]
    feishu_auth_token = sys.argv[2]
    douyin_url = sys.argv[3]
    max_videos = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    
    success = trigger_github_action(feishu_table_url, feishu_auth_token, douyin_url, max_videos)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()