#!/usr/bin/env python3
"""Make a blind copy of candidate questions for independent checking.

    python3 tools/blind.py candidates.json blind.json

Keeps only id, level, question and choices (no answer, no explanation), so the
checker has to solve each question on its own.
"""
import sys

from qclib import load_json, save_json


def main():
    src, dst = sys.argv[1], sys.argv[2]
    cands = load_json(src)
    blind = [{"id": c["id"], "level": c["level"], "question": c["question"],
              "choices": [f"{i}: {ch}" for i, ch in enumerate(c["choices"])]} for c in cands]
    save_json(dst, blind)
    print(f"{len(blind)} câu → {dst}")


if __name__ == "__main__":
    main()
