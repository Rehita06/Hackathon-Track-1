"use strict";
const LANGS = [["en", "EN"], ["hi", "हिं"], ["kn", "ಕನ್ನ"], ["ta", "தமி"], ["te", "తెలు"]];
const SPEECH = {en: "en-IN", hi: "hi-IN", kn: "kn-IN", ta: "ta-IN", te: "te-IN"};
const GROUPS = [
  {title: "sec_about", fields: [
    {k: "age", type: "number"},
    {k: "gender", type: "select", o: [["female", "o_female"], ["male", "o_male"], ["other", "o_other"]]},
    {k: "area", type: "select", o: [["rural", "o_rural"], ["urban", "o_urban"]]},
    {k: "occupation", type: "select", o: [["farmer", "o_farmer"], ["student", "o_student"], ["self_employed", "o_self_employed"], ["salaried", "o_salaried"], ["unemployed", "o_unemployed"], ["homemaker", "o_homemaker"], ["other", "o_other_occ"]]},
    {k: "category", type: "select", raw: true, o: [["General", "General"], ["OBC", "OBC"], ["SC", "SC"], ["ST", "ST"]]}]},
  {title: "sec_home", fields: [
    {k: "income", type: "number"}, {k: "bpl", type: "bool"}, {k: "owns_land", type: "bool"},
    {k: "has_lpg", type: "bool"}, {k: "girl_child_under10", type: "bool"}, {k: "student", type: "bool"}]},
  {title: "sec_status", fields: [
    {k: "bank_account", type: "bool"}, {k: "it_payer", type: "bool"}, {k: "govt_employee", type: "bool"}, {k: "pucca_house", type: "bool"}]}
];
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
let lang = localStorage.getItem("ys_lang") || "en";
if (!I18N[lang]) lang = "en";
const t = k => (I18N[lang] && I18N[lang][k]) || I18N.en[k] || k;
let profile = {}, lastResults = null, filter = "eligible", aiOn = false;

/* ---------- form ---------- */
function buildForm() {
  $("#profileForm").innerHTML = GROUPS.map(g => `<fieldset><legend>${t(g.title)}</legend><div class="grid">` + g.fields.map(f => {
    const v = profile[f.k] ?? "";
    if (f.type === "number") return `<label class="fld"><span>${t(f.k)}</span><input data-k="${f.k}" type="number" inputmode="numeric" min="0" value="${esc(v)}"></label>`;
    if (f.type === "select") {
      const opts = f.o.map(([val, l]) => `<option value="${val}" ${v === val ? "selected" : ""}>${esc(f.raw ? l : t(l))}</option>`).join("");
      return `<label class="fld"><span>${t(f.k)}</span><select data-k="${f.k}"><option value="">${t("select")}</option>${opts}</select></label>`;
    }
    const seg = [["yes", t("yes")], ["no", t("no")], ["", t("unsure")]].map(([val, l]) =>
      `<label><input type="radio" name="${f.k}" data-k="${f.k}" value="${val}" ${v === val ? "checked" : ""}>${esc(l)}</label>`).join("");
    return `<fieldset class="fld"><legend>${t(f.k)}</legend><div class="seg">${seg}</div></fieldset>`;
  }).join("") + `</div></fieldset>`).join("");
}
$("#profileForm").addEventListener("input", e => { const k = e.target.dataset.k; if (k) profile[k] = e.target.value; });
$("#profileForm").addEventListener("change", e => { const k = e.target.dataset.k; if (k) profile[k] = e.target.value; });

/* ---------- api ---------- */
async function api(path, body) {
  const r = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}

/* ---------- results ---------- */
function renderResults() {
  const data = lastResults; if (!data) { $("#stats").innerHTML = ""; $("#results").innerHTML = ""; return; }
  const c = data.counts;
  $("#stats").innerHTML = ["eligible", "maybe", "not_eligible"].map(s =>
    `<button class="stat ${s}" data-f="${s}" aria-pressed="${filter === s}"><b>${c[s]}</b><span>${t(s)}</span></button>`).join("");
  $("#stats").querySelectorAll(".stat").forEach(b => b.onclick = () => { filter = b.dataset.f; renderResults(); });
  const list = data.results.filter(r => r.status === filter);
  $("#results").innerHTML = list.length ? list.map(r => {
    const total = r.checks.length, met = r.checks.filter(x => x.result === true).length;
    const dots = r.checks.map(x => `<span class="dot ${x.result === true ? "t" : x.result === false ? "f" : "u"}"></span>`).join("");
    const rows = r.checks.map(x => `<li class="${x.result === true ? "t" : x.result === false ? "f" : "u"}"><b>${x.result === true ? "✓" : x.result === false ? "✗" : "?"}</b><span style="color:var(--ink)">${esc(x.label)}</span></li>`).join("");
    return `<article class="card ${r.status}"><div class="bar"></div><div class="body">
      <span class="cat">${esc((CATS[lang] && CATS[lang][r.category]) || r.category)}</span><h3>${esc(r.name)}</h3>
      <p class="benefit">${esc(r.benefit)}</p>
      <div class="meter"><div class="dots">${dots}</div><span>${t("met").replace("{n}", met).replace("{t}", total)}</span></div>
      <details ${r.status === "maybe" ? "open" : ""}><summary>${t("checks")}</summary><ul class="checks">${rows}</ul></details>
      <details><summary>${t("docs")} · ${t("apply")}</summary><p><strong>${t("docs")}:</strong> ${esc(r.docs.join(", "))}</p><p><strong>${t("apply")}:</strong> ${esc(r.apply)}</p></details>
      <div class="foot"><a class="link" href="${esc(r.portal)}" target="_blank" rel="noopener">${t("portal")}</a></div></div></article>`;
  }).join("") : `<p class="hint">${t("nothing")}</p>`;
}
async function findSchemes(scroll) {
  $("#stats").innerHTML = `<p class="hint">${t("loading")}</p>`;
  try {
    lastResults = await api("/api/eligibility", {profile, lang});
    if (scroll) filter = lastResults.counts.eligible ? "eligible" : lastResults.counts.maybe ? "maybe" : "not_eligible";
    renderResults();
    if (scroll) $("#stats").scrollIntoView({behavior: "smooth", block: "start"});
  } catch (e) { $("#stats").innerHTML = `<p class="hint">${esc(e.message)}</p>`; }
}

