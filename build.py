#!/usr/bin/env python3
"""Build the QC検定れんしゅう帳 static site.

Usage:
    python3 build.py            # builds ./dist  (upload this folder to GitHub Pages)
    python3 build.py --check    # only validates questions.json

Edit questions in src/data/questions.json and site settings in site.json,
then run this script again.
"""
import html
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
KEYS = ["ア", "イ", "ウ", "エ", "オ"]
FONTS = ("https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700"
         "&family=Be+Vietnam+Pro:wght@400;700"
         "&family=IBM+Plex+Mono&family=Shippori+Mincho+B1:wght@700;800&display=swap")

e = html.escape


def load():
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    data = json.loads((SRC / "data" / "questions.json").read_text(encoding="utf-8"))
    theory_path = SRC / "data" / "theory.json"
    data["theory"] = json.loads(theory_path.read_text(encoding="utf-8")) if theory_path.exists() else {}
    exams_path = SRC / "data" / "exams.json"
    data["exams"] = json.loads(exams_path.read_text(encoding="utf-8")) if exams_path.exists() else {}
    plan_path = ROOT / "content-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else {}
    data["exam_cfg"] = plan.get("exam", {"size": 50, "pass_rate": 0.7})
    return site, data


def validate_theory(data):
    errors = []
    keys = {f"{lv}:{t['id']}" for lv, L in data["levels"].items() for t in L["topics"]}
    for key, th in data["theory"].items():
        if key not in keys:
            errors.append(f"theory.json: '{key}' に対応する分野がありません")
            continue
        for si, sec in enumerate(th.get("sections", [])):
            for b in sec.get("blocks", []):
                if b.get("type") not in ("p", "list", "formula", "table", "point"):
                    errors.append(f"theory.json: {key} セクション{si + 1} に不明なブロック '{b.get('type')}'")
    return errors


def validate(data):
    errors, seen = [], set()
    topics = {lv: {t["id"] for t in L["topics"]} for lv, L in data["levels"].items()}
    for q in data["questions"]:
        qid = q.get("id", "?")
        if qid in seen:
            errors.append(f"{qid}: 問題IDが重複しています")
        seen.add(qid)
        lv = str(q.get("level"))
        if lv not in topics:
            errors.append(f"{qid}: level {lv} が levels にありません")
        elif q.get("topic") not in topics[lv]:
            errors.append(f"{qid}: topic '{q.get('topic')}' が {lv}級の分野にありません")
        ch = q.get("choices", [])
        if not 2 <= len(ch) <= 5:
            errors.append(f"{qid}: 選択肢は2〜5個にしてください（現在 {len(ch)}個）")
        if not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < len(ch):
            errors.append(f"{qid}: answer は 0〜{len(ch) - 1} の数字にしてください")
        for f in ("question", "explanation"):
            if not q.get(f):
                errors.append(f"{qid}: {f} が空です")
        if "explanation_vi" in q and not isinstance(q["explanation_vi"], str):
            errors.append(f"{qid}: explanation_vi は文字列にしてください")
    return errors


# ---------- templates ----------

def page(site, *, title, desc, body, depth=0, path="", nav=""):
    pre = "../" * depth
    full_title = f"{title} | {site['site_name']}" if title != site["site_name"] else f"{site['site_name']}｜{site['tagline']}"
    url = site["site_url"].rstrip("/") + "/" + path

    def nav_link(href, label, key):
        cur = ' aria-current="page"' if key == nav else ""
        return f'<a href="{pre}{href}"{cur}>{label}</a>'

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(url)}">
<meta property="og:site_name" content="{e(site['site_name'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{pre}assets/style.css">
<script>try{{document.documentElement.classList.add(localStorage.getItem("qc-renshu:vi")==="1"?"vi-on":"vi-off")}}catch(e){{document.documentElement.classList.add("vi-off")}}</script>
</head>
<body>
<header class="site-head"><div class="wrap">
  <a class="brand" href="{pre}index.html"><span class="mark">○</span>{e(site['site_name'])}</a>
  <nav class="nav" aria-label="メインメニュー">
    {nav_link('4kyu/index.html', '4級', '4')}
    {nav_link('3kyu/index.html', '3級', '3')}
    {nav_link('about.html', 'このサイトについて', 'about')}
  </nav>
