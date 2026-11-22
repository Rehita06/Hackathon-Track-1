from . import eligibility, i18n, llm, notice
from .retriever import Retriever

SCHEMES = eligibility.load_schemes()
RETR = Retriever(SCHEMES)


def _ctx(s):
    rules = "; ".join(r["en"] for r in s["rules"])
    return (f"SCHEME: {s['name']}\nSummary: {s['summary_en']}\nBenefit: {s['benefit_en']}\n"
            f"Eligibility: {rules}\nDocuments: {', '.join(s['docs'])}\nHow to apply: {s['apply_en']}\nOfficial portal: {s['portal']}")


def _offline_answer(hits, lang):
    L = i18n.labels(lang)
    if not hits:
        return L["nomatch"]
    s = hits[0][0]
    name, summary, benefit = i18n.scheme_text(s, lang)
    who = "; ".join(i18n.rule_label(r, lang) for r in s["rules"])
    docs = ", ".join(i18n.doc_label(d, lang) for d in s["docs"])
    how = s["apply_en"] if lang == "en" else i18n.apply_text(s, lang)
    text = (f"{name}\n{summary}\n\n{L['benefit']}: {benefit}\n{L['who']}: {who}\n"
            f"{L['docs']}: {docs}\n{L['how']}: {how} ({s['portal']})")
    if len(hits) > 1:
        text += "\n\n" + L["related"] + ": " + ", ".join(i18n.scheme_text(h[0], lang)[0] for h in hits[1:])
    return text + "\n\n" + L["check"]


def ask(question, lang="en", profile=None):
    hits = RETR.search(question, k=3)
    sources = [{"id": h[0]["id"], "name": h[0]["name"], "portal": h[0]["portal"]} for h in hits]
    mode = "offline"
    answer = None
    if llm.available() and hits:
        prof = ""
        if profile:
            ev = eligibility.evaluate(profile)
            prof = "\n\nCitizen profile check (deterministic):\n" + "\n".join(
                f"- {r['name']}: {r['status']}" for r in ev["results"] if r["id"] in {h[0]['id'] for h in hits})
        answer = llm.complete("Context:\n" + "\n\n".join(_ctx(h[0]) for h in hits) + prof +
                              f"\n\nQuestion: {question}\n\nAnswer simply with: what it is, who can get it, "
                              "documents, and exact next steps.", lang)
        if answer:
            mode = "ai"
    if not answer:
        answer = _offline_answer(hits, lang)
        if llm.available():
            mode = "fallback"
    return {"answer": answer, "sources": [dict(x, name=i18n.scheme_text(RETR.schemes[x["id"]], lang)[0]) for x in sources], "mode": mode}


def explain_notice(text, lang="en"):
    a = notice.analyse(text)
    mode, out = "offline", None
    if llm.available():
        out = llm.complete("Explain this government notice. Give: 1) what it says in 2 short sentences, "
                           "2) what the person must do, 3) money amounts, 4) deadlines, 5) documents needed, "
                           "6) any rights or penalties. If a section is absent, skip it.\n\nNOTICE:\n" + text[:6000],
                           lang, 1100)
        if out:
            mode = "ai"
    if not out:
        out = notice.format_plain(a)
        if llm.available():
            mode = "fallback"
    return {"explanation": out, "extracted": a, "mode": mode}
