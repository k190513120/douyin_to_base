#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse

# 尝试导入dotenv，如果失败则跳过
try:
    from dotenv import load_dotenv, find_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available, using environment variables directly")

from douyin_scraper import DouyinScraper
from feishu_writer import FeishuWriter


def load_config():
    """
    加载配置信息
    """
    if DOTENV_AVAILABLE:
        load_dotenv(find_dotenv())
    
    config = {
        'app_token': os.environ.get('FEISHU_APP_TOKEN') or os.environ.get('APP_TOKEN'),
        'personal_base_token': os.environ.get('FEISHU_PERSONAL_BASE_TOKEN') or os.environ.get('PERSONAL_BASE_TOKEN'),
        'table_id': os.environ.get('FEISHU_TABLE_ID') or os.environ.get('TABLE_ID'),
        'douyin_api_base_url': os.environ.get('DOUYIN_API_BASE_URL', 
                                            'https://tiktok-api-miaomiaocompany-c35bd5a6.koyeb.app')
    }
    
    return config


def validate_config(config):
    """
    验证配置信息
    """
    required_fields = ['app_token', 'personal_base_token', 'table_id']
    missing_fields = []
    
    for field in required_fields:
        if not config.get(field):
            missing_fields.append(field.upper())
    
    if missing_fields:
        print(f"错误: 缺少必要的环境变量: {', '.join(missing_fields)}")
        print("请检查 .env 文件或环境变量配置")
        return False
    
    return True


def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description='抖音视频信息抓取并同步到飞书多维表格',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --url "https://www.douyin.com/user/xxx" --max-videos 100
  python main.py --url "https://v.douyin.com/xxx" --max-videos 50
  
环境变量配置:
  APP_TOKEN: 飞书多维表格的APP_TOKEN
  PERSONAL_BASE_TOKEN: 飞书个人访问令牌
  TABLE_ID: 多维表格的TABLE_ID
        """
    )
    
    parser.add_argument(
        '--url',
        required=True,
        help='抖音博主的主页地址'
    )
    
    parser.add_argument(
        '--max-videos',
        type=int,
        default=1000,
        help='最大抓取视频数量 (默认: 1000)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='批量写入的批次大小 (默认: 10)'
    )
    
    parser.add_argument(
        '--config-file',
        help='指定配置文件路径 (可选)'
    )
    
    return parser.parse_args()


def interactive_input():
    """
    交互式输入模式
    """
    print("=== 抖音视频信息抓取工具 ===\n")
    
    # 输入抖音链接
    douyin_url = input("请输入抖音博主的主页地址: ").strip()
    if not douyin_url:
        print("错误: 抖音链接不能为空")
        return None
    
    # 输入最大视频数量
    try:
        max_videos_input = input("请输入最大抓取视频数量 (默认1000): ").strip()
        max_videos = int(max_videos_input) if max_videos_input else 1000
    except ValueError:
        print("使用默认值: 1000")
        max_videos = 1000
    
    return {
        'url': douyin_url,
        'max_videos': max_videos,
        'batch_size': 10
    }


def main():
    """
    主函数
    """
    print("抖音视频信息抓取工具 v1.0")
    print("=" * 50)
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        args = parse_arguments()
        params = {
            'url': args.url,
            'max_videos': args.max_videos,
            'batch_size': args.batch_size
        }
    else:
        # 交互式输入
        params = interactive_input()
        if not params:
            return 1
    
    # 加载配置
    config = load_config()
    if not validate_config(config):
        return 1
    
    try:
        # 初始化抖音抓取器
        print(f"\n1. 初始化抖音抓取器...")
        scraper = DouyinScraper()  # 移除错误的参数，使用默认的uifid
        
        # 抓取视频信息
        print(f"2. 开始抓取视频信息...")
        print(f"   - 抖音链接: {params['url']}")
        print(f"   - 最大视频数: {params['max_videos']}")
        
        videos = scraper.fetch_all_videos(params['url'], params['max_videos'])
        
        if not videos:
            print("错误: 未能获取到任何视频信息")
            return 1
        
        print(f"   - 成功获取 {len(videos)} 个视频信息")
        
        # 初始化飞书写入器
        print(f"\n3. 初始化飞书多维表格写入器...")
        from feishu_writer import BaseConfig
        feishu_config = BaseConfig(
            app_token=config['app_token'],
            personal_base_token=config['personal_base_token'],
            table_id=config['table_id'],
            region='domestic'
        )
        writer = FeishuWriter(feishu_config)
        
        # 批量写入数据
        print(f"4. 开始写入飞书多维表格...")
        result = writer.batch_create_records(videos, params['batch_size'])
        
        # 显示结果
        print(f"\n5. 同步完成!")
        print(f"   - 总计处理: {result['total']} 条记录")
        print(f"   - 成功写入: {result['success_count']} 条记录")
        print(f"   - 跳过重复: {result['skipped_count']} 条记录")
        print(f"   - 写入失败: {result['failed_count']} 条记录")
        
        if result['failed_count'] > 0:
            print(f"\n注意: 有 {result['failed_count']} 条记录写入失败，请检查日志")
            return 1
        
        print("\n✅ 所有操作完成!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        return 1
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)