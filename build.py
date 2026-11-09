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
                if b.get("type") not in ("p", "list", "formula", "table", "point", "mistake", "memo"):
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

def page(site, *, title, desc, body, depth=0, path="", nav="", crumbs=None, head_extra="", lang="ja", alternates=None):
    pre = "../" * depth
    base = site["site_url"].rstrip("/") + "/"
    for code, alt_path in (alternates or {}).items():
        head_extra += f'\n<link rel="alternate" hreflang="{code}" href="{e(base + alt_path)}">'
    crumbs_html = ""
    if crumbs:
        items = [("Trang chủ" if lang == "vi" else "ホーム", "")] + list(crumbs)
        ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": k, "name": n, "item": base + u} for k, (n, u) in enumerate(items, 1)]}
        head_extra += '\n<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"
        links = [f'<a href="{pre}{u or "index.html"}">{e(n)}</a>' for n, u in items[:-1]]
        crumbs_html = ('<nav class="crumbs" aria-label="パンくずリスト"><div class="wrap">'
                       + " › ".join(links + [f'<span aria-current="page">{e(items[-1][0])}</span>']) + "</div></nav>")
    full_title = (f"{title} | {site['site_name']}" if title != site["site_name"] else f"{site['site_name']}｜{site['tagline']}")
    url = site["site_url"].rstrip("/") + "/" + path
    gsv = (f'\n<meta name="google-site-verification" content="{e(site["google_site_verification"])}">'
           if site.get("google_site_verification") else "")

    def nav_link(href, label, key):
        cur = ' aria-current="page"' if key == nav else ""
        return f'<a href="{pre}{href}"{cur}>{label}</a>'

    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">{gsv}
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(url)}">
<meta property="og:site_name" content="{e(site['site_name'])}">
<meta property="og:locale" content="{'vi_VN' if lang == 'vi' else 'ja_JP'}">
<meta name="twitter:card" content="summary">{head_extra}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{pre}assets/style.css">
<script>try{{var v=localStorage.getItem("qc-renshu:vi");{'if(v===null){v="1";localStorage.setItem("qc-renshu:vi","1")}' if lang == "vi" else ""}document.documentElement.classList.add(v==="1"?"vi-on":"vi-off")}}catch(e){{document.documentElement.classList.add("{'vi-on' if lang == 'vi' else 'vi-off'}")}}</script>
</head>
<body>
<header class="site-head"><div class="wrap">
  <a class="brand" href="{pre}index.html"><span class="mark">○</span>{e(site['site_name'])}</a>
  <nav class="nav" aria-label="メインメニュー">
    {nav_link('4kyu/index.html', '4級', '4')}
    {nav_link('3kyu/index.html', '3級', '3')}
    {nav_link('exam.html', '試験について', 'exam')}
    {nav_link('progress.html', '進捗', 'progress')}
    <a href="{pre}vi/index.html" lang="vi" hreflang="vi"{' aria-current="page"' if nav == 'vi' else ''}>Tiếng Việt</a>
  </nav>
</div></header>
{crumbs_html}
{body}
<footer class="site-foot"><div class="wrap">
  <span>© {date.today().year} {e(site['site_name'])}　QC検定®は一般財団法人日本規格協会の登録商標です。本サイトは非公式の学習サイトです。</span>
  <span class="foot-links"><a href="{pre}about.html">このサイトについて・プライバシー</a><a href="{pre}exam.html">試験について・よくある質問</a></span>
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
<section aria-labelledby="h-try">
  <h2 id="h-try">1問ためしてみる</h2>
  <div id="sample-q"><div class="empty"><p>問題を読み込んでいます…</p></div></div>
</section>
<section aria-labelledby="h-more">
  <h2 id="h-more">試験の準備に</h2>
  <div class="levels">
    <a class="level-card link-card" href="exam.html"><h3>試験について</h3><p>CBTの形式、合格基準（3級は各分野50%以上も必要）、よくある質問。</p></a>
    <a class="level-card link-card" href="progress.html"><h3>学習の進捗</h3><p>分野ごとの正答率と、苦手な分野がひと目でわかります。</p></a>
    <a class="level-card link-card" href="3kyu/flashcards.html"><h3>用語フラッシュカード</h3><p>重要用語を読みとベトナム語訳つきのカードで覚えます。</p></a>
  </div>
