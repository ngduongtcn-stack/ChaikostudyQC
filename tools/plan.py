#!/usr/bin/env python3
"""Show progress toward the question targets and decide this run's allocation.

    python3 tools/plan.py            # progress only
    python3 tools/plan.py --day sun  # progress + how many questions to write per topic this run
    python3 tools/plan.py --day wed

The number of questions per run comes from content-plan.json ("per_run").
Allocation: split between levels by remaining need, then give each question to the
topic with the largest remaining gap (topics listed in "exhausted" are skipped).
"""
import argparse
import json
import sys

from qclib import PLAN, QUESTIONS, EXAMS, counts, load_json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", choices=["sun", "wed"])
    ap.add_argument("--json", action="store_true", help="print the allocation as JSON only")
    args = ap.parse_args()

    plan = load_json(PLAN)
    data = load_json(QUESTIONS)
    exams = load_json(EXAMS, {"4": [], "3": []})
    have = counts(data["questions"])

    remaining = {}
    report = []
    for lv in ("4", "3"):
        total = sum(have.get(lv, {}).values())
        target = plan["targets"][lv]
        open_gap = 0
        lines = []
        for topic, t_target in plan["topic_targets"][lv].items():
            n = have.get(lv, {}).get(topic, 0)
            ex = topic in plan["exhausted"].get(lv, [])
            gap = 0 if ex else max(0, t_target - n)
            open_gap += gap
            lines.append(f"    {topic:<16}{n:>4} / {t_target:<4}{'  (đã đủ nội dung — bỏ qua)' if ex else ''}")
        remaining[lv] = open_gap
        report.append(f"{lv}級: {total} / {target} câu, còn có thể thêm {open_gap} · đề thi thử: {len(exams.get(lv, []))} / {plan['exam']['max_exams'][lv]}")
        report.extend(lines)

    alloc = {"4": {}, "3": {}}
    if args.day:
        n_run = 0 if plan.get("paused") else int(plan["per_run"][args.day])
        total_rem = remaining["4"] + remaining["3"]
        n_run = min(n_run, total_rem)
        if n_run:
            n4 = round(n_run * remaining["4"] / total_rem)
            split = {"4": n4, "3": n_run - n4}
            for lv in ("4", "3"):
                gaps = {}
                for topic, t_target in plan["topic_targets"][lv].items():
                    if topic in plan["exhausted"].get(lv, []):
                        continue
                    g = t_target - have.get(lv, {}).get(topic, 0)
                    if g > 0:
                        gaps[topic] = g
                for _ in range(split[lv]):
                    if not gaps:
                        break
                    # largest remaining share of its own target first
                    topic = max(gaps, key=lambda t: gaps[t] / plan["topic_targets"][lv][t])
                    alloc[lv][topic] = alloc[lv].get(topic, 0) + 1
                    gaps[topic] -= 1
                    if gaps[topic] <= 0:
                        del gaps[topic]

    if args.json:
        print(json.dumps(alloc, ensure_ascii=False))
        return

    print("\n".join(report))
    if args.day:
        if plan.get("paused"):
            print("\ncontent-plan.json: paused = true → không soạn câu mới lần này.")
        elif not any(alloc[lv] for lv in alloc):
            print("\nĐã đạt mục tiêu (hoặc mọi phân野 đã đủ nội dung) → không soạn câu mới.")
        else:
            print(f"\nLần chạy {args.day}: soạn {sum(alloc['4'].values()) + sum(alloc['3'].values())} câu")
            for lv in ("4", "3"):
                for topic, n in alloc[lv].items():
                    print(f"    {lv}級 {topic}: {n}")


if __name__ == "__main__":
    sys.exit(main())
