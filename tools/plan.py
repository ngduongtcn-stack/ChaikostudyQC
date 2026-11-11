#!/usr/bin/env python3
"""Show progress toward the question targets and decide this run's allocation.

    python3 tools/plan.py            # progress only
    python3 tools/plan.py --day sun  # progress + how many questions to write per topic this run
    python3 tools/plan.py --day tue
    python3 tools/plan.py --day wed
    python3 tools/plan.py --day extra   # one-off extra runs (per_run.extra is 0; use boost_once.extra)

The number of questions per run comes from content-plan.json ("per_run").
A one-time value in "boost_once" for the day overrides it (a number, or a per-level
object such as {"4": 57, "3": 63}); the run removes that entry
afterwards (CONTENT_GUIDE.md step 7), so the next week is back to per_run.
Allocation: split between levels by remaining need, then give each question to the
topic with the largest remaining gap (topics listed in "exhausted" are skipped).
Once a level's base topic_targets are met, its questions go to the advanced phase:
"advanced_topic_targets" counts questions marked "advanced": true (topics in
"exhausted_advanced" are skipped). In --json output, alloc["adv"] holds that part.
"""
import argparse
import json
import sys

from qclib import PLAN, QUESTIONS, EXAMS, counts, load_json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", choices=["sun", "tue", "wed", "extra"])
    ap.add_argument("--json", action="store_true", help="print the allocation as JSON only")
    args = ap.parse_args()

    plan = load_json(PLAN)
    data = load_json(QUESTIONS)
    exams = load_json(EXAMS, {"4": [], "3": []})
    have = counts(data["questions"])

    adv_have = counts([q for q in data["questions"] if q.get("advanced")])
    adv_targets = plan.get("advanced_topic_targets", {})

    def base_gaps(lv):
        return {t: tt - have.get(lv, {}).get(t, 0) for t, tt in plan["topic_targets"][lv].items()
                if t not in plan["exhausted"].get(lv, []) and tt - have.get(lv, {}).get(t, 0) > 0}

    def adv_gaps(lv):
        return {t: tt - adv_have.get(lv, {}).get(t, 0) for t, tt in adv_targets.get(lv, {}).items()
                if t not in plan.get("exhausted_advanced", {}).get(lv, []) and tt - adv_have.get(lv, {}).get(t, 0) > 0}

    remaining = {}
    report = []
    for lv in ("4", "3"):
        total = sum(have.get(lv, {}).values())
        target = plan["targets"][lv]
        bg, ag = base_gaps(lv), adv_gaps(lv)
        remaining[lv] = sum(bg.values()) + sum(ag.values())
        n_adv = sum(adv_have.get(lv, {}).values())
        adv_t = plan.get("advanced_targets", {}).get(lv, 0)
        phase = "cơ bản" if bg else ("nâng cao" if ag else "xong")
        report.append(f"{lv}級: {total} / {target} câu cơ bản · nâng cao {n_adv} / {adv_t} · giai đoạn: {phase}"
                      f" · còn có thể thêm {remaining[lv]} · đề thi thử: {len(exams.get(lv, []))} / {plan['exam']['max_exams'][lv]}")
        for topic, t_target in plan["topic_targets"][lv].items():
            n = have.get(lv, {}).get(topic, 0)
            a = adv_have.get(lv, {}).get(topic, 0)
            at = adv_targets.get(lv, {}).get(topic, 0)
            flags = []
            if topic in plan["exhausted"].get(lv, []):
                flags.append("cơ bản đã hết nội dung")
            if topic in plan.get("exhausted_advanced", {}).get(lv, []):
                flags.append("nâng cao đã hết nội dung")
            report.append(f"    {topic:<16}{n:>4} / {t_target:<4}  nâng cao {a:>3} / {at:<3}"
                          + (f"  ({', '.join(flags)})" if flags else ""))

    # alloc: {"4": {topic: n}, "3": {...}} = câu cơ bản; alloc["adv"] = câu nâng cao (advanced: true)
    alloc = {"4": {}, "3": {}, "adv": {"4": {}, "3": {}}}
    if args.day:
        boost = plan.get("boost_once", {}).get(args.day)
        split = None
        if isinstance(boost, dict):
            # per-level boost, e.g. {"4": 57, "3": 63}
            split = {lv: 0 if plan.get("paused") else min(int(boost.get(lv, 0)), remaining[lv]) for lv in ("4", "3")}
            n_run = sum(split.values())
        else:
            n_run = 0 if plan.get("paused") else int(boost if boost is not None else plan["per_run"].get(args.day, 0))
        total_rem = remaining["4"] + remaining["3"]
        n_run = min(n_run, total_rem)
        if n_run and split is None:
            n4 = round(n_run * remaining["4"] / total_rem)
            split = {"4": n4, "3": n_run - n4}
        if n_run:
            for lv in ("4", "3"):
                left = split[lv]
                # base targets first, then advanced
                for gaps, targets, out in ((base_gaps(lv), plan["topic_targets"][lv], alloc[lv]),
                                           (adv_gaps(lv), adv_targets.get(lv, {}), alloc["adv"][lv])):
                    while left > 0 and gaps:
                        # largest remaining share of its own target first
                        topic = max(gaps, key=lambda t: gaps[t] / targets[t])
                        out[topic] = out.get(topic, 0) + 1
                        left -= 1
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
        elif not any(alloc[lv] for lv in ("4", "3")) and not any(alloc["adv"].values()):
            print("\nĐã đạt mục tiêu (hoặc mọi phân野 đã đủ nội dung) → không soạn câu mới.")
        else:
            n_all = sum(sum(alloc[lv].values()) + sum(alloc["adv"][lv].values()) for lv in ("4", "3"))
            print(f"\nLần chạy {args.day}: soạn {n_all} câu")
            note = plan.get("note_once", {}).get(args.day)
            if note:
                print(f"Ghi chú cho lần này (note_once): {note}")
            for lv in ("4", "3"):
                for topic, n in alloc[lv].items():
                    print(f"    {lv}級 {topic}: {n}")
                for topic, n in alloc["adv"][lv].items():
                    print(f"    {lv}級 {topic}: {n}  [nâng cao → \"advanced\": true]")


if __name__ == "__main__":
    sys.exit(main())
