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
            'accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
    
    def fetch_user_videos(self, sec_user_id: str, max_cursor: int = 0, count: int = 20) -> Dict:
        """
        获取用户的视频列表
        """
        try:
            url = f"{self.api_base_url}/api/douyin/web/fetch_user_post_videos"
            params = {
                'sec_user_id': sec_user_id,
                'max_cursor': max_cursor,
                'count': count
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != 200:
                print(f"API返回错误: {data}")
                return {}
            
            return data.get('data', {})
            
        except Exception as e:
            print(f"获取视频列表时出错: {e}")
            return {}
    
    def fetch_all_videos(self, douyin_url: str, max_videos: int = 1000) -> List[Dict]:
        """
        获取用户的所有视频信息
        """
        sec_user_id = self.extract_sec_user_id(douyin_url)
        if not sec_user_id:
            return []
        
        all_videos = []
        max_cursor = 0
        has_more = True
        page_count = 0
        
        print(f"开始抓取用户视频，sec_user_id: {sec_user_id}")
        print(f"目标获取视频数量: {max_videos}")
        
        while has_more and len(all_videos) < max_videos:
            page_count += 1
            # 计算本次请求应该获取的数量
            remaining_videos = max_videos - len(all_videos)
            current_count = min(20, remaining_videos)  # 每次最多20条，但不超过剩余需要的数量
            
            print(f"第 {page_count} 页: 正在获取第 {len(all_videos) + 1} - {len(all_videos) + current_count} 个视频...")
            
            data = self.fetch_user_videos(sec_user_id, max_cursor, current_count)
            
            if not data:
                print("API返回空数据，停止抓取")
                break
            
            aweme_list = data.get('aweme_list', [])
            if not aweme_list:
                print("没有更多视频数据，停止抓取")
                break
            
            print(f"本页获取到 {len(aweme_list)} 个视频")
            
            # 处理视频信息
            for video in aweme_list:
                if len(all_videos) >= max_videos:
                    break
                video_info = self.parse_video_info(video)
                if video_info:
                    all_videos.append(video_info)
            
            # 更新游标和分页信息
            max_cursor = data.get('max_cursor', 0)
            has_more = data.get('has_more', 0) == 1
            
            print(f"当前已获取 {len(all_videos)} 个视频，has_more: {has_more}, max_cursor: {max_cursor}")
            
            # 如果已经达到目标数量，停止抓取
            if len(all_videos) >= max_videos:
                print(f"已达到目标数量 {max_videos}，停止抓取")
                break
            
            # 如果没有更多数据，停止抓取
            if not has_more:
                print("API返回 has_more=False，没有更多数据")
                break
            
            # 避免请求过于频繁
            time.sleep(1)
        
        print(f"抓取完成，共获取 {len(all_videos)} 个视频")
        return all_videos[:max_videos]  # 确保不超过指定数量
    
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
                'video_url': video_url,
                'cover_url': cover_url,
                'duration': duration
            }
            
        except Exception as e:
            print(f"解析视频信息时出错: {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    scraper = DouyinScraper()
    
    # 示例抖音链接
    test_url = "https://www.douyin.com/user/MS4wLjABAAAANXSltcLCzDGmdNFI2Q_QixVTr67NiYzjKOIP5s03CAE"
    
    videos = scraper.fetch_all_videos(test_url, max_videos=5)
    
    for i, video in enumerate(videos, 1):
        print(f"\n视频 {i}:")
        print(f"ID: {video.get('aweme_id')}")
        print(f"标题: {video.get('title')}")
        print(f"作者: {video.get('author_name')}")
        print(f"发布时间: {video.get('create_time')}")
        print(f"点赞数: {video.get('digg_count')}")
        print(f"评论数: {video.get('comment_count')}")