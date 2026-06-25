
# 句集 / Excerpt

> 记录书中摘抄，书写个人感悟，打标签分类，快速检索回顾。
> *A quiet corner for the sentences that stay with you — record, reflect, and revisit.*

---

## 功能 / Features

- 📚 **书籍管理** — 添加/编辑/删除书籍，按书籍分组浏览摘抄
- ✍️ **摘抄记录** — 记录原文 + 个人感悟 + 相关链接 + 图片
- 🏷️ **标签分类** — 多标签管理，自由创建/重命名/变色，彩色标记
- 🔍 **全文检索** — MySQL ngram 中文分词 + LIKE 回退，搜索摘抄内容和个人想法
- 🎯 **标签联合筛选** — AND 逻辑精确匹配多个标签
- ⭐ **收藏功能** — 星标重要摘抄，一键筛选查看精华
- 🎲 **随机摘抄** — 书架页「今日摘抄」卡片，偶遇旧日灵感
- 📝 **导出** — 支持 Markdown / JSON 格式导出全部摘抄
- 🖼️ **图片上传** — 摘抄关联插图，支持预览
- 🌙 **暗色模式** — 亮/暗主题切换，localStorage 记忆偏好
- ⌨️ **快捷键** — `Ctrl+K` 快速聚焦搜索
- 📱 **响应式布局** — 手机端自适应
- 🔄 **Alembic 迁移** — 数据库 schema 版本管理
- 🏠 **纯本地部署** — 无 Docker，一键启动

---

## 技术栈 / Tech Stack

| 层 / Layer | 技术 / Technology |
|------------|-------------------|
| 后端 / Backend | Python 3.10+ / FastAPI / Uvicorn |
| ORM | SQLAlchemy 2.0 + aiomysql (async) |
| 迁移 / Migrations | Alembic |
| 数据库 / Database | MySQL 8.0 + ngram full-text index |
| 前端 / Frontend | Vue 3 (Composition API) + Vite |
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

### 2. 配置环境变量 / Configure Environment

编辑 `backend/.env`（首次从 init.sql 创建的用户名密码已匹配默认值）：

```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=memo
MYSQL_PASSWORD=memopass
MYSQL_DATABASE=memo_db
UPLOAD_DIR=./
```

### 3. 启动后端 / Start Backend

```bash
cd backend
pip install -r requirements.txt
# 应用数据库迁移（init.sql 之后的需要）
alembic upgrade head
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

> 启动时自动创建未存在的表和 FULLTEXT 索引，无需手动 DDL。

### 4. 启动前端 / Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. 访问 / Open

浏览器打开 `http://localhost:5173`

---

## 项目结构 / Project Structure

```
memo-app/
├── init.sql                       # 数据库初始化脚本
├── README.md
├── backend/
│   ├── .env                       # MySQL + 上传目录配置
│   ├── requirements.txt
│   ├── alembic.ini                # Alembic 迁移配置
│   ├── main.py                    # FastAPI 入口 + 自动建表 + 异常处理
│   ├── database.py                # 异步引擎 + Session 工厂
│   ├── models.py                  # ORM 模型 (Book/Excerpt/Tag/ExcerptTag)
│   ├── schemas.py                 # Pydantic 请求/响应模型
│   ├── migrations/                # Alembic 迁移文件
│   ├── routers/
│   │   ├── books.py               # 书籍 CRUD + 分组 + 更新
│   │   ├── excerpts.py            # 摘抄 CRUD + 全文检索 + 图片上传 + 导出 + 收藏 + 批量
│   │   └── tags.py                # 标签 CRUD + 更新
│   └── uploads/                   # 上传图片存储目录
└── frontend/
    ├── index.html
    ├── vite.config.js             # API 代理配置
    ├── package.json
    └── src/
        ├── main.js                # 入口 + Element Plus 全局注册
        ├── App.vue                # 顶层布局 + 暗色模式 + Ctrl+K
        ├── api/
        │   └── index.js           # Axios 实例 + 全局错误拦截 + 所有 API 函数
        ├── stores/
        │   └── appStore.js        # 共享状态缓存（标签/书籍）
        └── components/
            ├── BookList.vue       # 书架主视图 + 今日摘抄 + 导出
            ├── AddExcerpt.vue     # 添加摘抄表单
            ├── SearchView.vue     # 检索视图 + 高亮 + 收藏筛选 + 标签管理
            └── TagManager.vue     # 标签管理对话框（共享组件）
```

---

## API 概要 / API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | 健康检查 |
| GET/POST/DELETE | `/api/books` | 书籍列表/创建 |
| GET/PUT | `/api/books/{id}` | 书籍详情/更新 |
| GET | `/api/books/groups` | 按书分组摘抄 |
| GET/POST | `/api/excerpts` | 摘抄搜索/创建 |
| GET/PUT/DELETE | `/api/excerpts/{id}` | 摘抄详情/更新/删除 |
| PUT | `/api/excerpts/{id}/favorite` | 切换收藏 |
| GET | `/api/excerpts/random` | 随机摘抄 |
| GET | `/api/excerpts/export?fmt=md\|json` | 导出摘抄 |
| POST | `/api/excerpts/batch-delete` | 批量删除 |
| POST | `/api/excerpts/batch-tag` | 批量添加标签 |
| POST | `/api/excerpts/upload` | 上传图片 |
| GET/POST/DELETE | `/api/tags` | 标签列表/创建 |
| PUT | `/api/tags/{id}` | 标签更新（重命名/变色） |

---

## 搜索说明 / Search Notes

- **中文搜索**使用 `LIKE` 模糊匹配（兼容性好，无需分词器配置）
- **英文搜索**使用 MySQL FULLTEXT BOOLEAN MODE
- 支持同时按关键词 + 标签 + 书籍 + 收藏状态组合筛选
- 标签筛选为 AND 逻辑（摘抄必须拥有所有选中标签）

---

## License

MIT
