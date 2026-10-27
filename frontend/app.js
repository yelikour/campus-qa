/* ============ 智问校园 CampusMind 前端逻辑 ============ */
const API = location.origin.startsWith("http") ? "" : "http://127.0.0.1:8000";
const USER_TOKEN = localStorage.getItem("uid") || ("u-" + Math.random().toString(36).slice(2, 10));
localStorage.setItem("uid", USER_TOKEN);

let conversationId = null;
let streaming = false;
let curPage = 1;

/* ---------------- 视图切换 ---------------- */
function switchView(v) {
  ["chat", "kb", "dash"].forEach((x) => {
    document.getElementById("view-" + x).classList.toggle("hidden", x !== v);
    document.querySelector(`.view-tab[data-view="${x}"]`).classList.toggle("active", x === v);
  });
  if (v === "kb") loadKnowledge(1);
  if (v === "dash") loadDash();
}

/* ---------------- 聊天:发送与 SSE 流式渲染 ---------------- */
async function send() {
  const input = document.getElementById("input");
  const text = input.value.trim();
  if (!text || streaming) return;
  input.value = "";
  ask(text);
}

function quickAsk(btn) { ask(btn.textContent.trim()); }

async function ask(text) {
  if (streaming) return;
  streaming = true;
  document.querySelector(".btn-send").disabled = true;

  const box = document.getElementById("messages");
  const hero = document.querySelector(".hero");
  if (hero) hero.remove();

  appendMsg("user", text);
  const botEl = appendMsg("bot", `<span class="thinking"><i></i><i></i><i></i></span>`);
  const bubble = botEl.querySelector(".bubble");

  try {
    const resp = await fetch(API + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-User-Token": USER_TOKEN },
      body: JSON.stringify({ message: text, conversation_id: conversationId }),
    });
    if (resp.status === 429) { bubble.textContent = "⚠️ 触发限流保护,请稍后再试"; return; }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = "", answer = "", meta = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const events = buf.split("\n\n");
      buf = events.pop();
      for (const ev of events) {
        const lines = ev.split("\n");
        const type = (lines.find((l) => l.startsWith("event:")) || "").slice(6).trim();
        const dataLine = lines.find((l) => l.startsWith("data:"));
        if (!dataLine) continue;
        const data = JSON.parse(dataLine.slice(5).trim());

        if (type === "meta") {
          meta = data;
          if (data.conversation_id) { conversationId = data.conversation_id; loadHistory(); }
        } else if (type === "delta") {
          answer += data.text;
          bubble.innerHTML = escapeHtml(answer) + '<span class="cursor"></span>';
          box.scrollTop = box.scrollHeight;
        } else if (type === "done") {
          finishAnswer(bubble, answer, meta, data);
        }
      }
    }
  } catch (e) {
    bubble.textContent = "⚠️ 网络异常:" + e.message;
  } finally {
    streaming = false;
    document.querySelector(".btn-send").disabled = false;
  }
}

function finishAnswer(bubble, answer, meta, done) {
  bubble.innerHTML = escapeHtml(answer || "(空回答)");
  if (meta && meta.sources && meta.sources.length) {
    const src = document.createElement("div");
    src.className = "sources";
    src.innerHTML = `
      <div class="sources-head">📎 引用来源 · 混合检索命中 ${meta.sources.length} 条
        <span style="margin-left:auto">检索耗时 ${meta.retrieval_ms}ms</span></div>
      <div class="src-list">${meta.sources.map((s) => `
        <span class="src-chip">📄 ${escapeHtml(s.title)}
          <span class="ranks">BM25#${s.bm25_rank ?? "-"} · VEC#${s.vec_rank ?? "-"} · ${(s.score * 100).toFixed(0)}%</span>
        </span>`).join("")}
      </div>
      <div class="meta-line">引擎:${meta.provider} · 总耗时 ${done.total_ms ?? "-"}ms</div>`;
    bubble.appendChild(src);
  }
  const box = document.getElementById("messages");
  box.scrollTop = box.scrollHeight;
}

