"""Pydantic v2 schemas for the public API."""
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    score: float = Field(..., ge=0, le=900, description="学生中考分数")
    year: int | None = Field(None, description="一分档年份(默认最新)")
    ref_year: int | None = Field(None, description="比对/等位年份(默认同 year)")


class SchoolMatch(BaseModel):
    code: str
    name: str
    scope: str
    type: str | None = None
    location_district: str | None = None
    boarding: str | None = None
    class_types: str | None = None
    school_rank: int
    student_rank: int
    min_score: float | None = None
    plan: int | None = None
    ratio: float | None = None


class RecommendResponse(BaseModel):
    score: float
    year: int
    ref_year: int
    rank_whole: int
    rank_city6: int
    equiv_score_whole: int | None = None
    equiv_score_city6: int | None = None
    out_of_range: bool
    low_score_mode: bool = False  # 分数低于一分档最低档: 改为 reachable 列表
    config: dict[str, float]
    reachable: list[SchoolMatch] = []  # 低分模式下的"能上哪所上哪所"列表
    reach: list[SchoolMatch]
    stable: list[SchoolMatch]
    safe: list[SchoolMatch]


class YearStat(BaseModel):
    year: int
    plan: int | None = None
    min_score: float | None = None
    rank_city6: int | None = None
    rank_whole: int | None = None


class SchoolDetail(BaseModel):
    code: str
    name: str
    scope: str
    type: str | None = None
    location_district: str | None = None
    boarding: str | None = None
    canteen: str | None = None
    class_types: str | None = None
    subject_model: str | None = None
    class_adjust: str | None = None
    schedule: str | None = None
    fee: str | None = None
    fee_reduction: str | None = None
    remark: str | None = None
    other_info: str | None = None
    intro: str | None = None
    stats: list[YearStat]


# ---------------- Admin ----------------
class SchoolListItem(BaseModel):
    id: int
    code: str
    name: str
    scope: str
    type: str | None = None
    location_district: str | None = None


class SchoolUpdate(BaseModel):
    """学校静态字段更新(全部可选, 只改传入的字段)。"""

    name: str | None = None
    type: str | None = None
    location_district: str | None = None
    boarding: str | None = None
    canteen: str | None = None
    class_types: str | None = None
    subject_model: str | None = None
    class_adjust: str | None = None
    schedule: str | None = None
    fee: str | None = None
    fee_reduction: str | None = None
    remark: str | None = None
    other_info: str | None = None
    intro: str | None = None


class SchoolCreate(BaseModel):
    """新增学校。code + scope + name 必填, 其余可选。

    (code, scope) 为业务主键: 同一代码可在不同招生口径下各存一条。
    """

    code: str
    scope: str  # city6 / whole / suburb
    name: str
    type: str | None = None
    location_district: str | None = None
    boarding: str | None = None
    canteen: str | None = None
    class_types: str | None = None
    subject_model: str | None = None
    class_adjust: str | None = None
    schedule: str | None = None
    fee: str | None = None
    fee_reduction: str | None = None
    remark: str | None = None
    other_info: str | None = None
    intro: str | None = None


class StatUpsert(BaseModel):
    """新增/修改某校某年的录取数据。"""

    year: int
    plan: int | None = None
    min_score: float | None = None
    rank_city6: int | None = None
    rank_whole: int | None = None


class ScoreRankUpdate(BaseModel):
    cum_whole: int | None = None
    cum_city6: int | None = None
    band_whole: int | None = None
    band_city6: int | None = None


class ConfigUpdate(BaseModel):
    """阈值配置更新, 键值对。"""

    values: dict[str, float]
