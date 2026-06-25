# 项目 Prompt：读书摘抄检索系统

> 将此 Prompt 发送给任意 AI，可一次性生成完整可运行的全栈项目。

---

## 一、项目概述

开发一个**读书摘抄检索系统**——记录书中摘抄原文，添加个人见解，打标签分类，通过关键词全文检索和标签联合筛选快速查找。

**核心领域模型**：一本书 → 多条摘抄 → 每条摘抄包含"原文"+"个人想法"+"标签"

---

## 二、技术栈（严格遵循）

| 层 | 技术 | 说明 |
|---|------|------|
| 后端 | Python 3.10+ / FastAPI / Uvicorn | 异步 REST API |
| ORM | SQLAlchemy 2.0 + aiomysql | 异步引擎 |
| 数据库 | MySQL 8.0 | InnoDB，ngram 中文全文索引 |
| 前端 | Vue 3 (Composition API + `<script setup>`) + Vite | SPA |
| UI 库 | Element Plus 2.x + @element-plus/icons-vue | 全局图标注册 |
| HTTP | Axios | 前端请求 |
| 图片 | 后端本地存储 `/uploads`，FastAPI StaticFiles 挂载 `/static` | python-multipart |
| 部署 | 纯本地，无 Docker | 一键 `uvicorn` + `npm run dev` |

---

## 三、数据库设计（MySQL 8.0）

### 3.1 初始化脚本 `init.sql`

```sql
DROP DATABASE IF EXISTS memo_db;
CREATE DATABASE memo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE memo_db;

CREATE USER IF NOT EXISTS 'memo'@'%' IDENTIFIED BY 'memopass';
GRANT ALL PRIVILEGES ON memo_db.* TO 'memo'@'%';
FLUSH PRIVILEGES;
```

### 3.2 表结构

#### books（书籍表）

| 列 | 类型 | 约束 |
|----|------|------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT |
| title | VARCHAR(255) | NOT NULL |
| author | VARCHAR(255) | DEFAULT '' |
| cover | VARCHAR(500) | DEFAULT '' |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| | | UNIQUE(title, author) |

#### excerpts（摘抄表）

| 列 | 类型 | 约束 |
|----|------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT |
| book_id | INT UNSIGNED | FK→books.id ON DELETE CASCADE |
| content | TEXT | 摘抄原文 |
| insights | TEXT | 个人想法/评论 |
| links | JSON | DEFAULT (JSON_ARRAY()) |
| images | JSON | DEFAULT (JSON_ARRAY()) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP |
| | | FULLTEXT INDEX ft_excerpt (content, insights) WITH PARSER ngram |

#### tags（标签表）

| 列 | 类型 | 约束 |
|----|------|------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT |
| name | VARCHAR(50) | UNIQUE, NOT NULL |
| color | VARCHAR(7) | DEFAULT '#409EFF' |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

#### excerpt_tags（关联表）

| 列 | 类型 |
|----|------|
| excerpt_id | BIGINT UNSIGNED FK→excerpts.id CASCADE |
| tag_id | INT UNSIGNED FK→tags.id CASCADE |
| | PK(excerpt_id, tag_id) |

### 3.3 预置标签

```
哲学(#409EFF)、心理学(#67C23A)、文学(#E6A23C)、金句(#F56C6C)、方法论(#909399)、待整理(#9254DE)
```

---

## 四、后端 API 设计

### 4.1 项目结构

```
backend/
├── .env                  # MYSQL_HOST/PORT/USER/PASSWORD/DATABASE + UPLOAD_DIR=./
├── requirements.txt      # fastapi/uvicorn[standard]/sqlalchemy[asyncio]/aiomysql/python-dotenv/python-multipart/pydantic
├── main.py               # FastAPI app + CORS + StaticFiles + router 注册
├── database.py            # create_async_engine(mysql+aiomysql) + async_sessionmaker + get_db 依赖
├── models.py              # Book/Excerpt/Tag/ExcerptTag ORM 模型，每个带 to_dict()
├── schemas.py             # Pydantic v2 请求/响应模型
├── routers/
│   ├── books.py           # 书籍 CRUD + 分组接口
│   ├── excerpts.py        # 摘抄 CRUD + 全文检索 + 图片上传
│   └── tags.py            # 标签 CRUD
└── uploads/               # 图片上传目录
```

