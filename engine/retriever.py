"""Tiny dependency-free TF-IDF retriever over scheme facts (multilingual via tags)."""
import math
import re
from collections import Counter

_tok = re.compile(r"[\w\u0900-\u097F\u0C80-\u0CFF\u0B80-\u0BFF\u0C00-\u0C7F]+", re.UNICODE)
STOP = {"the", "a", "an", "is", "are", "of", "for", "to", "and", "or", "in", "on", "i", "me", "my",
        "can", "how", "what", "do", "get", "am", "it", "this", "that", "with", "से", "का", "की", "के",
        "में", "है", "और", "को", "क्या"}


def tokens(text):
    return [t for t in (w.lower() for w in _tok.findall(text or "")) if t not in STOP and len(t) > 1]


class Retriever:
    def __init__(self, schemes):
        self.schemes = {s["id"]: s for s in schemes}
        self.docs = []
        for s in schemes:
            text = " ".join([s["name"], s.get("name_hi", ""), s["category"], s["summary_en"], s["summary_hi"],
                             s["benefit_en"], s["benefit_hi"], s["apply_en"], " ".join(s["docs"]),
                             " ".join(r["en"] for r in s["rules"])])
            toks = tokens(text) + tokens(" ".join(s["tags"])) * 3  # tags weigh more
            self.docs.append((s["id"], Counter(toks)))
        n = len(self.docs)
        df = Counter()
        for _, c in self.docs:
            df.update(c.keys())
        self.idf = {t: math.log((n + 1) / (d + 0.5)) + 1 for t, d in df.items()}

    def _vec(self, counter):
        return {t: (1 + math.log(c)) * self.idf.get(t, 0) for t, c in counter.items() if t in self.idf}

    def search(self, query, k=3, min_score=0.05):
        q = self._vec(Counter(tokens(query)))
        if not q:
            return []
        qn = math.sqrt(sum(v * v for v in q.values()))
        scored = []
        for sid, c in self.docs:
            d = self._vec(c)
            dn = math.sqrt(sum(v * v for v in d.values())) or 1
            dot = sum(q[t] * d.get(t, 0) for t in q)
            scored.append((dot / (qn * dn), sid))
        scored.sort(reverse=True)
        return [(self.schemes[sid], s) for s, sid in scored[:k] if s >= min_score]