</div></header>
{body}
<footer class="site-foot"><div class="wrap">
  <span>© {date.today().year} {e(site['site_name'])}　QC検定®は一般財団法人日本規格協会の登録商標です。本サイトは非公式の学習サイトです。</span>
  <a href="{pre}about.html">運営方針・プライバシー</a>
</div></footer>
<script src="{pre}assets/config.js"></script>
<script src="{pre}assets/questions.js"></script>
<script src="{pre}assets/app.js"></script>
</body>
</html>
"""


def hero(eyebrow, h1, lead, extra=""):
    return f"""<div class="hero"><div class="wrap">
  <p class="eyebrow">{e(eyebrow)}</p>
  <h1>{e(h1)}</h1>
  <p class="lead">{e(lead)}</p>
  {extra}
</div></div>"""


def build_index(site, data):
    cards = []
    for lv in ("4", "3"):
        L = data["levels"][lv]
        n = sum(1 for q in data["questions"] if str(q["level"]) == lv)
        cards.append(f"""<div class="level-card" data-progress="{lv}:all">
  <span class="kyu">{lv}<small>級</small></span>
  <p>{e(L['lead'])}</p>
  <span class="meta">{n}問 ・ {len(L['topics'])}分野</span>
  <div class="bar"><i></i></div>
  <div class="btn-row">
    <a class="btn primary" href="{L['slug']}/index.html">分野を選ぶ</a>
    <a class="btn" href="quiz.html#{lv}.all.exam">ミニ模擬試験</a>
  </div>
</div>""")
    body = hero("QC KENTEI · FREE DRILL", "QC検定4級・3級を、無料で毎日すこしずつ。",
                "分野別の練習問題と解説、ミニ模擬試験、間違えた問題の自動復習。登録なしで、スマホからすぐ解けます。") + f"""
<main><div class="wrap">
<section aria-labelledby="h-levels">
  <h2 id="h-levels">級を選ぶ</h2>
  <div class="levels">{''.join(cards)}</div>
</section>
<section aria-labelledby="h-how">
  <h2 id="h-how">使い方</h2>
  <ul class="topics">
    <li><div><span class="t-name">要点を学ぶ</span><p class="t-desc">分野ごとのまとめページで、考え方・公式・重要用語（読み・ベトナム語訳つき）を確認できます。</p></div></li>
    <li><div><span class="t-name">分野別に練習する</span><p class="t-desc">1問ごとに正解と解説が出ます。苦手な分野だけをくり返し解けます。</p></div></li>
    <li><div><span class="t-name">ミニ模擬試験で力をはかる</span><p class="t-desc">全分野からランダムに最大{20}問。最後にまとめて採点し、所要時間も表示します。</p></div></li>
    <li><div><span class="t-name">間違えた問題を復習する</span><p class="t-desc">直近で間違えた問題が自動で集まります。正解すると復習リストから外れます。</p></div></li>
    <li lang="vi"><div><span class="t-name">Có giải thích bằng tiếng Việt</span><p class="t-desc">Dành cho người Việt đang làm việc tại Nhật: bấm「Xem giải thích bằng tiếng Việt」dưới mỗi câu. Thuật ngữ giữ nguyên tiếng Nhật kèm nghĩa để quen với đề thi thật.</p></div></li>
  </ul>
  <p class="note">学習の記録はお使いのブラウザの中にだけ保存され、外部には送信されません。</p>
</section>
</div></main>"""
    return page(site, title=site["site_name"], body=body, path="",
                desc=f"{site['tagline']}。分野別の練習問題と解説、ミニ模擬試験、間違えた問題の復習が無料・登録なしで使えます。")


def build_exam_section(data, lv):
    cfg = data["exam_cfg"]
    size = cfg.get("size", 50)
    sets = data["exams"].get(lv, [])
    n_level = sum(1 for q in data["questions"] if str(q["level"]) == lv)
    used = sum(len(x) for x in sets)
    left = size - (n_level - used)
    nxt = (f'<p class="note">次の模擬試験（第{len(sets) + 1}回）まで、あと{max(left, 0)}問。問題が{size}問たまるごとに、1回分ずつ追加されます。'
           f'<span lang="vi">　Cứ đủ {size} câu mới là có thêm một đề thi thử.</span></p>')
    if not sets:
        cards = '<div class="empty"><p>模擬試験は準備中です。</p></div>'
    else:
        items = "".join(
            f'<a class="exam-card" href="../quiz.html#{lv}.m{i}.exam"><span class="exam-no">第{i}回</span>'
            f'<span class="meta">{len(ex)}問</span><span class="meta exam-score" data-exam="{lv}:m{i}">未受験</span></a>'
            for i, ex in enumerate(sets, 1))
        cards = f'<div class="exam-grid">{items}</div>'
    return f"""<section aria-labelledby="h-exams">
  <h2 id="h-exams">模擬試験</h2>
  <p class="note">{size}問・時間を計って本番形式で解き、最後にまとめて採点します。合格の目安は正答率{round(cfg.get("pass_rate", 0.7) * 100)}%です。</p>
  {cards}
  {nxt if len(sets) < cfg.get("max_exams", {}).get(lv, 99) else ""}