### 4.2 API 端点

#### 健康检查
```
GET /api/health → {"status":"ok"}
```

#### 书籍
```
GET    /api/books              → 书籍列表（含 excerpt_count）
POST   /api/books              → 创建书籍 {title, author?, cover?}
DELETE /api/books/{id}         → 删除书籍（级联删除所有摘抄）
GET    /api/books/groups       → 按书籍分组的摘抄列表（主页核心接口）
         ?book_id= 可选筛选
```

**groups 响应结构**：
```json
[{ "book": {...}, "excerpts": [{...}, {...}] }]
```
摘抄按 updated_at 倒序排列，关联 book 和 tags。

#### 摘抄
```
POST   /api/excerpts           → 创建 {book_id, content?, insights?, links[], images[], tag_ids[]}
GET    /api/excerpts           → 搜索/列表
         ?keyword=           → 全文检索（搜索 content+insights，BOOLEAN MODE，前缀+）
         &tag_ids=1,2,3      → 标签联合筛选（AND 逻辑，HAVING COUNT 精确匹配）
         &book_id=            → 筛选书籍
         &page=&page_size=
GET    /api/excerpts/{id}      → 详情
PUT    /api/excerpts/{id}      → 更新（可选字段+可选标签替换）
DELETE /api/excerpts/{id}      → 删除
POST   /api/excerpts/upload    → 上传图片（multipart/form-data "file"）
         → {"url":"/static/xxx.png","filename":"xxx.png"}
```

#### 标签
```
GET    /api/tags               → 全部标签
POST   /api/tags               → 创建 {name, color?}
DELETE /api/tags/{id}          → 删除
```

### 4.3 关键后端实现细节

- **全文检索**：使用 `MATCH(content, insights) AGAINST(:kw IN BOOLEAN MODE)`，关键词加 `+` 前缀
- **标签联合筛选**：子查询 `excerpt_tags` 表，`GROUP BY ... HAVING COUNT = N` 确保匹配所有标签
- **图片上传**：`uuid.uuid4().hex` 重命名，存入本地 `uploads/`，StaticFiles 挂载 `/static`
- **CORS**：`allow_origins=["*"]`
- **database.py**：`mysql+aiomysql://user:pass@host:port/db?charset=utf8mb4`

---

## 五、前端设计

### 5.1 项目结构

```
frontend/
├── index.html
├── package.json          # vue3 / axios / element-plus / @element-plus/icons-vue / vite / @vitejs/plugin-vue
├── vite.config.js        # proxy /api→127.0.0.1:8000, /static→127.0.0.1:8000
└── src/
    ├── main.js           # createApp + ElementPlus.use + 全局注册 icons
    ├── App.vue           # 顶部标题 + el-tabs（书架/检索）
    ├── api/
    │   └── index.js      # Axios 实例 baseURL:/api，导出所有 API 函数
    └── components/
        ├── BookList.vue       # 书架主视图（含添加书籍/摘抄功能）
        ├── AddExcerpt.vue     # 添加摘抄表单（可嵌入 Dialog 使用）
        └── SearchView.vue     # 检索视图
```

### 5.2 页面布局与交互

#### App.vue — 顶层框架
- 顶部居中标题"读书摘抄" + 副标题
- `el-tabs` 两个标签页：**书架** | **检索**
- watch activeTab：切换标签时自动调用子组件 refresh()

#### BookList.vue — 书架（主视图）

**顶部**：右侧圆形棕色 + 按钮 → 点击弹出"添加书籍"Dialog
- Dialog 内含：书名(必填) + 作者(选填) → POST /api/books

