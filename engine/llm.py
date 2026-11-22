"""Optional LLM adapter using FREE-tier APIs (no SDK, standard library only).

Set ONE of these environment variables (checked in this order):
  GEMINI_API_KEY      Google AI Studio free tier  (aistudio.google.com/apikey, no card needed)
  GROQ_API_KEY        Groq free tier              (console.groq.com/keys)
  OPENROUTER_API_KEY  OpenRouter free models      (openrouter.ai/keys, use ':free' models)
Model names change over time, so override them with GEMINI_MODEL / GROQ_MODEL / OPENROUTER_MODEL if needed.
With no key (or on any error / rate limit) the app falls back to deterministic offline mode.
"""
import json
import os
import urllib.request

LANG_NAMES = {"en": "English", "hi": "Hindi", "kn": "Kannada", "ta": "Tamil", "te": "Telugu"}

SYSTEM = (
    "You are Yojana Saathi, a careful assistant that explains Indian government schemes, notices and "
    "citizen rights in very simple language for people with limited literacy. Rules: (1) Use ONLY the "
    "facts in the provided context; never invent amounts, dates or eligibility. (2) If the context does "
    "not contain the answer, say so and tell the person to check the official portal or visit the "
    "nearest Common Service Centre / Gram Panchayat. (3) Use short sentences, no jargon, and give clear "
    "next steps. (4) Reply entirely in the requested language, in plain text without markdown symbols. "
    "(5) Remind the person that final eligibility is decided by the government department."
)


def provider():
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    return None


def available():
    return provider() is not None


def _post(url, headers, body):
    h = {"content-type": "application/json", "user-agent": "yojana-saathi/1.0"}
    h.update(headers)
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=h)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def _openai_style(url, key, model, system, user, max_tokens, extra=None):
    data = _post(url, {"authorization": "Bearer " + key, **(extra or {})},
                 {"model": model, "max_tokens": max_tokens, "temperature": 0.2,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    return data["choices"][0]["message"]["content"].strip()


def complete(user_prompt, lang="en", max_tokens=900):
    p = provider()
    if not p:
        return None
    system = SYSTEM + " Reply language: " + LANG_NAMES.get(lang, "English") + "."
    try:
        if p == "gemini":
            model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            data = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                         {"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                         {"systemInstruction": {"parts": [{"text": system}]},
                          "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                          "generationConfig": {"maxOutputTokens": max(max_tokens, 2048), "temperature": 0.2}})
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(x.get("text", "") for x in parts).strip()
        elif p == "groq":
            text = _openai_style("https://api.groq.com/openai/v1/chat/completions", os.environ["GROQ_API_KEY"],
                                 os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"), system, user_prompt, max_tokens)
        else:
            text = _openai_style("https://openrouter.ai/api/v1/chat/completions", os.environ["OPENROUTER_API_KEY"],
                                 os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
                                 system, user_prompt, max_tokens, {"x-title": "Yojana Saathi"})
        return text or None
    except Exception as e:  # network / quota / bad key / model renamed -> offline fallback
        print("LLM error (" + p + "):", e)
        return None
