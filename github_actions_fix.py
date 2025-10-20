#!/usr/bin/env python3
"""
GitHub Actions环境修复脚本
用于诊断和修复GitHub Actions环境下的依赖和配置问题
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('github_actions_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_python_environment():
    """检查Python环境"""
    logger.info("=== 检查Python环境 ===")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"Python路径: {sys.executable}")
    logger.info(f"当前工作目录: {os.getcwd()}")
    
    # 检查pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        logger.info(f"pip版本: {result.stdout.strip()}")
    except Exception as e:
        logger.error(f"pip检查失败: {e}")

def check_installed_packages():
    """检查已安装的包"""
    logger.info("=== 检查已安装的包 ===")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        logger.info("已安装的包:")
        for line in result.stdout.split('\n')[:20]:  # 只显示前20行
            if line.strip():
                logger.info(f"  {line}")
    except Exception as e:
        logger.error(f"包列表检查失败: {e}")

def install_requirements():
    """安装依赖"""
    logger.info("=== 安装依赖 ===")
    
    # 检查requirements.txt是否存在
    if not os.path.exists('requirements.txt'):
        logger.error("requirements.txt文件不存在")
        return False
    
    try:
        # 升级pip
        logger.info("升级pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True)
        
        # 安装依赖
        logger.info("安装requirements.txt中的依赖...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True, check=True)
        logger.info("依赖安装成功")
        logger.info(f"安装输出: {result.stdout}")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"依赖安装失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return False

def test_imports():
    """测试关键模块导入"""
    logger.info("=== 测试模块导入 ===")
    
    modules_to_test = ['requests', 'dotenv', 'json', 'os', 'sys']
    
    for module in modules_to_test:
        try:
            if module == 'dotenv':
                __import__('dotenv')
            else:
                __import__(module)
            logger.info(f"✓ {module} 导入成功")
        except ImportError as e:
            logger.error(f"✗ {module} 导入失败: {e}")

def test_douyin_scraper():
    """测试DouyinScraper导入和初始化"""
    logger.info("=== 测试DouyinScraper ===")
    
    try:
        from douyin_scraper import DouyinScraper
        logger.info("✓ DouyinScraper 导入成功")
        
        # 测试初始化
        scraper = DouyinScraper()
        logger.info("✓ DouyinScraper 初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ DouyinScraper 测试失败: {e}")
        return False

def create_minimal_test():
    """创建最小化测试脚本"""
    logger.info("=== 创建最小化测试 ===")
    
    test_script = '''#!/usr/bin/env python3
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
'''
    
    with open('minimal_test.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    logger.info("最小化测试脚本已创建: minimal_test.py")

def main():
    """主函数"""
    logger.info("============================================================")
    logger.info("GitHub Actions环境修复开始")
    logger.info(f"修复时间: {datetime.now()}")
    logger.info("============================================================")
    
    # 1. 检查Python环境
    check_python_environment()
    
    # 2. 检查已安装的包
    check_installed_packages()
    
    # 3. 安装依赖
    if not install_requirements():
        logger.error("依赖安装失败，退出")
        sys.exit(1)
    
    # 4. 再次检查已安装的包
    check_installed_packages()
    
    # 5. 测试模块导入
    test_imports()
    
    # 6. 测试DouyinScraper
    if not test_douyin_scraper():
        logger.error("DouyinScraper测试失败")
    
    # 7. 创建最小化测试
    create_minimal_test()
    
    logger.info("============================================================")
    logger.info("GitHub Actions环境修复完成")
    logger.info("============================================================")

if __name__ == "__main__":
    main()