/* QC検定れんしゅう帳 — quiz engine and progress tracking.
   Data: window.QC_DATA (questions.js), settings: window.QC_CONFIG (config.js).
   Progress is stored only in this browser (localStorage). */
(function () {
  "use strict";
  var DATA = window.QC_DATA || { levels: {}, questions: [] };
  var CONFIG = window.QC_CONFIG || {};
  var KEYS = ["ア", "イ", "ウ", "エ", "オ"];
  var STORE_KEY = "qc-renshu:v1";
  var VI_KEY = "qc-renshu:vi";
  var EXAM_SIZE = 20;

  // ---------- Vietnamese explanation toggle ----------
  function viPref() {
    try { return localStorage.getItem(VI_KEY) === "1"; } catch (e) { return false; }
  }
  function setViPref(on) {
    try { localStorage.setItem(VI_KEY, on ? "1" : "0"); } catch (e) { /* storage unavailable */ }
  }
  // One switch for the whole site: remembered choice, page class (theory pages), quiz blocks.
  function setVi(on) {
    setViPref(on);
    var root = document.documentElement;
    root.classList.toggle("vi-on", on);
    root.classList.toggle("vi-off", !on);
    document.querySelectorAll(".vi-wrap").forEach(function (w) { if (w._set) w._set(on); });
    syncSwitch();
  }
  function syncSwitch() {
    var sw = document.getElementById("vi-switch");
    if (!sw) return;
    var on = document.documentElement.classList.contains("vi-on");
    sw.setAttribute("aria-pressed", String(on));
    var label = sw.querySelector(".vi-switch-text");
    if (label) label.textContent = on ? "Ẩn bản tiếng Việt" : "Hiện bản tiếng Việt";
  }
  function initViSwitch() {
    var sw = document.getElementById("vi-switch");
    if (!sw) return;
    syncSwitch();
    sw.addEventListener("click", function () { setVi(!document.documentElement.classList.contains("vi-on")); });
  }
  function viBlock(q) {
    if (!q.explanation_vi) return null;
    var open = viPref();
    var body = el("div", { class: "vi", lang: "vi" }, [
      el("span", { class: "vi-label", text: "Giải thích tiếng Việt" }),
      el("p", { text: q.explanation_vi })
    ]);
    body.hidden = !open;
    var btn = el("button", { type: "button", class: "vi-toggle", lang: "vi", "aria-expanded": String(open) });
    function label(on) {
      btn.replaceChildren(el("span", { class: "vi-badge", text: "VI" }),
        document.createTextNode(on ? "Ẩn giải thích tiếng Việt" : "Xem giải thích bằng tiếng Việt"));
    }
    label(open);
    btn.addEventListener("click", function () { setVi(body.hidden); });
    var wrap = el("div", { class: "vi-wrap" }, [btn, body]);
    wrap._set = function (on) { body.hidden = !on; btn.setAttribute("aria-expanded", String(on)); label(on); };
    return wrap;
  }

  // ---------- storage ----------
  function loadStats() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY) || "{}") || {}; }
    catch (e) { return {}; }
  }
  function saveStats(s) {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(s)); } catch (e) { /* storage unavailable */ }
  }
  function record(id, ok) {
    var s = loadStats();
    var r = s[id] || { c: 0, w: 0 };
    if (ok) r.c++; else r.w++;
    r.last = ok;
    s[id] = r;
    saveStats(s);
  }

  // ---------- helpers ----------
  function $(sel, root) { return (root || document).querySelector(sel); }
  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "text") n.textContent = attrs[k];
      else if (k === "html") n.innerHTML = attrs[k];
      else if (k === "class") n.className = attrs[k];
      else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), attrs[k]);
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { if (c) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function topicName(level, id) {
    var L = DATA.levels[String(level)];
    if (!L) return "";
    for (var i = 0; i < L.topics.length; i++) if (L.topics[i].id === id) return L.topics[i].name;
    return "";
  }
  function pool(level, topic) {
    return DATA.questions.filter(function (q) {
      return String(q.level) === String(level) && (topic === "all" || q.topic === topic);
    });
  }
  function feedbackLink(id) {
    var url = CONFIG.feedback_form_url;
    if (!url) return null;
    return el("a", {
      class: "fb", target: "_blank", rel: "noopener",
      href: url.split("{id}").join(encodeURIComponent(id)),
      text: "この問題について意見を送る（問題ID: " + id + "）"
    });
  }
  function fmtTime(ms) {
    var s = Math.round(ms / 1000), m = Math.floor(s / 60);
    return m + "分" + String(s % 60).padStart(2, "0") + "秒";
  }

  // ---------- progress bars on level/topic pages ----------
  function fillProgress() {
    var stats = loadStats();
    document.querySelectorAll("[data-progress]").forEach(function (node) {
      var parts = node.getAttribute("data-progress").split(":");
      var qs = pool(parts[0], parts[1] || "all");
      var done = 0, ok = 0;
      qs.forEach(function (q) { var r = stats[q.id]; if (r) { done++; if (r.last) ok++; } });
      var label = node.querySelector(".meta");
      var bar = node.querySelector(".bar > i");
      if (label) label.textContent = qs.length + "問 ・ 解いた " + done + " ・ 直近正解 " + ok;
      if (bar) bar.style.width = (qs.length ? Math.round(ok / qs.length * 100) : 0) + "%";
    });
    document.querySelectorAll("[data-review-count]").forEach(function (node) {
      var parts = node.getAttribute("data-review-count").split(":");
      var n = pool(parts[0], parts[1] || "all").filter(function (q) { return stats[q.id] && stats[q.id].last === false; }).length;
      node.textContent = String(n);
      var btn = node.closest("a, button");
      if (btn && n === 0) btn.classList.add("ghost");
    });
  }

  // ---------- quiz ----------
  function parseHash() {
    var h = (location.hash || "").replace(/^#/, "");
    var p = h.split(".");
    var level = p[0] === "3" ? "3" : (p[0] === "4" ? "4" : null);
    var topic = p[1] || "all";
    var mode = ["practice", "exam", "review"].indexOf(p[2]) >= 0 ? p[2] : "practice";
    if (!level) {
      var qs = new URLSearchParams(location.search);
      level = qs.get("level") === "3" ? "3" : "4";
      topic = qs.get("topic") || topic;
      mode = qs.get("mode") || mode;
    }
    return { level: level, topic: topic, mode: mode };
  }

  function Quiz(root) {
    this.root = root;
    this.start();
  }
  Quiz.prototype.start = function () {
    var p = parseHash();
    this.p = p;
    var qs = pool(p.level, p.topic);
    var stats = loadStats();
    if (p.mode === "review") qs = qs.filter(function (q) { return stats[q.id] && stats[q.id].last === false; });
    qs = shuffle(qs);
    if (p.mode === "exam") qs = qs.slice(0, EXAM_SIZE);
    this.items = qs.map(function (q) {
      var order = shuffle(q.choices.map(function (_, i) { return i; }));
      return { q: q, order: order, picked: null };
    });
    this.i = 0;
    this.t0 = Date.now();
    var L = DATA.levels[p.level] || {};
    var modeName = { practice: "練習", exam: "ミニ模擬試験", review: "間違えた問題の復習" }[p.mode];
    this.title = (L.name || "") + " ・ " + (p.topic === "all" ? "全分野" : topicName(p.level, p.topic)) + " ・ " + modeName;
    document.title = this.title + " | " + (CONFIG.site_name || "QC検定");
    var h = $("#quiz-title"); if (h) h.textContent = this.title;
    var back = $("#quiz-back"); if (back && L.slug) back.setAttribute("href", L.slug + "/index.html");
    if (!this.items.length) return this.renderEmpty();
    this.render();
  };
  Quiz.prototype.renderEmpty = function () {
    var p = this.p, L = DATA.levels[p.level] || {};
    var msg = p.mode === "review"
      ? "復習する問題はありません。間違えた問題は、ここに自動で集まります。"
      : "この分野の問題はまだありません。";
    this.root.replaceChildren(el("div", { class: "empty" }, [
      el("p", { text: msg }),
      el("div", { class: "btn-row" }, [
        el("a", { class: "btn primary", href: "quiz.html#" + p.level + "." + p.topic + ".practice", text: "練習をはじめる" }),
        el("a", { class: "btn", href: (L.slug || "4kyu") + "/index.html", text: "分野一覧へ" })
      ])
    ]));
  };
  Quiz.prototype.render = function () {
    var self = this, item = this.items[this.i], q = item.q, exam = this.p.mode === "exam";
    var answered = !exam && item.picked !== null;
    var n = this.items.length;

    var top = el("div", { class: "quiz-top" }, [
      el("span", { class: "meta", text: "第" + (this.i + 1) + "問 / " + n + "問" }),
      el("span", { class: "meta", text: topicName(q.level, q.topic) + " ・ " + q.id })
    ]);
    var prog = el("div", { class: "progress", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": String(n), "aria-valuenow": String(this.i + (answered ? 1 : 0)) },
      [el("i", { style: "width:" + Math.round((this.i + (answered || (exam && item.picked !== null) ? 1 : 0)) / n * 100) + "%" })]);

    var list = el("ul", { class: "choices" });
    item.order.forEach(function (orig, pos) {
      var cls = "choice";
      if (answered) {
        if (orig === q.answer) cls += " correct";
        else if (orig === item.picked) cls += " wrong";
      } else if (exam && item.picked === orig) cls += " picked";
      var b = el("button", { type: "button", class: cls, "data-pos": String(pos) }, [
        el("span", { class: "k", text: KEYS[pos] }), el("span", { text: q.choices[orig] })
      ]);
      if (answered) b.disabled = true;
      b.addEventListener("click", function () { self.pick(orig); });
      list.appendChild(el("li", null, [b]));
    });

    var sheet = el("div", { class: "sheet" }, [el("p", { class: "qtext", text: q.question }), list]);

    if (answered) {
      var ok = item.picked === q.answer;
      sheet.appendChild(el("span", { class: "pen", "aria-hidden": "true", text: ok ? "○" : "×" }));
      var correctPos = item.order.indexOf(q.answer);
      var exp = el("div", { class: "explain" }, [
        el("p", { class: "verdict " + (ok ? "ok" : "ng"), text: ok ? "正解です" : "不正解　正解は「" + KEYS[correctPos] + "」" }),
        el("p", { text: q.explanation }),
        viBlock(q),
        feedbackLink(q.id)
      ]);
      sheet.appendChild(exp);
    }

    var isLast = this.i === n - 1;
    var foot = el("div", { class: "quiz-foot" });
    var left = el("div", { class: "btn-row" });
    if (exam && this.i > 0) left.appendChild(el("button", { type: "button", class: "btn ghost", text: "前の問題", onclick: function () { self.i--; self.render(); } }));
    left.appendChild(el("span", { class: "kbd-hint", text: "キー操作：1〜4 で選択、Enter で次へ" }));
    var nextBtn = el("button", {
      type: "button", class: "btn primary", id: "next-btn",
      text: isLast ? (exam ? "採点する" : "結果を見る") : "次の問題",
      onclick: function () { self.next(); }
    });
    if ((exam && item.picked === null) || (!exam && !answered)) nextBtn.disabled = true;
    foot.appendChild(left);
    foot.appendChild(nextBtn);

    this.root.replaceChildren(top, prog, sheet, foot);
    if (answered) nextBtn.focus({ preventScroll: true });
  };
  Quiz.prototype.pick = function (orig) {
    var item = this.items[this.i];
    if (this.p.mode === "exam") { item.picked = orig; this.render(); return; }
    if (item.picked !== null) return;
    item.picked = orig;
    record(item.q.id, orig === item.q.answer);
    this.render();
  };
  Quiz.prototype.next = function () {
    var item = this.items[this.i];
    if (item.picked === null) return;
    if (this.i < this.items.length - 1) { this.i++; this.render(); window.scrollTo({ top: 0 }); return; }
    if (this.p.mode === "exam") this.items.forEach(function (it) { record(it.q.id, it.picked === it.q.answer); });
    this.renderResult();
  };
  Quiz.prototype.renderResult = function () {
    var p = this.p, L = DATA.levels[p.level] || {};
    var n = this.items.length, ok = this.items.filter(function (it) { return it.picked === it.q.answer; }).length;
    var pct = Math.round(ok / n * 100);
    var score = el("div", { class: "score" }, [
      el("span", { class: "big", html: ok + "<small> / " + n + "問</small>" }),
      el("span", { class: "meta", text: "正答率 " + pct + "%" + (p.mode === "exam" ? " ・ 所要時間 " + fmtTime(Date.now() - this.t0) : "") })
    ]);
    var comment = el("p", { class: "note", text: pct >= 70
      ? "合格の目安（正答率70%以上）に届いています。間違えた問題の解説を読んでおきましょう。"
      : "合格の目安は正答率70%以上です。間違えた問題を復習して、もう一度挑戦しましょう。" });

    var list = el("ul", { class: "result-list" });
    this.items.forEach(function (it, idx) {
      var good = it.picked === it.q.answer;
      list.appendChild(el("li", null, [
        el("span", { class: "m" + (good ? "" : " miss"), text: good ? "○" : "×" }),
        el("details", null, [
          el("summary", { text: "第" + (idx + 1) + "問　" + it.q.question }),
          el("div", { class: "detail" }, [
            el("span", { text: "あなたの答え：" + it.q.choices[it.picked] }),
            el("span", { text: "正解：" + it.q.choices[it.q.answer] }),
            el("span", { text: it.q.explanation }),
            viBlock(it.q),
            feedbackLink(it.q.id)
          ])
        ])
      ]));
    });

    var hasMiss = ok < n, self = this;
    var reviewHash = "#" + p.level + "." + p.topic + ".review";
    var actions = el("div", { class: "btn-row" }, [
      hasMiss ? el("button", { type: "button", class: "btn primary", text: "間違えた問題を復習", onclick: function () {
        if (location.hash === reviewHash) self.start(); else location.hash = reviewHash;
      } }) : null,
      el("button", { type: "button", class: "btn" + (hasMiss ? "" : " primary"), text: "もう一度", onclick: this.start.bind(this) }),
      el("a", { class: "btn ghost", href: (L.slug || "4kyu") + "/index.html", text: "分野一覧へ" })
    ]);
    this.root.replaceChildren(el("h2", { text: "結果" }), score, comment, actions, list);
    window.scrollTo({ top: 0 });
  };

  function initQuiz() {
    var root = document.getElementById("quiz");
    if (!root) return;
    var quiz = new Quiz(root);
    window.addEventListener("hashchange", function () { quiz.start(); });
    document.addEventListener("keydown", function (e) {
      if (e.target && /input|textarea|select/i.test(e.target.tagName)) return;
      var k = parseInt(e.key, 10);
      if (k >= 1 && k <= 5) {
        var b = root.querySelector('.choice[data-pos="' + (k - 1) + '"]');
        if (b && !b.disabled) { b.click(); e.preventDefault(); }
      } else if (e.key === "Enter" || e.key === "ArrowRight") {
        var nb = document.getElementById("next-btn");
        if (nb && !nb.disabled && document.activeElement !== nb) { nb.click(); e.preventDefault(); }
      }
    });
  }

  function initReset() {
    var btn = document.getElementById("reset-progress");
    if (!btn) return;
    var confirmBox = document.getElementById("reset-confirm");
    btn.addEventListener("click", function () { confirmBox.hidden = false; });
    document.getElementById("reset-yes").addEventListener("click", function () {
      saveStats({}); confirmBox.hidden = true; fillProgress();
      btn.textContent = "記録を消去しました";
    });
    document.getElementById("reset-no").addEventListener("click", function () { confirmBox.hidden = true; });
  }

  document.addEventListener("DOMContentLoaded", function () {
    fillProgress();
    initQuiz();
    initReset();
    initViSwitch();
  });
})();
