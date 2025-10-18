#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音视频信息到飞书多维表格同步脚本
实现抖音视频数据同步到飞书多维表格的功能
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time
import functools

from baseopensdk import BaseClient, JSON, LARK_DOMAIN, FEISHU_DOMAIN
from baseopensdk.api.base.v1 import *


class DataTypeMapper:
    """数据类型映射器"""
    
    @staticmethod
    def get_base_field_type(field_type: str) -> str:
        """将字段类型映射为飞书多维表格支持的类型"""
        type_mapping = {
            'varchar': 'Text',
            'text': 'Text',
            'longtext': 'Text',
            'char': 'Text',
            'string': 'Text',
            'int': 'Number',
            'bigint': 'Number',
            'decimal': 'Number',
            'float': 'Number',
            'double': 'Number',
            'datetime': 'DateTime',
            'timestamp': 'DateTime',
            'date': 'DateTime',
            'time': 'DateTime',
            'boolean': 'Checkbox',
            'tinyint': 'Checkbox',
            'json': 'Text',
            'url': 'Text'
        }
        return type_mapping.get(field_type.lower(), 'Text')


@dataclass
class BaseConfig:
    """飞书多维表格配置"""
    app_token: str
    personal_base_token: str
    table_id: str
    region: str = 'domestic'  # 'domestic' for 国内飞书, 'overseas' for 海外Lark


class DataTypeMapper:
    """数据类型映射器"""
    
    # 飞书多维表格字段类型映射
    BASE_FIELD_TYPE_MAPPING = {
        'Text': 1,
        'Number': 2,
        'SingleSelect': 3,
        'MultiSelect': 4,
        'DateTime': 5,
        'Checkbox': 7,
        'Attachment': 11,
        'Url': 15,
        'Phone': 13,
        'Email': 14
    }
    
    @classmethod
    def get_base_field_type(cls, field_type: str) -> str:
        """获取飞书多维表格字段类型"""
        return field_type
    
    @classmethod
    def get_field_type_code(cls, field_type: str) -> int:
        """获取字段类型代码"""
        return cls.BASE_FIELD_TYPE_MAPPING.get(field_type, 1)


