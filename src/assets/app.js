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
  // Mock exams (模擬試験) are addressed as topic "m1", "m2", ... and list fixed question IDs.
  var EXAM_CFG = DATA.exam_cfg || { pass_rate: 0.7 };
  var RESULTS_KEY = "qc-renshu:exams";
  function mockNo(topic) { var m = /^m(\d+)$/.exec(topic || ""); return m ? parseInt(m[1], 10) : 0; }
  function topicName(level, id) {
    var n = mockNo(id);
    if (n) return "模擬試験 第" + n + "回";
    var L = DATA.levels[String(level)];
    if (!L) return "";
    for (var i = 0; i < L.topics.length; i++) if (L.topics[i].id === id) return L.topics[i].name;
    return "";
  }
  var BY_ID = {};
  DATA.questions.forEach(function (q) { BY_ID[q.id] = q; });
  function pool(level, topic) {
    var n = mockNo(topic);
    if (n) {
      var sets = (DATA.exams && DATA.exams[String(level)]) || [];
      return (sets[n - 1] || []).map(function (id) { return BY_ID[id]; }).filter(Boolean);
    }
    return DATA.questions.filter(function (q) {
      return String(q.level) === String(level) && (topic === "all" || q.topic === topic);
    });
  }
  function loadResults() {
    try { return JSON.parse(localStorage.getItem(RESULTS_KEY) || "{}") || {}; } catch (e) { return {}; }
  }
  function saveResult(key, ok, n, passed) {
    var r = loadResults(), prev = r[key];
    r[key] = { last: ok, best: Math.max(ok, prev ? prev.best : 0), n: n, passed: !!(passed || (prev && prev.passed)) };
    try { localStorage.setItem(RESULTS_KEY, JSON.stringify(r)); } catch (e) { /* storage unavailable */ }
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
    var results = loadResults();
    document.querySelectorAll("[data-exam]").forEach(function (node) {
      var r = results[node.getAttribute("data-exam")];
      if (!r) return;
      var pass = r.passed !== undefined ? r.passed : r.best / r.n >= EXAM_CFG.pass_rate;
      node.textContent = "最高 " + r.best + "/" + r.n + (pass ? " ・ 合格ライン到達" : "");
      if (pass) node.classList.add("passed");
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
    var mock = mockNo(p.topic);
    if (mock && p.mode === "practice") p.mode = "exam";
    this.mock = mock;
    qs = shuffle(qs);
    if (p.mode === "exam" && !mock) qs = qs.slice(0, EXAM_SIZE);
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
    this.items = qs.map(function (q) {
      var order = shuffle(q.choices.map(function (_, i) { return i; }));
      return { q: q, order: order, picked: null };
    });
    this.i = 0;
    this.t0 = Date.now();
    var L = DATA.levels[p.level] || {};
    var modeName = { practice: "練習", exam: "ミニ模擬試験", review: "間違えた問題の復習" }[p.mode];
    if (mock && p.mode === "exam") this.title = (L.name || "") + " ・ " + topicName(p.level, p.topic);
    else this.title = (L.name || "") + " ・ " + (p.topic === "all" ? "全分野" : topicName(p.level, p.topic)) + " ・ " + modeName;
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
      : (this.mock ? "この模擬試験はまだ公開されていません。問題が増えると、順に追加されます。" : "この分野の問題はまだありません。");
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
      exam ? el("span", { class: "meta", id: "quiz-clock", text: "経過 " + fmtTime(Date.now() - this.t0) }) : null,
      el("span", { class: "meta", text: topicName(q.level, q.topic) + " ・ " + q.id })
    ]);
    if (exam && !this.timer) {
      var t0 = this.t0;
      this.timer = setInterval(function () {
        var c = document.getElementById("quiz-clock");
        if (c) c.textContent = "経過 " + fmtTime(Date.now() - t0);
      }, 1000);
    }
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
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
    var passPct = Math.round(EXAM_CFG.pass_rate * 100);
    var score = el("div", { class: "score" }, [
      el("span", { class: "big", html: ok + "<small> / " + n + "問</small>" }),
      el("span", { class: "meta", text: "正答率 " + pct + "%" + (p.mode === "exam" ? " ・ 所要時間 " + fmtTime(Date.now() - this.t0) : "") })
    ]);
    // per-domain scores (real exam: 3級 needs each domain >= 50% as well as 70% overall)
    var L0 = DATA.levels[p.level] || {}, domOf = {}, domNames = L0.domains || {};
    (L0.topics || []).forEach(function (t) { domOf[t.id] = t.domain; });
    var dom = {};
    this.items.forEach(function (it) {
      var d = domOf[it.q.topic] || "all";
      dom[d] = dom[d] || { ok: 0, n: 0 };
      dom[d].n++;
      if (it.picked === it.q.answer) dom[d].ok++;
    });
    var dmin = (EXAM_CFG.domain_min || {})[p.level];
    var domFail = [];
    var domRows = Object.keys(domNames).filter(function (d) { return dom[d]; }).map(function (d) {
      var r = dom[d], dp = Math.round(r.ok / r.n * 100);
      if (dmin && r.ok / r.n < dmin) domFail.push(domNames[d]);
      return el("li", null, [el("span", { text: domNames[d] }), el("span", { class: "meta", text: r.ok + " / " + r.n + "（" + dp + "%）" })]);
    });
    var passed = pct >= passPct && domFail.length === 0;
    var verdictText;
    if (passed) verdictText = "合格の目安に届いています。間違えた問題の解説を読んでおきましょう。";
    else if (pct >= passPct) verdictText = "総合は" + passPct + "%以上ですが、" + domFail.join("・") + "が" + Math.round(dmin * 100) + "%未満です。本番では分野ごとの基準もあるので、この分野を復習しましょう。";
    else verdictText = "合格の目安は総合" + passPct + "%以上" + (dmin ? "、かつ各分野" + Math.round(dmin * 100) + "%以上" : "") + "です。間違えた問題を復習して、もう一度挑戦しましょう。";
    var comment = el("div", { class: "explain" }, [
      el("p", { class: "verdict " + (passed ? "ok" : "ng"), text: passed ? "合格ライン到達" : "合格ラインまであと少し" }),
      el("p", { text: verdictText }),
      domRows.length > 1 ? el("ul", { class: "dom-scores" }, domRows) : null
    ]);

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

    if (this.mock && p.mode === "exam") saveResult(p.level + ":" + p.topic, ok, n, passed);
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


  // ---------- home: try one question ----------
  function initSample() {
    var root = document.getElementById("sample-q");
    if (!root || !DATA.questions.length) return;
    function show() {
      var q = DATA.questions[Math.floor(Math.random() * DATA.questions.length)];
      var order = shuffle(q.choices.map(function (_, i) { return i; }));
      var L = DATA.levels[String(q.level)] || {};
      var list = el("ul", { class: "choices" });
      var sheet = el("div", { class: "sheet" }, [
        el("span", { class: "meta", text: (L.name || "") + " ・ " + topicName(q.level, q.topic) }),
        el("p", { class: "qtext", text: q.question }), list
      ]);
      var buttons = [];
      order.forEach(function (orig, pos) {
        var b = el("button", { type: "button", class: "choice" }, [el("span", { class: "k", text: KEYS[pos] }), el("span", { text: q.choices[orig] })]);
        b.addEventListener("click", function () {
          var ok = orig === q.answer;
          record(q.id, ok);
          buttons.forEach(function (x, i) {
            x.disabled = true;
            if (order[i] === q.answer) x.classList.add("correct");
            else if (i === pos) x.classList.add("wrong");
          });
          sheet.appendChild(el("span", { class: "pen", "aria-hidden": "true", text: ok ? "○" : "×" }));
          sheet.appendChild(el("div", { class: "explain" }, [
            el("p", { class: "verdict " + (ok ? "ok" : "ng"), text: ok ? "正解です" : "不正解　正解は「" + KEYS[order.indexOf(q.answer)] + "」" }),
            el("p", { text: q.explanation }), viBlock(q)
          ]));
          sheet.appendChild(el("div", { class: "btn-row" }, [
            el("button", { type: "button", class: "btn", text: "別の問題", onclick: show }),
            el("a", { class: "btn primary", href: "quiz.html#" + q.level + "." + q.topic + ".practice", text: "この分野をもっと解く" })
          ]));
        });
        buttons.push(b);
        list.appendChild(el("li", null, [b]));
      });
      root.replaceChildren(sheet);
    }
    show();
  }

  // ---------- progress page ----------
  function initProgressPage() {
    var root = document.getElementById("progress-root");
    if (!root) return;
    var stats = loadStats(), results = loadResults();
    var blocks = [];
    var anyAnswered = false;
    ["4", "3"].forEach(function (lv) {
      var L = DATA.levels[lv];
      if (!L) return;
      var topics = L.topics.map(function (t) {
        var qs = pool(lv, t.id), done = 0, ok = 0;
        qs.forEach(function (q) { var r = stats[q.id]; if (r) { done++; if (r.last) ok++; } });
        return { t: t, n: qs.length, done: done, ok: ok, rate: done ? ok / done : null };
      });
      var done = topics.reduce(function (a, x) { return a + x.done; }, 0);
      var ok = topics.reduce(function (a, x) { return a + x.ok; }, 0);
      var total = topics.reduce(function (a, x) { return a + x.n; }, 0);
      if (done) anyAnswered = true;
      var sec = el("section", { class: "prog-level", "aria-label": L.name }, [
        el("h2", { text: L.name }),
        el("p", { class: "meta", text: "解いた問題 " + done + " / " + total + "　・　直近の正答率 " + (done ? Math.round(ok / done * 100) + "%" : "—") })
      ]);
      // domains
      var doms = L.domains || {};
      var drows = Object.keys(doms).map(function (d) {
        var ts = topics.filter(function (x) { return x.t.domain === d; });
        var dd = ts.reduce(function (a, x) { return a + x.done; }, 0), dk = ts.reduce(function (a, x) { return a + x.ok; }, 0);
        var pct = dd ? Math.round(dk / dd * 100) : 0;
        return el("li", null, [
          el("span", { text: doms[d] }),
          el("span", { class: "meta", text: dd ? pct + "%（" + dk + "/" + dd + "）" : "未着手" }),
          el("div", { class: "bar" }, [el("i", { style: "width:" + pct + "%" })])
        ]);
      });
      if (drows.length) sec.appendChild(el("ul", { class: "dom-scores prog-doms" }, drows));
      // weak topics: lowest rate with at least 3 answered
      var weak = topics.filter(function (x) { return x.done >= 3; }).sort(function (a, b) { return a.rate - b.rate; }).slice(0, 3)
        .filter(function (x) { return x.rate < 0.8; });
      var untouched = topics.filter(function (x) { return !x.done && x.n; });
      if (weak.length) {
        sec.appendChild(el("h3", { text: "苦手な分野（優先して復習）" }));
        sec.appendChild(el("ul", { class: "topics" }, weak.map(function (x) {
          return el("li", null, [
            el("div", null, [el("span", { class: "t-name", text: x.t.name }), el("p", { class: "t-desc", text: "正答率 " + Math.round(x.rate * 100) + "%（" + x.ok + "/" + x.done + "）" })]),
            el("div", { class: "t-actions" }, [
              el("a", { class: "btn", href: L.slug + "/learn/" + x.t.id + ".html", text: "学ぶ" }),
              el("a", { class: "btn primary", href: "quiz.html#" + lv + "." + x.t.id + ".review", text: "間違いを復習" })
            ])
          ]);
        })));
      }
      if (untouched.length && done) {
        sec.appendChild(el("p", { class: "note", text: "まだ解いていない分野：" + untouched.map(function (x) { return x.t.name; }).join("、") }));
      }
      // mock exams
      var sets = (DATA.exams && DATA.exams[lv]) || [];
      if (sets.length) {
        var cells = sets.map(function (_, i) {
          var r = results[lv + ":m" + (i + 1)];
          return el("a", { class: "exam-card", href: "quiz.html#" + lv + ".m" + (i + 1) + ".exam" }, [
            el("span", { class: "exam-no", text: "第" + (i + 1) + "回" }),
            el("span", { class: "meta exam-score" + (r && r.passed ? " passed" : ""), text: r ? "最高 " + r.best + "/" + r.n + (r.passed ? " ・ 合格ライン" : "") : "未受験" })
          ]);
        });
        sec.appendChild(el("h3", { text: "模擬試験" }));
        sec.appendChild(el("div", { class: "exam-grid" }, cells));
      }
      blocks.push(sec);
    });
    if (!anyAnswered) {
      blocks.unshift(el("div", { class: "empty" }, [
        el("p", { text: "まだ記録がありません。問題を解くと、ここに分野ごとの正答率が表示されます。" }),
        el("div", { class: "btn-row" }, [
          el("a", { class: "btn primary", href: "4kyu/index.html", text: "4級を解く" }),
          el("a", { class: "btn primary", href: "3kyu/index.html", text: "3級を解く" })
        ])
      ]));
    }
    root.replaceChildren.apply(root, blocks);
  }

  // ---------- flashcards ----------
  var CARDS_KEY = "qc-renshu:cards";
  function initFlashcards() {
    var root = document.getElementById("fc-root");
    if (!root) return;
    var all = [];
    try { all = JSON.parse(document.getElementById("fc-data").textContent); } catch (e) { all = []; }
    var known = {};
    try { known = JSON.parse(localStorage.getItem(CARDS_KEY) || "{}") || {}; } catch (e) { known = {}; }
    function saveKnown() { try { localStorage.setItem(CARDS_KEY, JSON.stringify(known)); } catch (e) { /* storage unavailable */ } }
    var sel = document.getElementById("fc-topic"), only = document.getElementById("fc-unknown");
    var card = document.getElementById("fc-card"), front = document.getElementById("fc-front"), back = document.getElementById("fc-back");
    var hint = document.getElementById("fc-hint"), count = document.getElementById("fc-count");
    var deck = [], i = 0;
    function build() {
      deck = shuffle(all.filter(function (c) {
        return (sel.value === "all" || c.k === sel.value) && (!only.checked || !known[c.t]);
      }));
      i = 0;
      draw();
    }
    function draw() {
      var nKnown = all.filter(function (c) { return known[c.t] && (sel.value === "all" || c.k === sel.value); }).length;
      var nAll = all.filter(function (c) { return sel.value === "all" || c.k === sel.value; }).length;
      count.textContent = "覚えた " + nKnown + " / " + nAll + " 語" + (deck.length ? "　・　" + (i + 1) + " 枚目 / " + deck.length : "");
      back.hidden = true; hint.hidden = false;
      if (!deck.length) {
        front.textContent = "このカードはすべて覚えました";
        back.textContent = "";
        hint.textContent = "「まだ覚えていないカードだけ」を外すと、もう一度すべて見られます";
        return;
      }
      var c = deck[i];
      front.textContent = c.t;
      back.replaceChildren(
        el("span", { class: "fc-yomi", text: c.y }),
        el("span", { class: "fc-vi", lang: "vi", text: c.v }),
        el("span", { class: "meta", text: c.n })
      );
      hint.textContent = "タップして裏を見る";
    }
    function flip() { if (deck.length) { back.hidden = !back.hidden; hint.hidden = !back.hidden ? true : false; } }
    function next(isKnown) {
      if (!deck.length) return;
      var c = deck[i];
      if (isKnown) known[c.t] = true; else delete known[c.t];
      saveKnown();
      if (only.checked && isKnown) { deck.splice(i, 1); if (i >= deck.length) i = 0; }
      else { i = (i + 1) % deck.length; }
      draw();
    }
    card.addEventListener("click", flip);
    document.getElementById("fc-known").addEventListener("click", function () { next(true); });
    document.getElementById("fc-again").addEventListener("click", function () { next(false); });
    sel.addEventListener("change", build);
    only.addEventListener("change", build);
    document.addEventListener("keydown", function (e) {
      if (e.target && /input|select|textarea/i.test(e.target.tagName)) return;
      if (e.key === " ") { e.preventDefault(); flip(); }
      else if (e.key === "ArrowRight") next(true);
      else if (e.key === "ArrowLeft") next(false);
    });
    build();
  }

  document.addEventListener("DOMContentLoaded", function () {
    // each feature starts on its own, so a problem in one never blocks the others
    [fillProgress, initQuiz, initReset, initViSwitch, initSample, initProgressPage, initFlashcards].forEach(function (fn) {
      try { fn(); } catch (err) { if (window.console) console.error(err); }
    });
  });
})();
