#!/usr/bin/env python3
"""
GitHub Actions 环境增强测试脚本
测试新的反爬虫策略和环境检测功能
"""

import os
import sys
import time
import random
from douyin_scraper import DouyinScraper

def test_github_actions_environment():
    """测试 GitHub Actions 环境下的抖音爬虫功能"""
    
    print("=== GitHub Actions 环境增强测试 ===")
    print(f"Python 版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 模拟 GitHub Actions 环境
    os.environ['GITHUB_ACTIONS'] = 'true'
    os.environ['RUNNER_OS'] = 'Linux'
    os.environ['RUNNER_ARCH'] = 'X64'
    
    print(f"GITHUB_ACTIONS: {os.getenv('GITHUB_ACTIONS')}")
    print(f"RUNNER_OS: {os.getenv('RUNNER_OS')}")
    print(f"RUNNER_ARCH: {os.getenv('RUNNER_ARCH')}")
    
    # 测试抖音爬虫
    print("\n=== 初始化抖音爬虫 ===")
    scraper = DouyinScraper()
    
    # 测试 URL
    test_url = "https://www.douyin.com/user/MS4wLjABAAAAnAFnkWlOm9jteymsi42fanYLMzfbqdGIwCILEUqDNmFyjfK9N8fSJdS_D2UWk_we"
    
    print(f"\n=== 测试抖音用户视频抓取 ===")
    print(f"测试URL: {test_url}")
    
    try:
        # 提取 sec_user_id
        sec_user_id = scraper.extract_sec_user_id(test_url)
        if not sec_user_id:
            print("❌ 无法提取 sec_user_id")
            return False
        
        print(f"✅ 成功提取 sec_user_id: {sec_user_id}")
        
        # 测试获取视频列表
        print(f"\n=== 测试获取视频列表 ===")
        result = scraper.fetch_user_videos(sec_user_id, max_cursor=0, count=5, retry_count=3)
        
        if not result:
            print("❌ 获取视频列表失败")
            return False
        
        aweme_list = result.get('aweme_list', [])
        print(f"✅ 成功获取 {len(aweme_list)} 个视频")
        
        if aweme_list:
            print(f"\n=== 第一个视频信息 ===")
            first_video = aweme_list[0]
            video_info = scraper.parse_video_info(first_video)
            
            for key, value in video_info.items():
                if key in ['title', 'author_name', 'aweme_id']:
                    print(f"{key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_anti_crawler_strategies():
    """测试反爬虫策略"""
    
    print("\n=== 测试反爬虫策略 ===")
    
    # 测试多次请求
    scraper = DouyinScraper()
    test_url = "https://www.douyin.com/user/MS4wLjABAAAAnAFnkWlOm9jteymsi42fanYLMzfbqdGIwCILEUqDNmFyjfK9N8fSJdS_D2UWk_we"
    sec_user_id = scraper.extract_sec_user_id(test_url)
    
    success_count = 0
    total_tests = 3
    
    for i in range(total_tests):
        print(f"\n--- 第 {i+1} 次请求测试 ---")
        
        try:
            result = scraper.fetch_user_videos(sec_user_id, max_cursor=0, count=3, retry_count=2)
            
            if result and result.get('aweme_list'):
                success_count += 1
                print(f"✅ 第 {i+1} 次请求成功，获取到 {len(result['aweme_list'])} 个视频")
            else:
                print(f"❌ 第 {i+1} 次请求失败或返回空结果")
            
            # 请求间隔
            if i < total_tests - 1:
                delay = random.uniform(3.0, 6.0)
                print(f"等待 {delay:.2f} 秒后进行下一次请求...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"❌ 第 {i+1} 次请求出错: {e}")
    
    success_rate = success_count / total_tests * 100
    print(f"\n=== 反爬虫测试结果 ===")
    print(f"成功率: {success_rate:.1f}% ({success_count}/{total_tests})")
    
    return success_rate >= 50  # 至少50%成功率

def main():
    """主函数"""
    
    print("GitHub Actions 环境增强测试开始...")
    
    # 测试1: 基本环境测试
    test1_result = test_github_actions_environment()
    
    # 测试2: 反爬虫策略测试
    test2_result = test_anti_crawler_strategies()
    
    print(f"\n=== 最终测试结果 ===")
    print(f"基本环境测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"反爬虫策略测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("🎉 所有测试通过！GitHub Actions 环境优化成功")
        return 0
    else:
        print("⚠️  部分测试失败，需要进一步优化")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)