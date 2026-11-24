# 🎯 Placement Interview Coach (GenAI Project)

A web app that uses a Large Language Model (Google Gemini) to run mock placement interviews.
The AI asks role-specific questions, scores your answers out of 10, gives feedback, and shows a model answer.

**Free to use:** runs on the Google Gemini API **free tier** (no credit card needed).

**Developed by:** Arnab – MCA, School of Computer Applications, Dayananda Sagar University

## Problem & societal value
Many students do not have access to mock interviews or coaching. This app gives free, repeatable interview practice.

## GenAI concepts used
- Role prompting (AI acts as a placement interviewer)
- Structured JSON output (`responseMimeType: application/json`) parsed into the UI
- Context management (previous questions passed back to avoid repeats)
- LLM-as-a-judge evaluation and feedback
- Robust API handling: automatic model fallback, short timeouts, temporary exclusion of failing models

## Tech stack
Python, Flask, Google Gemini API (REST), HTML/CSS/JavaScript

## How to run (VS Code or Antigravity)
1. Get a **free API key** (no card): https://aistudio.google.com/apikey -> *Create API key*.
2. Open this folder in VS Code / Antigravity. In the terminal:
   ```
   python -m venv venv
   venv\Scripts\activate
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to a new file named `.env` and paste your key:
   ```
   GEMINI_API_KEY=your_key_here
   ```
4. Start the app:
   ```
   python app.py
   ```
5. Open http://127.0.0.1:5000 in your browser.

In VS Code you can also press **F5** (a launch config is included).

## Troubleshooting
- Run `python check_connection.py` first. It shows your key status and which Gemini models work.
- "API key missing / invalid": check `.env` is next to `app.py`, has no quotes or spaces, then restart.
- "Free-tier limit reached": wait a minute and retry (free tier has per-minute/day limits).
- "Gemini too slow / cannot reach": try a mobile hotspot (college Wi-Fi may block it), turn off VPN/proxy.
- Model names change often; the app picks a working Flash model automatically.

## Measuring quality (for the research paper)
`python evaluate_system.py` sends 9 author-written answers (good/average/poor) 3 times each and prints
validity, mean scores, score spread and response time. Results are saved to `evaluation_results.csv`.

## Project structure
```
app.py                Flask server + Gemini API calls
templates/index.html  Page layout and footer
static/style.css      Styling
static/app.js         Interview flow (frontend logic)
requirements.txt      Dependencies
.env.example          API key template (copy to .env)
check_connection.py   Diagnoses connection / API key / model problems
evaluate_system.py    Measures feedback quality and consistency
```

## Privacy note
On Google's free tier, prompts may be used to improve Google products. Do not enter confidential information.

## Limitations
- Requires internet and a free API key; free tier has rate limits.
- AI scores are a practice aid, not a real evaluation.
- No data is stored; each session starts fresh.
