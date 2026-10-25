#!/usr/bin/env python3
"""Create new mock exams (模擬試験) from questions not yet used in any exam.

    python3 tools/make_exams.py

Each exam has exam.size questions (content-plan.json), drawn across topics in
proportion to what is available, with no question shared between exams. Existing
exams never change, so learners' results stay comparable. Stops at exam.max_exams.
"""
import sys

from qclib import EXAMS, PLAN, QUESTIONS, load_json, save_json


def main():
    plan = load_json(PLAN)
    data = load_json(QUESTIONS)
    exams = load_json(EXAMS, {"4": [], "3": []})
    size = plan["exam"]["size"]
    made = []
    for lv in ("4", "3"):
        exams.setdefault(lv, [])
        used = {i for ex in exams[lv] for i in ex}
        while len(exams[lv]) < plan["exam"]["max_exams"][lv]:
            free = [q for q in data["questions"] if str(q["level"]) == lv and q["id"] not in used]
            if len(free) < size:
                break
            by_topic = {}
            for q in free:
                by_topic.setdefault(q["topic"], []).append(q["id"])
            # proportional quota per topic, remainder to the largest pools
            quota = {t: len(ids) * size // len(free) for t, ids in by_topic.items()}
            short = size - sum(quota.values())
            for t in sorted(by_topic, key=lambda t: len(by_topic[t]) - quota[t], reverse=True)[:short]:
                quota[t] += 1
            pick = [i for t, ids in by_topic.items() for i in ids[:quota[t]]]
            order = {q["id"]: k for k, q in enumerate(data["questions"])}
            pick.sort(key=order.get)
            exams[lv].append(pick)
            used.update(pick)
            made.append(f"{lv}級 第{len(exams[lv])}回")
        free_n = len([q for q in data["questions"] if str(q["level"]) == lv and q["id"] not in used])
        print(f"{lv}級: {len(exams[lv])} đề, còn {free_n} câu chưa dùng (cần {size} câu cho đề tiếp theo)")
    save_json(EXAMS, exams)
    print("Đề mới: " + ("、".join(made) if made else "không có"))


if __name__ == "__main__":
    sys.exit(main())