</section>
<section aria-labelledby="h-how">
  <h2 id="h-how">使い方</h2>
  <ul class="topics">
    <li><div><span class="t-name">要点を学ぶ</span><p class="t-desc">分野ごとのまとめページで、考え方・公式・重要用語（読み・ベトナム語訳つき）を確認できます。</p></div></li>
    <li><div><span class="t-name">分野別に練習する</span><p class="t-desc">1問ごとに正解と解説が出ます。苦手な分野だけをくり返し解けます。</p></div></li>
    <li><div><span class="t-name">ミニ模擬試験で力をはかる</span><p class="t-desc">全分野からランダムに最大{20}問。最後にまとめて採点し、所要時間も表示します。</p></div></li>
    <li><div><span class="t-name">間違えた問題を復習する</span><p class="t-desc">直近で間違えた問題が自動で集まります。正解すると復習リストから外れます。</p></div></li>
    <li><div><span class="t-name">ベトナム語版もあります</span><p class="t-desc">メニューの「<a href="vi/index.html" lang="vi" hreflang="vi">Tiếng Việt</a>」から、ベトナム語の解説つきで学べます。</p></div></li>
  </ul>
  <p class="note">学習の記録はお使いのブラウザの中にだけ保存され、外部には送信されません。</p>
</section>
</div></main>"""
    return page(site, title=site["site_name"], body=body, path="", alternates={"ja": "", "vi": "vi/", "x-default": ""},
                desc=f"{site['tagline']}。分野別の練習問題と解説、ミニ模擬試験、間違えた問題の復習が無料・登録なしで使えます。")


def build_exam_section(data, lv):
    cfg = data["exam_cfg"]
    size = cfg.get("size", 50)
    sets = data["exams"].get(lv, [])
    n_level = sum(1 for q in data["questions"] if str(q["level"]) == lv)
    used = sum(len(x) for x in sets)
    left = size - (n_level - used)
    nxt = (f'<p class="note">次の模擬試験（第{len(sets) + 1}回）まで、あと{max(left, 0)}問。問題が{size}問たまるごとに、1回分ずつ追加されます。</p>')
    dmin = cfg.get("domain_min", {}).get(lv)
    pr = round(cfg.get("pass_rate", 0.7) * 100)
    if dmin:
        names = "・".join(data["levels"][lv]["domains"].values())
        rule = f"本番と同じく、総合{pr}%以上かつ{names}がそれぞれ{round(dmin * 100)}%以上で合格ラインです。各回は分野のバランスを本番に合わせています。"
    else:
        rule = f"合格の目安は総合{pr}%以上です。"
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
  <p class="note">{size}問・時間を計って本番形式で解き、最後にまとめて採点します。{rule}</p>
  {cards}
  {nxt if len(sets) < cfg.get("max_exams", {}).get(lv, 99) else ""}
</section>"""


def build_level(site, data, lv):
    L = data["levels"][lv]
    rows = []
    groups = {}
    for t in L["topics"]:
        groups.setdefault(t.get("domain", "all"), []).append(t)
    for t in [t for d in groups for t in groups[d]]:
        n = sum(1 for q in data["questions"] if str(q["level"]) == lv and q["topic"] == t["id"])
        has_theory = f"{lv}:{t['id']}" in data["theory"]
        name_href = f"learn/{t['id']}.html" if has_theory else f"{t['id']}.html"
        learn_btn = f'<a class="btn" href="learn/{t["id"]}.html">学ぶ</a>' if has_theory else ""
        rows.append((t.get("domain", "all"), f"""<li data-progress="{lv}:{t['id']}">
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
</li>"""))
    dnames = L.get("domains", {})
    grouped = ""
    for d in groups:
        items = "".join(r for dd, r in rows if dd == d)
        label = dnames.get(d, "")
        grouped += (f'<h3 class="domain-h">{e(label)}</h3>' if label else "") + f'<ul class="topics">{items}</ul>'
    extra = f"""<div class="btn-row" style="margin-top:20px">
    <a class="btn primary" href="../quiz.html#{lv}.all.practice">全分野で練習</a>
    <a class="btn" href="../quiz.html#{lv}.all.exam">ミニ模擬試験（最大20問）</a>
    <a class="btn" href="../quiz.html#{lv}.all.review">間違えた問題を復習（<span data-review-count="{lv}:all">0</span>）</a>
    <a class="btn" href="flashcards.html">用語フラッシュカード</a>
  </div>"""
    exam_section = build_exam_section(data, lv)
    body = hero(f"QC KENTEI LEVEL {lv}", f"{L['name']} 練習問題", L["lead"], extra) + f"""
<main><div class="wrap">
{exam_section}
<section aria-labelledby="h-topics">
  <h2 id="h-topics">分野別に学ぶ・練習する</h2>
  <p class="note">「学ぶ」で要点を読んでから「解く」で確認するのがおすすめです。</p>
  {grouped}
</section>
</div></main>"""
    return page(site, title=f"{L['name']} 練習問題", depth=1, path=f"{L['slug']}/", nav=lv, body=body,
                crumbs=[(L["name"], f"{L['slug']}/")],
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
                crumbs=[(L["name"], f"{L['slug']}/"), (f"{t['name']}の問題", f"{L['slug']}/{t['id']}.html")],
                desc=f"{L['name']}「{t['name']}」の練習問題{len(qs)}問と解説。{t['desc']}")


