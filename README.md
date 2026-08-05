# 《伤寒论》RAG 智能问答系统

基于 LlamaIndex + 通义千问 构建的《伤寒论》智能问答系统。

## 📁 项目结构

```
D:\ragpp\
├── config.py                 # 统一配置
├── requirements.txt          # 依赖清单
├── .env.example              # 环境变量模板
│
├── data/                     # 数据目录
│   └── shanghanlun_raw.json  # 原始条文（236条）
│
├── src/                      # 核心 RAG 模块
│   ├── data_loader.py        # 数据加载与清洗
│   ├── indexer.py            # 向量索引构建
│   ├── retriever.py          # 检索链路
│   ├── prompt_template.py    # Prompt 模板
│   └── qa_engine.py         # 问答引擎
│
├── backend/                  # FastAPI 后端
│   ├── main.py              # 入口
│   ├── config.py            # 后端配置
│   ├── routers/             # API 路由
│   ├── models/             # Pydantic 模型
│   ├── middleware/         # 中间件
│   ├── services/          # 业务逻辑
│   ├── database/          # 数据库层
│   └── utils/            # 工具函数
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 调用
│   │   ├── components/   # Vue 组件
│   │   └── main.ts
│   └── package.json
│
├── scripts/               # 运维脚本
│   ├── build_index.py    # 构建索引
│   └── interactive_qa.py # 交互问答
│
├── tests/                # 测试
│   └── test_pipeline.py
│
└── storage/             # 运行时存储
    └── vector_store/    # 向量索引
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY
```

### 3. 构建向量索引

```bash
python scripts/build_index.py
```

### 4. 启动服务

**方式一：交互式终端**
```bash
python scripts/interactive_qa.py
```

**方式二：后端 API**
```bash
cd backend && uvicorn main:app --reload --port 8000
# 访问 http://localhost:8000/docs 查看 API 文档
```

**方式三：前端 + 后端**
```bash
# 终端1: 启动后端
cd backend && uvicorn main:app --reload --port 8000

# 终端2: 启动前端
cd frontend && npm install && npm run dev
```

## 📡 API 接口

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/qa` | 智能问答 |
| POST | `/api/v1/qa/stream` | 流式问答（SSE） |
| POST | `/api/v1/search` | 条文检索 |
| POST | `/api/v1/index/build` | 重建索引 |
| GET | `/api/v1/index/status` | 索引状态 |
| GET | `/health` | 健康检查 |

## 🔧 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| DASHSCOPE_API_KEY | 阿里云 DashScope API Key | 必填 |
| EMBEDDING_MODEL | Embedding 模型 | text-embedding-v3 |
| LLM_MODEL | LLM 模型 | qwen-plus |
| TOP_K | 检索数量 | 5 |
| SIMILARITY_THRESHOLD | 相似度阈值 | 0.7 |

## 📖 示例问题


- 太阳病的主要症状是什么？
- 桂枝汤的组成是什么？
- 什么是少阳病？
- 小青龙汤适用于什么症状？
- 阳明病的特点是什么？

## 🏗️ 企业级扩展

项目预留了以下企业级接口：

- **JWT 认证**：`backend/middleware/auth.py`
- **限流中间件**：`backend/middleware/rate_limit.py`
- **数据库 ORM**：`backend/database/models.py`
- **Redis 缓存接口**：`backend/utils/cache.py`
- **Prometheus 监控接口**：`backend/routers/health.py`

## License

MIT
