# HighSchoolMatch · 天津中考志愿填报辅助系统

用学生中考分数辅助填报志愿。核心思路：**位次法**——分数逐年不可比，位次相对稳定。
学生分数经「一分档」换算成位次，再与各校历史录取位次比对，按 **冲 / 稳 / 保** 给出建议。
配套学校一览、一分一段表、智能问答（DeepSeek + 语义检索 + 位次引擎）。

> 免责声明：本系统结果仅供参考，志愿填报请以官方招生政策与正式发布数据为准。

---

## 功能总览

### 公开端（学生 / 家长）

| 页面 | 路由 | 说明 |
|---|---|---|
| 志愿推荐 | `/` | 输入分数 → 位次换算 → 冲/稳/保三档推荐学校列表，含历年位次趋势小图 |
| 学校一览 | `/schools` | 全部学校表格，支持名称/代码搜索、招生口径·所在区·性质筛选、按编号或录取分数排序；点击名称弹层看详情 |
| 智能问答 | `/chat` | 自然语言提问，SSE 流式回答；LLM 调用位次匹配 + 语义检索 + 学校详情工具 |
| 一分一段表 | `/score-rank` | 全市 / 市内六区累计位次表，支持分数定位高亮 |

### 管理后台（`/admin`，登录后可用）

- **数据导入**：上传 xlsx 导入一分档 / 高中数据，`commit=false` 预览 / `commit=true` 入库
- **学校管理**：CRUD 学校基本信息 + 历年录取数据（按年增删改）
- **数据导出**：学校列表导出为 `.xlsx` / `.csv`（含当前筛选条件）
- **一分档管理**：按年查看 / 编辑 / 删除一分档
- **阈值配置**：调整冲/稳/保分类阈值（`stable_margin` / `safe_floor` / `reach_ceiling`）
- **向量索引**：重建语义检索索引、试检索（补全学校简介后需重建）

### 智能问答能力

LLM（DeepSeek）通过 5 个工具回答家长问题，工具调用对用户透明：

| 工具 | 作用 |
|---|---|
| `recommend` | 位次法冲稳保推荐（可叠加 `candidate_codes` 与语义检索结果取交集） |
| `score_to_rank` | 分数 → 全市/市内六区位次 |
| `get_school_detail` | 按代码取学校完整信息 + 历年录取 |
| `search_schools_by_text` | 语义检索学校（"管得严的公办校"等模糊描述） |
| `get_thresholds` | 取当前冲稳保阈值 |

复合问题（如"管得严的公办校 720 分"）：模型先语义检索得候选 code，再 `recommend(score=720, candidate_codes=[...])`，交集在服务端完成，保证精确。

---

## 数据口径

- 学生范围：暂只支持**市内六区**考生（后续可扩展）。
- **填报范围**：市内六区考生只能填报「面向市内六区招生」和「面向全市招生」的学校；
  「面向郊区招生」的学校市内六区考生不能填报，**已从推荐结果与学校一览中排除**（数据仍在库中）。
- 一分档同时含「全市累计」「市内六区累计」两列，按学校招生口径配对：

  | 学校招生范围 | 用学生的哪个位次 | 比对学校的哪列 | 市内六区考生可报 |
  |---|---|---|---|
  | 面向市内六区 | 市内六区位次 | 市区录取位次 | ✅ |
  | 面向全市 | 全市位次 | 全市录取位次 | ✅ |
  | 面向郊区 | 全市位次 | 全市录取位次 | ❌ 不可报 |

- 数据按 `year` 版本化，2026 与 2025 并存，后台可直接替换。

### 学校字段（2026 数据源）

基本信息：`code` · `scope`(city6/whole/suburb) · `name` · `location_district` · `type`(公办/民办) · `boarding` · `canteen` · `class_types` · `fee` · `fee_reduction`
扩展信息：`subject_model`(选科模式) · `class_adjust`(调班机制) · `schedule`(作息) · `remark` · `other_info`
**`intro`（学校简介）**：手动补全，**不从 xlsx 导入**——它是语义检索的主体，需在后台逐校填写后重建向量索引。

### 语义检索方案

