#!/usr/bin/env python3
"""Import one 2級 chapter (prepared from the daily 2級 lessons) into the site data.

Usage:
    python3 tools/import_2kyu.py --chapter B1 --bundle in/B1.json --sec out/B1-sec.json \
        --quiz out/B1-quiz.json --check chk/B1.json [--dry-run]

- bundle: the raw chapter bundle (sections, quiz with options/answer, terms)
- sec / quiz: the cleaned text (pure-Vietnamese *_vi, no personal references)
- check: the independent blind check ([{id, answer, confident}]); a question is kept only
  if the checker's answer matches and it was confident, and it is not in the cleaner's "drop" list.

Questions keep their original choice order ("keep_order": true) because the explanations
refer to ア・イ・ウ…. Re-importing a chapter replaces that chapter's theory and questions.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QF = ROOT / "src" / "data" / "questions.json"
TF = ROOT / "src" / "data" / "theory.json"
JP = re.compile(r"[　-ヿ㐀-鿿！-｠]")

CHAPTERS = {
    "B1": ("データの取り方とまとめ方", "Lấy và tổng hợp dữ liệu", "shuho",
           "データの種類、母集団とサンプル、誤差、基本統計量（平方和・分散・標準偏差）、データの変換。"),
    "B2": ("QC七つ道具", "7 công cụ QC", "shuho",
           "パレート図・特性要因図・チェックシート・ヒストグラム・散布図・グラフ・層別の使い方と読み方。"),
    "B3": ("新QC七つ道具", "7 công cụ QC mới", "shuho", "親和図・連関図・系統図・マトリックス図・アローダイアグラム・PDPC・マトリックス・データ解析法。"),
    "B4": ("確率分布", "Phân phối xác suất", "shuho", "正規分布・二項分布・ポアソン分布、χ²・t・F分布、期待値と分散の加法性、中心極限定理。"),
    "B5": ("検定と推定（計量値）", "Kiểm định và ước lượng (giá trị đo)", "shuho", "母平均・母分散の検定と推定、2つの母集団の比較、対応のあるデータ。"),
    "B6": ("検定と推定（計数値）", "Kiểm định và ước lượng (giá trị đếm)", "shuho", "母不適合品率・母不適合数の検定と推定、分割表による検定。"),
    "B7": ("管理図", "Biểu đồ kiểm soát", "shuho", "管理図の考え方と判定ルール、X̄-R・X̄-s・X-Rs・p・np・u・c管理図。"),
    "B8": ("工程能力指数", "Chỉ số năng lực quy trình", "shuho", "Cp・Cpk の計算と判断、規格外れ率の推定。"),
    "B9": ("抜取検査", "Kiểm tra lấy mẫu", "shuho", "OC曲線、計数規準型・計量規準型抜取検査。"),
    "B10": ("実験計画法", "Thiết kế thí nghiệm", "shuho", "フィッシャーの3原則、一元配置・二元配置実験。"),
    "B11": ("相関分析", "Phân tích tương quan", "shuho", "相関係数、系列相関（大波・小波の相関）。"),
    "B12": ("単回帰分析", "Phân tích hồi quy đơn", "shuho", "回帰式の推定、回帰の分散分析と寄与率、残差の検討。"),
    "B13": ("信頼性工学", "Kỹ thuật độ tin cậy", "shuho", "信頼性モデル、故障率・MTBF、保全性と設計信頼性。"),
    "A1": ("品質管理の基本（QC的ものの見方・考え方）", "Cách nhìn và tư duy QC", "jissen", "源流管理・プロセス重視・重点指向など、品質管理の基本的な考え方。"),
    "A2": ("品質の概念", "Khái niệm chất lượng", "jissen", "要求品質、品質特性・代用特性、狩野モデル、顧客満足、社会的品質。"),
    "A3": ("管理の方法", "Phương pháp quản lý", "jissen", "維持と改善、PDCA・SDCA、問題解決型・課題達成型QCストーリー。"),
    "A4": ("品質保証", "Đảm bảo chất lượng", "jissen", "新製品開発とプロセス保証、QFD・DR・FMEA・FTA、検査、計測。"),
    "A5": ("品質経営の要素", "Các yếu tố của quản trị chất lượng", "jissen", "方針管理・日常管理・標準化・小集団活動・人材育成・品質マネジメントシステム。"),
}


def ckey(code):
    a, b = code[1:].split(".")
    return (code[0], int(a), int(b))


def plain(t):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", t or "").strip()


def main():
    ap = argparse.ArgumentParser()
    for a in ("--chapter", "--bundle", "--sec", "--quiz", "--check"):
        ap.add_argument(a, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    ch = args.chapter
    tid = ch.lower()
    name, name_vi, domain, desc = CHAPTERS[ch]
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    sec = {s["key"]: s for s in json.loads(Path(args.sec).read_text(encoding="utf-8"))["sections"]}
    qout = json.loads(Path(args.quiz).read_text(encoding="utf-8"))
    qclean = {q["id"]: q for q in qout["quiz"]}
    drop = set(qout.get("drop", []))
    chk = {c["id"]: c for c in json.loads(Path(args.check).read_text(encoding="utf-8"))}

    # theory
    sections = []
    for s in sorted(bundle["sections"], key=lambda s: (ckey(s["code"]), s["key"])):
        c = sec[s["key"]]
        assert not JP.search(c["body_vi"] + c["heading_vi"]), s["key"]
        sections.append({"h": {"ja": c.get("heading_ja") or s["heading_ja"], "vi": c["heading_vi"]},
                         "blocks": [{"type": "md", "ja": c["body_ja"], "vi": c["body_vi"]}]})
    terms = [[t["ja"], t.get("yomi") or "", t.get("vi") or ""] for t in bundle["terms"] if t.get("ja")]
    theory_entry = {"intro": {"ja": desc, "vi": f"Lý thuyết QC Kentei cấp 2 – {name_vi}."},
                    "sections": sections, "terms": terms}

    # questions
    kept, dropped = [], []
    for q in bundle["quiz"]:
        c, k = qclean.get(q["id"]), chk.get(q["id"])
        why = None
        if q["id"] in drop or c is None:
            why = "loại khi biên tập"
        elif not k or k.get("answer") != q["answer"] or not k.get("confident", False):
            why = "không qua kiểm tra độc lập"
        if why:
            dropped.append((q["id"], why)); continue
        vi = f"Đề bài: {plain(c['q_vi'])} Giải thích: {plain(c['exp_vi'])}"
        assert not JP.search(vi), q["id"]
        kept.append({"level": 2, "topic": tid, "question": plain(c.get("q_ja") or q["q_ja"]), "choices": [plain(o) for o in q["options"]],
                     "answer": q["answer"], "explanation": plain(c.get("exp_ja") or q["exp_ja"]),
                     "explanation_vi": vi, "keep_order": True, "status": "checked", "src": q["id"]})

    data = json.loads(QF.read_text(encoding="utf-8"))
    L = data["levels"].setdefault("2", {
        "name": "QC検定2級", "slug": "2kyu", "name_vi": "QC Kentei cấp 2",
        "lead": "統計的手法（検定・推定、管理図、工程能力など）と品質経営の実践。学習ページを順次公開しています。",
        "domains": {"shuho": "手法分野", "jissen": "実践分野"}, "domains_vi": {"shuho": "Phương pháp", "jissen": "Thực tiễn"},
        "topics": []})
    if not any(t["id"] == tid for t in L["topics"]):
        L["topics"].append({"id": tid, "name": name, "desc": desc, "domain": domain, "name_vi": name_vi})
        order = list(CHAPTERS)
        L["topics"].sort(key=lambda t: order.index(t["id"].upper()))
    data["questions"] = [q for q in data["questions"] if not (q["level"] == 2 and q["topic"] == tid)]
    used = [int(q["id"].split("-")[1]) for q in data["questions"] if q["level"] == 2]
    n = max(used, default=0)
    for q in kept:
        n += 1
        q["id"] = f"2-{n:03d}"
    data["questions"] += [{k: v for k, v in q.items() if k != "src"} for q in kept]
    theory = json.loads(TF.read_text(encoding="utf-8"))
    theory[f"2:{tid}"] = theory_entry
    print(f"{ch}: {len(sections)} mục lý thuyết, {len(terms)} thuật ngữ, thêm {len(kept)} câu, loại {len(dropped)}")
    for i, w in dropped:
        print("  bỏ", i, w)
    if args.dry_run:
        return
    QF.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TF.write_text(json.dumps(theory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
