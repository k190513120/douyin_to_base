#!/usr/bin/env python3
import sys
import os

print("Python版本:", sys.version)
print("当前目录:", os.getcwd())

try:
    import requests
    print("✓ requests 导入成功")
except ImportError as e:
    print("✗ requests 导入失败:", e)
    sys.exit(1)

try:
    from douyin_scraper import DouyinScraper
    print("✓ DouyinScraper 导入成功")
    
    scraper = DouyinScraper()
    print("✓ DouyinScraper 初始化成功")
    
    # 测试简单的网络请求
    response = requests.get("https://www.douyin.com", timeout=10)
    print(f"✓ 网络请求成功，状态码: {response.status_code}")
    
except Exception as e:
    print("✗ 测试失败:", e)
    sys.exit(1)

print("✓ 所有测试通过")
