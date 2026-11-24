import csv
import os
import statistics as st
import sys
import time

import app as A

REPEATS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
PAUSE = float(os.getenv("EVAL_PAUSE", "5"))

DATA = [
    ("Software Developer", "What is the difference between a process and a thread?", [
        ("good", "A process is an independent program in execution with its own memory space, while a thread is a lightweight unit of execution inside a process that shares the process's memory and resources. Threads are cheaper to create and switch between, but need synchronization such as locks to avoid race conditions. Processes are isolated, so one crashing does not affect others."),
        ("average", "A process is a running program and a thread is part of a process. Threads share memory."),
        ("poor", "They are both same thing, just different names used in operating system."),
    ]),
    ("Cloud / DevOps Engineer", "What is the difference between IaaS, PaaS and SaaS?", [
        ("good", "IaaS gives virtual machines, storage and networking and the user manages the OS and apps, for example AWS EC2. PaaS also manages the OS and runtime so developers only deploy code, for example Google App Engine. SaaS delivers a complete application to the user over the internet, for example Gmail. The customer's responsibility decreases from IaaS to SaaS."),
        ("average", "IaaS is infrastructure like servers, PaaS is a platform for developers and SaaS is software like Gmail."),
        ("poor", "Cloud is on the internet and they are all types of cloud, I do not remember exactly."),
    ]),
    ("HR / Behavioural round", "Tell me about a time you faced a challenge in a team project and how you handled it.", [
        ("good", "In a group project our model accuracy was low and a teammate and I disagreed about the approach. I suggested we test both ideas on a small sample, compared the results and picked the better one. I also made a shared task list so everyone knew their part. We finished on time and I learned to resolve disagreements with data and clear communication."),
        ("average", "We had a problem in our project and we solved it by working together and finishing on time."),
        ("poor", "I never faced any challenge, everything was easy."),
    ]),
]

client = A.app.test_client()
rows = []
total = sum(len(a) for _, _, a in DATA) * REPEATS
n = 0
for role, question, answers in DATA:
    for tier, answer in answers:
        for rep in range(1, REPEATS + 1):
            n += 1
            t = time.time()
            r = client.post("/api/evaluate", json={"role": role, "level": "Fresher", "question": question, "answer": answer})
            dt = time.time() - t
            j = r.get_json() or {}
            ok = (r.status_code == 200 and isinstance(j.get("score"), (int, float)) and 0 <= j["score"] <= 10
                  and isinstance(j.get("strengths"), list) and isinstance(j.get("improvements"), list)
                  and bool(j.get("model_answer")))
            rows.append(dict(role=role, tier=tier, rep=rep, score=j.get("score") if ok else "", valid=int(ok),
                             seconds=round(dt, 2), error="" if ok else (j.get("error") or "invalid reply")[:80]))
            print(f"[{n}/{total}] {role[:18]:18} {tier:8} rep{rep}: "
                  f"{'score ' + str(j.get('score')) if ok else 'FAILED ' + rows[-1]['error']} ({dt:.1f}s)")
            time.sleep(PAUSE)

with open("evaluation_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

good = [r for r in rows if r["valid"]]
tiers = {t: [r["score"] for r in good if r["tier"] == t] for t in ("good", "average", "poor")}
sds, order_ok = [], 0
for role, _, answers in DATA:
    means = {}
    for tier, _ in answers:
        s = [r["score"] for r in good if r["role"] == role and r["tier"] == tier]
        if len(s) > 1:
            sds.append(st.pstdev(s))
        means[tier] = st.mean(s) if s else None
    if all(v is not None for v in means.values()) and means["good"] > means["average"] > means["poor"]:
        order_ok += 1

print("\n================ RESULTS FOR THE PAPER ================")
print(f"Total evaluation calls              : {len(rows)}")
print(f"Valid structured replies            : {len(good)}/{len(rows)} = {100*len(good)/len(rows):.1f}%")
print(f"Mean response time (s)              : {st.mean(r['seconds'] for r in rows):.1f}")
for t in ("good", "average", "poor"):
    if tiers[t]:
        print(f"Mean score, {t:8} answers        : {st.mean(tiers[t]):.2f} / 10")
print(f"Mean score spread (SD) on repeats   : {st.mean(sds):.2f}" if sds else "Score spread: not enough repeats")
print(f"Questions with correct ordering     : {order_ok}/{len(DATA)}  (good > average > poor)")
print("Model used                          :", getattr(A, "WORKING", None))
print("Saved: evaluation_results.csv")
