#!/usr/bin/env python3
"""Create new mock exams (模擬試験) from questions not yet used in any exam.

    python3 tools/make_exams.py

Each exam has exam.size questions (content-plan.json) and no question is shared
between exams. When exam.domain_split is set for a level (3級: 手法 50% / 実践 50%,
like the real exam), each domain gets its share of the exam and the exam is only
created once every domain has enough unused questions. Inside a domain, questions
are spread across topics in proportion to what is available. Existing exams never
change, so learners' results stay comparable. Stops at exam.max_exams.
"""
import sys

from qclib import EXAMS, PLAN, QUESTIONS, load_json, save_json


def spread(pool_by_topic, n):
    """Pick n ids across topics in proportion to pool size (earliest ids first)."""
    total = sum(len(v) for v in pool_by_topic.values())
    quota = {t: len(ids) * n // total for t, ids in pool_by_topic.items()}
    short = n - sum(quota.values())
    for t in sorted(pool_by_topic, key=lambda t: len(pool_by_topic[t]) - quota[t], reverse=True)[:short]:
        quota[t] += 1
    return [i for t, ids in pool_by_topic.items() for i in ids[:quota[t]]]


def main():
    plan = load_json(PLAN)
    data = load_json(QUESTIONS)
    exams = load_json(EXAMS, {"4": [], "3": []})
    size = plan["exam"]["size"]
    splits = plan["exam"].get("domain_split", {})
    order = {q["id"]: k for k, q in enumerate(data["questions"])}
    made = []
    for lv in ("4", "3"):
        exams.setdefault(lv, [])
        domain_of = {t["id"]: t.get("domain", "all") for t in data["levels"][lv]["topics"]}
        split = splits.get(lv)
        used = {i for ex in exams[lv] for i in ex}
        while len(exams[lv]) < plan["exam"]["max_exams"][lv]:
            free = [q for q in data["questions"] if str(q["level"]) == lv and q["id"] not in used]
            if split:
                need = {d: round(size * share) for d, share in split.items()}
                need[max(need, key=need.get)] += size - sum(need.values())
                pools = {}
                for q in free:
                    d = domain_of.get(q["topic"], "all")
                    pools.setdefault(d, {}).setdefault(q["topic"], []).append(q["id"])
                if any(sum(len(v) for v in pools.get(d, {}).values()) < n for d, n in need.items()):
                    break
                pick = [i for d, n in need.items() for i in spread(pools[d], n)]
            else:
                if len(free) < size:
                    break
                by_topic = {}
                for q in free:
                    by_topic.setdefault(q["topic"], []).append(q["id"])
                pick = spread(by_topic, size)
            pick.sort(key=order.get)
            exams[lv].append(pick)
            used.update(pick)
            made.append(f"{lv}級 第{len(exams[lv])}回")
        free_qs = [q for q in data["questions"] if str(q["level"]) == lv and q["id"] not in used]
        if split:
            have = {d: sum(1 for q in free_qs if domain_of.get(q["topic"]) == d) for d in split}
            need = {d: round(size * s) for d, s in split.items()}
            detail = "、".join(f"{d}: còn {have[d]}/{need[d]}" for d in split)
            print(f"{lv}級: {len(exams[lv])} đề · câu chưa dùng theo 分野 ({detail})")
        else:
            print(f"{lv}級: {len(exams[lv])} đề, còn {len(free_qs)} câu chưa dùng (cần {size} câu cho đề tiếp theo)")
    save_json(EXAMS, exams)
    print("Đề mới: " + ("、".join(made) if made else "không có"))


if __name__ == "__main__":
    sys.exit(main())
