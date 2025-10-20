#!/usr/bin/env python3
"""
模拟GitHub Actions环境的测试脚本
用于诊断抖音爬虫在云环境下的问题
"""

import os
import sys
import subprocess
import time
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('github_actions_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_github_actions_environment():
    """设置模拟GitHub Actions的环境变量"""
    logger.info("=== 设置GitHub Actions模拟环境 ===")
    
    # 模拟GitHub Actions的环境变量
    github_actions_env = {
        # Python环境
        'pythonLocation': '/opt/hostedtoolcache/Python/3.9.24/x64',
        'PKG_CONFIG_PATH': '/opt/hostedtoolcache/Python/3.9.24/x64/lib/pkgconfig',
        'Python_ROOT_DIR': '/opt/hostedtoolcache/Python/3.9.24/x64',
        'Python2_ROOT_DIR': '/opt/hostedtoolcache/Python/3.9.24/x64',
        'Python3_ROOT_DIR': '/opt/hostedtoolcache/Python/3.9.24/x64',
        'LD_LIBRARY_PATH': '/opt/hostedtoolcache/Python/3.9.24/x64/lib',
        
        # GitHub Actions特有环境变量
        'GITHUB_ACTIONS': 'true',
        'CI': 'true',
        'RUNNER_OS': 'Linux',
        'RUNNER_ARCH': 'X64',
        'GITHUB_WORKFLOW': 'Douyin Sync',
        'GITHUB_RUN_ID': '18656286940',
        'GITHUB_RUN_NUMBER': '1',
        'GITHUB_REPOSITORY': 'k190513120/douyin_to_base',
        'GITHUB_ACTOR': 'k190513120',
        
        # 抖音相关环境变量
        'DOUYIN_URL': 'https://www.douyin.com/user/MS4wLjABAAAAnAFnkWlOm9jteymsi42fanYLMzfbqdGIwCILEUqDNmFyjfK9N8fSJdS_D2UWk_we',
        'MAX_VIDEOS': '50',
        
        # 清除可能影响的本地环境变量
        'HOME': '/github/home',
        'USER': 'runner',
        'SHELL': '/bin/bash',
        'TERM': 'xterm',
        'LANG': 'C.UTF-8',
        'LC_ALL': 'C.UTF-8',
    }
    
    # 设置环境变量
    for key, value in github_actions_env.items():
        os.environ[key] = value
        logger.debug(f"设置环境变量: {key}={value}")
    
    # 清除可能的本地配置
    local_vars_to_clear = ['DOUYIN_UIFID', 'FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'FEISHU_TABLE_ID']
    for var in local_vars_to_clear:
        if var in os.environ:
            del os.environ[var]
            logger.debug(f"清除本地环境变量: {var}")

def test_network_connectivity():
    """测试网络连接"""
    logger.info("=== 测试网络连接 ===")
    
    test_urls = [
        'https://www.douyin.com',
        'https://www.douyin.com/aweme/v1/web/aweme/post/',
        'https://github.com',
        'https://www.google.com'
    ]
    
    for url in test_urls:
        try:
            import requests
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            logger.info(f"✓ {url} - 状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"✗ {url} - 错误: {e}")

def test_douyin_scraper_import():
    """测试抖音爬虫模块导入"""
    logger.info("=== 测试模块导入 ===")
    
    try:
        from douyin_scraper import DouyinScraper
        logger.info("✓ DouyinScraper 导入成功")
        
        # 测试初始化
        scraper = DouyinScraper()
        logger.info(f"✓ DouyinScraper 初始化成功，uifid: {scraper.uifid[:50]}...")
        
        return scraper
    except Exception as e:
        logger.error(f"✗ DouyinScraper 导入/初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def test_sec_user_id_extraction(scraper):
    """测试sec_user_id提取"""
    logger.info("=== 测试sec_user_id提取 ===")
    
    if not scraper:
        logger.error("爬虫对象为空，跳过测试")
        return None
    
    test_url = os.environ.get('DOUYIN_URL')
    try:
        sec_user_id = scraper.extract_sec_user_id(test_url)
        logger.info(f"✓ 提取sec_user_id成功: {sec_user_id}")
        return sec_user_id
    except Exception as e:
        logger.error(f"✗ 提取sec_user_id失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def test_single_request(scraper, sec_user_id):
    """测试单个API请求"""
    logger.info("=== 测试单个API请求 ===")
    
    if not scraper or not sec_user_id:
        logger.error("爬虫对象或sec_user_id为空，跳过测试")
        return
    
    try:
        logger.info("开始发送API请求...")
        result = scraper.fetch_user_videos(sec_user_id, max_cursor=0, count=1, retry_count=1)
        
        if result:
            logger.info(f"✓ API请求成功，返回数据键: {list(result.keys())}")
            if 'aweme_list' in result:
                logger.info(f"✓ 获取到 {len(result['aweme_list'])} 个视频")
        else:
            logger.error("✗ API请求返回空结果")
            
    except Exception as e:
        logger.error(f"✗ API请求失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

def test_main_script():
    """测试主脚本执行"""
    logger.info("=== 测试主脚本执行 ===")
    
    try:
        # 构建命令
        cmd = [
            sys.executable, 'main.py',
            '--url', os.environ.get('DOUYIN_URL'),
            '--max-videos', os.environ.get('MAX_VIDEOS', '5')  # 减少数量以快速测试
        ]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        # 执行命令并捕获输出
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60秒超时
            cwd=os.getcwd()
        )
        end_time = time.time()
        
        logger.info(f"命令执行时间: {end_time - start_time:.2f}秒")
        logger.info(f"返回码: {result.returncode}")
        
        if result.stdout:
            logger.info("=== 标准输出 ===")
            logger.info(result.stdout)
        
        if result.stderr:
            logger.error("=== 标准错误 ===")
            logger.error(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        logger.error("✗ 主脚本执行超时")
        return False
    except Exception as e:
        logger.error(f"✗ 主脚本执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("开始GitHub Actions环境诊断测试")
    logger.info(f"测试时间: {datetime.now()}")
    logger.info("=" * 60)
    
    # 1. 设置环境
    setup_github_actions_environment()
    
    # 2. 测试网络连接
    test_network_connectivity()
    
    # 3. 测试模块导入
    scraper = test_douyin_scraper_import()
    
    # 4. 测试sec_user_id提取
    sec_user_id = test_sec_user_id_extraction(scraper)
    
    # 5. 测试单个API请求
    test_single_request(scraper, sec_user_id)
    
    # 6. 测试主脚本
    main_success = test_main_script()
    
    logger.info("=" * 60)
    logger.info("诊断测试完成")
    logger.info(f"主脚本执行: {'成功' if main_success else '失败'}")
    logger.info("详细日志已保存到 github_actions_debug.log")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()