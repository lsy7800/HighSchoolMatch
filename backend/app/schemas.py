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
    school_rank: int
    student_rank: int
    min_score: float | None = None
    plan: int | None = None
    ratio: float


class RecommendResponse(BaseModel):
    score: float
    year: int
    ref_year: int
    rank_whole: int
    rank_city6: int
    equiv_score_whole: int | None = None
    equiv_score_city6: int | None = None
    out_of_range: bool
    config: dict[str, float]
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
    home_district: str | None = None
    location_district: str | None = None
    recruit_area: str | None = None
    boarding: str | None = None
    canteen: str | None = None
    class_types: str | None = None
    fee: str | None = None
    dorm_fee: str | None = None
    address: str | None = None
    phone: str | None = None
    remark: str | None = None
    stats: list[YearStat]
