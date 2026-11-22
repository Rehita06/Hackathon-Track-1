# Yojana Saathi - Multilingual Policy, Rights & Scheme Explainer
IDEA//FORGE Online Hackathon | Track 1: Civic Pulse, Digital Governance & Public Information | Problem 1

Citizens often miss welfare benefits because schemes are written in legal English, scattered across portals, and
hard to check against their own situation. Yojana Saathi lets a person say who they are (or ask by voice) and
returns the schemes they qualify for, why, which documents to carry, and how to apply, in simple language.

## Features
1. **Scheme eligibility check** - transparent rule engine (13 central schemes). Every result shows which conditions
   passed (check), failed (cross) or are unknown (question mark). Eligibility is decided by code, never by the AI.
2. **Ask by text or voice** - retrieval (TF-IDF with multilingual tags) finds the right scheme; the LLM explains it
   grounded only in retrieved facts. Voice input uses the browser Web Speech API (Chrome recommended).
3. **Notice explainer** - paste a government notice; get what to do, amounts, deadlines, documents and rights.
4. **Languages** - the whole app (form, results, answers) follows the language picked at the top: English, Hindi, Kannada, Tamil, Telugu. Scheme text is built in for all five, so it works offline; an AI key adds richer free-text answers.
5. **Works offline of any AI key** - deterministic fallback (built-in scheme text in 5 languages, regex notice analyser), so the
   demo never breaks.

## Run (no installation needed, Python 3.8+)
```bash
python3 server.py            # http://localhost:8000
# optional, enables multilingual AI answers:
export GEMINI_API_KEY=your_free_key   # or GROQ_API_KEY / OPENROUTER_API_KEY (all have free tiers)
python3 -m unittest discover -s tests -v
```

## Deploy for the MVP link (pick one, all free tiers)
- **Render / Railway / Fly**: connect the repo, start command `python3 server.py` (it reads `$PORT`). Add `GEMINI_API_KEY` as a secret.
- **Docker**: `docker build -t yojana . && docker run -p 8000:8000 -e GEMINI_API_KEY=... yojana`
Then open the link in an incognito window before submitting.

## Architecture
```
Browser (static/ HTML+JS, Web Speech API)
   |  JSON
server.py (stdlib HTTP) -> engine/eligibility.py  rules -> true / false / unknown
                        -> engine/retriever.py    TF-IDF over scheme facts
                        -> engine/notice.py       offline notice analyser
                        -> engine/llm.py          Gemini / Groq / OpenRouter free tiers (optional)
data/schemes.json  <- single source of truth: rules, benefits, documents, official portals
```
Responsible AI: the LLM sees only retrieved scheme text, is told never to invent amounts or dates, and every answer
links the official portal and carries a "final decision rests with the department" notice. No personal data is stored
(profile lives in the browser session only).

## Extending
Add a scheme by appending an entry to `data/schemes.json` (rules use ops: true, false, eq, in, gte, lte, any).
State schemes, more languages and an OCR step for photographed notices are the natural next steps.

## Credits / disclosure
Built with Python standard library, vanilla JS and the browser Web Speech API. Optional generation by a free-tier LLM API
(Google Gemini by default; Groq or OpenRouter also supported). Override model names with GEMINI_MODEL / GROQ_MODEL / OPENROUTER_MODEL. Scheme data compiled from official portals; amounts and limits change, so always verify on the linked site.