- **模型**：bge-m3（硅基流动远程 embedding，OpenAI 兼容接口）
- **存储**：无向量数据库。137~278 所学校直接存 SQLite `school_embedding` 表（float32 二进制），内存里暴力余弦相似度，亚毫秒级
- **增量**：按 `doc_hash + model` 增量重建，只重算变更项；re-seed 后自动清理孤儿向量
- **文档构造**：`名称 + 性质 + 所在区 + 班型 + 简介`——长结构化字段（作息/选科）各校相似会稀释信号，不纳入向量，由 `get_school_detail` 按需取

---

## 技术栈

- **后端**：FastAPI + SQLAlchemy 2.0 + SQLite + pydantic v2 + openpyxl
- **前端**：Vue 3 + Vite + Element Plus + Vue Router + marked + DOMPurify
- **LLM / 检索**：DeepSeek 官方 API（tool calling）+ 硅基流动 bge-m3 embedding
- **部署**：Docker Compose（前端 nginx 托管静态产物并反代 `/api`、`/health`；后端 FastAPI + SQLite 卷持久化）

## 目录结构

```
HighSchoolMatch/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI 入口
│   │   ├── config.py          环境变量配置(本地自动加载 .env)
│   │   ├── database.py        SQLAlchemy 引擎 + 轻量迁移(_ensure_schema)
│   │   ├── models.py          School / SchoolStat / ScoreRank / SchoolEmbedding
│   │   ├── schemas.py         pydantic 模型
│   │   ├── matching.py        位次法引擎(冲稳保)
│   │   ├── embedding.py       远程 embedding 客户端 + 余弦相似度
│   │   ├── retrieval.py       向量建索引 + 检索
│   │   ├── chat.py            DeepSeek tool-calling + SSE 流式
│   │   ├── auth.py            JWT + bcrypt
│   │   ├── importers/         schools_xlsx.py / score_rank_xlsx.py
│   │   └── routers/           public.py / admin.py
│   ├── scripts/seed.py        一次性导入 一分档 + 高中数据 + 校验
│   ├── data/app.db            (gitignored, 由 seed 生成)
│   ├── Dockerfile
│   ├── docker-entrypoint.sh   首次启动自动 seed
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/             Home / SchoolsView / ChatView / ScoreRank + admin/*
│   │   ├── components/        SchoolSheet / TrendChart / SchoolCard
│   │   ├── api/index.js       axios 封装 + SSE 流式 fetch
│   │   ├── router.js
│   │   └── styles.css         全局样式 + 色彩系统
│   ├── nginx.conf             反代 + SSE 缓冲关闭 + SPA 回退
│   └── Dockerfile             多阶段构建(node → nginx)
├── data_source/               原始 xlsx / pdf（参照 + seed 用）
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 本地开发

### 后端

推荐用 [uv](https://docs.astral.sh/uv/)（已提供 `backend/pyproject.toml` + `uv.lock`）：

```bash
cd backend
uv sync                                  # 创建 .venv 并安装依赖
uv run python -m scripts.seed            # 建库 + 导入 一分档 + 高中数据 + 校验
uv run uvicorn app.main:app --reload     # http://127.0.0.1:8000
uv run pytest                            # 测试
```

或用 pip：

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd backend && python -m scripts.seed
```

校验通过应输出：`Validation OK — seed complete. (city6=88 whole=49 total=137)`。

### 前端

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (dev 代理已转发 /api → 后端 8000)
```

需同时运行后端。学生端在 `/`，管理后台在 `/admin`（默认 `admin` / `admin123`，**生产环境务必用环境变量覆盖**）。

### 补全学校简介（闭环）

`intro` 不在 xlsx 里，需手动补：

1. 后台「学校管理」→ 编辑学校 → 填写「简介」→ 保存；或导出 xlsx 离线填写
2. 补完后**重建向量索引**：后台调用 `POST /api/admin/embeddings/reindex`，或后续在后台 UI 一键重建
3. 重建为增量，按 `doc_hash` 只重算 intro 变更的学校

---

## Docker 部署

整个项目（前端 + 后端）用 docker compose 一键部署：后端 FastAPI + SQLite（命名卷持久化），前端 nginx 托管静态产物并反代 `/api`、`/health`。**首次启动自动 seed**（一分档 + 高中数据），之后重启不重复导入。

### 1. 准备环境变量

```bash
cp .env.example .env
vi .env
```

必填项：

| 变量 | 用途 | 获取 |
|---|---|---|
| `ADMIN_PASSWORD` | 管理后台密码 | 自定强密码 |
| `JWT_SECRET` | 登录令牌签名 | 随机长字符串 |
| `SILICONFLOW_API_KEY` | 学校简介向量化（bge-m3） | https://siliconflow.cn 控制台新建令牌 |
| `DEEPSEEK_API_KEY` | 智能问答 LLM | https://platform.deepseek.com → API Keys |

可选项：

| 变量 | 默认 | 说明 |
|---|---|---|
| `ADMIN_USERNAME` | admin | 管理员用户名 |
| `JWT_EXPIRE_HOURS` | 12 | 令牌有效期 |
| `DEEPSEEK_MODEL` | deepseek-v4-flash | 对话模型 |
| `DEEPSEEK_MAX_TOKENS` | 4096 | 单次最大 token |
| `CHAT_MAX_TOOL_ROURDS` | 6 | 单会话 tool-call 轮次上限（防死循环） |
| `CHAT_RATE_PER_MIN` | 20 | 每 IP 每分钟提问上限 |
| `HTTP_PORT` | 80 | 对外端口 |

### 2. 构建并启动

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f backend     # 首次可见 seed 输出与 Validation OK
```