def render_block(b, lang="ja"):
    """Render one theory block in a single language (ja pages and vi pages are separate)."""
    t = b["type"]
    txt = b.get(lang) or (b.get("ja") if lang == "vi" else "")
    if t == "p":
        return f"<p>{e(txt)}</p>" if txt else ""
    if t == "list":
        tag = "ol" if b.get("ol") else "ul"
        items = txt if isinstance(txt, list) else b.get("ja", [])
        return f'<{tag} class="learn-list">' + "".join(f"<li>{e(x)}</li>" for x in items) + f"</{tag}>"
    if t == "formula":
        out = '<div class="formula" lang="ja">' + "".join(f"<span>{e(line)}</span>" for line in b["f"]) + "</div>"
        return out + (f"<p>{e(txt)}</p>" if txt else "")
    if t == "table":
        head, rows = b["head"], b["rows"]
        if lang == "vi" and b.get("rows_vi"):
            head, rows = b.get("head_vi", head), b["rows_vi"]
        th = "".join(f'<th scope="col">{e(h)}</th>' for h in head)
        trs = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in rows)
        return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'
    if t in ("mistake", "memo", "point"):
        labels = {"ja": {"mistake": "よくある間違い", "memo": "覚え方", "point": "ポイント"},
                  "vi": {"mistake": "Lỗi hay gặp", "memo": "Mẹo nhớ", "point": "Điểm chính"}}
        return (f'<aside class="{t}"><span class="point-label">{labels[lang][t]}</span>'
                f"<p>{e(txt)}</p></aside>")
    return ""