</section>"""


def build_level(site, data, lv):
    L = data["levels"][lv]
    rows = []
    for t in L["topics"]:
        n = sum(1 for q in data["questions"] if str(q["level"]) == lv and q["topic"] == t["id"])
        has_theory = f"{lv}:{t['id']}" in data["theory"]
        name_href = f"learn/{t['id']}.html" if has_theory else f"{t['id']}.html"
        learn_btn = f'<a class="btn" href="learn/{t["id"]}.html">学ぶ</a>' if has_theory else ""
        rows.append(f"""<li data-progress="{lv}:{t['id']}">
  <div>
    <a class="t-name" href="{name_href}">{e(t['name'])}</a>
    <p class="t-desc">{e(t['desc'])}</p>
    <span class="meta">{n}問</span>
    <div class="bar"><i></i></div>
  </div>
  <div class="t-actions">
    {learn_btn}
    <a class="btn ghost" href="{t['id']}.html">問題一覧</a>
    <a class="btn primary" href="../quiz.html#{lv}.{t['id']}.practice">解く</a>
  </div>
</li>""")
    extra = f"""<div class="btn-row" style="margin-top:20px">
    <a class="btn primary" href="../quiz.html#{lv}.all.practice">全分野で練習</a>
    <a class="btn" href="../quiz.html#{lv}.all.exam">ミニ模擬試験（最大20問）</a>
    <a class="btn" href="../quiz.html#{lv}.all.review">間違えた問題を復習（<span data-review-count="{lv}:all">0</span>）</a>
  </div>"""
    exam_section = build_exam_section(data, lv)
    body = hero(f"QC KENTEI LEVEL {lv}", f"{L['name']} 練習問題", L["lead"], extra) + f"""
<main><div class="wrap">
{exam_section}
<section aria-labelledby="h-topics">
  <h2 id="h-topics">分野別に学ぶ・練習する</h2>
  <p class="note">「学ぶ」で要点を読んでから「解く」で確認するのがおすすめです。<span lang="vi">　Nên đọc「学ぶ」(lý thuyết) trước, rồi làm「解く」(bài tập).</span></p>
  <ul class="topics">{''.join(rows)}</ul>
</section>
</div></main>"""
    return page(site, title=f"{L['name']} 練習問題", depth=1, path=f"{L['slug']}/", nav=lv, body=body,
                desc=f"{L['name']}の無料練習問題。{'・'.join(t['name'] for t in L['topics'][:4])}など分野別に、解説つきで練習できます。")


def build_topic(site, data, lv, idx):
    L = data["levels"][lv]
    t = L["topics"][idx]
    qs = [q for q in data["questions"] if str(q["level"]) == lv and q["topic"] == t["id"]]
    items = []
    for q in qs:
        lis = "".join(f'<li data-k="{KEYS[i]}">{e(c)}</li>' for i, c in enumerate(q["choices"]))
        vi = ""
        if q.get("explanation_vi"):
            vi = (f'\n    <details class="vi-details" lang="vi"><summary><span class="vi-badge">VI</span>'
                  f'Giải thích bằng tiếng Việt</summary><p>{e(q["explanation_vi"])}</p></details>')
        items.append(f"""<article class="qitem" id="q{q['id']}">
  <span class="qid">問題ID {q['id']}</span>
  <p><strong>{e(q['question'])}</strong></p>
  <ol>{lis}</ol>
  <details>
    <summary>正解と解説を見る</summary>
    <p class="ans">正解：<b>{KEYS[q['answer']]}</b>　{e(q['choices'][q['answer']])}</p>
    <p>{e(q['explanation'])}</p>{vi}
  </details>
