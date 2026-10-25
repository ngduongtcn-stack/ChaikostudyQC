#!/usr/bin/env python3
"""Keep only candidates the independent checker answered the same way.

    python3 tools/compare.py candidates.json checker.json verified.json

checker.json: [{"id": "...", "answer": 2, "confident": true, "note": "..."}]
A candidate passes when the checker's answer equals the candidate's answer AND the
checker marked it confident (no ambiguity, no second defensible choice).
"""
import sys

from qclib import load_json, save_json


def main():
    cands = load_json(sys.argv[1])
    checks = {c["id"]: c for c in load_json(sys.argv[2])}
    ok, dropped = [], []
    for c in cands:
        chk = checks.get(c["id"])
        if not chk:
            dropped.append((c["id"], "checker không trả lời"))
        elif chk.get("answer") != c["answer"]:
            dropped.append((c["id"], f"đáp án lệch: soạn={c['answer']} kiểm tra={chk.get('answer')} {chk.get('note', '')}"))
        elif not chk.get("confident", False):
            dropped.append((c["id"], f"không chắc chắn: {chk.get('note', '')}"))
        else:
            ok.append(c)
    save_json(sys.argv[3], ok)
    print(f"Qua kiểm tra: {len(ok)} / {len(cands)}")
    for qid, why in dropped:
        print(f"  bỏ {qid}: {why}")


if __name__ == "__main__":
    main()
