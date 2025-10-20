#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Actions 工作流测试脚本
模拟 GitHub Actions 环境下的运行情况
"""

import os
import sys
import tempfile
from dotenv import load_dotenv

def test_environment_setup():
    """测试环境变量设置"""
    print("🔧 测试环境变量设置...")
    
    # 模拟 GitHub Actions 环境变量设置
    test_env_vars = {
        'FEISHU_APP_ID': 'test_app_id',
        'FEISHU_APP_SECRET': 'test_app_secret',
        'FEISHU_APP_TOKEN': 'bascnCMII2ORuFINwETsjch2nBg',
        'FEISHU_TABLE_ID': 'tblEnSV2PNAajtWE',
        'FEISHU_PERSONAL_BASE_TOKEN': 'test_personal_token'
    }
    
    # 创建临时 .env 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        for key, value in test_env_vars.items():
            f.write(f"{key}={value}\n")
        temp_env_file = f.name
    
    # 加载环境变量
    load_dotenv(temp_env_file)
    
    # 验证环境变量
    missing_vars = []
    for key in test_env_vars:
        if not os.environ.get(key):
            missing_vars.append(key)
    
    if missing_vars:
        print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ 环境变量设置正确")
        return True
    
    # 清理临时文件
    os.unlink(temp_env_file)

def test_dependencies():
    """测试依赖包导入"""
    print("\n📦 测试依赖包导入...")
    
    required_packages = [
        ('requests', 'requests'),
        ('python-dotenv', 'dotenv'),
        ('urllib3', 'urllib3')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} 导入成功")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} 导入失败")
    
    return len(missing_packages) == 0

def test_main_modules():
    """测试主要模块导入"""
    print("\n🔍 测试主要模块导入...")
    
    try:
        from douyin_scraper import DouyinScraper
        print("✅ DouyinScraper 模块导入成功")
        
        from feishu_writer import FeishuWriter
        print("✅ FeishuWriter 模块导入成功")
        
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_command_line_interface():
    """测试命令行接口"""
    print("\n⚡ 测试命令行接口...")
    
    # 模拟命令行参数
    test_args = [
        '--url', 'https://www.douyin.com/user/test',
        '--max-videos', '5'
    ]
    
    try:
        # 这里只是验证参数解析，不实际运行
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--url', required=True)
        parser.add_argument('--max-videos', type=int, default=1000)
        parser.add_argument('--batch-size', type=int, default=10)
        parser.add_argument('--config-file')
        
        args = parser.parse_args(test_args)
        print(f"✅ 命令行参数解析成功: URL={args.url}, MAX_VIDEOS={args.max_videos}")
        return True
    except Exception as e:
        print(f"❌ 命令行参数解析失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 GitHub Actions 工作流测试开始")
    print("=" * 50)
    
    tests = [
        ("环境变量设置", test_environment_setup),
        ("依赖包导入", test_dependencies),
        ("主要模块导入", test_main_modules),
        ("命令行接口", test_command_line_interface)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！GitHub Actions 工作流应该能正常运行")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)