</article>""")
    prev_t = L["topics"][idx - 1] if idx > 0 else None
    next_t = L["topics"][idx + 1] if idx + 1 < len(L["topics"]) else None
    pager = '<div class="btn-row">'
    if prev_t:
        pager += f'<a class="btn ghost" href="{prev_t["id"]}.html">← {e(prev_t["name"])}</a>'
    if next_t:
        pager += f'<a class="btn ghost" href="{next_t["id"]}.html">{e(next_t["name"])} →</a>'
    pager += "</div>"
    learn_link = (f'<a class="btn" href="learn/{t["id"]}.html">この分野のまとめを読む</a>'
                  if f"{lv}:{t['id']}" in data["theory"] else "")
    extra = f"""<div class="btn-row" style="margin-top:20px">
    <a class="btn primary" href="../quiz.html#{lv}.{t['id']}.practice">この分野をクイズ形式で解く</a>
    {learn_link}
    <a class="btn ghost" href="index.html">{e(L['name'])}の分野一覧</a>
  </div>"""
    body = hero(f"{L['name']} ・ {len(qs)}問", f"{t['name']}の練習問題", t["desc"], extra) + f"""
<main><div class="wrap">
<section aria-label="問題一覧">
  <div class="qlist">{''.join(items) if items else '<div class="empty"><p>この分野の問題は準備中です。</p></div>'}</div>
</section>
{pager}
<p class="note">{e(site['contact_note'])}</p>
</div></main>"""
    return page(site, title=f"{L['name']}「{t['name']}」練習問題", depth=1, path=f"{L['slug']}/{t['id']}.html", nav=lv, body=body,
                desc=f"{L['name']}「{t['name']}」の練習問題{len(qs)}問と解説。{t['desc']}")


def vi_switch():
    return ('<button type="button" class="vi-switch" id="vi-switch" aria-pressed="false" lang="vi">'
            '<span class="vi-badge">VI</span><span class="vi-switch-text">Hiện bản tiếng Việt</span></button>')


def render_block(b):
    t = b["type"]
    if t == "p":
        return f'<p>{e(b["ja"])}</p>' + (f'<p class="vi-t" lang="vi">{e(b["vi"])}</p>' if b.get("vi") else "")
    if t == "list":
        tag = "ol" if b.get("ol") else "ul"
        out = f'<{tag} class="learn-list">' + "".join(f"<li>{e(x)}</li>" for x in b["ja"]) + f"</{tag}>"
        if b.get("vi"):
            out += f'<{tag} class="learn-list vi-t" lang="vi">' + "".join(f"<li>{e(x)}</li>" for x in b["vi"]) + f"</{tag}>"
        return out
    if t == "formula":
        out = '<div class="formula">' + "".join(f"<span>{e(line)}</span>" for line in b["f"]) + "</div>"
        if b.get("ja"):
            out += f'<p>{e(b["ja"])}</p>'
        if b.get("vi"):
            out += f'<p class="vi-t" lang="vi">{e(b["vi"])}</p>'
        return out
    if t == "table":
        def table(head, rows, extra=""):
            th = "".join(f'<th scope="col">{e(h)}</th>' for h in head)
            trs = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in rows)
            return f'<div class="table-wrap{extra}"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'
        out = table(b["head"], b["rows"])
        if b.get("rows_vi"):
            out = out + table(b.get("head_vi", b["head"]), b["rows_vi"], ' vi-t" lang="vi')
        return out
    if t == "point":
        return ('<aside class="point"><span class="point-label">ポイント</span>'
                f'<p>{e(b["ja"])}</p>' + (f'<p class="vi-t" lang="vi">{e(b["vi"])}</p>' if b.get("vi") else "") + "</aside>")
    return ""


def build_theory(site, data, lv, idx):
    L = data["levels"][lv]
    t = L["topics"][idx]
    th = data["theory"][f"{lv}:{t['id']}"]
    n = sum(1 for q in data["questions"] if str(q["level"]) == lv and q["topic"] == t["id"])

    toc, secs = [], []
    for i, s in enumerate(th["sections"], 1):
        toc.append(f'<li><a href="#s{i}">{e(s["h"]["ja"])}</a></li>')
        blocks = "".join(render_block(b) for b in s["blocks"])
        secs.append(f"""<section class="learn-sec" id="s{i}" aria-labelledby="h{i}">
  <div class="learn-h"><h2 id="h{i}">{e(s['h']['ja'])}</h2><p class="vi-t vi-h" lang="vi">{e(s['h'].get('vi', ''))}</p></div>
  {blocks}
