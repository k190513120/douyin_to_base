import requests
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs


class DouyinScraper:
    def __init__(self, uifid: str = None):
        # 使用抖音官方接口，不再依赖第三方API
        self.douyin_api_url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
        self.uifid = uifid or self._get_default_uifid()
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'uifid': self.uifid,
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        })
    
    def _get_default_uifid(self) -> str:
        """
        获取默认的uifid，可以从环境变量或配置文件中读取
        如果没有配置，使用用户提供的uifid
        """
        import os
        return os.getenv('DOUYIN_UIFID', '9e5c45806baed1121aef2e4ebdb50ae0783a7b9267143d29acaade7dde1bacd57f38b71be96aa0bff47a3f2074178a779ca220a333bd33fcf42e1ba5b397a819cbec2844ea96dc486dcf6360403bbf76f0291d77a3d69a29e56c0e467bbe9c0e46337ece433506542ae444dc2127f40bbe70a4d3f18f02f002a4309ca11a256633fa839151f3a7c4f8b9232ad2335937d7d15091c9acff5412f86dd1821e150ecbab849028d577aee3a88780b0c05199')
    
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
        使用抖音官方接口获取用户的视频列表
        """
        try:
            url = self.douyin_api_url
            
            params = {
                "aid": "6383",
                "sec_user_id": sec_user_id,
                "max_cursor": max_cursor,
                "publish_video_strategy_type": "2",
                "count": str(count)
            }
            
            print(f"[DEBUG] 爬虫请求参数: {params}")
            print(f"[DEBUG] 请求URL: {url}")
            print(f"[DEBUG] uifid: {self.uifid}")
            
            response = self.session.get(url, params=params, timeout=30)
            print(f"[DEBUG] HTTP状态码: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            
            print(f"[DEBUG] 爬虫响应状态码: {data.get('status_code', 'N/A')}")
            print(f"[DEBUG] 响应数据键: {list(data.keys())}")
            
            # 抖音官方接口的响应结构
            if data.get('status_code') != 0:
                print(f"抖音接口返回错误: {data}")
                return {}
            
            # 添加详细的调试信息
            aweme_list = data.get('aweme_list', [])
            has_more = data.get('has_more', 0)
            max_cursor_new = data.get('max_cursor', 0)
            
            print(f"[DEBUG] 返回视频数量: {len(aweme_list)}")
            print(f"[DEBUG] has_more: {has_more}")
            print(f"[DEBUG] max_cursor: {max_cursor_new}")
            
            return data
            
        except Exception as e:
            print(f"获取视频列表时出错: {e}")
            return {}
    
    def fetch_all_videos(self, douyin_url: str, max_videos: int = 1000) -> List[Dict]:
        """
        获取用户的视频信息 - 使用分页逻辑获取更多数据
        """
        sec_user_id = self.extract_sec_user_id(douyin_url)
        if not sec_user_id:
            return []
        
        print(f"开始抓取用户视频，sec_user_id: {sec_user_id}")
        print(f"目标获取视频数量: {max_videos}")
        print(f"使用爬虫分页逻辑获取数据...")
        
        all_videos = []
        has_more = 1
        max_cursor = 0
        page = 1
        
        while has_more == 1 and len(all_videos) < max_videos:
            print(f"\n--- 获取第 {page} 页数据 ---")
            
            # 每页获取20个视频
            count = min(20, max_videos - len(all_videos))
            data = self.fetch_user_videos(sec_user_id, max_cursor=max_cursor, count=count)
            
            if not data:
                print("接口返回空数据，停止获取")
                break
            
            aweme_list = data.get('aweme_list', [])
            if not aweme_list:
                print("没有获取到视频数据，停止获取")
                break
            
            print(f"第 {page} 页获取到 {len(aweme_list)} 个视频")
            
            # 处理视频信息
            for video in aweme_list:
                video_info = self.parse_video_info(video)
                if video_info:
                    all_videos.append(video_info)
            
            # 更新分页参数
            has_more = data.get('has_more', 0)
            max_cursor = data.get('max_cursor', 0)
            page += 1
            
            print(f"当前已获取 {len(all_videos)} 个视频，has_more: {has_more}")
            
            # 如果没有更多数据，停止获取
            if has_more != 1:
                print("没有更多数据，停止获取")
                break
            
            # 添加延迟避免请求过快
            time.sleep(2)
        
        print(f"\n=== 获取完成 ===")
        print(f"成功获取 {len(all_videos)} 个视频信息")
        return all_videos
    
    def parse_video_info(self, video_data: Dict) -> Dict:
        """
        解析视频信息，提取需要的字段，适配爬虫数据结构
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
            collect_count = statistics.get('collect_count', 0)  # 收藏数
            play_count = statistics.get('play_count', 0)  # 播放数
            
            # 获取视频封面
            cover_url = ''
            video = video_data.get('video', {})
            if video:
                cover = video.get('cover', {})
                url_list = cover.get('url_list', [])
                if url_list:
                    cover_url = url_list[0]
            
            # 获取音乐播放链接
            play_url = ''
            music = video_data.get('music', {})
            if music:
                play_addr = music.get('play_url', {})
                if isinstance(play_addr, dict):
                    uri = play_addr.get('uri', '')
                    if uri:
                        play_url = uri
                elif isinstance(play_addr, str):
                    play_url = play_addr
            
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
                'collect_count': collect_count,
                'play_count': play_count,
                'cover_url': cover_url,
                'play_url': play_url,
                'duration': duration
            }
            
        except Exception as e:
            print(f"解析视频信息时出错: {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    print("开始测试抖音爬虫实现...")
    scraper = DouyinScraper()
    
    # 测试URL
    test_url = "https://www.douyin.com/user/MS4wLjABAAAAnAFnkWlOm9jteymsi42fanYLMzfbqdGIwCILEUqDNmFyjfK9N8fSJdS_D2UWk_we"
    
    try:
        videos = scraper.fetch_all_videos(test_url, max_videos=100)
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
            print(f"分享数: {video.get('share_count')}")
            print(f"收藏数: {video.get('collect_count')}")
            print(f"封面URL: {video.get('cover_url')}")
            print(f"播放URL: {video.get('play_url')}")
        
        if len(videos) > 5:
            print(f"\n... 还有 {len(videos) - 5} 个视频未显示")
    
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()