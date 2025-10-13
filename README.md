# 2Web3 KOL 空投活动汇总服务

该项目提供一个可以在服务器上部署的 FastAPI 服务，用于追踪并总结 X（Twitter） 上 2Web3 领域 KOL 账号发布的空投 / 奖励活动信息。

## 功能特性

- 支持配置需要跟踪的 KOL 账号和关键词。
- 默认集成示例数据，便于在没有 Twitter API Key 的环境下测试。
- 提供 REST API：
  - `GET /health`：服务健康检查。
  - `GET /summaries`：获取最新的空投活动总结（可通过 `force_refresh=true` 强制刷新）。
  - `POST /summaries/refresh`：手动刷新缓存并返回最新摘要。
- 汇总输出包含：
  - 追踪账号的空投提及次数、关键词热度、最新重点活动。
  - 全局热门关键词列表。

## 快速开始

1. 创建虚拟环境并安装依赖：

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. 配置环境变量（可选）：

   - `TWITTER_BEARER_TOKEN`：Twitter/X API v2 的 Bearer Token。
   - `TRACKED_HANDLES`：以逗号分隔的账号列表，例如 `2web3kol,Web3Airdrops`。
   - `AIRDROP_KEYWORDS`：检测空投活动的关键词，默认为常见英文/中文组合。
   - `USE_SAMPLE_DATA`：设置为 `true` 时使用 `data/sample_tweets.json` 中的示例数据。

   也可以通过 `.env` 文件统一管理这些配置。

3. 启动服务：

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. 调用 API：

   ```bash
   curl "http://localhost:8000/summaries?force_refresh=true"
   ```

## 运行测试

```bash
pytest
```

## 项目结构

```
.
├── app
│   ├── airdrop_detector.py   # 关键词匹配与统计
│   ├── config.py             # 配置加载
│   ├── models.py             # 数据模型
│   ├── service.py            # 服务编排
│   ├── summarizer.py         # 摘要生成逻辑
│   └── twitter_client.py     # Twitter/X API 调用或示例数据读取
├── data
│   └── sample_tweets.json    # 示例推文数据
├── main.py                   # FastAPI 入口
├── requirements.txt          # 依赖列表
└── tests                     # 单元测试
```

## 部署建议

- 使用 `systemd`、`supervisor` 或容器化方式（Docker）运行 `uvicorn`。
- 配合 `nginx` 做反向代理以及 HTTPS 终端。
- 使用定时任务（如 `cron`）定期调用 `POST /summaries/refresh` 触发数据更新。
- 将配置和密钥保存在安全的 `.env` 或密钥管理服务中。

## 许可证

本项目以 MIT 许可证发布，可自由修改和部署。