**书籍分组可折叠列表**：
- 每本书一个白色卡片，点击标题行展开/收起
- 标题行：▶箭头(折叠动画旋转90°) + 书名 + 作者 + 摘抄数量tag
- 标题行右侧按钮：
  - **+ 摘抄** — 弹出摘抄 Dialog，自动预选该书
  - **删除** — 二次确认后删除整本书

**展开后三列并排摘抄卡片**：
- 左列(棕色左边框)：摘抄原文
- 中列(蓝色左边框)：个人想法
- 右列(max 140px)：彩色 tag 标签
- 下方：链接列表、图片网格(可预览)、时间戳
- 右下角：编辑 / 删除 按钮

**编辑摘抄 Dialog**：
- 可改书籍、原文、想法、链接、标签

**添加摘抄 Dialog**（`destroy-on-close`）：
- 直接复用 `<AddExcerpt>` 组件
- 传入 `preset-book-id` prop 预选书籍
- 保存后自动关闭并刷新书架

#### AddExcerpt.vue — 添加摘抄表单

**Props**：`presetBookId: Number` — 预选书籍 ID，`watch` 监听自动填充

**表单字段**：
- 所属书籍：`el-select` 下拉（filterable，仅选已有书籍）
- 摘抄原文：textarea 6行，maxlength 5000
- 个人想法：textarea 3行，maxlength 5000
- 相关链接：动态增删行，每行 input+删除按钮
- 图片：`el-upload`（before-upload 返回 false，手动调用 /upload API），预览网格，可删除
- 标签：`el-select` multiple + filterable + allow-create
  - 输入新标签名 → `@change` 检测 string 类型 → 自动 POST /api/tags 创建
  - 已选标签显示为可删除 tag chip

**标签管理**：表单项 label 右侧有"管理标签"链接按钮
- 弹出 Dialog：顶部**添加区**（input + el-color-picker + 添加按钮）
- 下方列表：每行色点 + 标签名 + 删除按钮（二次确认）

#### SearchView.vue — 检索

- 搜索栏：`el-input` 大号 + 搜索按钮，回车触发
- 标签筛选：`el-checkbox-group` 内嵌彩色 tag，勾选触发搜索
- 结果统计："共找到 N 条摘抄"
- 结果卡片：
  - 书名行（📖图标 + 书名 + 作者）
  - 摘抄原文（棕色左边框）
  - 个人想法（蓝色左边框）
  - 标签、链接、图片、时间
- 分页：`el-pagination` prev/pager/next
- `refresh()` 同时重新拉取标签和搜索结果

### 5.3 前端关键实现细节

- **Vite 代理**：`proxy: { '/api': 'http://127.0.0.1:8000', '/static': 'http://127.0.0.1:8000' }`
- **全局图标**：在 main.js 中 `for...of Object.entries(ElementPlusIconsVue)` 全局注册
- **axios 实例**：`baseURL: '/api'`, `timeout: 15000`
- **API 函数**：`getBooks/createBook/deleteBook/getBookGroups`、`createExcerpt/getExcerpts/getExcerpt/updateExcerpt/deleteExcerpt/uploadImage`、`getTags/createTag/deleteTag`
- **颜色方案**：暖色书本主题 `#f5f0eb` 背景，`#5c4a32` 主色，`#3d3226` 文字

---

## 六、启动流程

### 1. 初始化数据库
```bash
mysql -u root -p < init.sql
# 密码根据本地 MySQL root 密码填写
```

### 2. 启动后端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 4. 访问
浏览器打开 `http://localhost:5173`

---

## 七、环境变量

`backend/.env`：
```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=memo
MYSQL_PASSWORD=memopass
MYSQL_DATABASE=memo_db
UPLOAD_DIR=./
```

---

## 八、关键约束

- 不使用 Docker
- 所有代码完整可运行，无省略占位符
- 后端用异步引擎（async/await）
- 标签允许多选 + 动态创建
- 摘抄卡片摘要与想法三列水平并排
- 添加书籍和添加摘抄为独立入口
- 添加书籍：书架顶部 + 号按钮
- 添加摘抄：每本书标题行右侧 + 摘抄按钮