def build_theory(site, data, lv, idx, lang="ja"):
    L = data["levels"][lv]
    t = L["topics"][idx]
    th = data["theory"][f"{lv}:{t['id']}"]
    n = sum(1 for q in data["questions"] if str(q["level"]) == lv and q["topic"] == t["id"])
    vi = lang == "vi"
    T = (lambda ja, v: v) if vi else (lambda ja, v: ja)
    name = t.get("name_vi", t["name"]) if vi else t["name"]
    ja_path = f"{L['slug']}/learn/{t['id']}.html"
    vi_path = f"vi/{L['slug']}/{t['id']}.html"
    up = "../../"  # both page kinds sit two levels deep

    def heading(h):
        if vi:
            return f'<h2 id="{{id}}">{e(h.get("vi") or h["ja"])}</h2><p class="vi-h" lang="ja">{e(h["ja"])}</p>'
        return f'<h2 id="{{id}}">{e(h["ja"])}</h2>'

    basic = [s for s in th["sections"] if s.get("basic")]
    summary = [s for s in th["sections"] if not s.get("basic")]
    toc, secs = [], []
    k = 0
    for group, label, badge in ((basic, T("基礎から学ぶ（はじめての人へ）", "Học từ cơ bản (cho người mới bắt đầu)"), T("入門", "Cơ bản")),
                                (summary, T("要点まとめ", "Tóm tắt ý chính"), "")):
        if not group:
            continue
        gid = "g-basic" if badge else "g-sum"
        secs.append(f'<h2 class="learn-group" id="{gid}">{e(label)}</h2>')
        sub = []
        for s in group:
            k += 1
            title = (s["h"].get("vi") or s["h"]["ja"]) if vi else s["h"]["ja"]
            sub.append(f'<li><a href="#s{k}">{e(title)}</a></li>')
            blocks = "".join(render_block(b, lang) for b in s["blocks"])
            tag = f'<span class="basic-badge">{e(badge)}</span>' if badge else ""
            secs.append(f"""<section class="learn-sec{' basic' if badge else ''}" id="s{k}" aria-labelledby="h{k}">
  <div class="learn-h">{tag}{heading(s['h']).replace('{id}', f'h{k}')}</div>
  {blocks}
</section>""")
        toc.append(f'<li><a href="#{gid}">{e(label)}</a><ul>{"".join(sub)}</ul></li>')

    terms = ""
    if th.get("terms"):
        if vi:
            rows = "".join(f'<tr><td class="term" lang="ja">{e(a)}</td><td class="yomi" lang="ja">{e(b)}</td><td>{e(c)}</td></tr>'
                           for a, b, c in th["terms"])
            head = '<th scope="col">Thuật ngữ</th><th scope="col">Cách đọc</th><th scope="col">Nghĩa</th>'
        else:
            rows = "".join(f'<tr><td class="term">{e(a)}</td><td class="yomi">{e(b)}</td></tr>' for a, b, c in th["terms"])
            head = '<th scope="col">用語</th><th scope="col">読み</th>'
        terms = f"""<section class="learn-sec" id="terms" aria-labelledby="h-terms">
  <div class="learn-h"><h2 id="h-terms">{T('重要用語', 'Thuật ngữ quan trọng')}</h2></div>
  <div class="table-wrap"><table class="glossary"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>
</section>"""
        toc.append(f'<li><a href="#terms">{T("重要用語", "Thuật ngữ quan trọng")}</a></li>')

    def sib(o):
        return f"{o['id']}.html"
    prev_t = L["topics"][idx - 1] if idx > 0 else None
    next_t = L["topics"][idx + 1] if idx + 1 < len(L["topics"]) else None
    nm = (lambda o: o.get("name_vi", o["name"])) if vi else (lambda o: o["name"])
    pager = '<div class="btn-row">'
    if prev_t and f"{lv}:{prev_t['id']}" in data["theory"]:
        pager += f'<a class="btn ghost" href="{sib(prev_t)}">← {e(nm(prev_t))}</a>'
    if next_t and f"{lv}:{next_t['id']}" in data["theory"]:
        pager += f'<a class="btn ghost" href="{sib(next_t)}">{e(nm(next_t))} →</a>'
    pager += "</div>"

    intro = th["intro"]
    if vi:
        switch = f'<a class="btn ghost lang-link" lang="ja" hreflang="ja" href="{up}{ja_path}">日本語で読む</a>'
        lead = intro.get("vi") or intro["ja"]
        h1 = f"Lý thuyết: {name}"
        eyebrow = f"{L['name']} · Lý thuyết · {t['name']}"
        cta_h, cta_btn, cta_list = ("Hiểu rồi thì làm bài tập để kiểm tra", f"Làm bài tập ({n} câu)", "Danh sách câu hỏi và giải thích")
        crumbs = [("Tiếng Việt", "vi/"), (f"{L['name']} · {name}", vi_path)]
        title = f"Lý thuyết {L['name']}: {name} ({t['name']})"
        desc = f"Lý thuyết {L['name']} phần {name} ({t['name']}) bằng tiếng Việt: giải thích từ cơ bản cho người mới, ví dụ thực tế, tóm tắt ý chính và thuật ngữ."
    else:
        switch = f'<a class="btn ghost lang-link" lang="vi" hreflang="vi" href="{up}{vi_path}">Tiếng Việt</a>'
        lead = intro["ja"]
        h1 = f"{t['name']}のまとめ"
        eyebrow = f"{L['name']} ・ 学ぶ"
        cta_h, cta_btn, cta_list = ("理解できたら、問題で確認しよう", f"練習問題を解く（{n}問）", "問題と解説の一覧")
        crumbs = [(L["name"], f"{L['slug']}/"), (f"{t['name']}のまとめ", ja_path)]
        title = f"{L['name']}「{t['name']}」のまとめ"
        desc = f"{L['name']}「{t['name']}」を基礎から解説。はじめての人向けの説明と例題、要点まとめ、重要用語の読みつき。"
    extra = f'<div class="btn-row" style="margin-top:20px">{switch}</div>'
    body = hero(eyebrow, h1, lead, extra) + f"""
<main><div class="wrap">
<nav class="toc" aria-label="{T('目次', 'Mục lục')}"><p class="eyebrow">{T('目次', 'Mục lục')}</p><ul>{''.join(toc)}</ul></nav>
<article class="learn">{''.join(secs)}{terms}</article>
<section class="cta" aria-labelledby="h-cta">
  <h2 id="h-cta">{e(cta_h)}</h2>
  <div class="btn-row">
    <a class="btn primary" href="{up}quiz.html#{lv}.{t['id']}.practice">{e(cta_btn)}</a>
    <a class="btn" href="{up}{L['slug']}/{t['id']}.html">{e(cta_list)}</a>
  </div>
</section>
{pager}
</div></main>"""
    return page(site, title=title, depth=2, path=vi_path if vi else ja_path, nav="vi" if vi else lv, body=body,
                lang=lang, crumbs=crumbs, desc=desc,
                alternates={"ja": ja_path, "vi": vi_path, "x-default": ja_path})


