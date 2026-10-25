"""Shared helpers for the content tools (plan, add_questions, make_exams, blind)."""
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "src" / "data" / "questions.json"
EXAMS = ROOT / "src" / "data" / "exams.json"
PLAN = ROOT / "content-plan.json"


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(text):
    """Normalise Japanese text for similarity checks: width, spaces, punctuation."""
    t = unicodedata.normalize("NFKC", text or "")
    t = re.sub(r"[\s　、。，．,.・「」『』（）()\[\]【】:：;；?？!！]", "", t)
    return t.lower()


def similarity(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def counts(questions):
    """{level: {topic: n}}"""
    out = {}
    for q in questions:
        out.setdefault(str(q["level"]), {}).setdefault(q["topic"], 0)
        out[str(q["level"])][q["topic"]] += 1
    return out


def next_id(questions, level):
    nums = [int(q["id"].split("-")[1]) for q in questions if str(q["level"]) == str(level)]
    return (max(nums) if nums else 0) + 1
