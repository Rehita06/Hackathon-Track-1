"""Rule-based, explainable eligibility engine.

Each scheme lists rules. A rule evaluates to True / False / None (unknown, because the
citizen did not answer). Status is derived deterministically, so the AI never decides
eligibility - it only explains it.
"""
import json
import os

from . import i18n

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "schemes.json")
BOOL_FIELDS = ["owns_land", "bpl", "bank_account", "it_payer", "govt_employee",
               "has_lpg", "pucca_house", "girl_child_under10", "student"]


def load_schemes():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def _to_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("yes", "true", "y", "1"):
            return True
        if s in ("no", "false", "n", "0"):
            return False
    return None


def _to_num(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def normalize_profile(raw):
    p = {}
    raw = raw or {}
    p["age"] = _to_num(raw.get("age"))
    p["income"] = _to_num(raw.get("income"))
    for k in ("gender", "area", "category", "occupation"):
        v = raw.get(k)
        p[k] = v.strip() if isinstance(v, str) and v.strip() else None
    for k in BOOL_FIELDS:
        p[k] = _to_bool(raw.get(k))
    if p["student"] is None and p["occupation"] == "student":
        p["student"] = True
    if p["owns_land"] is None and p["occupation"] == "farmer":
        p["owns_land"] = None  # farmers may be tenants; keep unknown
    return p


def _atom(rule, p):
    val = p.get(rule["f"])
    if val is None:
        return None
    op, v = rule["op"], rule.get("v")
    if op == "true":
        return val is True
    if op == "false":
        return val is False
    if op == "eq":
        return val == v
    if op == "in":
        return val in v
    if op == "gte":
        return val >= v
    if op == "lte":
        return val <= v
    raise ValueError("unknown op " + op)


def eval_rule(rule, p):
    if "any" in rule:
        res = [_atom(r, p) for r in rule["any"]]
        if any(r is True for r in res):
            return True
        if all(r is False for r in res):
            return False
        return None
    return _atom(rule, p)


def _rule_fields(rule):
    if "any" in rule:
        return [r["f"] for r in rule["any"]]
    return [rule["f"]]


def check(scheme, p, lang="en"):
    checks, missing = [], []
    for r in scheme["rules"]:
        res = eval_rule(r, p)
        checks.append({"label": i18n.rule_label(r, lang), "result": res})
        if res is None:
            for f in _rule_fields(r):
                if f not in missing:
                    missing.append(f)
    results = [c["result"] for c in checks]
    if any(r is False for r in results):
        status = "not_eligible"
    elif all(r is True for r in results):
        status = "eligible"
    else:
        status = "maybe"
    passed = sum(1 for r in results if r is True)
    name, summary, benefit = i18n.scheme_text(scheme, lang)
    return {
        "id": scheme["id"], "name": name, "summary": summary, "benefit": benefit,
        "category": scheme["category"], "docs": [i18n.doc_label(d, lang) for d in scheme["docs"]],
        "apply": scheme["apply_en"] if lang == "en" else i18n.apply_text(scheme, lang),
        "portal": scheme["portal"], "status": status, "checks": checks, "missing": missing,
        "score": passed / max(1, len(results)),
    }


def evaluate(raw_profile, schemes=None, lang="en"):
    schemes = schemes or load_schemes()
    p = normalize_profile(raw_profile)
    out = [check(s, p, lang) for s in schemes]
    order = {"eligible": 0, "maybe": 1, "not_eligible": 2}
    out.sort(key=lambda x: (order[x["status"]], -x["score"], x["id"]))
    return {"profile": p, "results": out,
            "counts": {k: sum(1 for x in out if x["status"] == k) for k in order}}
