# HighSchoolMatch · 中考志愿填报辅助系统

用学生中考分数辅助填报中考志愿。核心思路：**位次法**——分数逐年不可比，位次相对稳定。
学生分数经「一分档」换算成位次，再与各校历史录取位次比对，按 **冲 / 稳 / 保** 给出建议。

## 数据口径

- 学生范围：暂只支持**市内六区**考生（后续可扩展）。
- 一分档同时含「全市累计」「市内六区累计」两列，按学校招生口径配对：
  | 学校招生范围 | 用学生的哪个位次 | 比对学校的哪列 |
  |---|---|---|
  | 面向市内六区 | 市内六区位次 | 市区录取位次 |
  | 面向全市 | 全市位次 | 全市录取位次 |
  | 面向郊区 | 全市位次 | 全市录取位次 |
- 数据按 `year` 版本化，2026 年数据可与 2025 并存，后台直接替换。

## 技术栈

- 后端：FastAPI + SQLAlchemy 2.0 + SQLite
- 前端：Vue3 + Vite（学生端 + `/admin` 管理后台）
- 数据导入：openpyxl 解析 xlsx

## 目录结构

```
backend/         FastAPI 后端
  app/           models / database / importers / routers / matching / auth
  scripts/       seed_2025.py  一次性导入 2025 数据
  data/          app.db (gitignored, 由 seed 生成)
frontend/        Vue3 前端 (待建)
data_source/     原始 PDF / xlsx 数据（参照）
```

## 本地启动（后端）

推荐用 [uv](https://docs.astral.sh/uv/) 管理（已提供 `backend/pyproject.toml` + `uv.lock`）：

```bash
cd backend
uv sync                          # 按 uv.lock 创建 .venv 并安装依赖(含开发依赖)
uv run python -m scripts.seed_2025   # 建库 + 导入 2025 数据 + 校验
uv run uvicorn app.main:app --reload # 启动后端 (http://127.0.0.1:8000)
uv run pytest                    # 运行测试
```

生产环境跳过开发依赖：`uv sync --no-dev`。

或用传统 pip（备选）：

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd backend
python -m scripts.seed_2025
```

校验通过应输出：一分档 281 档；学校 city6=81 / whole=48 / suburb=149，共 278 校。

## 进度

- [x] M1 项目骨架 + 数据库模型 + 2025 数据导入与校验
- [x] M2 匹配引擎（位次换算 / 等位分 / 冲稳保）+ 公开 API
- [x] M3 前端（学生查询端 + 管理后台，Vue3 + 纯 CSS，移动优先）
- [x] M4 管理后台后端（登录 + xlsx 导入 + CRUD + 阈值配置）
- [x] M5 打磨（等位分展示 / 历年位次趋势小图 / 文案与免责声明）

## 本地启动（前端）

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (dev 代理已转发 /api 到后端 8000)
```

需同时运行后端（见上）。学生查询页在 `/`，管理后台在 `/admin`（默认 admin / admin123）。

## 管理后台 API（M4）

需先登录拿 token，后续请求带 `Authorization: Bearer <token>`。

- `POST /api/admin/login`（表单 username/password）→ access_token
- `POST /api/admin/import/score-rank`、`/import/schools`（上传 xlsx，`commit=false` 预览 / `commit=true` 入库）
- `GET/PUT/DELETE /api/admin/schools`、`PUT /api/admin/schools/{id}/stat`
- `GET/PUT/DELETE /api/admin/score-rank`
- `GET/PUT /api/admin/config`（冲稳保阈值）

默认管理员账号 `admin` / `admin123`，**生产环境务必用环境变量覆盖**：
`ADMIN_USERNAME`、`ADMIN_PASSWORD`、`JWT_SECRET`。

> 免责声明：本系统结果仅供参考，志愿填报请以官方招生政策与正式发布数据为准。
