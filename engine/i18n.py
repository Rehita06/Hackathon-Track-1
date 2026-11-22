"""Localisation helpers: scheme text, rule labels and document names in en/hi/kn/ta/te."""
import json
import os

with open(os.path.join(os.path.dirname(__file__), "..", "data", "translations.json"), encoding="utf-8") as f:
    T = json.load(f)


def labels(lang):
    return T["labels"].get(lang, T["labels"]["en"])


def scheme_text(s, lang):
    if lang == "hi":
        return s.get("name_hi", s["name"]), s["summary_hi"], s["benefit_hi"]
    tr = T["schemes"].get(s["id"], {}).get(lang)
    if tr:
        return tr["name"], tr["summary"], tr["benefit"]
    return s["name"], s["summary_en"], s["benefit_en"]


def rule_label(rule, lang):
    if lang == "hi" and rule.get("hi"):
        return rule["hi"]
    return T["rules"].get(rule["en"], {}).get(lang, rule["en"])


def doc_label(doc, lang):
    return T["docs"].get(doc, {}).get(lang, doc)


def apply_text(s, lang):
    return T["apply"].get(lang, s["apply_en"])