</section>""")

    terms = ""
    if th.get("terms"):
        rows = "".join(f'<tr><td class="term">{e(a)}</td><td class="yomi">{e(b)}</td><td lang="vi">{e(c)}</td></tr>'
                       for a, b, c in th["terms"])
        terms = f"""<section class="learn-sec" id="terms" aria-labelledby="h-terms">
  <div class="learn-h"><h2 id="h-terms">重要用語</h2><p class="vi-t vi-h" lang="vi">Thuật ngữ quan trọng</p></div>
  <div class="table-wrap"><table class="glossary"><thead><tr><th scope="col">用語</th><th scope="col">読み</th><th scope="col" lang="vi">Tiếng Việt</th></tr></thead><tbody>{rows}</tbody></table></div>
</section>"""

    prev_t = L["topics"][idx - 1] if idx > 0 else None
    next_t = L["topics"][idx + 1] if idx + 1 < len(L["topics"]) else None
    pager = '<div class="btn-row">'
    if prev_t:
        pager += f'<a class="btn ghost" href="{prev_t["id"]}.html">← {e(prev_t["name"])}</a>'
    if next_t:
        pager += f'<a class="btn ghost" href="{next_t["id"]}.html">{e(next_t["name"])} →</a>'
    pager += "</div>"

    intro = th["intro"]
    lead_vi = f'<p class="lead vi-t" lang="vi">{e(intro["vi"])}</p>' if intro.get("vi") else ""
    extra = f"""{lead_vi}
  <div class="btn-row" style="margin-top:20px">{vi_switch()}</div>"""
    body = hero(f"{L['name']} ・ 学ぶ", f"{t['name']}のまとめ", intro["ja"], extra) + f"""
<main><div class="wrap">
<nav class="toc" aria-label="目次"><p class="eyebrow">目次</p><ul>{''.join(toc)}{'<li><a href="#terms">重要用語</a></li>' if terms else ''}</ul></nav>
<article class="learn">{''.join(secs)}{terms}</article>
<section class="cta" aria-labelledby="h-cta">
  <h2 id="h-cta">理解できたら、問題で確認しよう</h2>
  <p class="vi-t" lang="vi">Hiểu rồi thì làm bài tập để kiểm tra lại nhé.</p>
  <div class="btn-row">
    <a class="btn primary" href="../../quiz.html#{lv}.{t['id']}.practice">練習問題を解く（{n}問）</a>
    <a class="btn" href="../{t['id']}.html">問題と解説の一覧</a>
  </div>
</section>
{pager}
</div></main>"""
    return page(site, title=f"{L['name']}「{t['name']}」のまとめ", depth=2,
                path=f"{L['slug']}/learn/{t['id']}.html", nav=lv, body=body,
                desc=f"{L['name']}「{t['name']}」の要点まとめ。{t['desc']} 重要用語の読みとベトナム語訳つき。")


def build_quiz(site):
    body = """<main><div class="wrap">
<section aria-labelledby="quiz-title">
  <div class="quiz-top">
    <h1 id="quiz-title" style="font-size:1.3rem">練習問題</h1>
    <a id="quiz-back" class="btn ghost" href="4kyu/index.html">分野一覧へ</a>
  </div>
  <div id="quiz"><div class="empty"><p>問題を読み込んでいます…</p></div></div>
  <noscript><p>問題を解くにはJavaScriptを有効にしてください。各分野の問題一覧ページでは、JavaScriptなしで問題と解説を読めます。</p></noscript>
</section>
</div></main>"""
    return page(site, title="練習問題を解く", path="quiz.html", body=body,
                desc="QC検定4級・3級の練習問題をクイズ形式で解けます。1問ごとの解説、ミニ模擬試験、間違えた問題の復習に対応。")


def build_about(site):
    fb = ("各問題の下にある「この問題について意見を送る」から、Googleフォームでお知らせください。"
          if site.get("feedback_form_url") else "意見送信フォームは準備中です。")
    body = hero("ABOUT", "このサイトについて", "QC検定の勉強を始めたい人が、参考書を買う前でも無料で練習できる場所を目指しています。") + f"""
<main><div class="wrap">
<section class="prose" aria-labelledby="h-policy">
  <h2 id="h-policy">運営方針</h2>
  <p>掲載している問題と解説は、すべて運営者が独自に作成したものです。市販の問題集や過去問題をそのまま転載したものではありません。</p>
  <p>内容には注意していますが、誤りが含まれる可能性があります。正確な出題範囲や試験情報は、日本規格協会の公式情報をご確認ください。</p>
  <p>問題の誤りやわかりにくい解説を見つけたら、{fb}いただいた意見は確認のうえ、問題の修正に反映します。</p>
