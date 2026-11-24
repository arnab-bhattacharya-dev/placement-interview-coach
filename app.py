import json
import os
import re
import time

import requests
from flask import Flask, jsonify, render_template, request

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

BASE = os.getenv("GEMINI_BASE", "https://generativelanguage.googleapis.com/v1beta")
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_MODEL", "").strip()
PREFERRED = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash-lite",
             "gemini-2.0-flash", "gemini-flash-lite-latest", "gemini-flash-latest"]
TIMEOUT = float(os.getenv("GEMINI_TIMEOUT", "25"))

SYSTEM = (
    "You are a campus-placement interviewer for Indian university students. "
    "Be fair, specific and encouraging. Reply with valid JSON only, no extra text."
)


class LLMError(Exception):
    pass


WORKING = None
_CANDS = None
BAD = {}


def _headers():
    return {"Content-Type": "application/json", "x-goog-api-key": API_KEY}


def candidates() -> list:
    global _CANDS
    if _CANDS is not None:
        return _CANDS
    names = []
    try:
        r = requests.get(f"{BASE}/models?pageSize=200", headers=_headers(), timeout=20)
        r.raise_for_status()
        for m in r.json().get("models", []):
            n = m["name"].split("/", 1)[1]
            if ("generateContent" in m.get("supportedGenerationMethods", []) and "flash" in n
                    and not any(x in n for x in ("image", "tts", "live", "audio", "thinking", "robotics", "computer"))):
                names.append(n)
    except Exception:
        pass
    pref = [n for n in PREFERRED if n in names]
    rest = sorted([n for n in names if n not in pref and "lite" in n], reverse=True) + \
        sorted([n for n in names if n not in pref and "lite" not in n], reverse=True)
    order = ([MODEL] if MODEL else []) + pref + rest
    if not names:
        order = ([MODEL] if MODEL else []) + PREFERRED
    seen, out = set(), []
    for n in order:
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    _CANDS = out[:10]
    return _CANDS


def ask_llm(prompt: str) -> dict:
    global WORKING
    if not API_KEY:
        raise LLMError("GEMINI_API_KEY is missing. Create a .env file (see README) and restart.")

    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }
    models = ([WORKING] if WORKING else []) + [m for m in candidates() if m != WORKING]
    now = time.time()
    models = [m for m in models if BAD.get(m, 0) < now] or models
    last = ""
    for m in models:
        try:
            r = requests.post(f"{BASE}/models/{m}:generateContent", headers=_headers(),
                              json=body, timeout=(10, TIMEOUT))
        except requests.exceptions.SSLError as e:
            raise LLMError("SSL/certificate problem while contacting Gemini. Details: " + str(e)[:180])
        except requests.exceptions.Timeout:
            print(f"[Gemini] {m}: too slow, trying next model")
            BAD[m] = time.time() + 120
            last = "slow"
            continue
        except requests.exceptions.RequestException as e:
            raise LLMError("Cannot reach generativelanguage.googleapis.com. Details: " + str(e)[:180])

        if r.status_code == 404:
            BAD[m] = time.time() + 3600
            last = "notfound"
            continue
        if r.status_code in (429, 500, 503):
            print(f"[Gemini] {m}: busy/limit ({r.status_code}), trying next model")
            BAD[m] = time.time() + 120
            last = "busy"
            continue
        if r.status_code in (400, 401, 403):
            try:
                msg = r.json().get("error", {}).get("message", "")
            except ValueError:
                msg = ""
            if r.status_code in (401, 403) or "API key" in msg:
                raise LLMError("Invalid or missing API key. Check GEMINI_API_KEY in your .env file.")
            last = msg or "bad request"
            continue
        if not r.ok:
            last = f"HTTP {r.status_code}"
            continue
        try:
            data = r.json()
            text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
            result = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        except (KeyError, IndexError, AttributeError, TypeError, ValueError):
            last = "badreply"
            continue
        if WORKING != m:
            print(f"[Gemini] using model: {m}")
        WORKING = m
        return result

    WORKING = None
    if last == "slow":
        raise LLMError("Gemini is responding too slowly on your network. Run: python check_connection.py")
    if last == "busy":
        raise LLMError("The free-tier limit is reached right now. Wait a minute and try again.")
    raise LLMError("No Gemini model answered (" + (last or "unknown") + "). Run: python check_connection.py")


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/question")
def question():
    d = request.get_json(force=True)
    prompt = (
        f"Role: {d.get('role')}. Level: {d.get('level')}.\n"
        "Ask ONE interview question (mix of concepts, scenarios, behavioural).\n"
        f"Do not repeat any of these: {json.dumps(d.get('asked', []))}\n"
        'Return JSON: {"question": "..."}'
    )
    try:
        out = ask_llm(prompt)
        if not out.get("question"):
            raise LLMError("The AI returned no question. Please retry.")
        return jsonify(question=out["question"])
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.post("/api/evaluate")
def evaluate():
    d = request.get_json(force=True)
    answer = (d.get("answer") or "").strip()
    if len(answer) < 15:
        return jsonify(error="Answer is too short."), 400
    prompt = (
        f"Role: {d.get('role')}. Level: {d.get('level')}.\n"
        f"Question: {d.get('question')}\nCandidate answer: {answer}\n\n"
        "Evaluate honestly. Return JSON: "
        '{"score": integer 0-10, "strengths": ["..",".."], '
        '"improvements": ["..",".."], '
        '"model_answer": "ideal answer in 3-5 sentences"}'
    )
    try:
        return jsonify(ask_llm(prompt))
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
