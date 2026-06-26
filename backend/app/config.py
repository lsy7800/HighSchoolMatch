"""App settings from environment variables (with dev defaults).

For production, set:
  ADMIN_USERNAME, ADMIN_PASSWORD, JWT_SECRET
  SILICONFLOW_API_KEY  (用于学校简介向量化检索)
  DEEPSEEK_API_KEY     (用于智能问答 LLM)

本地开发: 启动时自动加载仓库根目录的 .env(已存在的环境变量不被覆盖,
所以 Docker 部署时 compose 注入的变量优先生效)。
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    # config.py 在 backend/app/, 仓库根 = 上溯三级
    _repo_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_repo_root / ".env", override=False)
except ImportError:
    pass


class Settings:
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    # Dev default password; OVERRIDE in production via ADMIN_PASSWORD env.
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production-0123456789")
    jwt_alg: str = "HS256"
    jwt_expire_hours: int = int(os.getenv("JWT_EXPIRE_HOURS", "12"))

    # ---- 向量检索(远程 embedding, 硅基流动 OpenAI 兼容接口) ----
    embed_api_key: str = os.getenv("SILICONFLOW_API_KEY", "")
    embed_base_url: str = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
    embed_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

    # ---- 对话 LLM(DeepSeek 官方接口) ----
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    deepseek_max_tokens: int = int(os.getenv("DEEPSEEK_MAX_TOKENS", "4096"))
    # 每个会话最多 tool-call 轮次(防死循环)
    chat_max_tool_rounds: int = int(os.getenv("CHAT_MAX_TOOL_ROUNDS", "6"))
    # 简单限流: 每 IP 每分钟最多消息数
    chat_rate_per_min: int = int(os.getenv("CHAT_RATE_PER_MIN", "20"))


settings = Settings()
