const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
let asked = [], results = [], cur = "";

const ctx = () => ({ role: $("#role").value, level: $("#lvl").value });

async function post(url, body) {
  const r = await fetch(url, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body) });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || "Request failed");
  return j;
}
function busy(b) { document.querySelectorAll("button").forEach(x => x.disabled = b); }

async function nextQ() {
  $("#fb").hidden = true; $("#sum").hidden = true;
  $("#qcard").hidden = false; $("#q").textContent = "Preparing your question…"; $("#ans").value = "";
  busy(true);
  try {
    const r = await post("/api/question", { ...ctx(), asked });
    cur = r.question; asked.push(cur);
    $("#q").textContent = cur;
    $("#qmeta").textContent = `Question ${asked.length} · ${$("#role").value}`;
  } catch (e) { $("#q").innerHTML = '<span class="err">Could not get a question: ' + esc(e.message) + '</span>'; }
  busy(false);
}

$("#start").onclick = () => { asked = []; results = []; $("#setup").hidden = true; nextQ(); };
$("#skip").onclick = nextQ;

$("#sub").onclick = async () => {
  const a = $("#ans").value.trim();
  if (a.length < 15) { alert("Write a slightly longer answer first."); return; }
  busy(true); $("#sub").textContent = "Evaluating…";
  try {
    const r = await post("/api/evaluate", { ...ctx(), question: cur, answer: a });
    const sc = Math.max(0, Math.min(10, +r.score || 0));
    results.push({ q: cur, score: sc });
    $("#fb").hidden = false;
    $("#fb").innerHTML = `<div class="score">${sc}/10</div><div class="bar"><i style="width:${sc*10}%"></i></div>
      <div class="good">What went well</div><ul>${(r.strengths||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
      <div class="warn">How to improve</div><ul>${(r.improvements||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
      <b>Model answer</b><p>${esc(r.model_answer)}</p>
      <div class="row"><button class="p" id="nx">Next question</button></div>`;
    $("#nx").onclick = nextQ;
    $("#fb").scrollIntoView({ behavior: "smooth" });
  } catch (e) { $("#fb").hidden = false; $("#fb").innerHTML = '<span class="err">Evaluation failed: ' + esc(e.message) + '</span>'; }
  $("#sub").textContent = "Submit answer"; busy(false);
};

$("#end").onclick = () => {
  $("#qcard").hidden = true; $("#fb").hidden = true; $("#sum").hidden = false;
  if (!results.length) {
    $("#sum").innerHTML = '<p>No answers submitted yet.</p><div class="row"><button class="p" id="again">Start again</button></div>';
  } else {
    const avg = (results.reduce((s, r) => s + r.score, 0) / results.length).toFixed(1);
    $("#sum").innerHTML = `<h3 style="margin-top:0">Session summary</h3><div class="score">${avg}/10</div>
      <div class="mut">Average over ${results.length} answer(s)</div>
      <ul>${results.map(r=>`<li>${r.score}/10 – ${esc(r.q)}</li>`).join("")}</ul>
      <div class="row"><button class="p" id="again">Start again</button></div>`;
  }
  $("#again").onclick = () => { $("#sum").hidden = true; $("#setup").hidden = false; };
};
