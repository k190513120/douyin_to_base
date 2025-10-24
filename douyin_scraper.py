import requests
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs


class DouyinScraper:
    def __init__(self, api_base_url: str = "https://tiktok-api-miaomiaocompany-c35bd5a6.koyeb.app"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': 'https://www.douyin.com/',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        })
    
    def extract_sec_user_id(self, douyin_url: str) -> Optional[str]:
        """
        从抖音主页链接中提取sec_user_id
        支持多种抖音链接格式
        """
        try:
            # 如果是短链接，先获取重定向后的完整链接
            if 'v.douyin.com' in douyin_url or 'iesdouyin.com' in douyin_url:
                response = self.session.head(douyin_url, allow_redirects=True)
                douyin_url = response.url
            
            # 从URL中提取sec_user_id
            patterns = [
                r'sec_user_id=([^&]+)',
                r'/user/([^/?]+)',
                r'sec_uid=([^&]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, douyin_url)
                if match:
                    return match.group(1)
            
            print(f"无法从URL中提取sec_user_id: {douyin_url}")
            return None
            
        except Exception as e:
            print(f"提取sec_user_id时出错: {e}")
            return None
    
    def fetch_user_videos(self, sec_user_id: str, max_cursor: int = 0, count: int = 20, retry_count: int = 0) -> Dict:
        """
        获取用户的视频列表
        """
        try:
            url = f"{self.api_base_url}/api/douyin/web/fetch_user_post_videos"
            
            # 尝试不同的参数组合
            params_variations = [
                # 标准参数
                {
                    'sec_user_id': sec_user_id,
                    'max_cursor': max_cursor,
                    'count': count
                },
                # 添加更多参数
                {
                    'sec_user_id': sec_user_id,
                    'max_cursor': max_cursor,
                    'count': count,
                    'cut_version': '1',
                    'req_real_time': '1'
                },
                # 使用字符串格式的cursor
                {
                    'sec_user_id': sec_user_id,
                    'max_cursor': str(max_cursor),
                    'count': count,
                    'publish_video_strategy_type': '2'
                }
            ]
            
            params = params_variations[min(retry_count, len(params_variations) - 1)]
            
            print(f"[DEBUG] API请求参数 (尝试 {retry_count + 1}): {params}")
            print(f"[DEBUG] 请求URL: {url}")
            print(f"[DEBUG] 请求Headers: {dict(self.session.headers)}")
            
            response = self.session.get(url, params=params, timeout=30)
            print(f"[DEBUG] HTTP状态码: {response.status_code}")
            print(f"[DEBUG] 响应Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            data = response.json()
            
            print(f"[DEBUG] API响应状态码: {data.get('code')}")
            print(f"[DEBUG] API响应消息: {data.get('message', 'N/A')}")
            print(f"[DEBUG] 完整响应: {data}")
            
            if data.get('code') != 200:
                print(f"API返回错误: {data}")
                # 如果是第一次尝试且失败，尝试其他参数组合
                if retry_count < 2:
                    print(f"尝试不同的参数组合...")
                    time.sleep(3)  # 增加延迟
                    return self.fetch_user_videos(sec_user_id, max_cursor, count, retry_count + 1)
                return {}
            
            result_data = data.get('data', {})
            
            # 添加详细的调试信息
            aweme_list = result_data.get('aweme_list', [])
            has_more = result_data.get('has_more', 0)
            max_cursor_new = result_data.get('max_cursor', 0)
            
            print(f"[DEBUG] 返回视频数量: {len(aweme_list)}")
            print(f"[DEBUG] has_more: {has_more}")
            print(f"[DEBUG] max_cursor: {max_cursor_new}")
            print(f"[DEBUG] 完整响应数据键: {list(result_data.keys())}")
            
            # 如果返回空数据但之前有数据，尝试重试
            if len(aweme_list) == 0 and max_cursor > 0 and retry_count < 2:
                print(f"[WARNING] 返回空数据，尝试重试...")
                time.sleep(5)  # 更长的延迟
                return self.fetch_user_videos(sec_user_id, max_cursor, count, retry_count + 1)
            
            return result_data
            
        except Exception as e:
            print(f"获取视频列表时出错: {e}")
            # 重试机制
            if retry_count < 2:
                print(f"网络错误，{3}秒后重试...")
                time.sleep(3)
                return self.fetch_user_videos(sec_user_id, max_cursor, count, retry_count + 1)
            return {}
    
    def fetch_all_videos(self, douyin_url: str, max_videos: int = 1000) -> List[Dict]:
        """
        获取用户的视频信息 - 简化版本，直接一次性获取指定数量
        """
        sec_user_id = self.extract_sec_user_id(douyin_url)
        if not sec_user_id:
            return []
        
        print(f"开始抓取用户视频，sec_user_id: {sec_user_id}")
        print(f"目标获取视频数量: {max_videos}")
        print(f"使用简化逻辑，一次性请求 {max_videos} 个视频...")
        
        # 直接使用用户指定的数量作为count参数，一次性获取
        data = self.fetch_user_videos(sec_user_id, max_cursor=0, count=max_videos)
        
        if not data:
            print("API返回空数据")
            return []
        
        aweme_list = data.get('aweme_list', [])
        if not aweme_list:
            print("没有获取到视频数据")
            return []
        
        print(f"API返回 {len(aweme_list)} 个视频")
        
        # 处理视频信息
        all_videos = []
        for video in aweme_list:
            video_info = self.parse_video_info(video)
            if video_info:
                all_videos.append(video_info)
        
        print(f"成功解析 {len(all_videos)} 个视频信息")
        return all_videos
    
    def parse_video_info(self, video_data: Dict) -> Dict:
        """
        解析视频信息，提取需要的字段
        """
        try:
            # 获取视频基本信息
            aweme_id = video_data.get('aweme_id', '')
            desc = video_data.get('desc', '')
            create_time = video_data.get('create_time', 0)
            
            # 获取作者信息
            author = video_data.get('author', {})
            author_name = author.get('nickname', '')
            author_uid = author.get('uid', '')
            
            # 获取统计信息
            statistics = video_data.get('statistics', {})
            digg_count = statistics.get('digg_count', 0)  # 点赞数
            comment_count = statistics.get('comment_count', 0)  # 评论数
            share_count = statistics.get('share_count', 0)  # 分享数
            play_count = statistics.get('play_count', 0)  # 播放数
            collect_count = statistics.get('collect_count', 0)  # 收藏数
            
            # 获取视频URL
            video_url = ''
            video = video_data.get('video', {})
            if video:
                play_addr = video.get('play_addr', {})
                url_list = play_addr.get('url_list', [])
                if url_list:
                    video_url = url_list[0]
            
            # 获取封面图片
            cover_url = ''
            if video:
                cover = video.get('cover', {})
                url_list = cover.get('url_list', [])
                if url_list:
                    cover_url = url_list[0]
            
            # 获取视频时长
            duration = 0
            if video:
                duration = video.get('duration', 0)
            
            # 转换时间戳为可读格式
            create_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(create_time))
            
            return {
                'aweme_id': aweme_id,
                'title': desc,
                'author_name': author_name,
                'author_uid': author_uid,
                'create_time': create_time_str,
                'create_timestamp': create_time,
                'digg_count': digg_count,
                'comment_count': comment_count,
                'share_count': share_count,
                'play_count': play_count,
                'collect_count': collect_count,
                'video_url': video_url,
                'cover_url': cover_url,
                'duration': duration
            }
            
        except Exception as e:
            print(f"解析视频信息时出错: {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    print("开始测试抖音API分页修复...")
    scraper = DouyinScraper()
    
    # 示例抖音链接
    test_url = "https://www.douyin.com/user/MS4wLjABAAAAnAFnkWlOm9jteymsi42fanYLMzfbqdGIwCILEUqDNmFyjfK9N8fSJdS_D2UWk_we"
    
    try:
        videos = scraper.fetch_all_videos(test_url, max_videos=50)
        print(f"\n=== 测试结果 ===")
        print(f"总共获取到 {len(videos)} 个视频")
        
        for i, video in enumerate(videos[:5], 1):
            print(f"\n视频 {i}:")
            print(f"ID: {video.get('aweme_id')}")
            print(f"标题: {video.get('title')}")
            print(f"作者: {video.get('author_name')}")
            print(f"发布时间: {video.get('create_time')}")
            print(f"点赞数: {video.get('digg_count')}")
            print(f"评论数: {video.get('comment_count')}")
            
        if len(videos) > 5:
            print(f"\n... 还有 {len(videos) - 5} 个视频未显示")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()