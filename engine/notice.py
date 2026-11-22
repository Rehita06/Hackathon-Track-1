"""Offline notice analyser: pulls out money, dates, deadlines and documents from a government
notice, so the tool still works when no LLM key is configured."""
import re

MONEY = re.compile(r"(?:₹|Rs\.?|INR|रु\.?|रुपये)\s?[\d,]+(?:\.\d+)?(?:\s?(?:lakh|lakhs|crore|crores|लाख|करोड़))?|[\d,]+(?:\.\d+)?\s?(?:lakh|lakhs|crore|crores|लाख|करोड़)", re.I)
DATE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4}\b", re.I)
DEADLINE_WORDS = ("last date", "deadline", "on or before", "not later than", "before", "within", "अंतिम तिथि", "तक")
DOC_WORDS = ("aadhaar", "aadhar", "pan", "certificate", "passbook", "ration card", "income proof", "photograph", "आधार", "प्रमाण पत्र")
ACTION_WORDS = ("apply", "submit", "register", "visit", "upload", "pay", "attend", "furnish", "enrol", "enroll", "आवेदन", "जमा")
RIGHTS_WORDS = ("entitled", "eligible", "benefit", "right", "penalty", "fine", "prohibited", "must", "shall", "पात्र", "दंड")


def split_sentences(text):
    parts = re.split(r"(?<=[.!?।])\s+|\n+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _uniq(xs):
    seen, out = set(), []
    for x in xs:
        k = x.strip().lower()
        if k not in seen:
            seen.add(k)
            out.append(x.strip())
    return out


def analyse(text):
    sents = split_sentences(text)
    amounts = _uniq(m.group(0) for m in MONEY.finditer(text))
    dates = _uniq(m.group(0) for m in DATE.finditer(text))
    deadlines = [s for s in sents if any(w in s.lower() for w in DEADLINE_WORDS) and (DATE.search(s) or "days" in s.lower() or "दिन" in s)]
    docs = [d for d in DOC_WORDS if d in text.lower()]
    actions = [s for s in sents if any(w in s.lower() for w in ACTION_WORDS)][:4]
    rights = [s for s in sents if any(w in s.lower() for w in RIGHTS_WORDS)][:3]
    summary = sents[:2] if sents else []
    return {"summary": summary, "amounts": amounts[:8], "dates": dates[:8], "deadlines": deadlines[:3],
            "documents": docs, "actions": actions, "rights": rights, "sentences": len(sents)}


def format_plain(a):
    lines = []
    if a["summary"]:
        lines.append("In short: " + " ".join(a["summary"]))
    if a["actions"]:
        lines.append("What you need to do:\n- " + "\n- ".join(a["actions"]))
    if a["amounts"]:
        lines.append("Amounts mentioned: " + ", ".join(a["amounts"]))
    if a["dates"] or a["deadlines"]:
        lines.append("Dates and deadlines: " + ", ".join(a["dates"]) + ("\n- " + "\n- ".join(a["deadlines"]) if a["deadlines"] else ""))
    if a["documents"]:
        lines.append("Documents to keep ready: " + ", ".join(a["documents"]))
    if a["rights"]:
        lines.append("Your rights / rules to note:\n- " + "\n- ".join(a["rights"]))
    if not lines:
        lines.append("I could not find clear details in this text. Please paste the full notice.")
    return "\n\n".join(lines)
