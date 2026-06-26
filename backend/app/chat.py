"""智能问答编排: DeepSeek(推理模型, function calling) + 本地工具。

架构: LLM 当大脑和嘴, 本地匹配引擎当计算器, 靠 tool calling 连起来。
所有分数/位次/分类都由本地函数精确算出, 模型只负责理解意图 + 组织语言。
向量检索(retrieval)用于"管得严"这类抽象语义筛选。

流式输出 SSE 事件:
  thinking / delta / tool / done / error
"""
import json
import time
from collections import defaultdict, deque

import httpx
from sqlalchemy.orm import Session

from . import matching, retrieval
from .config import settings
from .models import School, ScoreRank

# 市内六区考生不可填报郊区招生, 详情/检索里都过滤郊区
SCOPE_LABEL = {"city6": "市内六区", "whole": "全市", "suburb": "郊区"}

SYSTEM_PROMPT = """你是「天津中考志愿助手」，面向天津市内六区考生和家长，帮助理解中考志愿填报。

核心规则:
1. 你只能基于工具返回的数据回答学校、分数、位次、录取等事实问题。涉及具体数字时必须先调用相应工具，绝不编造分数、位次、学校名单或录取数据。
2. 学校录取推荐用「位次法」: 学生分数经一分档换算成位次，再与各校往年录取位次比对，分冲/稳/保三档。调用 recommend 工具获取。
3. 市内六区考生只能填报「面向市内六区招生」和「面向全市招生」的学校；「面向郊区招生」的学校市内六区考生不可填报（工具已自动过滤）。
4. 当用户用抽象描述筛学校(如"管得严""校风自由""重视理科""有住宿")，调用 search_schools_by_text 做语义检索；如同时给了分数，再调用 recommend 并把检索到的学校代码作为 candidate_codes 传入，让两者在服务端取交集(不要自己脑补交集)。
5. 回答要简洁、通俗、有温度。不要把工具返回的全部学校逐条罗列，应归纳总结、点出重点，并主动提出可深入介绍某所。
6. 介绍单校详情(班型/住宿/历年录取)用 get_school_detail。
7. 位次换算、等位分用 score_to_rank。
8. 数据可能不完整(部分学校简介未补全)，若工具未返回相关信息，如实说明"暂无该信息"，不要臆测。

每次回答末尾附一句简短免责: 以上仅供参考，志愿填报请以教育考试院等官方信息为准。"""


# ---------------- 工具实现 ----------------
def _latest_year(db: Session) -> int | None:
    row = db.query(ScoreRank.year).order_by(ScoreRank.year.desc()).first()
    return row[0] if row else None


def _compact_school(s) -> dict:
    """recommend 结果里单校的精简表示(省 token)。兼容 dict / 对象。"""
    g = (lambda k: s.get(k)) if isinstance(s, dict) else (lambda k: getattr(s, k, None))
    scope = g("scope")
    return {
        "code": g("code"), "name": g("name"),
        "scope": SCOPE_LABEL.get(scope, scope),
        "type": g("type"), "min_score": g("min_score"),
        "school_rank": g("school_rank"), "plan": g("plan"),
    }


def _school_code(s) -> str:
    c = s.get("code") if isinstance(s, dict) else getattr(s, "code", None)
    return "" if c is None else str(c)


def _tool_recommend(db: Session, args: dict) -> dict:
    score = args.get("score")
    if score is None:
        return {"error": "缺少 score 参数"}
    year = args.get("year") or _latest_year(db)
    if year is None:
        return {"error": "无一分档数据"}
    result = matching.recommend(db, float(score), int(year), None)
    if isinstance(result, dict) and "error" in result:
        return {"error": result["error"]}

    candidate_codes = args.get("candidate_codes")
    if candidate_codes:
        cand = {str(c) for c in candidate_codes}
        for key in ("reach", "stable", "safe", "reachable"):
            if result.get(key):
                result[key] = [s for s in result[key] if _school_code(s) in cand]

    def tier(items):
        return [_compact_school(s) for s in (items or [])]

    return {
        "score": result.get("score"), "year": result.get("year"),
        "ref_year": result.get("ref_year"),
        "rank_whole": result.get("rank_whole"), "rank_city6": result.get("rank_city6"),
        "equiv_score_city6": result.get("equiv_score_city6"),
        "equiv_score_whole": result.get("equiv_score_whole"),
        "out_of_range": result.get("out_of_range"),
        "low_score_mode": result.get("low_score_mode", False),
        "reach": tier(result.get("reach")),
        "stable": tier(result.get("stable")),
        "safe": tier(result.get("safe")),
        "reachable": tier(result.get("reachable")),
    }