FAQ = [
    ("QC検定3級・4級は、いまどのような形式の試験ですか？",
     "2025年9月の第40回から、3級・4級はテストセンターで受けるコンピュータ試験（CBT）になりました。決められた期間の中で、空いている会場と日時を選んで受検します。",
     "Từ kỳ thi lần thứ 40 (tháng 9/2025), 3級 và 4級 thi trên máy tính (CBT) tại trung tâm thi. Thí sinh chọn địa điểm và giờ còn trống trong khoảng thời gian quy định."),
    ("3級の合格基準を教えてください。",
     "総合得点率がおおむね70%以上で、かつ手法分野・実践分野それぞれの得点率がおおむね50%以上であることが目安です。片方の分野だけが得意でも合格できないので、両方をバランスよく学びましょう。",
     "Mốc đỗ 3級: tổng điểm khoảng 70% trở lên, đồng thời phần 手法 (phương pháp) và phần 実践 (thực tiễn) mỗi phần khoảng 50% trở lên. Giỏi một phần thôi thì chưa đỗ, nên cần học cân bằng cả hai."),
    ("4級の出題範囲と合格基準は？",
     "4級は「実践分野」「手法分野」「企業活動の基本」から出題され、総合でおおむね70%以上が合格の目安です。品質管理の基本的な用語と考え方が中心です。",
     "4級 ra đề từ 3 phần: 実践 (thực tiễn), 手法 (phương pháp) và 企業活動の基本 (cơ bản về hoạt động doanh nghiệp). Mốc đỗ là tổng điểm khoảng 70% trở lên."),
    ("4級と3級、どちらから受ければいいですか？",
     "受検資格の制限はないので、どちらからでも受けられます。品質管理を初めて学ぶなら4級から、職場でQC七つ道具や管理図を使う機会があるなら3級から始める人も多いです。",
     "Không có điều kiện dự thi nên bắt đầu từ cấp nào cũng được. Mới học QC thì nên bắt đầu từ 4級; nếu ở chỗ làm đã dùng 7 công cụ QC, biểu đồ kiểm soát thì nhiều người thi thẳng 3級."),
    ("このサイトの問題は過去問ですか？",
     "いいえ。掲載している問題と解説は、すべて運営者が独自に作成したものです。過去問題や市販の問題集を転載したものではありません。",
     "Không. Tất cả câu hỏi và lời giải thích đều do người làm web tự soạn, không chép từ đề thi cũ hay sách bán ngoài thị trường."),
    ("無料で使えますか？ベトナム語の解説はありますか？",
     "すべて無料で、登録も不要です。解説の下の「Xem giải thích bằng tiếng Việt」を押すと、ベトナム語の解説が表示されます。",
     "Hoàn toàn miễn phí, không cần đăng ký. Bấm「Xem giải thích bằng tiếng Việt」dưới phần giải thích để xem bản tiếng Việt."),
]


def build_exam_info(site, data):
    faq_html = "".join(
        f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>'
        for q, a, v in FAQ)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a, _ in FAQ]}
    body = hero("EXAM GUIDE", "QC検定3級・4級の試験について",
                "試験の形式と合格基準、このサイトでの学び方をまとめました。最新の日程や申込方法は、必ず公式情報で確認してください。",
                '') + f"""
<main><div class="wrap">
<section aria-labelledby="h-fmt">
  <h2 id="h-fmt">試験の概要</h2>
  <div class="table-wrap"><table>
    <thead><tr><th scope="col">項目</th><th scope="col">3級</th><th scope="col">4級</th></tr></thead>
    <tbody>
      <tr><td>試験方式</td><td>CBT（テストセンターのコンピュータ試験）</td><td>CBT（テストセンターのコンピュータ試験）</td></tr>
      <tr><td>出題分野</td><td>手法分野・実践分野</td><td>実践分野・手法分野・企業活動の基本</td></tr>
      <tr><td>合格基準（目安）</td><td>総合70%以上、かつ各分野50%以上</td><td>総合70%以上</td></tr>
      <tr><td>試験時間</td><td>90分</td><td>公式情報で確認</td></tr>
      <tr><td>解答方式</td><td>選択式</td><td>選択式</td></tr>
    </tbody>
  </table></div>
  <aside class="point"><span class="point-label">ポイント</span>
    <p>3級は、総合点が高くても片方の分野が50%未満だと不合格になります。このサイトの3級模擬試験は、手法と実践を25問ずつ出題し、分野ごとの得点も表示します。</p>
  </aside>
  <p class="note">実施時期は年2回（3級はおおむね6月下旬〜9月下旬と、12月中旬〜翌年3月中旬）とされています。日程・受検料・申込方法は変わることがあるため、日本規格協会（JSA）の公式情報と<a href="https://cbt-s.com/page/qckc_all.html/" rel="noopener" target="_blank">CBT申込ページ</a>で確認してください。</p>
</section>
<section aria-labelledby="h-how2">
  <h2 id="h-how2">このサイトでの学び方</h2>
  <ol class="learn-list">
    <li>各級のページで分野を選び、「学ぶ」で要点と重要用語を確認する</li>
    <li>「解く」で分野別の問題を解き、解説を読む</li>
    <li>「進捗」ページで苦手な分野を確認し、間違えた問題を復習する</li>
    <li>模擬試験で、本番と同じ合格基準で力を確かめる</li>
  </ol>
  <div class="btn-row"><a class="btn primary" href="4kyu/index.html">4級をはじめる</a><a class="btn primary" href="3kyu/index.html">3級をはじめる</a><a class="btn" href="progress.html">進捗を見る</a></div>
</section>
<section aria-labelledby="h-faq">
  <h2 id="h-faq">よくある質問</h2>
  {faq_html}
</section>
</div></main>"""
    return page(site, title="QC検定3級・4級の試験について（形式・合格基準・よくある質問）", path="exam.html", nav="exam", body=body,
                crumbs=[("試験について", "exam.html")],
                head_extra='\n<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>",
                desc="QC検定3級・4級の試験形式（CBT）、合格基準（3級は総合70%以上かつ各分野50%以上）、出題分野とよくある質問をまとめています。")


