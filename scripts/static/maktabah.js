/* Ponomar Library of Liturgical Texts — interface behaviour (no dependencies). */
(function () {
  "use strict";
  var D = document, html = D.documentElement;
  var LIB = window.MAKTABAH || { books: [], i18n: { en: {}, ru: {} }, categories: [] };
  var ROOT = html.getAttribute("data-root") || "";
  var PAGE = html.getAttribute("data-page");
  var $ = function (s, el) { return (el || D).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || D).querySelectorAll(s)); };

  /* ── preferences ─────────────────────────────────────────────────────── */
  var KEY = "maktabah";
  var prefs = {};
  try { prefs = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { prefs = {}; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (e) { /* private mode */ } }
  var DEFAULT_SIZE = window.matchMedia("(max-width: 520px)").matches ? 20 : 22;

  /* ── language ────────────────────────────────────────────────────────── */
  function lang() { return html.getAttribute("data-ui") === "ru" ? "ru" : "en"; }
  function tr(key, vars) {
    var s = (LIB.i18n[lang()] || {})[key] || (LIB.i18n.en || {})[key] || key;
    if (vars) Object.keys(vars).forEach(function (k) { s = s.replace("{" + k + "}", vars[k]); });
    return s;
  }
  function pick(obj) { return obj ? (obj[lang()] || obj.en || "") : ""; }
  function setLang(l) {
    html.setAttribute("data-ui", l);
    html.lang = l;
    prefs.lang = l; save();
    applyLang();
  }
  function applyLang() {
    $$("[data-set-lang]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-set-lang") === lang())); });
    $$("[data-i18n-title]").forEach(function (el) { var s = tr(el.getAttribute("data-i18n-title")); el.title = s; el.setAttribute("aria-label", s); });
    $$("[data-i18n-placeholder]").forEach(function (el) { el.placeholder = tr(el.getAttribute("data-i18n-placeholder")); });
    $$("[data-i18n-aria]").forEach(function (el) { el.setAttribute("aria-label", tr(el.getAttribute("data-i18n-aria"))); });
    $$("a.pg[data-l]").forEach(function (a) { a.setAttribute("aria-label", tr("page_n", { l: a.getAttribute("data-l") })); });
    $$("span.pg[data-l]").forEach(function (a) { a.setAttribute("aria-label", tr("page_plain", { l: a.getAttribute("data-l") })); a.setAttribute("role", "note"); });
    if (PAGE === "library") D.title = pick({ en: LIB.site.title_en, ru: LIB.site.title_ru });
    if (PAGE === "chapter") buildLibraryNav();
    if (PAGE === "scan") scanHeader();
  }
  D.addEventListener("click", function (e) {
    var b = e.target.closest("[data-set-lang]");
    if (b) setLang(b.getAttribute("data-set-lang"));
  });

  function toast(msg) {
    var t = $(".toast"); if (!t) return;
    t.textContent = msg; t.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { t.hidden = true; }, 3200);
  }

  function bookById(id) { for (var i = 0; i < LIB.books.length; i++) if (LIB.books[i].id === id) return LIB.books[i]; return null; }

  /* ── library page: filter ────────────────────────────────────────────── */
  function initLibrary() {
    var input = $("#book-filter"); if (!input) return;
    var books = $$(".book"), shelves = $$(".shelf"), none = $(".no-match");
    function norm(s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ҃-҉꙯-ꙿⷠ-ⷿ]/g, "").replace(/ё/g, "е"); }
    books.forEach(function (b) { b._s = norm(b.getAttribute("data-search") || ""); });
    function run() {
      var q = norm(input.value.trim()), any = false;
      books.forEach(function (b) { var ok = !q || b._s.indexOf(q) >= 0; b.hidden = !ok; if (ok) any = true; });
      shelves.forEach(function (s) { s.hidden = !$$(".book:not([hidden])", s).length; });
      none.hidden = any;
    }
    input.addEventListener("input", run);
    $("[data-clear-filter]").addEventListener("click", function () { input.value = ""; run(); input.focus(); });
    D.addEventListener("keydown", function (e) {
      if (e.key === "/" && D.activeElement !== input) { e.preventDefault(); input.focus(); }
    });
  }

  /* ── reader ──────────────────────────────────────────────────────────── */
  var openEl = null, opener = null;
  function openPanel(id, btn) {
    closePanel();
    var el = D.getElementById(id); if (!el) return;
    el.hidden = false; openEl = el; opener = btn;
    if (btn) btn.setAttribute("aria-expanded", "true");
    if (id === "drawer") { $(".scrim").hidden = false; var cur = $(".nav-chapters .current", el); if (cur) cur.scrollIntoView({ block: "center" }); }
    var f = $("[aria-selected=true], input:checked, button, a", el); if (f) f.focus({ preventScroll: true });
  }
  function closePanel() {
    if (!openEl) return;
    openEl.hidden = true;
    if (openEl.id === "drawer") $(".scrim").hidden = true;
    if (opener) { opener.setAttribute("aria-expanded", "false"); opener.focus({ preventScroll: true }); }
    openEl = opener = null;
  }

  function applyPrefs() {
    var size = prefs.size || DEFAULT_SIZE;
    html.style.setProperty("--cu-size", size + "px");
    var out = $("#size-out"); if (out) out.textContent = size;
    if (prefs.face && (LIB.typefaces || []).indexOf(prefs.face) >= 0) html.style.setProperty("--cu-face", '"' + prefs.face + '"'); else html.style.removeProperty("--cu-face");
    if (prefs.theme && prefs.theme !== "light") html.setAttribute("data-theme", prefs.theme); else html.removeAttribute("data-theme");
    html.setAttribute("data-pages", prefs.pages || "margin");
    $$("input[name=face]").forEach(function (i) { i.checked = i.value === (prefs.face || (LIB.typefaces || ["Triodion"])[0]); });
    $$("input[name=theme]").forEach(function (i) { i.checked = i.value === (prefs.theme || "light"); });
    $$("input[name=pages]").forEach(function (i) { i.checked = i.value === (prefs.pages || "margin"); });
  }

  function buildLibraryNav() {
    var box = $(".nav-library"); if (!box) return;
    var cur = box.getAttribute("data-current"), out = [];
    LIB.categories.forEach(function (c) {
      var items = LIB.books.filter(function (b) { return b.cat === c.id && b.first; });
      if (!items.length) return;
      out.push("<h3>" + esc(pick(c)) + "</h3><ul>");
      items.forEach(function (b) {
        var yr = (b.edition.ru.match(/\d{4}\s*$/) || [""])[0];
        out.push('<li><a href="' + ROOT + b.id + '/index.html"' + (b.id === cur ? ' aria-current="true"' : "") + "><span>" + esc(pick(b.title)) + '</span><span class="yr">' + yr + "</span></a></li>");
      });
      out.push("</ul>");
    });
    box.innerHTML = out.join("");
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* copy the whole section as formatted text (inline styles survive pasting into Word) */
  function copySection() {
    var src = $(".text .body"); if (!src) return;
    var title = $(".chapter-title");
    var clone = src.cloneNode(true);
    $$(".pg, .footnote-backref", clone).forEach(function (n) { n.remove(); });
    var face = getComputedStyle(src).fontFamily, red = getComputedStyle(html).getPropertyValue("--kinovar").trim() || "#cc0803";
    $$(".red, .verse", clone).forEach(function (n) { n.style.color = red; });
    $$(".wide", clone).forEach(function (n) { n.style.letterSpacing = "0.1em"; });
    $$(".bukvitsa", clone).forEach(function (n) { n.style.color = red; n.style.fontFamily = '"Indiction", "Indiction Unicode"'; n.style.fontSize = "200%"; n.style.lineHeight = "1"; });
    $$("h1,h2,h3,h4", clone).forEach(function (n) { n.style.color = red; n.style.textAlign = "center"; n.style.fontWeight = "normal"; });
    $$("a", clone).forEach(function (a) { var s = D.createElement("span"); s.innerHTML = a.innerHTML; s.style.cssText = a.style.cssText; a.replaceWith(s); });
    var head = title ? '<p style="text-align:center;color:' + red + '">' + esc(title.textContent) + "</p>" : "";
    var htmlText = '<div style="font-family:' + face.replace(/"/g, "'") + ';font-size:14pt">' + head + clone.innerHTML + "</div>";
    var plain = (title ? title.textContent + "\n\n" : "") + $$("p, h1, h2, h3, h4, li", clone).map(function (p) {
      return p.textContent.replace(/\s+/g, " ").trim();
    }).filter(Boolean).join("\n\n");
    function fallback() {
      var ok = false, box = D.createElement("div");
      box.contentEditable = "true"; box.innerHTML = htmlText; box.style.cssText = "position:fixed;left:-9999px;top:0";
      D.body.appendChild(box);
      var r = D.createRange(); r.selectNodeContents(box); var sel = getSelection(); sel.removeAllRanges(); sel.addRange(r);
      try { ok = D.execCommand("copy"); } catch (e) { ok = false; }
      sel.removeAllRanges(); box.remove();
      toast(tr(ok ? "copied" : "copy_failed"));
    }
    if (navigator.clipboard && window.ClipboardItem) {
      navigator.clipboard.write([new ClipboardItem({
        "text/html": new Blob([htmlText], { type: "text/html" }),
        "text/plain": new Blob([plain], { type: "text/plain" })
      })]).then(function () { toast(tr("copied")); }, fallback);
    } else fallback();
  }

  /* footnote popovers */
  var pop = null;
  function closePop() { if (pop) { pop.remove(); pop = null; } }
  function showNote(ref) {
    closePop();
    var id = decodeURIComponent(ref.getAttribute("href").slice(1));
    var li = D.getElementById(id); if (!li) return false;
    pop = D.createElement("div"); pop.className = "note-pop cu"; pop.setAttribute("role", "note");
    pop.innerHTML = li.innerHTML;
    D.body.appendChild(pop);
    var r = ref.getBoundingClientRect(), w = pop.offsetWidth;
    var left = Math.max(8, Math.min(window.scrollX + r.left - w / 2, window.scrollX + D.documentElement.clientWidth - w - 8));
    pop.style.left = left + "px"; pop.style.top = (window.scrollY + r.bottom + 6) + "px";
    return true;
  }

  /* page links: on wide screens the scan opens beside the text */
  var panelBook = null, panelUrl = null, activePg = null;
  function wide() { return window.matchMedia("(min-width: 1100px)").matches; }
  function scanTarget(href) {
    var u = new URL(href, location.href), q = u.searchParams;
    var b = bookById(q.get("b")); if (!b || !b.pdf.length) return null;
    var v = Math.min(parseInt(q.get("v") || "0", 10) || 0, b.pdf.length - 1), vol = b.pdf[v];
    var idx = q.get("i") ? parseInt(q.get("i"), 10) : (parseInt(q.get("p"), 10) || 1) + (vol.offset || 0);
    return { book: b, vol: vol, v: v, index: Math.max(1, idx), label: q.get("l") || q.get("p") || String(idx) };
  }
  function viewerSrc(pdfUrl, index) {
    var file = new URL(ROOT + pdfUrl, location.href).pathname;
    return ROOT + LIB.pdfjs + "?file=" + encodeURIComponent(file) + "#page=" + index + "&zoom=page-fit&pagemode=none";
  }
  function openScanPanel(a) {
    var t = scanTarget(a.href); if (!t) return false;
    var panel = $("#scan-panel"), frame = $(".scan-frame", panel);
    panel.hidden = false; html.classList.add("scan-open");
    $(".scan-panel-page", panel).textContent = t.label;
    $(".scan-full", panel).href = a.href;
    if (activePg) activePg.classList.remove("is-active");
    activePg = a; a.classList.add("is-active");
    var app = null;
    try { app = frame.contentWindow.PDFViewerApplication; } catch (e) { app = null; }
    if (panelUrl === t.vol.url && app && app.pdfDocument) { app.page = t.index; }
    else { panelUrl = t.vol.url; frame.src = viewerSrc(t.vol.url, t.index); }
    return true;
  }
  function closeScanPanel() {
    var panel = $("#scan-panel"); if (!panel) return;
    panel.hidden = true; html.classList.remove("scan-open");
    if (activePg) { activePg.classList.remove("is-active"); activePg.focus({ preventScroll: true }); }
  }

  /* #page=123 (from the scan viewer): scroll to that page, or the closest one before it */
  function gotoPageFromHash() {
    var m = location.hash.match(/^#page=(\d+)/); if (!m) return;
    var n = parseInt(m[1], 10), best = null;
    $$(".pg[data-p]").forEach(function (p) { var k = parseInt(p.getAttribute("data-p"), 10); if (k <= n && (!best || k >= parseInt(best.getAttribute("data-p"), 10))) best = p; });
    if (!best) best = $(".pg[data-p]");
    if (best) { best.scrollIntoView({ block: "start" }); best.classList.add("flash"); }
  }

  function initReader() {
    applyPrefs();
    D.addEventListener("click", function (e) {
      var t = e.target;
      var op = t.closest("[data-open]");
      if (op) { var id = op.getAttribute("data-open"); if (openEl && openEl.id === id) closePanel(); else openPanel(id, op); return; }
      if (t.closest("[data-close]") || t.closest(".scrim")) { closePanel(); return; }
      if (t.closest("[data-close-scan]")) { closeScanPanel(); return; }
      var act = t.closest("[data-action]");
      if (act) { var a = act.getAttribute("data-action"); if (a === "copy") copySection(); if (a === "print") window.print(); return; }
      var sz = t.closest("[data-size]");
      if (sz) { prefs.size = Math.max(14, Math.min(44, (prefs.size || DEFAULT_SIZE) + 2 * parseInt(sz.getAttribute("data-size"), 10))); save(); applyPrefs(); return; }
      var tab = t.closest("[role=tab]");
      if (tab) { $$("[role=tab]").forEach(function (x) { var on = x === tab; x.setAttribute("aria-selected", String(on)); D.getElementById(x.getAttribute("aria-controls")).hidden = !on; }); return; }
      var fn = t.closest(".footnote-ref");
      if (fn) { if (showNote(fn)) e.preventDefault(); return; }
      if (pop && !t.closest(".note-pop")) closePop();
      var pg = t.closest("a.pg");
      if (pg && !e.metaKey && !e.ctrlKey && !e.shiftKey && wide()) { if (openScanPanel(pg)) e.preventDefault(); return; }
      if (openEl && openEl.id === "settings" && !t.closest("#settings")) closePanel();
      if (openEl && openEl.id === "drawer" && t.closest("#drawer a[href^='#']")) closePanel();
    });
    D.addEventListener("change", function (e) {
      var n = e.target.name;
      if (n === "face" || n === "theme" || n === "pages") { prefs[n] = e.target.value; save(); applyPrefs(); }
    });
    D.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { if (pop) closePop(); else if (openEl) closePanel(); else closeScanPanel(); return; }
      if (e.altKey || e.ctrlKey || e.metaKey || /INPUT|SELECT|TEXTAREA/.test((D.activeElement || {}).tagName || "") || openEl) return;
      if (e.key === "ArrowLeft") { var p = $("link[rel=prev]"); if (p) location.href = p.href; }
      if (e.key === "ArrowRight") { var n = $("link[rel=next]"); if (n) location.href = n.href; }
    });
    window.addEventListener("hashchange", gotoPageFromHash);
    gotoPageFromHash();
  }

  /* ── pdf.js: viewer options, set from the embedding page ─────────────── */
  D.addEventListener("webviewerloaded", function (e) {
    try {
      var opts = e.detail.source.PDFViewerApplicationOptions;
      opts.set("disablePreferences", true);   // always open where the link points
      opts.set("disableAutoFetch", true);     // with a linearized PDF, load only the pages being viewed
      opts.set("disableHistory", true);
      opts.set("sidebarViewOnLoad", 0);
      opts.set("annotationEditorMode", -1);   // a reader, not an editor: hide the drawing tools
      opts.set("localeProperties", { lang: lang() === "ru" ? "ru" : "en-US" });
    } catch (err) { /* older or newer pdf.js: defaults are fine */ }
  });

  /* ── scan viewer page ────────────────────────────────────────────────── */
  var scanState = null;
  function scanHeader() {
    if (!scanState) return;
    var s = scanState, b = s.book;
    var nameEl = $(".scan-book");
    nameEl.textContent = pick(b.title) + (b.pdf.length > 1 ? " — " + pick(s.vol.label) : "") + " · " + tr("page_plain", { l: s.label });
    D.title = tr("scan_of") + ": " + pick(b.title);
    var sel = $(".vol-select select");
    if (b.pdf.length > 1) {
      $(".vol-select").hidden = false;
      sel.innerHTML = b.pdf.map(function (v, i) { return '<option value="' + i + '"' + (i === s.v ? " selected" : "") + ">" + esc(pick(v.label)) + "</option>"; }).join("");
    }
  }
  function initScan() {
    var q = new URLSearchParams(location.search);
    var t = scanTarget(location.href), frame = $(".scan-main .scan-frame");
    var b = bookById(q.get("b"));
    var bookHref = b ? ROOT + b.id + "/index.html" : ROOT + "index.html";
    $(".scan-back").href = bookHref; $(".scan-book").href = bookHref;
    if (!t) { frame.hidden = true; $(".scan-missing").hidden = false; $(".scan-download").hidden = true; if (b) $(".scan-book").textContent = pick(b.title); return; }
    scanState = t;
    frame.src = viewerSrc(t.vol.url, t.index);
    $(".scan-download").href = ROOT + t.vol.url;
    // link back to the text: the section whose pages include this one
    var page = q.get("p") ? parseInt(q.get("p"), 10) : t.index - (t.vol.offset || 0);
    function textHref(p) {
      var hit = null;
      (b.ranges || []).forEach(function (r) { if ((r[3] || 0) === t.v && r[1] <= p && p <= r[2] && !hit) hit = r; });
      return hit ? ROOT + b.id + "/" + hit[0] + "#page=" + p : null;
    }
    var th = textHref(page);
    if (th) { $(".scan-back").href = th; var tt = $(".scan-totext"); tt.href = th; tt.hidden = false; }
    // keep the "show in text" link in step with the page the reader turns to
    frame.addEventListener("load", function () {
      try {
        var app = frame.contentWindow.PDFViewerApplication;
        app.initializedPromise.then(function () {
          app.eventBus.on("pagechanging", function (ev) {
            var p = ev.pageNumber - (t.vol.offset || 0), h = textHref(p), tt = $(".scan-totext");
            if (h) { tt.href = h; tt.hidden = false; $(".scan-back").href = h; } else { tt.hidden = true; }
          });
        });
      } catch (e) { /* cross-origin viewer: no sync */ }
    });
    $(".vol-select select").addEventListener("change", function (e) {
      var u = new URL(location.href); u.searchParams.set("v", e.target.value); u.searchParams.set("i", "1"); u.searchParams.delete("p"); u.searchParams.delete("l");
      location.href = u.href;
    });
    scanHeader();
  }

  /* ── start ───────────────────────────────────────────────────────────── */
  if (PAGE === "library") initLibrary();
  if (PAGE === "chapter") initReader();
  if (PAGE === "scan") initScan();
  applyLang();
})();