def _tool_score_to_rank(db: Session, args: dict) -> dict:
    score = args.get("score")
    if score is None:
        return {"error": "缺少 score 参数"}
    year = args.get("year") or _latest_year(db)
    if year is None:
        return {"error": "无一分档数据"}
    rr = matching.score_to_rank(db, float(score), int(year))
    if rr is None:
        return {"error": "无该年一分档"}
    return {
        "score": rr.score, "year": int(year),
        "rank_whole": rr.rank_whole, "rank_city6": rr.rank_city6,
        "out_of_range": rr.out_of_range, "below_floor": rr.below_floor,
    }


def _tool_get_school_detail(db: Session, args: dict) -> dict:
    code = str(args.get("code") or "").strip()
    if not code:
        return {"error": "缺少 code 参数"}
    schools = db.query(School).filter(School.code == code).all()
    if not schools:
        return {"error": f"未找到学校代码 {code}"}
    # 市内六区考生不可报郊区, 过滤掉
    schools = [s for s in schools if s.scope != "suburb"]
    if not schools:
        return {"error": f"学校 {code} 仅面向郊区招生，市内六区考生不可填报"}
    out = []
    for s in schools:
        stats = sorted(s.stats, key=lambda x: x.year, reverse=True)
        out.append({
            "code": s.code, "name": s.name, "scope": SCOPE_LABEL.get(s.scope, s.scope),
            "type": s.type, "location_district": s.location_district,
            "home_district": s.home_district, "recruit_area": s.recruit_area,
            "boarding": s.boarding, "canteen": s.canteen, "class_types": s.class_types,
            "fee": s.fee, "dorm_fee": s.dorm_fee, "address": s.address,
            "phone": s.phone, "remark": s.remark, "intro": s.intro,
            "stats": [
                {"year": st.year, "plan": st.plan, "min_score": st.min_score,
                 "rank_city6": st.rank_city6, "rank_whole": st.rank_whole}
                for st in stats
            ],
        })
    return {"schools": out}


def _tool_search_schools_by_text(db: Session, args: dict) -> dict:
    query = (args.get("query") or "").strip()
    if not query:
        return {"error": "缺少 query 参数"}
    k = int(args.get("k") or 10)
    results = retrieval.search(db, query, k)
    return {"query": query, "count": len(results), "schools": results}


def _tool_get_thresholds(db: Session, args: dict) -> dict:
    return matching.get_config(db)


TOOL_DISPATCH = {
    "recommend": _tool_recommend,
    "score_to_rank": _tool_score_to_rank,
    "get_school_detail": _tool_get_school_detail,
    "search_schools_by_text": _tool_search_schools_by_text,
    "get_thresholds": _tool_get_thresholds,
}

TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "recommend",
            "description": "用位次法按中考分数推荐可冲/可稳/可保的学校(面向市内六区考生)。返回三档名单及位次/等位分。",
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {"type": "number", "description": "中考总分, 0-900"},
                    "year": {"type": "integer", "description": "一分档年份, 不传用最新年"},
                    "candidate_codes": {
                        "type": "array", "items": {"type": "string"},
                        "description": "可选: 只在这些学校代码范围内做冲稳保分类(用于与语义检索结果取交集)",
                    },
                },
                "required": ["score"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_to_rank",
            "description": "把中考分数换算成全市/市内六区位次(及是否超出一分档范围)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {"type": "number", "description": "中考总分"},
                    "year": {"type": "integer", "description": "年份, 不传用最新"},
                },
                "required": ["score"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_school_detail",
            "description": "按学校代码查单校详情: 班型/住宿/学费/地址/简介/历年录取(计划/最低分/位次)。市内六区不可报的郊区线已过滤。",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string", "description": "学校代码, 如 10101"}},
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_schools_by_text",
            "description": "按自然语言语义检索学校(如'管得严的公办校''校风自由''重视理科')。返回最相关的若干所及简介片段。用于抽象/定性筛选。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索描述, 如'管理严格的公办校'"},
                    "k": {"type": "integer", "description": "返回数量, 默认10"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_thresholds",
            "description": "查询当前冲/稳/保划分阈值。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ---------------- 限流(每 IP 每分钟) ----------------
_rate_buckets: dict[str, deque] = defaultdict(deque)


def check_rate(ip: str) -> bool:
    """返回 True 表示未超限。简单滑动窗口, 内存。"""
    now = time.time()
    q = _rate_buckets[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.chat_rate_per_min:
        return False
    q.append(now)
    return True


# ---------------- SSE 辅助 ----------------
def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


# ---------------- 主流程: 流式 tool-call 循环 ----------------
def _run_loop(client: httpx.Client, messages: list, db: Session):
    """实际的流式 tool-call 循环, yield SSE 事件。"""
    for _ in range(settings.chat_max_tool_rounds):
        content_buf = ""
        thinking_buf = ""
        tool_acc: dict[int, dict] = {}
        finish = None

        with client.stream(
            "POST",
            f"{settings.deepseek_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.deepseek_model,
                "messages": messages,
                "tools": TOOL_SPECS,
                "stream": True,
                "max_tokens": settings.deepseek_max_tokens,
            },
        ) as resp:
            if resp.status_code != 200:
                # 读出错误体
                body = resp.read().decode("utf-8", "ignore")[:300]
                yield _sse({"type": "error", "message": f"DeepSeek 返回 {resp.status_code}: {body}"})
                return
            for line in resp.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].lstrip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = obj.get("choices") or []
                if not choices:
                    continue
                choice = choices[0]
                delta = choice.get("delta") or {}

                rc = delta.get("reasoning_content")
                if rc:
                    thinking_buf += rc
                    yield _sse({"type": "thinking", "text": rc})

                c = delta.get("content")
                if c:
                    content_buf += c
                    yield _sse({"type": "delta", "text": c})

                tcs = delta.get("tool_calls")
                if tcs:
                    for tc in tcs:
                        idx = tc.get("index", 0)
                        slot = tool_acc.setdefault(idx, {"id": None, "name": None, "arguments": ""})
                        if tc.get("id"):
                            slot["id"] = tc["id"]
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            slot["name"] = fn["name"]
                        if fn.get("arguments"):
                            slot["arguments"] += fn["arguments"]

                if choice.get("finish_reason"):
                    finish = choice["finish_reason"]

        if finish != "tool_calls":
            yield _sse({"type": "done"})
            return

        # 有 tool_calls: 执行并继续
        calls = []
        for idx in sorted(tool_acc):
            slot = tool_acc[idx]
            try:
                args = json.loads(slot["arguments"]) if slot["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            calls.append({"id": slot["id"], "name": slot["name"], "args": args})

        # 把 assistant 的 tool_call 消息入历史(DeepSeek 要求带 tool_calls 字段)
        messages.append({
            "role": "assistant",
            "content": content_buf or None,
            "tool_calls": [
                {"id": c["id"], "type": "function",
                 "function": {"name": c["name"], "arguments": json.dumps(c["args"], ensure_ascii=False)}}
                for c in calls
            ],
        })

        for c in calls:
            yield _sse({"type": "tool", "name": c["name"]})
            fn = TOOL_DISPATCH.get(c["name"])
            if fn is None:
                result = {"error": f"未知工具 {c['name']}"}
            else:
                try:
                    result = fn(db, c["args"])
                except Exception as e:  # noqa: BLE001
                    result = {"error": f"工具执行出错: {e}"}
            messages.append({
                "role": "tool",
                "tool_call_id": c["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })

    yield _sse({"type": "error", "message": "工具调用轮次超限，请缩小问题范围"})


def stream_chat(message: str, history: list[dict], db: Session):
    """生成器: yield SSE 字符串。对外入口。"""
    if not settings.deepseek_api_key:
        yield _sse({"type": "error", "message": "未配置 DEEPSEEK_API_KEY，无法启用问答"})
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in (history or []):
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": message})

    client = httpx.Client(timeout=httpx.Timeout(120.0, connect=10.0))
    try:
        for event in _run_loop(client, messages, db):
            yield event
    except httpx.HTTPError as e:
        yield _sse({"type": "error", "message": f"网络错误: {e}"})
    except Exception as e:  # noqa: BLE001
        yield _sse({"type": "error", "message": f"内部错误: {e}"})
    finally:
        client.close()