def build_progress(site):
    body = hero("MY PROGRESS", "学習の進捗", "このブラウザで解いた問題の記録から、分野ごとの正答率と苦手な分野を表示します。") + """
<main><div class="wrap">
  <div id="progress-root"><div class="empty"><p>記録を読み込んでいます…</p></div></div>
  <noscript><p>進捗の表示にはJavaScriptを有効にしてください。</p></noscript>
  <p class="note">記録はこのブラウザにだけ保存されています。別の端末やブラウザとは共有されません。</p>
</div></main>"""
    return page(site, title="学習の進捗", path="progress.html", nav="progress", body=body,
                desc="分野ごとの正答率、苦手な分野、模擬試験の最高点を確認できます。")


def build_flashcards(site, data, lv):
    L = data["levels"][lv]
    cards = []
    for t in L["topics"]:
        th = data["theory"].get(f"{lv}:{t['id']}")
        if not th:
            continue
        for term, yomi, vi in th.get("terms", []):
            cards.append({"t": term, "y": yomi, "v": vi, "k": t["id"], "n": t["name"]})
    topics_opts = "".join(f'<option value="{t["id"]}">{e(t["name"])}</option>' for t in L["topics"]
                          if f"{lv}:{t['id']}" in data["theory"])
    body = hero(f"{L['name']} ・ 用語", f"{L['name']} 用語フラッシュカード",
                f"重要用語{len(cards)}語を、カードをめくって覚えます。表は用語、裏は読みとベトナム語の意味です。") + f"""
<main><div class="wrap">
<section class="fc" id="fc-root" aria-label="フラッシュカード">
  <div class="fc-controls">
    <label for="fc-topic">分野</label>
    <select id="fc-topic"><option value="all">すべての分野</option>{topics_opts}</select>
    <label class="fc-check"><input type="checkbox" id="fc-unknown"> まだ覚えていないカードだけ</label>
  </div>
  <p class="meta" id="fc-count"></p>
  <button type="button" class="fc-card" id="fc-card" aria-live="polite">
    <span class="fc-front" id="fc-front"></span>
    <span class="fc-back" id="fc-back" hidden></span>
    <span class="fc-hint" id="fc-hint">タップして裏を見る</span>
  </button>
  <div class="btn-row fc-actions">
    <button type="button" class="btn ghost" id="fc-again">もう一度</button>
    <button type="button" class="btn primary" id="fc-known">覚えた</button>
  </div>
  <p class="note">キー操作：スペースでめくる、→ で「覚えた」、← で「もう一度」。</p>
  <script type="application/json" id="fc-data">{json.dumps(cards, ensure_ascii=False)}</script>
</section>
</div></main>"""
    return page(site, title=f"{L['name']} 用語フラッシュカード", depth=1, path=f"{L['slug']}/flashcards.html", nav=lv, body=body,
                crumbs=[(L["name"], f"{L['slug']}/"), ("用語フラッシュカード", f"{L['slug']}/flashcards.html")],
                desc=f"{L['name']}の重要用語{len(cards)}語をフラッシュカードで覚えられます。読みとベトナム語訳つき。")



