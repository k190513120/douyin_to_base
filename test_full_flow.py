#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整流程：抖音数据抓取 + 飞书多维表格写入
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv
from douyin_scraper import DouyinScraper
from feishu_writer import FeishuWriter, BaseConfig

def test_full_flow():
    """测试完整流程"""
    print("=== 开始测试完整流程 ===")
    
    # 加载环境变量
    load_dotenv(find_dotenv())
    
    # 检查环境变量
    APP_TOKEN = os.environ.get('APP_TOKEN')
    PERSONAL_BASE_TOKEN = os.environ.get('PERSONAL_BASE_TOKEN')
    TABLE_ID = os.environ.get('TABLE_ID')
    
    if not all([APP_TOKEN, PERSONAL_BASE_TOKEN, TABLE_ID]):
        print("❌ 请先配置飞书环境变量")
        return False
    
    # 1. 测试抖音数据抓取
    print("\n1. 测试抖音数据抓取...")
    scraper = DouyinScraper()
    test_url = "https://www.douyin.com/user/MS4wLjABAAAAnAFnkWlOm9jteymsi42fanYLMzfbqdGIwCILEUqDNmFyjfK9N8fSJdS_D2UWk_we"
    
    try:
        # 获取更多视频进行测试
        videos = scraper.fetch_all_videos(test_url, max_videos=15)
        print(f"✅ 成功获取 {len(videos)} 个视频")
        
        # 显示第一个视频的详细信息
        if videos:
            video = videos[0]
            print(f"\n📹 第一个视频信息:")
            print(f"   ID: {video.get('aweme_id')}")
            print(f"   标题: {video.get('title')}")
            print(f"   作者: {video.get('author_name')}")
            print(f"   点赞数: {video.get('digg_count')}")
            print(f"   分享数: {video.get('share_count')}")
            print(f"   封面URL: {video.get('cover_url')[:50]}..." if video.get('cover_url') else "   封面URL: 无")
            print(f"   播放URL: {video.get('play_url')[:50]}..." if video.get('play_url') else "   播放URL: 无")
            print(f"   播放URL: {video.get('play_url')[:50]}..." if video.get('play_url') else "   播放URL: 无")
        
    except Exception as e:
        print(f"❌ 抖音数据抓取失败: {e}")
        return False
    
    # 2. 测试飞书多维表格写入
    print("\n2. 测试飞书多维表格写入...")
    
    try:
        # 配置飞书写入器
        config = BaseConfig(
            app_token=APP_TOKEN,
            personal_base_token=PERSONAL_BASE_TOKEN,
            table_id=TABLE_ID,
            region='domestic'
        )
        
        writer = FeishuWriter(config)
        
        # 批量写入视频数据
        result = writer.batch_create_records(videos)
        
        print(f"✅ 飞书写入完成:")
        print(f"   总数: {result['total']}")
        print(f"   成功: {result['success_count']}")
        print(f"   跳过: {result['skipped_count']}")
        print(f"   失败: {result['failed_count']}")
        
        # 显示详细结果
        for detail in result['details']:
            status_emoji = "✅" if detail['status'] == 'success' else "⏭️" if detail['status'] == 'skipped' else "❌"
            reason = f" ({detail.get('reason', '')})" if detail.get('reason') else ""
            print(f"   {status_emoji} {detail['aweme_id']}: {detail['status']}{reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ 飞书写入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_flow()
    if success:
        print("\n🎉 完整流程测试成功！")
    else:
        print("\n💥 完整流程测试失败！")
        sys.exit(1)