#!/usr/bin/env python3
"""
简化的抖音API测试脚本
"""

from douyin_scraper import DouyinScraper
import sys

def test_api():
    print("=== 抖音API分页修复测试 ===")
    
    scraper = DouyinScraper()
    test_url = "https://www.douyin.com/user/MS4wLjABAAAAnAFnkWlOm9jteymsi42fanYLMzfbqdGIwCILEUqDNmFyjfK9N8fSJdS_D2UWk_we"