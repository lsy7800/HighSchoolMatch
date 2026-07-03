"""ORM models for the admission-matching system.

Year-versioned design so 2026 data can be loaded alongside 2025
without deleting history.

  score_rank   一分档 (one row per score band per year)
  school       学校静态属性 (keyed by business code)
  school_stat  逐年录取数据 (wide Excel columns un-pivoted to long rows)
  app_config   可调参数 (冲/稳/保 阈值等)
"""
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# Recruitment scopes — determines which rank column is used when matching.
SCOPE_CITY6 = "city6"   # 面向市内六区招生  -> 用市内六区位次
SCOPE_WHOLE = "whole"   # 面向全市招生      -> 用全市位次
SCOPE_SUBURB = "suburb"  # 面向郊区招生      -> 用全市位次


class ScoreRank(Base):
    """一分档: 分数 <-> 累计人数(位次). One row per integer score per year."""

    __tablename__ = "score_rank"
    __table_args__ = (UniqueConstraint("year", "score", name="uq_year_score"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    score: Mapped[int] = mapped_column(Integer, index=True)
    cum_whole: Mapped[int] = mapped_column(Integer)      # 全市累计 (city_sum)
    cum_city6: Mapped[int] = mapped_column(Integer)      # 市内六区累计 (districts_sum)
    band_whole: Mapped[int] = mapped_column(Integer)     # 全市该分人数 (cum diff)
    band_city6: Mapped[int] = mapped_column(Integer)     # 市内六区该分人数 (cum diff)


class School(Base):
    """学校静态属性.

    A school may recruit under more than one scope (e.g. 天津六力 appears in
    both 全市 and 郊区 with different cutoffs), so the natural key is
    (code, scope), not code alone — each scope is a distinct admission channel.
    """

    __tablename__ = "school"
    __table_args__ = (UniqueConstraint("code", "scope", name="uq_code_scope"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, index=True)
    scope: Mapped[str] = mapped_column(String, index=True)  # SCOPE_*
    name: Mapped[str] = mapped_column(String, index=True)
    location_district: Mapped[str | None] = mapped_column(String, nullable=True)  # 所在区
    type: Mapped[str | None] = mapped_column(String, nullable=True)               # 公办/民办
    boarding: Mapped[str | None] = mapped_column(String, nullable=True)           # 住宿
    canteen: Mapped[str | None] = mapped_column(String, nullable=True)            # 餐饮
    class_types: Mapped[str | None] = mapped_column(String, nullable=True)        # 班型设置
    subject_model: Mapped[str | None] = mapped_column(Text, nullable=True)        # 选科模式
    class_adjust: Mapped[str | None] = mapped_column(Text, nullable=True)         # 调班机制
    schedule: Mapped[str | None] = mapped_column(Text, nullable=True)             # 作息
    fee: Mapped[str | None] = mapped_column(String, nullable=True)                # 学费
    fee_reduction: Mapped[str | None] = mapped_column(String, nullable=True)      # 学费减免
    remark: Mapped[str | None] = mapped_column(String, nullable=True)             # 备注
    other_info: Mapped[str | None] = mapped_column(Text, nullable=True)           # 其他情况
    intro: Mapped[str | None] = mapped_column(Text, nullable=True)               # 学校简介(手动补全, 不从xlsx导入)

    stats: Mapped[list["SchoolStat"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )


class SchoolStat(Base):
    """逐年录取数据 (一所学校一年一行)."""

    __tablename__ = "school_stat"
    __table_args__ = (UniqueConstraint("school_id", "year", name="uq_school_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("school.id"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    plan: Mapped[int | None] = mapped_column(Integer, nullable=True)          # 招生计划
    min_score: Mapped[float | None] = mapped_column(Float, nullable=True)     # 录取最低分
    rank_city6: Mapped[int | None] = mapped_column(Integer, nullable=True)    # 市区录取位次 (仅六区表)
    rank_whole: Mapped[int | None] = mapped_column(Integer, nullable=True)    # 全市录取位次

    school: Mapped["School"] = relationship(back_populates="stats")


class SchoolEmbedding(Base):
    """学校简介的向量(用于语义检索)。一所学校一条, 按 doc_hash 增量更新。"""

    __tablename__ = "school_embedding"

    school_id: Mapped[int] = mapped_column(ForeignKey("school.id"), primary_key=True)
    model: Mapped[str] = mapped_column(String)         # 生成该向量所用模型, 换模型需重建
    dim: Mapped[int] = mapped_column(Integer)
    doc_hash: Mapped[str] = mapped_column(String)      # 源文档 sha1, 用于跳过未变更项
    vec: Mapped[bytes] = mapped_column(LargeBinary)    # float32 little-endian(array.tobytes)


class AppConfig(Base):
    """Key-value config (e.g. 冲/稳/保 阈值)."""

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String)