### 3. 访问

- 学生端：`http://<服务器IP>:<HTTP_PORT>/`
- 管理后台：`http://<服务器IP>:<HTTP_PORT>/admin`
- 健康检查：`http://<服务器IP>:<HTTP_PORT>/health`

### 部署说明

- 前后端**同源**（nginx 反代 `/api`），浏览器无 CORS 问题；SSE 流式通过 `proxy_buffering off` + 后端 `X-Accel-Buffering: no` 实时下发
- SQLite 数据持久化在命名卷 `backend-data`；删除数据需 `docker compose down -v`
- 后端容器**不对外暴露端口**，仅经前端 nginx 反代访问
- 数据更新：后台导入新 xlsx（`commit=true` 入库）后，如有 intro 变更需重建向量索引

### HTTPS / 域名

在 `docker compose` 前再加一层反代（Caddy / Nginx + certbot）终结 TLS，再转发到 `HTTP_PORT` 即可。

---

## API 概览

### 公开接口（`/api`，无需登录）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/years` | 一分档可用年份（降序） |
| GET | `/score-rank?year=` | 某年一分一段表 |
| POST | `/recommend` | 位次法冲稳保推荐 |
| GET | `/districts` | 学校所在区去重列表（筛选用） |
| GET | `/schools?q=&scope=&type=&district=` | 学校列表 + 最新一年录取摘要 |
| GET | `/schools/{code}` | 学校详情（含全市/郊区多条招生线 + 历年 stats） |
| POST | `/chat` | 智能问答（SSE 流式，按 IP 限流） |

### 管理接口（`/api/admin`，需 `Authorization: Bearer <token>`）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/login` | 表单登录 → access_token |
| GET | `/me` | 当前用户 |
| POST | `/import/score-rank` | 上传一分档 xlsx |
| POST | `/import/schools` | 上传高中 xlsx |
| GET | `/schools` | 学校列表（管理视图） |
| GET | `/schools/export?format=` | 导出 xlsx/csv |
| POST/PUT/DELETE | `/schools/{id}` | 学校 CRUD |
| PUT/DELETE | `/schools/{id}/stat[/{year}]` | 历年录取数据增删改 |
| GET/PUT/DELETE | `/score-rank[/{year}]` | 一分档管理 |
| GET/PUT | `/config` | 冲稳保阈值 |
| POST | `/embeddings/reindex` | 重建向量索引 |
| GET | `/embeddings/search?q=` | 试检索 |

---

## 进度

- [x] M1 项目骨架 + 数据库模型 + 2026 数据导入与校验
- [x] M2 匹配引擎（位次换算 / 等位分 / 冲稳保）+ 公开 API
- [x] M3 前端学生端（志愿推荐 / 学校一览 / 一分一段表，Vue3 + Element Plus）
- [x] M4 管理后台（登录 + xlsx 导入 + CRUD + 阈值配置 + 导出）
- [x] M5 向量检索（bge-m3 远程 embedding + 内存余弦 + 增量索引）
- [x] M6 智能问答（DeepSeek tool-calling + SSE 流式 + markdown 渲染）
- [x] M7 Docker Compose 一键部署（nginx 反代 + 自动 seed + 卷持久化）
