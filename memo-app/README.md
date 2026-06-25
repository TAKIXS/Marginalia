
# 句集 / Excerpt

> 记录书中摘抄，书写个人感悟，打标签分类，快速检索回顾。
> *A quiet corner for the sentences that stay with you — record, reflect, and revisit.*

---

## 功能 / Features

- 📚 **书籍管理** — 添加/编辑/删除书籍，按书籍分组浏览摘抄
- ✍️ **摘抄记录** — 记录原文 + 个人感悟 + 相关链接 + 图片
- 🤖 **AI 帮写感悟** — DeepSeek 自动生成读书笔记，降低记录门槛
- 🏷️ **标签分类** — 多标签管理，自由创建/重命名/变色
- 🔍 **全文检索** — 中文 LIKE 模糊 + 英文 MySQL FULLTEXT 混合搜索
- 🎯 **联合筛选** — 关键词 + 标签 AND 逻辑 + 书籍 + 收藏状态
- ⭐ **收藏功能** — 星标重要摘抄，一键筛选精华
- 🎲 **随机摘抄** — 书架页「今日摘抄」卡片，偶遇旧日灵感
- 📝 **导出** — Markdown / JSON 格式导出
- 🖼️ **图片上传** — 摘抄关联插图，支持预览
- 🌙 **暗色模式** — 亮/暗主题切换，localStorage 记忆
- ⌨️ **快捷键** — `Ctrl+K` 快速聚焦搜索
- 📱 **响应式** — 手机端自适应
- 🔄 **自动建表** — 启动时自动创建缺失表和 FULLTEXT 索引
- 🏠 **零 Docker** — 纯本地 Python + Node.js 部署

---

## 技术栈 / Tech Stack

| 层 | 技术 |
|----|------|
| 后端 | Python 3.9+ / FastAPI / Uvicorn |
| ORM | SQLAlchemy 2.0 + aiomysql (async) |
| 迁移 | Alembic |
| AI | DeepSeek (OpenAI SDK) |
| 数据库 | MySQL 8.0 + ngram 全文索引 |
| 前端 | Vue 3 (Composition API) + Vite |
| UI | Element Plus |
| HTTP | Axios |

---

## 快速开始 / Quick Start

### 前置条件

- Python 3.9+
- Node.js 18+
- MySQL 8.0

### 1. 初始化数据库

```bash
mysql -u root -p < init.sql
```

### 2. 配置环境变量

编辑 `backend/.env`：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=memo
MYSQL_PASSWORD=memopass
MYSQL_DATABASE=memo_db
UPLOAD_DIR=./

# AI 感悟生成（可选，不填则按钮显示提示）
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 5. 访问

浏览器打开 `http://localhost:5173`

---

## 项目结构 / Project Structure

```
memo-app/
├── init.sql                         # 数据库初始化
├── README.md
├── backend/
│   ├── .env                         # 配置（不入 git）
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── main.py                      # FastAPI 入口 + 自动建表
│   ├── database.py                  # 异步引擎
│   ├── models.py                    # ORM 模型
│   ├── schemas.py                   # Pydantic 模型
│   ├── ai.py                        # AI 感悟生成（DeepSeek）
│   ├── migrations/                  # Alembic 迁移
│   ├── routers/
│   │   ├── books.py                 # 书籍 CRUD
│   │   ├── excerpts.py              # 摘抄 CRUD + 搜索 + 导出 + AI
│   │   └── tags.py                  # 标签 CRUD
│   └── uploads/                     # 上传图片
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.js
        ├── App.vue                  # 顶层布局 + 暗色模式 + Ctrl+K
        ├── utils.js                 # 共享工具函数
        ├── api/
        │   └── index.js             # Axios + 全局错误拦截
        └── components/
            ├── BookList.vue         # 书架 + 今日摘抄 + 导出
            ├── AddExcerpt.vue       # 添加摘抄 + AI 感悟
            ├── SearchView.vue       # 检索 + 高亮 + 收藏筛选
            └── TagManager.vue       # 标签管理（共享组件）
```

---

## API 概要

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | 健康检查 |
| GET/POST | `/api/books` | 书籍列表/创建 |
| GET/PUT/DELETE | `/api/books/{id}` | 书籍详情/更新/删除 |
| GET | `/api/books/groups` | 按书分组摘抄 |
| GET/POST | `/api/excerpts` | 摘抄搜索/创建 |
| GET/PUT/DELETE | `/api/excerpts/{id}` | 摘抄详情/更新/删除 |
| PUT | `/api/excerpts/{id}/favorite` | 切换收藏 |
| GET | `/api/excerpts/random` | 随机摘抄 |
| GET | `/api/excerpts/export?fmt=md\|json` | 导出 |
| POST | `/api/excerpts/generate-insights` | AI 生成感悟 |
| POST | `/api/excerpts/batch-delete` | 批量删除 |
| POST | `/api/excerpts/batch-tag` | 批量添加标签 |
| POST | `/api/excerpts/upload` | 上传图片 |
| GET/POST | `/api/tags` | 标签列表/创建 |
| PUT/DELETE | `/api/tags/{id}` | 标签更新/删除 |

---

## AI 感悟配置

支持任何 OpenAI 兼容接口。默认使用 DeepSeek：

```env
LLM_API_KEY=sk-your-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

换成其他服务只需改 URL 和 model：

```env
# 通义千问
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-turbo

# 智谱
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash
```

不配 Key 也能正常使用，点按钮会提示「请配置 API Key」。

---

## License

MIT