VI_FAQ = [
    ("QC検定 là gì?",
     "QC検定 (品質管理検定 – Kiểm định quản lý chất lượng) là kỳ thi do Hiệp hội Tiêu chuẩn Nhật Bản (JSA) và Hiệp hội Khoa học Kỹ thuật Nhật Bản (JUSE) tổ chức, đánh giá kiến thức quản lý chất lượng. Có 4 cấp, từ 4級 (cơ bản nhất) đến 1級. Nhiều nhà máy ở Nhật khuyến khích nhân viên thi 4級, 3級."),
    ("Hiện nay 3級 và 4級 thi như thế nào?",
     "Từ kỳ thi lần thứ 40 (tháng 9/2025), 3級 và 4級 thi trên máy tính (CBT) tại trung tâm thi. Thí sinh tự chọn địa điểm và giờ thi trong khoảng thời gian quy định. Đề thi hoàn toàn bằng tiếng Nhật, dạng trắc nghiệm."),
    ("Tiêu chuẩn đỗ là bao nhiêu?",
     "3級: tổng điểm khoảng 70% trở lên, đồng thời phần 手法 (phương pháp) và phần 実践 (thực tiễn) mỗi phần khoảng 50% trở lên. 4級: tổng điểm khoảng 70% trở lên."),
    ("Không giỏi tiếng Nhật có học được không?",
     "Đề thi bằng tiếng Nhật nên vẫn cần học thuật ngữ tiếng Nhật. Trên web này, câu hỏi giữ nguyên tiếng Nhật như đề thật, còn lời giải thích và bài lý thuyết có thêm bản tiếng Việt; thuật ngữ có cách đọc hiragana và nghĩa tiếng Việt, kèm flashcard để học thuộc."),
    ("Web có mất phí hay cần đăng ký không?",
     "Không. Web hoàn toàn miễn phí, không cần đăng ký. Tiến độ học được lưu ngay trên trình duyệt của bạn."),
    ("Câu hỏi trên web có phải đề thi cũ không?",
     "Không. Tất cả câu hỏi và lời giải thích đều được soạn riêng, không chép từ đề thi cũ hay sách. Mỗi câu đều qua bước kiểm tra độc lập trước khi đăng. Mỗi tuần web đều thêm câu hỏi mới."),
]


