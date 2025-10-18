#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：分析抖音数据准确性问题
"""

import json
import sys
from douyin_scraper import DouyinScraper
from feishu_writer import FeishuWriter, BaseConfig, DouyinDataTypeMapper
import os
from dotenv import load_dotenv, find_dotenv

def print_json_pretty(data, title="数据"):
    """美化打印JSON数据"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"{'='*50}\n")

def analyze_single_video(url, max_videos=1):
    """分析单个视频的数据准确性"""
    
    # 1. 抓取原始数据
    print("🔍 开始抓取抖音数据...")
    scraper = DouyinScraper()
    videos_data = scraper.fetch_all_videos(url, max_videos=max_videos)
    
    if not videos_data:
        print("❌ 没有抓取到任何数据")
        return
    
    print(f"✅ 成功抓取到 {len(videos_data)} 条数据")
    
    # 2. 分析第一条数据
    video_data = videos_data[0]
    print_json_pretty(video_data, "原始抖音数据结构")
    
    # 3. 分析数据字段
    print("\n📊 数据字段分析:")
    print("-" * 50)
    
    def analyze_nested_dict(data, prefix="", level=0):
        """递归分析嵌套字典结构"""
        indent = "  " * level
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                print(f"{indent}{key}: (dict, {len(value)} keys)")
                if level < 2:  # 限制递归深度
                    analyze_nested_dict(value, full_key, level + 1)
            elif isinstance(value, list):
                print(f"{indent}{key}: (list, {len(value)} items)")
                if value and isinstance(value[0], dict) and level < 2:
                    print(f"{indent}  └─ 第一个元素:")
                    analyze_nested_dict(value[0], f"{full_key}[0]", level + 2)
            else:
                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"{indent}{key}: {type(value).__name__} = {value_str}")
    
    analyze_nested_dict(video_data)
    
    # 4. 模拟飞书写入器的数据处理
    print("\n🔄 模拟数据处理过程:")
    print("-" * 50)
    
    # 加载配置
    load_dotenv(find_dotenv())
    config = BaseConfig(
        app_token=os.environ.get('APP_TOKEN'),
        personal_base_token=os.environ.get('PERSONAL_BASE_TOKEN'),
        table_id=os.environ.get('TABLE_ID'),
        region='domestic'
    )
    
    writer = FeishuWriter(config)
    processed_fields = writer._prepare_record_fields(video_data)
    
    print_json_pretty(processed_fields, "处理后的字段数据")
    
    # 5. 对比分析
    print("\n🔍 数据准确性对比分析:")
    print("-" * 50)
    
    # 检查关键字段的映射（使用与feishu_writer相同的逻辑）
    key_mappings = {
        'aweme_id': video_data.get('aweme_id'),
        'desc': video_data.get('title', '') or video_data.get('desc', ''),
        'create_time': video_data.get('create_time'),
        'author_nickname': video_data.get('author_name', '') or video_data.get('author', {}).get('nickname', ''),
        'author_unique_id': video_data.get('author', {}).get('unique_id'),
        'author_uid': video_data.get('author_uid', '') or video_data.get('author', {}).get('uid', ''),
        'digg_count': video_data.get('digg_count', 0) or video_data.get('statistics', {}).get('digg_count', 0),
        'comment_count': video_data.get('comment_count', 0) or video_data.get('statistics', {}).get('comment_count', 0),
        'share_count': video_data.get('share_count', 0) or video_data.get('statistics', {}).get('share_count', 0),
        'play_count': video_data.get('play_count', 0) or video_data.get('statistics', {}).get('play_count', 0),
        'collect_count': video_data.get('collect_count', 0) or video_data.get('statistics', {}).get('collect_count', 0),
    }
    
    print("字段映射对比:")
    for field_name, original_value in key_mappings.items():
        processed_value = processed_fields.get(field_name)
        converted_value = DouyinDataTypeMapper.convert_value(field_name, original_value)
        
        print(f"\n{field_name}:")
        print(f"  原始值: {original_value} ({type(original_value).__name__})")
        print(f"  处理值: {processed_value} ({type(processed_value).__name__})")
        print(f"  转换值: {converted_value} ({type(converted_value).__name__})")
        
        if str(original_value) != str(processed_value):
            print(f"  ⚠️  数据不一致!")
    
    # 6. 检查视频和封面URL
    print(f"\n媒体URL分析:")
    video_url_original = writer._extract_video_url(video_data)
    cover_url_original = writer._extract_cover_url(video_data)
    
    print(f"视频URL: {video_url_original}")
    print(f"封面URL: {cover_url_original}")
    
    # 7. 检查时间格式
    if 'create_time' in video_data:
        create_time = video_data['create_time']
        print(f"\n时间格式分析:")
        print(f"原始时间: {create_time} ({type(create_time).__name__})")
        
        converted_time = DouyinDataTypeMapper.convert_value('create_time', create_time)
        print(f"转换时间: {converted_time} ({type(converted_time).__name__})")
    
    return video_data, processed_fields

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python debug_data.py <抖音用户URL>")
        print("示例: python debug_data.py 'https://www.douyin.com/user/MS4wLjABAAAAZOOYD9flTg8JWjfjM5EmEgRgte_SJQ9Kp3YrtasgHJgEHK6wI0YKhSwQBDZQFDW6'")
        return
    
    url = sys.argv[1]
    analyze_single_video(url, max_videos=1)

if __name__ == "__main__":
    main()