/* ---------- ask ---------- */
async function ask(text) {
  const q = (text || $("#q").value).trim(); if (!q) return;
  $("#q").value = "";
  const chat = $("#chat");
  chat.insertAdjacentHTML("afterbegin", `<div class="msg a" id="pending"><span class="typing"><span></span><span></span><span></span></span></div><div class="msg u">${esc(q)}</div>`);
  const box = $("#pending"); box.removeAttribute("id");
  try {
    const a = await api("/api/ask", {question: q, lang, profile});
    const src = a.sources.length ? `<div class="src">${a.sources.map(s => `<a href="${esc(s.portal)}" target="_blank" rel="noopener">${esc(s.name)}</a>`).join("")}</div>` : "";
    box.innerHTML = esc(a.answer) + src + (a.mode === "fallback" ? `<div class="note">${t("fallback")}</div>` : "");
  } catch (e) { box.textContent = e.message; }
}
function mic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { alert(t("mic_na")); return; }
  const rec = new SR(), btn = $("#micBtn"); rec.lang = SPEECH[lang]; btn.classList.add("live");
  rec.onresult = e => ask(e.results[0][0].transcript);
  rec.onend = rec.onerror = () => btn.classList.remove("live");
  rec.start();
}

/* ---------- explain ---------- */
async function explain() {
  const text = $("#notice").value.trim(), out = $("#explainOut");
  out.innerHTML = `<div class="panelbox"><span class="typing"><span></span><span></span><span></span></span></div>`;
  try {
    const r = await api("/api/explain", {text, lang}), x = r.extracted || {};
    const chips = (title, arr, cls) => arr && arr.length ? `<h4>${t(title)}</h4><div class="chipset">${arr.map(v => `<span class="chip ${cls}">${esc(v)}</span>`).join("")}</div>` : "";
    out.innerHTML = `<div class="panelbox">${chips("k_amounts", x.amounts, "")}${chips("k_dates", x.dates, "c")}${chips("k_docs", x.documents, "d")}<div class="txt">${esc(r.explanation)}</div>${r.mode === "fallback" ? `<div class="note">${t("fallback")}</div>` : ""}</div>`;
  } catch (e) { out.innerHTML = `<div class="panelbox">${esc(e.message)}</div>`; }
}

/* ---------- shell ---------- */
function applyLang() {
  document.documentElement.lang = lang;
  $("#langs").innerHTML = LANGS.map(([c, l]) => `<button type="button" data-l="${c}" aria-pressed="${c === lang}">${l}</button>`).join("");
  $("#langs").querySelectorAll("button").forEach(b => b.onclick = () => { lang = b.dataset.l; localStorage.setItem("ys_lang", lang); applyLang(); if (lastResults) findSchemes(false); });
  $("#tagline").textContent = t("tagline"); $("#sub").textContent = t("sub");
  ["find", "ask", "explain"].forEach(x => $("#tab_" + x).textContent = t("tab_" + x));
  $("#findBtn").textContent = t("find"); $("#resetBtn").textContent = t("reset");
  $("#askBtn").textContent = t("ask_btn"); $("#explainBtn").textContent = t("explain_btn"); $("#sampleBtn").textContent = t("sample");
  $("#q").placeholder = t("ask_ph"); $("#askHint").textContent = t("ask_hint"); $("#notice").placeholder = t("explain_ph");
  $("#disclaimer").textContent = t("disclaimer"); $("#modeBadge").textContent = aiOn ? t("ai_on") : t("ai_off");
  $("#chips").innerHTML = t("chips").map(c => `<button type="button">${esc(c)}</button>`).join("");
  $("#chips").querySelectorAll("button").forEach(b => b.onclick = () => ask(b.textContent));
  buildForm(); renderResults();
}
document.querySelectorAll(".tabs button").forEach(b => b.onclick = () => {
  document.querySelectorAll(".tabs button").forEach(x => x.setAttribute("aria-selected", x === b));
  ["find", "ask", "explain"].forEach(n => $("#panel-" + n).hidden = n !== b.dataset.tab);
});
$("#findBtn").onclick = () => findSchemes(true);
$("#resetBtn").onclick = () => { profile = {}; lastResults = null; buildForm(); renderResults(); };
$("#askBtn").onclick = () => ask(); $("#micBtn").onclick = mic;
$("#q").onkeydown = e => { if (e.key === "Enter") ask(); };
$("#explainBtn").onclick = explain; $("#sampleBtn").onclick = () => { $("#notice").value = SAMPLE; };
applyLang();
fetch("/api/health").then(r => r.json()).then(h => { aiOn = h.ai; applyLang(); }).catch(() => {});
