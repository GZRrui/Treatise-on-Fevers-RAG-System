# 阶段 0 环境契约

配置优先级为显式初始化参数、进程环境变量、项目根目录 `.env`、代码默认值。环境名称只能是 `development`、`test` 或 `production`。

| 配置 | development | test | production |
|---|---|---|---|
| `APP_ENV` | `development` | `test` | `production` |
| `RAG_OFFLINE_MODE` | 默认 `true`，可显式联网 | 必须 `true` | 必须 `false` |
| `DASHSCOPE_API_KEY` | 离线时可空 | 必须为空 | 必填且不得为示例值 |
| `DATA_DIR` | `./data` | 临时目录 | 显式持久目录 |
| `STORAGE_DIR` | `./storage` | 临时目录 | 显式持久目录 |
| `DATABASE_URL` | 默认本地 SQLite | 临时 SQLite | 必填 |
| `DEBUG` | 默认 `false` | 必须 `false` | 必须 `false` |
| `CORS_ORIGINS` | 仅本地开发源 | 测试源 | 一个或多个显式 HTTPS 源 |
| `JWT_SECRET` | 开发默认值 | 测试专用值 | 至少 32 字符且不得为默认值 |
| 网络 | 按 Provider 选择 | `pytest-socket` 禁止外部网络，仅允许事件循环所需回环/Unix socket | 按部署网络策略 |

开发、测试和生产示例分别位于 `.env.example`、`.env.test.example` 和 `.env.production.example`。生产配置在应用创建时校验，任何禁项都会阻止启动；密钥字段不会进入配置对象的 `repr`。
