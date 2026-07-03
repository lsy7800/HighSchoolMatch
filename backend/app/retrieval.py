"""学校语义检索: 建索引 + 查询。

向量来自远程 embedding(见 embedding.py), 存在 school_embedding 表。
无向量数据库: 278 条直接内存里算余弦。

文档构造: 名称 + 性质 + 所在区 + 班型 + 简介。简介为空时也能按基本信息检索;
简介补全后语义检索效果提升。重建索引按 doc_hash 增量, 只重算变更项。
"""
import hashlib
from array import array

from sqlalchemy.orm import Session

from .config import settings
from .embedding import Embedder, cosine
from .models import School, SchoolEmbedding

_SCOPE_LABEL = {"city6": "市内六区", "whole": "全市", "suburb": "郊区"}


def _school_doc(s: School) -> str:
    """拼接用于向量化的文档。各字段以换行分隔, 空字段跳过。

    以简介(intro)为语义主体——它是为检索而写的校风/特色摘要。
    结构化长文本(作息/选科/调班)各校相似、会稀释 intro 信号, 不纳入向量,
    需要时由 get_school_detail 工具按需取。
    """
    parts = [s.name, s.type, s.location_district, s.class_types, s.intro]
    return "\n".join(p for p in parts if p)


def _doc_hash(doc: str) -> str:
    return hashlib.sha1(doc.encode("utf-8")).hexdigest()


def _vec_to_bytes(vec: list[float]) -> bytes:
    return array("f", vec).tobytes()  # float32 little-endian


def _bytes_to_vec(b: bytes) -> list[float]:
    a = array("f")
    a.frombytes(b)
    return list(a)


def _brief(s: School, score: float) -> dict:
    intro = (s.intro or "").strip()
    return {
        "id": s.id,
        "code": s.code,
        "name": s.name,
        "scope": s.scope,
        "scope_label": _SCOPE_LABEL.get(s.scope, s.scope),
        "type": s.type,
        "location_district": s.location_district,
        "score": round(score, 4),
        "intro_snippet": intro[:80] + ("…" if len(intro) > 80 else ""),
    }


def reindex(db: Session) -> dict:
    """重建向量索引。按 doc_hash + model 增量: 只向量化变更/缺失的学校。"""
    emb = Embedder.from_settings()
    schools = db.query(School).order_by(School.code).all()
    existing = {row.school_id: row for row in db.query(SchoolEmbedding).all()}

    # 清理孤儿向量: school 已被 re-seed 删除/换 id 后, 旧 school_id 的向量无意义
    current_ids = {s.id for s in schools}
    orphan = [sid for sid in existing if sid not in current_ids]
    if orphan:
        db.query(SchoolEmbedding).filter(SchoolEmbedding.school_id.in_(orphan)).delete()
        for sid in orphan:
            existing.pop(sid, None)

    targets: list[tuple[School, str]] = []
    for s in schools:
        doc = _school_doc(s)
        if not doc.strip():
            continue  # 无任何文本的学校跳过
        cur = existing.get(s.id)
        if cur and cur.model == settings.embed_model and cur.doc_hash == _doc_hash(doc):
            continue  # 未变更, 跳过
        targets.append((s, doc))

    if not targets:
        return {"embedded": 0, "skipped": len(schools), "total": len(schools), "model": settings.embed_model}

    vectors = emb.embed([doc for _, doc in targets])
    for (s, doc), vec in zip(targets, vectors):
        row = existing.get(s.id)
        if row is None:
            row = SchoolEmbedding(school_id=s.id)
            db.add(row)
        row.model = settings.embed_model
        row.dim = len(vec)
        row.doc_hash = _doc_hash(doc)
        row.vec = _vec_to_bytes(vec)
    db.commit()
    return {
        "embedded": len(targets),
        "skipped": len(schools) - len(targets),
        "total": len(schools),
        "model": settings.embed_model,
    }


def search(db: Session, query: str, k: int = 10) -> list[dict]:
    """语义检索学校。返回 top-k, 带相似度分数。"""
    query = (query or "").strip()
    if not query:
        return []
    emb = Embedder.from_settings()
    qv = emb.embed_one(query)

    rows = (
        db.query(SchoolEmbedding)
        .filter(SchoolEmbedding.model == settings.embed_model)
        .all()
    )
    if not rows:
        return []

    scored: list[tuple[float, int]] = []
    for r in rows:
        vec = _bytes_to_vec(r.vec)
        scored.append((cosine(qv, vec), r.school_id))
    scored.sort(reverse=True)

    top = scored[: max(0, k)]
    if not top:
        return []
    ids = [sid for _, sid in top]
    schools = {s.id: s for s in db.query(School).filter(School.id.in_(ids)).all()}
    # 保持按分数排序
    return [_brief(schools[sid], sc) for sc, sid in top if sid in schools]