function appendMsg(role, html) {
  const box = document.getElementById("messages");
  const el = document.createElement("div");
  el.className = "msg " + (role === "user" ? "user" : "bot");
  el.innerHTML = `
    <div class="avatar">${role === "user" ? "同学" : "🎓"}</div>
    <div class="bubble">${role === "user" ? escapeHtml(html) : html}</div>`;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
  return el;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ---------------- 会话历史 ---------------- */
async function loadHistory() {
  try {
    const resp = await fetch(API + "/api/conversations", { headers: { "X-User-Token": USER_TOKEN } });
    const list = await resp.json();
    const el = document.getElementById("history");
    el.innerHTML = (list || []).map((c) => `
      <div class="hist-item ${c.id === conversationId ? "active" : ""}" onclick="openConversation('${c.id}')">
        ${escapeHtml(c.title || "新会话")}
      </div>`).join("");
  } catch (e) { /* 忽略 */ }
}

async function openConversation(cid) {
  conversationId = cid;
  loadHistory();
  switchView("chat");
  const resp = await fetch(`${API}/api/conversations/${cid}/messages`, { headers: { "X-User-Token": USER_TOKEN } });
  const msgs = await resp.json();
  const box = document.getElementById("messages");
  box.innerHTML = "";
  // 历史回放统一转义:回答内容可能来自知识库文本,不可直接作为 HTML 注入
  for (const m of msgs) appendMsg(m.role, m.role === "user" ? m.content : escapeHtml(m.content));
  box.scrollTop = box.scrollHeight;
}

function newConversation() {
  conversationId = null;
  switchView("chat");
  location.reload();
}

/* ---------------- 知识库管理 ---------------- */
async function loadKnowledge(page = 1) {
  if (page < 1) page = 1;
  curPage = page;
  const cat = document.getElementById("kbCategory").value;
  const q = document.getElementById("kbSearch").value.trim();
  const resp = await fetch(`${API}/api/knowledge?page=${page}&size=9&category=${encodeURIComponent(cat)}&q=${encodeURIComponent(q)}`);
  const data = await resp.json();

  const sel = document.getElementById("kbCategory");
  if (sel.options.length === 1) {
    data.categories.forEach((c) => sel.add(new Option(c, c)));
  }
  document.getElementById("kbCount").textContent = `共 ${data.total} 条 · ${data.categories.length} 个分类`;
  document.getElementById("kbPage").textContent = `第 ${data.page} 页`;
  document.getElementById("kbList").innerHTML = data.items.map((d) => `
    <div class="kb-card">
      <span class="cat">${d.category}</span>
      <div class="q">${escapeHtml(d.question)}</div>
      <div class="a">${escapeHtml(d.answer)}</div>
      <div class="src">🗂 ${escapeHtml(d.source)} · ${d.updated_at}</div>
    </div>`).join("");
}

function toggleKbForm() { document.getElementById("kbForm").classList.toggle("hidden"); }

async function submitKnowledge() {
  const body = [{
    category: document.getElementById("formCat").value.trim() || "其他",
    question: document.getElementById("formQ").value.trim(),
    answer: document.getElementById("formA").value.trim(),
    source: document.getElementById("formSrc").value.trim() || "管理员录入",
  }];
  if (!body[0].question || !body[0].answer) { showToast("请填写问法与答案", true); return; }
  const adminHeaders = { "Content-Type": "application/json" };
  const adminToken = localStorage.getItem("adminToken");
  if (adminToken) adminHeaders["X-Admin-Token"] = adminToken;
  const resp = await fetch(API + "/api/knowledge", {
    method: "POST", headers: adminHeaders, body: JSON.stringify(body),
  });
  if (resp.status === 401) {
    // 服务端启用了 ADMIN_TOKEN 鉴权:提示录入管理令牌后重试
    const token = prompt("该服务已启用管理鉴权,请输入管理令牌(X-Admin-Token):");
    if (token) {
      localStorage.setItem("adminToken", token);
      return submitKnowledge();
    }
    showToast("未提供管理令牌,已取消录入", true);
    return;
  }
  const r = await resp.json();
  if (r.added) {
    showToast(`✅ 已新增 ${r.added} 条,索引热重建:当前 ${r.total_chunks} chunks(v${r.index_version})`);
    document.getElementById("formQ").value = document.getElementById("formA").value = "";
    loadKnowledge(1); refreshStatus();
  }
}

function showToast(msg, isWarn) {
  let t = document.querySelector(".toast");
  if (!t) {
    t = document.createElement("div");
    t.className = "toast";
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.toggle("warn", !!isWarn);
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 4200);
}

/* ---------------- 看板 ---------------- */
async function loadDash() {
  const resp = await fetch(API + "/api/admin/stats");
  const s = await resp.json();
  document.getElementById("dashCards").innerHTML = [
    ["累计提问", s.total_queries ?? 0, "次"],
    ["知识命中率", s.hit_rate == null ? "—" : (s.hit_rate * 100).toFixed(1) + "%", ""],
    ["平均生成时延", s.avg_latency_ms ?? 0, "ms"],
    ["会话数 / 索引块", `${s.conversations ?? 0} / ${s.chunk_count ?? 0}`, ""],
  ].map(([l, v, u]) => `
    <div class="stat-card"><div class="label">${l}</div><div class="value">${v}<small> ${u}</small></div></div>`).join("");

  const cats = Object.entries(s.top_categories || {});
  const max = Math.max(1, ...cats.map(([, v]) => v));
  document.getElementById("dashBars").innerHTML = cats.length
    ? cats.map(([c, v]) => `
      <div class="bar-row"><span>${escapeHtml(c)}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${(v / max) * 100}%"></div></div>
        <span>${v}</span></div>`).join("")
    : '<p style="font-size:13px;color:var(--ink-2)">暂无数据,去提几个问题吧</p>';
}

/* ---------------- 初始化 ---------------- */
async function refreshStatus() {
  try {
    const s = await (await fetch(API + "/api/admin/stats")).json();
    document.getElementById("chunkCount").textContent = s.chunk_count ?? "—";
    // 引擎可观察性:LLM Provider / 向量 Provider / 索引版本
    const engine = `LLM:${s.llm_provider ?? "-"} · 向量:${s.embedding_provider ?? "-"} · 索引 v${s.index_version ?? "-"}`;
    const engineEl = document.getElementById("engineInfo");
    if (engineEl) engineEl.textContent = engine;
    const badge = document.getElementById("providerBadge");
    if (badge) badge.textContent = `RAG 引擎在线 · 向量 ${s.embedding_provider ?? "-"} · 索引 v${s.index_version ?? "-"}`;
  } catch (e) { /* 后端未启动 */ }
}
refreshStatus();
loadHistory();