def build_vi(site, data):
    lv_blocks = []
    for lv in ("4", "3"):
        L = data["levels"][lv]
        n = sum(1 for q in data["questions"] if str(q["level"]) == lv)
        n_ex = len(data["exams"].get(lv, []))
        groups = {}
        for t in L["topics"]:
            groups.setdefault(t.get("domain", "all"), []).append(t)
        rows = ""
        for d, ts in groups.items():
            dj = L.get("domains", {}).get(d, ""); dv = L.get("domains_vi", {}).get(d, "")
            rows += f'<h3 class="domain-h">{e(dv)} <span lang="ja">（{e(dj)}）</span></h3><ul class="topics">'
            for t in ts:
                k = sum(1 for q in data["questions"] if str(q["level"]) == lv and q["topic"] == t["id"])
                learn = (f'<a class="btn" href="{L["slug"]}/{t["id"]}.html">Lý thuyết</a>'
                         if f"{lv}:{t['id']}" in data["theory"] else "")
                rows += f"""<li><div>
    <span class="t-name">{e(t.get('name_vi', t['name']))}</span>
    <p class="t-desc" lang="ja">{e(t['name'])}</p>
    <span class="meta">{k} câu</span>
  </div><div class="t-actions">
    {learn}
    <a class="btn primary" href="../quiz.html#{lv}.{t['id']}.practice">Làm bài</a>
  </div></li>"""
            rows += "</ul>"
        lv_blocks.append(f"""<section aria-labelledby="vi-h{lv}">
  <h2 id="vi-h{lv}">{e(L['name'])} <span class="meta">· {n} câu · {n_ex} đề thi thử</span></h2>
  <div class="btn-row">
    <a class="btn primary" href="../{L['slug']}/index.html">Vào trang {e(L['name'])}</a>
    <a class="btn" href="../{L['slug']}/flashcards.html">Flashcard thuật ngữ</a>
  </div>
  {rows}
</section>""")
    faq_html = "".join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in VI_FAQ)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": "vi", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in VI_FAQ]}
    total = len(data["questions"])
    body = hero("QC KENTEI · TIẾNG VIỆT", "Ôn thi QC検定 4級・3級 miễn phí, có giải thích tiếng Việt",
                f"Dành cho người Việt đang làm việc tại Nhật. Câu hỏi bằng tiếng Nhật như đề thật, lời giải thích và lý thuyết có bản tiếng Việt. Hiện có {total} câu, mỗi tuần đều thêm câu mới.",
                '<div class="btn-row" style="margin-top:20px"><a class="btn primary" href="../4kyu/index.html">Bắt đầu 4級</a><a class="btn primary" href="../3kyu/index.html">Bắt đầu 3級</a><a class="btn" href="../progress.html">Xem tiến độ</a></div>') + f"""
<main><div class="wrap">
<section aria-labelledby="vi-how">
  <h2 id="vi-how">Học trên web này như thế nào</h2>
  <ol class="learn-list">
    <li><b>Đọc lý thuyết</b> bằng tiếng Việt của từng phân野: phần cơ bản cho người mới, tóm tắt ý chính, công thức, lỗi hay gặp, mẹo nhớ và bảng thuật ngữ có cách đọc, nghĩa tiếng Việt.</li>
    <li><b>Làm bài tập</b> theo phân野: chọn đáp án là biết đúng sai ngay, kèm giải thích tiếng Nhật và tiếng Việt.</li>
    <li><b>Ôn câu sai</b>: câu làm sai được tự động gom lại để ôn.</li>
    <li><b>Thi thử 50 câu</b>: có đồng hồ, chấm theo đúng tiêu chuẩn đỗ (3級 cần tổng ≥ 70% và mỗi phần ≥ 50%).</li>
  </ol>
  <aside class="point"><span class="point-label">MẸO</span>
    <p>Mới học QC lần đầu? Hãy bắt đầu từ phần「Học từ cơ bản」ở đầu mỗi bài lý thuyết: giải thích bằng ví dụ thực tế, rồi đến ví dụ tính toán từng bước. Câu hỏi bài tập giữ nguyên tiếng Nhật như đề thật; giải thích tiếng Việt hiện ngay dưới mỗi câu (bấm「Ẩn giải thích tiếng Việt」nếu muốn luyện chỉ tiếng Nhật).</p>
  </aside>
</section>
{''.join(lv_blocks)}
<section aria-labelledby="vi-faq">
  <h2 id="vi-faq">Câu hỏi thường gặp</h2>
  {faq_html}
  <p class="note">Lịch thi, lệ phí và cách đăng ký có thể thay đổi; hãy xem thông tin chính thức của JSA và <a href="https://cbt-s.com/page/qckc_all.html/" rel="noopener" target="_blank">trang đăng ký thi CBT</a>. Tóm tắt bằng tiếng Nhật: <a href="../exam.html" lang="ja">試験について</a>.</p>
</section>
</div></main>"""
    return page(site, title="Ôn thi QC検定 4級・3級 miễn phí – giải thích tiếng Việt", depth=1, path="vi/", nav="vi", body=body,
                lang="vi", alternates={"vi": "vi/", "ja": "", "x-default": ""},
                crumbs=[("Tiếng Việt", "vi/")],
                head_extra='\n<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>",
                desc=f"Web ôn thi QC検定 4級・3級 miễn phí cho người Việt tại Nhật: {total} câu hỏi có giải thích tiếng Việt, lý thuyết song ngữ, flashcard thuật ngữ và đề thi thử chấm như thi thật.")

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
         "exam_cfg": {"pass_rate": data["exam_cfg"].get("pass_rate", 0.7),
                      "domain_min": data["exam_cfg"].get("domain_min", {})}},
        ensure_ascii=False, separators=(",", ":")) + ";\n")
    write("assets/config.js", "window.QC_CONFIG = " + json.dumps(
        {"site_name": site["site_name"], "feedback_form_url": site.get("feedback_form_url", "")},
        ensure_ascii=False) + ";\n")

    pages = ["", "quiz.html", "about.html"]
    write("index.html", build_index(site, data))
    write("quiz.html", build_quiz(site))
    write("about.html", build_about(site))
    write("exam.html", build_exam_info(site, data))
    write("progress.html", build_progress(site))
    write("vi/index.html", build_vi(site, data))
    pages.append("vi/")
    pages.append("exam.html")
    for lv, L in data["levels"].items():
        write(f"{L['slug']}/index.html", build_level(site, data, lv))
        pages.append(f"{L['slug']}/")
        write(f"{L['slug']}/flashcards.html", build_flashcards(site, data, lv))
        pages.append(f"{L['slug']}/flashcards.html")
        for i, t in enumerate(L["topics"]):
            write(f"{L['slug']}/{t['id']}.html", build_topic(site, data, lv, i))
            pages.append(f"{L['slug']}/{t['id']}.html")
            if f"{lv}:{t['id']}" in data["theory"]:
                write(f"{L['slug']}/learn/{t['id']}.html", build_theory(site, data, lv, i))
                pages.append(f"{L['slug']}/learn/{t['id']}.html")
                write(f"vi/{L['slug']}/{t['id']}.html", build_theory(site, data, lv, i, lang="vi"))
                pages.append(f"vi/{L['slug']}/{t['id']}.html")

    base = site["site_url"].rstrip("/")
    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{e(base + '/' + p)}</loc><lastmod>{today}</lastmod></url>" for p in pages)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write("sitemap.txt", "".join(base + "/" + p + "\n" for p in pages))
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