</section>
<section class="prose" aria-labelledby="h-privacy">
  <h2 id="h-privacy">プライバシーについて</h2>
  <p>解いた問題の記録（正解・不正解）は、お使いのブラウザの中（ローカルストレージ）にだけ保存されます。運営者や第三者のサーバーには送信されません。</p>
  <p>文字の表示にGoogle Fontsを利用しています。意見送信フォームはGoogleフォームを利用しており、送信内容はGoogleのサービス上で管理されます。</p>
  <div class="btn-row">
    <button type="button" class="btn ghost" id="reset-progress">このブラウザの学習記録を消去する</button>
  </div>
  <div id="reset-confirm" class="empty" hidden>
    <p>解いた問題の記録をすべて消去します。元に戻せません。</p>
    <div class="btn-row">
      <button type="button" class="btn primary" id="reset-yes">消去する</button>
      <button type="button" class="btn" id="reset-no">やめる</button>
    </div>
  </div>
</section>
</div></main>"""
    return page(site, title="このサイトについて", path="about.html", nav="about", body=body,
                desc=f"{site['site_name']}の運営方針と、学習記録の扱い（プライバシー）について。")


def write(rel, text):
    p = DIST / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    site, data = load()
    errors = validate(data) + validate_theory(data)
    if errors:
        print("questions.json にエラーがあります：")
        for m in errors:
            print("  -", m)
        sys.exit(1)
    counts = {lv: sum(1 for q in data["questions"] if str(q["level"]) == lv) for lv in data["levels"]}
    st = {}
    for q in data["questions"]:
        st[q.get("status", "draft")] = st.get(q.get("status", "draft"), 0) + 1
    print(f"OK: {len(data['questions'])}問（" + "、".join(f"{lv}級 {n}問" for lv, n in counts.items()) + "）、状態: "
          + "、".join(f"{k} {v}" for k, v in sorted(st.items())))
    if "--check" in sys.argv:
        return

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    for f in ("style.css", "app.js"):
        shutil.copy(SRC / "assets" / f, DIST / "assets" / f)

    fields = ("id", "level", "topic", "question", "choices", "answer", "explanation", "explanation_vi")
    public_q = [{k: q[k] for k in fields if k in q} for q in data["questions"]]
    known = {q["id"] for q in public_q}
    exams = {lv: [ex for ex in sets if all(i in known for i in ex)] for lv, sets in data["exams"].items()}
    write("assets/questions.js", "window.QC_DATA = " + json.dumps(
        {"levels": data["levels"], "questions": public_q, "exams": exams,
         "exam_cfg": {"pass_rate": data["exam_cfg"].get("pass_rate", 0.7)}},
        ensure_ascii=False, separators=(",", ":")) + ";\n")
    write("assets/config.js", "window.QC_CONFIG = " + json.dumps(
        {"site_name": site["site_name"], "feedback_form_url": site.get("feedback_form_url", "")},
        ensure_ascii=False) + ";\n")

    pages = ["", "quiz.html", "about.html"]
    write("index.html", build_index(site, data))
    write("quiz.html", build_quiz(site))
    write("about.html", build_about(site))
    for lv, L in data["levels"].items():
        write(f"{L['slug']}/index.html", build_level(site, data, lv))
        pages.append(f"{L['slug']}/")
        for i, t in enumerate(L["topics"]):
            write(f"{L['slug']}/{t['id']}.html", build_topic(site, data, lv, i))
            pages.append(f"{L['slug']}/{t['id']}.html")
            if f"{lv}:{t['id']}" in data["theory"]:
                write(f"{L['slug']}/learn/{t['id']}.html", build_theory(site, data, lv, i))
                pages.append(f"{L['slug']}/learn/{t['id']}.html")

    base = site["site_url"].rstrip("/")
    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{e(base + '/' + p)}</loc><lastmod>{today}</lastmod></url>" for p in pages)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    write(".nojekyll", "")
    # files that must be served as-is from the site root (e.g. Google Search Console verification)
    static = SRC / "static"
    if static.exists():
        for f in static.iterdir():
            if f.is_file():
                shutil.copy(f, DIST / f.name)
    print(f"dist/ に {len(pages)} ページを書き出しました")


if __name__ == "__main__":
    main()
