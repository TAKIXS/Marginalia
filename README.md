# Marginalia
记录书中摘抄，书写个人感悟，打标签分类，快速检索回顾。/A quiet corner for the sentences that stay with you — record, reflect, and revisit.

## 功能 / Features

- 📚 **书籍管理** — 添加/删除书籍，按书籍分组浏览摘抄
- ✍️ **摘抄记录** — 记录原文 + 个人感悟 + 相关链接 + 图片
- 🏷️ **标签分类** — 多标签管理，自由创建，彩色标记
- 🔍 **全文检索** — MySQL ngram 中文分词，搜索摘抄内容和个人想法
- 🎯 **标签联合筛选** — AND 逻辑精确匹配多个标签
- 🖼️ **图片上传** — 摘抄关联插图，支持预览
- 🏠 **纯本地部署** — 无 Docker，一键启动

---

- 📚 **Book Management** — Add/delete books, browse excerpts grouped by book
- ✍️ **Excerpt Journal** — Capture original text + personal insights + links + images
- 🏷️ **Tag System** — Multi-tag with custom colors, create tags on the fly
- 🔍 **Full-text Search** — MySQL ngram parser for Chinese, across content & insights
- 🎯 **Tag Filtering** — AND-logic filtering for precise multi-tag matching
- 🖼️ **Image Upload** — Attach images to excerpts, inline preview
- 🏠 **Local-first** — No Docker, just run and go

---

## 技术栈 / Tech Stack

| 层 / Layer | 技术 / Technology |
|------------|-------------------|
| 后端 / Backend | Python 3.10+ / FastAPI / Uvicorn |
| ORM | SQLAlchemy 2.0 + aiomysql (async) |
| 数据库 / Database | MySQL 8.0 + ngram full-text index |
| 前端 / Frontend | Vue 3 (Composition API + `<script setup>`) + Vite |
| UI | Element Plus 2.x |
| HTTP | Axios |

---

## 快速开始 / Quick Start

### 前置条件 / Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0

### 1. 初始化数据库 / Initialize Database

```bash
mysql -u root -p < init.sql
```

### 2. 启动后端 / Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 启动前端 / Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问 / Open

浏览器打开 `http://localhost:5173`

---

## 项目结构 / Project Structure

```
memo-app/
├── init.sql                  # 数据库初始化脚本 / DB init script
├── PROMPT.md                 # AI 生成项目用的完整 Prompt
├── backend/
│   ├── .env                  # MySQL + 上传目录配置
│   ├── requirements.txt
│   ├── main.py               # FastAPI 入口 + CORS + 路由注册
│   ├── database.py           # 异步引擎 + Session 工厂
│   ├── models.py             # ORM 模型 (Book/Excerpt/Tag)
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── books.py          # 书籍 CRUD + 分组接口
│   │   ├── excerpts.py       # 摘抄 CRUD + 全文检索 + 图片上传
│   │   └── tags.py           # 标签 CRUD
│   └── uploads/              # 上传图片存储目录
└── frontend/
    ├── index.html
    ├── vite.config.js        # API 代理配置
    ├── package.json
    └── src/
        ├── main.js           # 入口 + Element Plus 全局注册
        ├── App.vue           # 顶层布局（书架 / 检索）
        ├── api/
        │   └── index.js      # Axios 实例 + 所有 API 函数
        └── components/
            ├── BookList.vue   # 书架主视图
            ├── AddExcerpt.vue # 添加摘抄表单
            └── SearchView.vue # 检索视图
```

---

## API 概要 / API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | 健康检查 / Health check |
| GET/POST/DELETE | `/api/books` | 书籍 CRUD |
| GET | `/api/books/groups` | 按书分组摘抄 / Grouped excerpts |
| GET/POST | `/api/excerpts` | 摘抄列表/创建（支持检索参数） |
| GET/PUT/DELETE | `/api/excerpts/{id}` | 摘抄详情/更新/删除 |
| POST | `/api/excerpts/upload` | 上传图片 |
| GET/POST/DELETE | `/api/tags` | 标签 CRUD |

---

## 环境变量 / Environment Variables

`backend/.env`:

```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=memo
MYSQL_PASSWORD=memopass
MYSQL_DATABASE=memo_db
UPLOAD_DIR=./
```

---

## License

MIT
