# GitHub Actions HTTP API 调用方法

## 概述

本项目支持通过 HTTP API 触发 GitHub Actions 来执行抖音视频同步任务。现在支持四个输入参数：
1. 飞书多维表格链接
2. 飞书多维表格授权码
3. 抖音用户主页URL
4. 最大视频数量

## 配置要求

### 1. GitHub Secrets 配置

在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加以下密钥：

- `FEISHU_APP_ID`: 飞书应用 ID
- `FEISHU_APP_SECRET`: 飞书应用密钥

**注意**: 不再需要预先配置 `FEISHU_APP_TOKEN`，因为它会从多维表格链接中自动提取。

### 2. GitHub Personal Access Token

需要创建一个具有 `repo` 权限的 Personal Access Token：

1. 访问 GitHub Settings > Developer settings > Personal access tokens
2. 点击 "Generate new token (classic)"
3. 选择 `repo` 权限
4. 复制生成的 token

## 调用方法

### 方法一：使用 Python 脚本

```bash
# 设置环境变量
export GITHUB_TOKEN="your_github_token_here"

# 运行脚本
python trigger_action.py "https://xxx.feishu.cn/base/APP_TOKEN?table=TABLE_ID" "your_auth_token" "https://www.douyin.com/user/MS4wLjABAAAA..." 30
```

### 方法二：直接使用 curl

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/k190513120/douyin_to_base/dispatches \
  -d '{
    "event_type": "douyin-sync",
    "client_payload": {
      "feishu_table_url": "https://xxx.feishu.cn/base/APP_TOKEN?table=TABLE_ID",
      "feishu_auth_token": "your_auth_token",
      "douyin_url": "https://www.douyin.com/user/MS4wLjABAAAA...",
      "max_videos": "30"
    }
  }'
```

### 方法三：使用 JavaScript/Node.js

```javascript
const axios = require('axios');

async function triggerDouyinSync(feishuTableUrl, feishuAuthToken, douyinUrl, maxVideos = 20) {
  const response = await axios.post(
    'https://api.github.com/repos/k190513120/douyin_to_base/dispatches',
    {
      event_type: 'douyin-sync',
      client_payload: {
        feishu_table_url: feishuTableUrl,
        feishu_auth_token: feishuAuthToken,
        douyin_url: douyinUrl,
        max_videos: maxVideos.toString()
      }
    },
    {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': `token ${process.env.GITHUB_TOKEN}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  return response.status === 204;
}

// 使用示例
triggerDouyinSync(
  'https://xxx.feishu.cn/base/APP_TOKEN?table=TABLE_ID',
  'your_auth_token',
  'https://www.douyin.com/user/MS4wLjABAAAA...',
  30
)
  .then(success => console.log(success ? '触发成功' : '触发失败'))
  .catch(error => console.error('错误:', error));
```

### 方法四：使用 Python requests

```python
import requests
import os

def trigger_douyin_sync(feishu_table_url, feishu_auth_token, douyin_url, max_videos=20):
    url = "https://api.github.com/repos/k190513120/douyin_to_base/dispatches"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "event_type": "douyin-sync",
        "client_payload": {
            "feishu_table_url": feishu_table_url,
            "feishu_auth_token": feishu_auth_token,
            "douyin_url": douyin_url,
            "max_videos": str(max_videos)
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 204

# 使用示例
success = trigger_douyin_sync(
    "https://xxx.feishu.cn/base/APP_TOKEN?table=TABLE_ID",
    "your_auth_token",
    "https://www.douyin.com/user/MS4wLjABAAAA...",
    30
)
print("触发成功" if success else "触发失败")
```

## 参数说明

- `feishu_table_url` (必需): 飞书多维表格链接，格式如：`https://xxx.feishu.cn/base/APP_TOKEN?table=TABLE_ID`
- `feishu_auth_token` (必需): 飞书多维表格授权码
- `douyin_url` (必需): 抖音用户主页URL
- `max_videos` (可选): 最大视频数量，默认为 20

## 多维表格链接格式说明

飞书多维表格链接通常格式为：
```
https://xxx.feishu.cn/base/APP_TOKEN?table=TABLE_ID&view=VIEW_ID
```

系统会自动从链接中提取：
- `APP_TOKEN`: base/ 后面到 ? 之间的部分
- `TABLE_ID`: table= 后面到 & 之间的部分（如果没有 & 则到末尾）

## 响应说明

- **成功**: HTTP 204 No Content
- **失败**: HTTP 4xx/5xx 错误码

## 查看执行状态

触发成功后，可以在以下地址查看执行状态：
https://github.com/k190513120/douyin_to_base/actions

## 注意事项

1. GitHub Token 需要具有 `repo` 权限
2. 确保仓库的 Secrets 已正确配置（FEISHU_APP_ID 和 FEISHU_APP_SECRET）
3. 飞书多维表格链接必须是有效的格式
4. 飞书授权码必须具有对应表格的读写权限
5. 抖音 URL 必须是有效的用户主页链接
6. 建议在生产环境中使用环境变量存储敏感信息

## 错误排查

1. **401 Unauthorized**: 检查 GitHub Token 是否正确
2. **404 Not Found**: 检查仓库路径是否正确
3. **422 Unprocessable Entity**: 检查请求体格式是否正确