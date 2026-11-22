# Submission answers (copy into Challazo form)

**Project name:** Yojana Saathi - Multilingual Scheme, Rights & Notice Explainer

**Problem statement:** Rural and low-literacy citizens, senior citizens, students from SC/ST/OBC families, women and
small farmers in India are entitled to dozens of welfare schemes but miss them because notices are in legal English,
information is spread over many portals, and nobody tells them which scheme fits their situation. It matters because
unclaimed benefits (health cover, pension, scholarships, housing) directly affect poverty, health and education outcomes.

**Solution description:** Yojana Saathi is a web app in English, Hindi, Kannada, Tamil and Telugu. The citizen answers a
short profile form, and a transparent rule engine returns schemes they qualify for with a pass/fail/unknown reason per
condition, benefits, documents and how to apply. They can also ask questions by voice or text: retrieval finds the
relevant scheme and a free-tier LLM (Google Gemini) explains it in simple language grounded only in retrieved facts. A notice explainer
turns pasted government circulars into what-to-do, amounts, deadlines, documents and rights. Eligibility is computed by
code, the AI only explains, so answers are auditable. A deterministic offline mode keeps the app working without AI.

**AI usage:** Gemini LLM for grounded multilingual explanation and notice simplification; TF-IDF retrieval for scheme search;
browser speech recognition and synthesis for voice.

**Demo video script (2 min):** 1) Pick Hindi, fill profile (woman, village, BPL, no LPG) -> show Ujjwala/MGNREGA/Ayushman
results and the reason checklist. 2) Switch to Kannada, ask by mic "farmer help" -> spoken answer. 3) Paste the sample
notice -> show deadline and amounts extraction. 4) Show tests passing and the architecture diagram.

**Credits:** Python stdlib, vanilla JS, Web Speech API, Google Gemini API free tier (optional).
