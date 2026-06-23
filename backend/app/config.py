"""App settings from environment variables (with dev defaults).

For production, set:
  ADMIN_USERNAME, ADMIN_PASSWORD, JWT_SECRET
"""
import os


class Settings:
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    # Dev default password; OVERRIDE in production via ADMIN_PASSWORD env.
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production-0123456789")
    jwt_alg: str = "HS256"
    jwt_expire_hours: int = int(os.getenv("JWT_EXPIRE_HOURS", "12"))


settings = Settings()
