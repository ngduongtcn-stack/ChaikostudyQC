#!/usr/bin/env python3
"""Validate, de-duplicate and add verified questions to the bank.

    python3 tools/add_questions.py verified.json --alloc "$(python3 tools/plan.py --day sun --json)"
    python3 tools/add_questions.py verified-1.json verified-2.json --alloc ... --reserve ...
    python3 tools/add_questions.py verified.json [--limit-4 N] [--limit-3 N] [--dry-run]

--alloc takes this run's per-topic allocation from plan.py. Each topic first gets up to
its allocated number; if a topic falls short, spare verified questions from other topics
of the same level fill the gap, so the level total still matches the plan.

- Checks each question's format (4 choices recommended, answer index, both explanations).
- Rejects near-duplicates of questions already in the bank (and of each other):
  question+correct answer similarity >= 0.80, or question similarity >= 0.85 together
  with choice-set similarity >= 0.60. (Question stems alone are not enough: many
  questions share stems like 「〜として、最も適切なものはどれか」.)
- Assigns new IDs (4-037, 3-041, ...), sets status "checked" (passed the independent
  check, not yet reviewed by a person) and appends to src/data/questions.json.
"""
import argparse
import sys

from qclib import QUESTIONS, PLAN, load_json, next_id, save_json, similarity

Q_SIM = 0.85
QA_SIM = 0.80
CHOICE_SIM = 0.60


def problems(q, topics):
    errs = []
    lv = str(q.get("level"))
    if lv not in topics:
        errs.append("level không hợp lệ")
    elif q.get("topic") not in topics[lv]:
        errs.append(f"topic '{q.get('topic')}' không có ở {lv}級")
    ch = q.get("choices") or []
    if not 3 <= len(ch) <= 5:
        errs.append("cần 3–5 lựa chọn")
    if len(set(ch)) != len(ch):
        errs.append("có lựa chọn trùng nhau")
    if not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < len(ch):
        errs.append("answer sai")
    for f in ("question", "explanation", "explanation_vi"):
        if not str(q.get(f, "")).strip():
            errs.append(f"thiếu {f}")
    return errs


def qa_text(q):
    return q["question"] + " " + q["choices"][q["answer"]]


def choices_text(q):
    return " ".join(sorted(q["choices"]))


def is_dup(a, b):
    if similarity(qa_text(a), qa_text(b)) >= QA_SIM:
        return True
    return similarity(a["question"], b["question"]) >= Q_SIM and similarity(choices_text(a), choices_text(b)) >= CHOICE_SIM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="one or more verified.json files (one per batch)")
    ap.add_argument("--limit-4", type=int)
    ap.add_argument("--limit-3", type=int)
    ap.add_argument("--alloc", help="JSON from plan.py --json: {level: {topic: n}}")
    ap.add_argument("--reserve", help="reserve file: verified questions left over from earlier runs; used first, leftovers saved back")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_json(QUESTIONS)
    plan = load_json(PLAN)
    topics = {lv: set(t) for lv, t in plan["topic_targets"].items()}
    limits = {"4": args.limit_4, "3": args.limit_3}
    cands = [c for f in args.files for c in load_json(f)]
    reserve_in = load_json(args.reserve, []) if args.reserve else []
    cands = reserve_in + cands
    if args.alloc:
        import json as _json
        alloc = _json.loads(args.alloc)
        limits = {lv: sum(alloc.get(lv, {}).values()) for lv in ("4", "3")}
        # pass 1: candidates within their topic's quota; pass 2: the rest, as fillers
        used = {}
        first, rest = [], []
        for c in cands:
            key = (str(c.get("level")), c.get("topic"))
            if used.get(key, 0) < alloc.get(key[0], {}).get(key[1], 0):
                used[key] = used.get(key, 0) + 1
                first.append(c)
            else:
                rest.append(c)
        cands = first + rest

    bank = list(data["questions"])
    added = {"4": 0, "3": 0}
    rejected = []
    spare = []
    for c in cands:
        lv = str(c.get("level"))
        errs = problems(c, topics)
        if errs:
            rejected.append((c.get("id", "?"), "; ".join(errs)))
            continue
        if limits.get(lv) is not None and added[lv] >= limits[lv]:
            rejected.append((c.get("id", "?"), "đã đủ số câu cho lần này → để dành"))
            spare.append(c)
            continue
        dup = None
        for q in bank:
            if str(q["level"]) != lv:
                continue
            if is_dup(c, q):
                dup = q["id"]
                break
        if dup:
            rejected.append((c.get("id", "?"), f"trùng với {dup}"))
            continue
        new = {
            "id": f"{lv}-{next_id(bank, lv):03d}",
            "level": int(lv),
            "topic": c["topic"],
            "status": "checked",
            "question": c["question"].strip(),
            "choices": [x.strip() for x in c["choices"]],
            "answer": c["answer"],
            "explanation": c["explanation"].strip(),
            "explanation_vi": c["explanation_vi"].strip(),
        }
        bank.append(new)
        added[lv] += 1

    q4 = [q for q in bank if q["level"] == 4]
    q3 = [q for q in bank if q["level"] == 3]
    data["questions"] = q4 + q3
    if not args.dry_run:
        save_json(QUESTIONS, data)
        if args.reserve:
            for k, c in enumerate(spare, 1):
                if not str(c.get("id", "")).startswith("r-"):
                    c["id"] = f"r-{c.get('id', k)}"
            save_json(args.reserve, spare)
            print(f"Kho dự trữ: {len(spare)} câu → {args.reserve}")
    print(f"Đã thêm: 4級 {added['4']} câu, 3級 {added['3']} câu{' (dry-run, chưa ghi)' if args.dry_run else ''}")
    print(f"Tổng hiện tại: 4級 {len(q4)}, 3級 {len(q3)}")
    for qid, why in rejected:
        print(f"  bỏ {qid}: {why}")


if __name__ == "__main__":
    sys.exit(main())