class DouyinDataTypeMapper:
    """抖音数据类型映射器"""
    
    # 抖音字段到飞书多维表格字段类型映射
    TYPE_MAPPING = {
        # 基础字段
        'aweme_id': 'Text',
        'desc': 'Text',
        'create_time': 'DateTime',
        
        # 作者信息
        'author_nickname': 'Text',
        'author_uid': 'Text',
        
        # 统计数据
        'digg_count': 'Number',
        'comment_count': 'Number',
        'share_count': 'Number',
        'play_count': 'Number',
        'collect_count': 'Number',
        
        # 媒体信息
        'video_play_addr': 'Url',
        'cover_url': 'Url',
        'duration': 'Number',
        
        # 系统字段
        'sync_time': 'DateTime',
    }
    
    @classmethod
    def get_field_type(cls, field_name: str) -> str:
        """获取飞书多维表格字段类型"""
        return cls.TYPE_MAPPING.get(field_name, 'Text')
    
    @classmethod
    def convert_value(cls, field_name: str, value: Any) -> Any:
        """转换数据值"""
        if value is None:
            return None
            
        field_type = cls.get_field_type(field_name)
        
        # 日期时间类型转换
        if field_type == 'DateTime':
            if isinstance(value, datetime):
                return int(value.timestamp() * 1000)  # 转换为毫秒时间戳
            elif isinstance(value, str):
                try:
                    # 尝试解析时间字符串
                    if value.isdigit():
                        # 如果是时间戳
                        timestamp = int(value)
                        if timestamp > 1000000000000:  # 毫秒时间戳
                            return timestamp
                        else:  # 秒时间戳
                            return timestamp * 1000
                    else:
                        # 尝试解析日期字符串
                        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                        return int(dt.timestamp() * 1000)
                except:
                    # 如果解析失败，保持原始值
                    return value
            else:
                return value
        
        # 数值类型转换
        elif field_type == 'Number':
            try:
                return int(value) if isinstance(value, (int, float, str)) and str(value).isdigit() else 0
            except:
                return 0
        
        # URL类型转换
        elif field_type == 'Url':
            return str(value) if value else ''
        
        # 布尔类型转换
        elif field_type == 'Checkbox':
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'yes', 'on']
            else:
                return bool(value) if value is not None else False
        
        # 其他类型转为字符串
        else:
            return str(value) if value is not None else ''


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """改进的重试装饰器，支持指数退避和特定异常处理"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # 获取logger实例（如果存在）
                    logger = None
                    if args and hasattr(args[0], 'logger'):
                        logger = args[0].logger
                    
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff_factor ** attempt)
                        if logger:
                            logger.warning(f"第 {attempt + 1} 次尝试失败: {e}, {wait_time:.1f}秒后重试...")
                        time.sleep(wait_time)
                    else:
                        if logger:
                            logger.error(f"所有 {max_retries} 次尝试都失败了: {e}")
                    continue
            
            # 如果所有重试都失败，返回False而不是抛出异常
            if 'create_record' in func.__name__ or 'check_record_exists' in func.__name__:
                return False
            raise last_exception
        return wrapper
    return decorator


class FeishuWriter:
    """飞书多维表格写入器"""
    
    def __init__(self, config: BaseConfig):
        self.config = config
        self.client = None
        self.data_mapper = DouyinDataTypeMapper()
        
        # 先设置日志记录器
        self.logger = self._setup_logger()
        
        # 连接飞书
        if not self._connect_base():
            raise Exception("无法连接到飞书多维表格")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('feishu_writer')
        logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler('feishu_sync.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def create_base_table(self, table_name: str, schema: List[Dict]) -> Optional[str]:
        """在飞书多维表格中创建表"""
        try:
            # 构建字段定义 - 使用正确的AppTableCreateHeader.builder()格式
            fields = []
            for col in schema:
                field_type = DataTypeMapper.get_base_field_type(col['type'])
                type_mapping = {
                    'Text': 1,
                    'Number': 2,
                    'SingleSelect': 3,
                    'MultiSelect': 4,
                    'DateTime': 5,
                    'Checkbox': 7,
                    'Attachment': 11
                }
                
                field_builder = AppTableCreateHeader.builder() \
                    .field_name(col['name']) \
                    .type(type_mapping.get(field_type, 1))  # 默认为文本类型
                
                # 添加ui_type（可选）
                if field_type in ['SingleSelect', 'MultiSelect', 'DateTime', 'Checkbox', 'Attachment']:
                    field_builder.ui_type(field_type)
                
                # 为单选和多选字段添加选项
                if field_type == 'SingleSelect':
                    property_builder = AppTableFieldProperty.builder() \
                        .options([
                            AppTableFieldPropertyOption.builder()
                                .name('选项1')
                                .color(1)
                                .build(),
                            AppTableFieldPropertyOption.builder()
                                .name('选项2')
                                .color(2)
                                .build(),
                            AppTableFieldPropertyOption.builder()
                                .name('选项3')
                                .color(3)
                                .build()
                        ])
                    field_builder.property(property_builder.build())
                elif field_type == 'MultiSelect':
                    property_builder = AppTableFieldProperty.builder() \
                        .options([
                            AppTableFieldPropertyOption.builder()
                                .name('选项1')
                                .color(1)
                                .build(),
                            AppTableFieldPropertyOption.builder()
                                .name('选项2')
                                .color(2)
                                .build(),
                            AppTableFieldPropertyOption.builder()
                                .name('选项3')
                                .color(3)
                                .build()
                        ])
                    field_builder.property(property_builder.build())
                
                fields.append(field_builder.build())
            
            # 创建表请求
            request = CreateAppTableRequest.builder() \
                .request_body(
                    CreateAppTableRequestBody.builder()
                    .table(
                        ReqTable.builder()
                        .name(table_name)
                        .default_view_name("默认视图")
                        .fields(fields)
                        .build()
                    )
                    .build()
                ) \
                .build()
            
            response = self.client.base.v1.app_table.create(request)
            
            if response.success():
                table_id = response.data.table_id
                self.logger.info(f"成功创建飞书表格: {table_name} (ID: {table_id})")
                return table_id
            else:
                self.logger.error(f"创建飞书表格失败: {response.msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"创建飞书表格 {table_name} 失败: {e}")
            return None
    
    def ensure_required_fields(self) -> bool:
        """确保表格中存在所需的字段"""
        try:
            # 获取当前表格字段
            table_fields = self.get_table_fields()
            existing_fields = set()
            
            if hasattr(table_fields, 'items') and table_fields.items:
                for field in table_fields.items:
                    existing_fields.add(field.field_name)
            elif isinstance(table_fields, dict) and 'items' in table_fields:
                for field in table_fields['items']:
                    field_name = field.get('field_name') if isinstance(field, dict) else field.field_name
                    existing_fields.add(field_name)
            
            self.logger.info(f"现有字段: {existing_fields}")
            
            # 暂时跳过字段创建，使用现有字段
            if '视频名称' in existing_fields:
                self.logger.info("使用现有的'视频名称'字段进行测试")
                return True
            else:
                self.logger.error("表格中没有找到'视频名称'字段")
                return False
            
        except Exception as e:
            self.logger.error(f"确保字段存在时出错: {e}")
            return False
    
    def get_base_tables(self) -> Dict[str, str]:
        """获取飞书多维表格中的所有表"""
        try:
            request = ListAppTableRequest.builder().build()
            response = self.client.base.v1.app_table.list(request)
            
            if response.success():
                tables = {}
                for table in response.data.items:
                    tables[table.name] = table.table_id
                self.logger.info(f"发现 {len(tables)} 个飞书表格")
                return tables
            else:
                self.logger.error(f"获取飞书表格列表失败: {response.msg}")
                return {}
        except Exception as e:
            self.logger.error(f"获取飞书表格列表失败: {e}")
            return {}
    
    def ensure_table_exists(self, table_name: str = "抖音视频数据") -> bool:
        """确保表格存在，如果不存在则创建"""
        try:
            # 获取现有表格
            existing_tables = self.get_base_tables()
            
            if table_name in existing_tables:
                # 表格已存在，更新table_id
                self.config.table_id = existing_tables[table_name]
                self.logger.info(f"找到现有表格: {table_name} (ID: {self.config.table_id})")
                return True
            else:
                # 表格不存在，创建新表格
                self.logger.info(f"表格 {table_name} 不存在，开始创建...")
                
                # 定义抖音视频数据的字段结构
                schema = [
                    {'name': 'aweme_id', 'type': 'Text'},
                    {'name': 'desc', 'type': 'Text'},
                    {'name': 'create_time', 'type': 'DateTime'},
                    {'name': 'author_nickname', 'type': 'Text'},
                    {'name': 'author_uid', 'type': 'Text'},
                    {'name': 'digg_count', 'type': 'Number'},
                    {'name': 'comment_count', 'type': 'Number'},
                    {'name': 'collect_count', 'type': 'Number'},
                    {'name': 'share_count', 'type': 'Number'},
                    {'name': 'play_count', 'type': 'Number'},
                    {'name': 'video_url', 'type': 'Text'},
                    {'name': 'cover_url', 'type': 'Text'},
                    {'name': 'duration', 'type': 'Number'},
                    {'name': 'sync_time', 'type': 'DateTime'}
                ]
                
                table_id = self.create_base_table(table_name, schema)
                if table_id:
                    self.config.table_id = table_id
                    self.logger.info(f"成功创建表格: {table_name} (ID: {table_id})")
                    return True
                else:
                    self.logger.error(f"创建表格 {table_name} 失败")
                    return False
                    
        except Exception as e:
            self.logger.error(f"确保表格存在失败: {e}")
            return False
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler('feishu_sync.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _connect_base(self) -> bool:
        """连接飞书多维表格"""
        try:
            # 根据区域选择domain
            domain = LARK_DOMAIN if self.config.region == 'overseas' else FEISHU_DOMAIN
            
            self.client = BaseClient.builder() \
                .app_token(self.config.app_token) \
                .personal_base_token(self.config.personal_base_token) \
                .domain(domain) \
                .build()
            
            region_name = "海外Lark" if self.config.region == 'overseas' else "国内飞书"
            self.logger.info(f"成功连接到{region_name}多维表格")
            return True
        except Exception as e:
            self.logger.error(f"连接飞书多维表格失败: {e}")
            return False
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_table_fields(self) -> Dict:
        """获取表格的字段信息"""
        try:
            request = ListAppTableFieldRequest.builder() \
                .table_id(self.config.table_id) \
                .build()
            
            response = self.client.base.v1.app_table_field.list(request)
            
            if response.code == 0:
                self.logger.debug("成功获取表格字段信息")
                return response.data
            else:
                self.logger.error(f"获取表格字段失败: {response.msg}")
                return {}
                
        except Exception as e:
            self.logger.error(f"获取表格字段时出错: {e}")
            raise
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def list_records(self, page_size: int = 20) -> Dict:
        """列出表格中的记录"""
        try:
            request = ListAppTableRecordRequest.builder() \
                .table_id(self.config.table_id) \
                .page_size(page_size) \
                .build()
            
            response = self.client.base.v1.app_table_record.list(request)
            
            if response.code == 0:
                self.logger.debug(f"成功获取 {len(response.data.items or [])} 条记录")
                return response.data
            else:
                self.logger.error(f"获取记录失败: {response.msg}")
                return {}
                
        except Exception as e:
            self.logger.error(f"获取记录时出错: {e}")
            raise
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def check_record_exists(self, aweme_id: str) -> bool:
        """检查记录是否已存在（基于aweme_id）"""
        try:
            # 先获取所有记录，然后在本地检查是否存在相同的aweme_id
            records_data = self.list_records(page_size=100)
            
            # 检查响应数据结构
            if hasattr(records_data, 'items') and records_data.items:
                items = records_data.items
            elif isinstance(records_data, dict) and 'items' in records_data:
                items = records_data['items']
            else:
                self.logger.debug("未找到记录数据")
                return False
            
            for item in items:
                # 处理不同的数据结构
                if hasattr(item, 'fields'):
                    fields = item.fields
                elif isinstance(item, dict) and 'fields' in item:
                    fields = item['fields']
                else:
                    continue
                
                # 检查字段中是否有匹配的aweme_id
                if hasattr(fields, 'get'):
                    aweme_id_value = fields.get('aweme_id')
                elif isinstance(fields, dict):
                    aweme_id_value = fields.get('aweme_id')
                else:
                    continue
                
                if aweme_id_value == aweme_id:
                    self.logger.debug(f"记录已存在: {aweme_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查记录存在性时出错: {e}")
            return False  # 出错时返回False，允许继续创建记录
    
    def _prepare_record_fields(self, video_info: Dict) -> Dict:
        """准备记录字段数据"""
        fields = {}
        
        # 获取表格字段信息
        try:
            table_fields = self.get_table_fields()
            available_fields = {}
            if hasattr(table_fields, 'items') and table_fields.items:
                for field in table_fields.items:
                    available_fields[field.field_name] = field.field_id
            elif isinstance(table_fields, dict) and 'items' in table_fields:
                for field in table_fields['items']:
                    field_name = field.get('field_name') if isinstance(field, dict) else field.field_name
                    field_id = field.get('field_id') if isinstance(field, dict) else field.field_id
                    available_fields[field_name] = field_id
            
            self.logger.debug(f"可用字段: {list(available_fields.keys())}")
            
            # 如果表格中没有足够的字段，尝试创建表格
            if len(available_fields) <= 1:  # 只有默认的"视频名称"字段
                self.logger.info("检测到表格字段不足，尝试确保表格存在...")
                if self.ensure_table_exists():
                    # 重新获取字段信息
                    table_fields = self.get_table_fields()
                    available_fields = {}
                    if hasattr(table_fields, 'items') and table_fields.items:
                        for field in table_fields.items:
                            available_fields[field.field_name] = field.field_id
                    elif isinstance(table_fields, dict) and 'items' in table_fields:
                        for field in table_fields['items']:
                            field_name = field.get('field_name') if isinstance(field, dict) else field.field_name
                            field_id = field.get('field_id') if isinstance(field, dict) else field.field_id
                            available_fields[field_name] = field_id
                    self.logger.info(f"更新后的可用字段: {list(available_fields.keys())}")
            
        except Exception as e:
            self.logger.error(f"获取表格字段失败: {e}")
            available_fields = {'视频名称': 'fld2ZQI3wS'}  # 使用默认字段
        
        # 根据可用字段准备数据
        if '视频名称' in available_fields:
            # 如果只有视频名称字段，将视频描述作为主要内容
            video_title = video_info.get('desc', '')
            if not video_title:
                video_title = f"抖音视频_{video_info.get('aweme_id', 'unknown')}"
            fields['视频名称'] = video_title
        
        # 如果有其他字段，按需添加
        field_mapping = {
            'aweme_id': video_info.get('aweme_id', ''),
            'desc': video_info.get('title', '') or video_info.get('desc', ''),  # 优先使用title，fallback到desc
            'create_time': video_info.get('create_time', ''),  # 保持原始字符串格式
            'author_nickname': video_info.get('author_name', '') or video_info.get('author', {}).get('nickname', ''),
            'author_uid': video_info.get('author_uid', '') or video_info.get('author', {}).get('uid', ''),
            'digg_count': video_info.get('digg_count', 0) or video_info.get('statistics', {}).get('digg_count', 0),
            'comment_count': video_info.get('comment_count', 0) or video_info.get('statistics', {}).get('comment_count', 0),
            'collect_count': video_info.get('collect_count', 0) or video_info.get('statistics', {}).get('collect_count', 0),
            'share_count': video_info.get('share_count', 0) or video_info.get('statistics', {}).get('share_count', 0),
            'play_count': video_info.get('play_count', 0) or video_info.get('statistics', {}).get('play_count', 0),
            'video_url': video_info.get('video_url', '') or self._extract_video_url(video_info),
            'cover_url': video_info.get('cover_url', '') or self._extract_cover_url(video_info),
            'duration': video_info.get('duration', 0) or video_info.get('video', {}).get('duration', 0),
            'sync_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 只添加表格中存在的字段
        for field_name, value in field_mapping.items():
            if field_name in available_fields:
                try:
                    # 对于author_uid字段，确保正确获取值
                    if field_name == 'author_uid' and not value:
                        value = video_info.get('author_uid', '')
                    
                    converted_value = DouyinDataTypeMapper.convert_value(field_name, value)
                    # 验证转换后的值
                    if self._validate_field_value(field_name, converted_value):
                        fields[field_name] = converted_value
                    else:
                        self.logger.warning(f"字段值验证失败: {field_name}={converted_value}, 使用默认值")
                        fields[field_name] = self._get_default_value(field_name)
                except Exception as e:
                    self.logger.error(f"字段转换失败: {field_name}={value}, 错误: {e}")
                    fields[field_name] = self._get_default_value(field_name)
        
        return fields
    
    def _validate_field_value(self, field_name: str, value: Any) -> bool:
        """验证字段值是否符合类型要求"""
        field_type = self.data_mapper.get_field_type(field_name)
        
        if field_type == 'Number':
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif field_type == 'DateTime':
            return isinstance(value, (int, float)) and value > 0
        elif field_type in ['Text', 'Url']:
            return isinstance(value, str)
        elif field_type == 'SingleSelect':
            return isinstance(value, str) and value in ['已同步', '待处理', '失败']
        else:
            return True
    
    def _get_default_value(self, field_name: str) -> Any:
        """获取字段的默认值"""
        field_type = self.data_mapper.get_field_type(field_name)
        
        if field_type == 'Number':
            return 0
        elif field_type == 'DateTime':
            return int(datetime.now().timestamp() * 1000)
        elif field_type == 'SingleSelect':
            return '已同步'
        else:
            return ''
    
    def _extract_video_url(self, video_info: Dict) -> str:
        """提取视频URL"""
        video = video_info.get('video', {})
        play_addr = video.get('play_addr', {})
        url_list = play_addr.get('url_list', [])
        return url_list[0] if url_list else ''
    
    def _extract_cover_url(self, video_info: Dict) -> str:
        """提取封面URL"""
        video = video_info.get('video', {})
        cover = video.get('cover', {})
        url_list = cover.get('url_list', [])
        return url_list[0] if url_list else ''
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def create_record(self, video_info: Dict) -> bool:
        """创建单条记录"""
        aweme_id = video_info.get('aweme_id', '')
        
        try:
            # 准备记录数据
            fields = self._prepare_record_fields(video_info)
            
            # 调试输出字段信息
            self.logger.debug(f"准备创建记录的字段: {fields}")
            
            # 构建记录对象
            record = AppTableRecord.builder() \
                .fields(fields) \
                .build()
            
            request = CreateAppTableRecordRequest.builder() \
                .table_id(self.config.table_id) \
                .request_body(record) \
                .build()
            
            response = self.client.base.v1.app_table_record.create(request)
            
            if response.code == 0:
                self.logger.debug(f"成功创建记录: {aweme_id}")
                return True
            else:
                self.logger.error(f"创建记录失败: {response.msg}, aweme_id: {aweme_id}")
                self.logger.error(f"失败的字段数据: {fields}")
                return False
                
        except Exception as e:
            self.logger.error(f"创建记录时出错: {e}, aweme_id: {aweme_id}")
            return False
    
    def batch_create_records(self, videos_info: List[Dict], batch_size: int = 10) -> Dict:
        """批量创建记录"""
        result = {
            'total': len(videos_info),
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'details': []
        }
        
        # 首先确保表格存在
        if not self.ensure_table_exists():
            self.logger.error("确保表格存在失败，无法继续写入记录")
            result['failed_count'] = result['total']
            return result
        
        self.logger.info(f"开始批量写入 {len(videos_info)} 条记录到飞书多维表格...")
        
        for i, video_info in enumerate(videos_info, 1):
            aweme_id = video_info.get('aweme_id', f'unknown_{i}')
            
            try:
                self.logger.info(f"处理第 {i}/{len(videos_info)} 条记录: {aweme_id}")
                
                # 检查记录是否已存在
                try:
                    if self.check_record_exists(aweme_id):
                        result['skipped_count'] += 1
                        result['details'].append({
                            'aweme_id': aweme_id,
                            'status': 'skipped',
                            'reason': '记录已存在'
                        })
                        self.logger.info(f"记录已存在，跳过: {aweme_id}")
                        continue
                except Exception as check_error:
                    self.logger.warning(f"检查记录存在性失败，继续创建: {check_error}")
                
                # 创建记录
                try:
                    if self.create_record(video_info):
                        result['success_count'] += 1
                        result['details'].append({
                            'aweme_id': aweme_id,
                            'status': 'success'
                        })
                        self.logger.info(f"成功创建记录: {aweme_id}")
                    else:
                        result['failed_count'] += 1
                        result['details'].append({
                            'aweme_id': aweme_id,
                            'status': 'failed',
                            'reason': '创建失败'
                        })
                        self.logger.error(f"创建记录失败: {aweme_id}")
                except Exception as create_error:
                    result['failed_count'] += 1
                    result['details'].append({
                        'aweme_id': aweme_id,
                        'status': 'error',
                        'reason': str(create_error)
                    })
                    self.logger.error(f"创建记录时出错: {create_error}, aweme_id: {aweme_id}")
                
                # 批量处理时的延迟，避免API限流
                if i % batch_size == 0:
                    self.logger.info(f"已处理 {i} 条记录，暂停1秒避免限流...")
                    time.sleep(1)
                else:
                    time.sleep(0.3)  # 增加延迟时间
                
            except Exception as e:
                self.logger.error(f"处理记录时出错: {e}, aweme_id: {aweme_id}")
                result['failed_count'] += 1
                result['details'].append({
                    'aweme_id': aweme_id,
                    'status': 'error',
                    'reason': str(e)
                })
        
        # 输出结果统计
        self.logger.info(f"批量写入完成:")
        self.logger.info(f"总计: {result['total']} 条")
        self.logger.info(f"成功: {result['success_count']} 条")
        self.logger.info(f"失败: {result['failed_count']} 条")
        self.logger.info(f"跳过: {result['skipped_count']} 条")
        
        return result
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def update_record(self, record_id: str, video_info: Dict) -> bool:
        """更新记录"""
        try:
            # 准备更新字段（只更新可变的统计数据）
            fields = {
                "desc": self.data_mapper.convert_value('desc', video_info.get('desc', '')),
                "statistics_digg_count": self.data_mapper.convert_value('statistics_digg_count', 
                                                                      video_info.get('statistics', {}).get('digg_count', 0)),
                "statistics_comment_count": self.data_mapper.convert_value('statistics_comment_count', 
                                                                         video_info.get('statistics', {}).get('comment_count', 0)),
                "statistics_share_count": self.data_mapper.convert_value('statistics_share_count', 
                                                                       video_info.get('statistics', {}).get('share_count', 0)),
                "statistics_play_count": self.data_mapper.convert_value('statistics_play_count', 
                                                                      video_info.get('statistics', {}).get('play_count', 0)),
                "sync_time": self.data_mapper.convert_value('sync_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            }
            
            request = UpdateAppTableRecordRequest.builder() \
                .table_id(self.config.table_id) \
                .record_id(record_id) \
                .build()
            
            request.record = AppTableRecord.builder() \
                .fields(fields) \
                .build()
            
            response = self.client.base.v1.app_table_record.update(request)
            
            if response.code == 0:
                self.logger.info(f"成功更新记录: {record_id}")
                return True
            else:
                self.logger.error(f"更新记录失败: {response.msg}, record_id: {record_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新记录时出错: {e}, record_id: {record_id}")
            raise


if __name__ == "__main__":
    # 测试代码
    import os
    from dotenv import load_dotenv, find_dotenv
    
    load_dotenv(find_dotenv())
    
    APP_TOKEN = os.environ.get('APP_TOKEN')
    PERSONAL_BASE_TOKEN = os.environ.get('PERSONAL_BASE_TOKEN')
    TABLE_ID = os.environ.get('TABLE_ID')
    
    if not all([APP_TOKEN, PERSONAL_BASE_TOKEN, TABLE_ID]):
        print("请先配置环境变量")
        sys.exit(1)
    
    # 创建配置
    config = BaseConfig(
        app_token=APP_TOKEN,
        personal_base_token=PERSONAL_BASE_TOKEN,
        table_id=TABLE_ID,
        region='domestic'
    )
    
    try:
        writer = FeishuWriter(config)
        
        # 测试获取表格字段
        fields = writer.get_table_fields()
        print("表格字段信息:")
        print(JSON.marshal(fields, indent=2))
        
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)