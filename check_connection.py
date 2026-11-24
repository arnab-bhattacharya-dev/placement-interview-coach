import time

import requests

import app as A

print("1) API key found in .env:", "YES" if A.API_KEY and A.API_KEY != "paste_your_key_here" else "NO  <-- fix this first")
try:
    r = requests.get(f"{A.BASE}/models", headers=A._headers(), timeout=20)
    print("2) Reached Google. HTTP status:", r.status_code, "(200 = key works)")
    if r.status_code != 200:
        print("  ", r.text[:200])
except requests.exceptions.RequestException as e:
    print("2) Cannot connect:", str(e)[:250])
    raise SystemExit

print("3) Testing models (stops after 2 working models; 429 = no free quota, 503 = Google busy):")
body = {"contents": [{"role": "user", "parts": [{"text": 'Reply with JSON {"ok": true}'}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 50}}
wins = 0
for m in A.candidates():
    if wins >= 2:
        break
    t = time.time()
    try:
        x = requests.post(f"{A.BASE}/models/{m}:generateContent", headers=A._headers(), json=body, timeout=(10, 30))
        wins += 1 if x.ok else 0
        print(f"   {m}: HTTP {x.status_code} in {time.time()-t:.1f}s", "  <-- WORKS" if x.ok else "")
    except requests.exceptions.RequestException as e:
        print(f"   {m}: FAILED after {time.time()-t:.1f}s ({type(e).__name__})")
print("Send a screenshot of this output if the app still fails.")
