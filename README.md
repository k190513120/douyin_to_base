# 抖音视频信息抓取工具

这是一个用于抓取抖音博主视频信息并同步到飞书多维表格的Python工具。

## 功能特性

- 🎯 **自动抓取**: 根据抖音博主主页链接自动抓取所有视频信息
- 📊 **数据丰富**: 获取视频标题、作者、发布时间、点赞数、评论数、分享数、播放数等
- 🔄 **智能同步**: 自动检测重复记录，避免重复写入
- 📋 **批量处理**: 支持批量写入飞书多维表格
- 🛡️ **错误处理**: 完善的错误处理和重试机制
- 💻 **多种使用方式**: 支持命令行参数和交互式输入

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置环境变量

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的配置信息：
```env
# 飞书多维表格配置
APP_TOKEN=your_app_token_here
PERSONAL_BASE_TOKEN=your_personal_base_token_here
TABLE_ID=your_table_id_here

# 抖音API配置
DOUYIN_API_BASE_URL=https://tiktok-api-miaomiaocompany-c35bd5a6.koyeb.app
```

### 获取飞书配置信息

#### 1. 获取多维表格链接信息
- 打开你的飞书多维表格
- 从浏览器地址栏复制链接，格式类似：
  ```
  https://example.feishu.cn/base/APP_TOKEN?table=TABLE_ID&view=VIEW_ID
  ```
- 从链接中提取 `APP_TOKEN` 和 `TABLE_ID`

#### 2. 获取个人访问令牌 (PERSONAL_BASE_TOKEN)
- 访问 [飞书开放平台](https://open.feishu.cn/)
- 登录后进入"开发者后台"
- 创建应用或使用现有应用
- 在应用设置中找到"个人访问令牌"
- 复制令牌值作为 `PERSONAL_BASE_TOKEN`

## 使用方法

### 方法1: 交互式使用
直接运行脚本，按提示输入信息：
```bash
python main.py
```

### 方法2: 命令行参数
```bash
python main.py --url "https://www.douyin.com/user/xxx" --max-videos 100
```

#### 命令行参数说明
- `--url`: 抖音博主的主页地址（必需）
- `--max-videos`: 最大抓取视频数量（默认：1000）
- `--batch-size`: 批量写入的批次大小（默认：10）

### 支持的抖音链接格式
- 完整链接：`https://www.douyin.com/user/MS4wLjABAAAA...`
- 短链接：`https://v.douyin.com/xxx`
- 分享链接：`https://iesdouyin.com/share/user/xxx`

## 数据字段说明

工具会抓取以下视频信息并写入飞书表格：

| 字段名 | 说明 | 类型 |
|--------|------|------|
| aweme_id | 视频唯一ID | 文本 |
| title | 视频标题/描述 | 文本 |
| author_name | 作者昵称 | 文本 |
| author_uid | 作者UID | 文本 |
| create_time | 发布时间 | 文本 |
| digg_count | 点赞数 | 数字 |
| comment_count | 评论数 | 数字 |
| share_count | 分享数 | 数字 |
| play_count | 播放数 | 数字 |
| video_url | 视频链接 | 文本 |
| cover_url | 封面图片链接 | 文本 |
| sync_time | 同步时间 | 文本 |

## 项目结构

```
抖音同步/
├── main.py              # 主脚本
├── douyin_scraper.py    # 抖音视频抓取模块
├── feishu_writer.py     # 飞书表格写入模块
├── requirements.txt     # Python依赖
├── .env.example        # 环境变量示例
├── .env               # 环境变量配置（需要自己创建）
└── README.md          # 使用说明
```

## 注意事项

1. **API限制**: 抖音API可能有访问频率限制，工具已内置延时机制
2. **数据准确性**: 抓取的数据取决于第三方API的可用性和准确性
3. **重复检测**: 工具会自动检测已存在的记录（基于aweme_id），避免重复写入
4. **网络环境**: 确保网络连接稳定，能够访问抖音和飞书服务
5. **权限配置**: 确保飞书应用有足够的权限访问和修改多维表格

## 故障排除

### 常见问题

1. **"无法从URL中提取sec_user_id"**
   - 检查抖音链接格式是否正确
   - 尝试使用完整的用户主页链接

2. **"获取视频列表时出错"**
   - 检查网络连接
   - 确认第三方API服务是否正常

3. **"创建记录失败"**
   - 检查飞书配置信息是否正确
   - 确认应用权限是否足够
   - 检查表格字段是否匹配

4. **"缺少必要的环境变量"**
   - 确认 `.env` 文件存在且配置正确
   - 检查环境变量名称是否拼写正确

### 调试模式
如果遇到问题，可以单独测试各个模块：

```bash
# 测试抖音抓取功能
python douyin_scraper.py

# 测试飞书写入功能
python feishu_writer.py
```

## 更新日志

### v1.0.0
- 初始版本发布
- 支持抖音视频信息抓取
- 支持飞书多维表格写入
- 支持重复记录检测
- 支持批量处理

## 许可证

本项目仅供学习和研究使用，请遵守相关平台的使用条款。