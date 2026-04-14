from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aegis</title>
<style>
/* ------------------------------------------------------------------ */
/* Color tokens                                                         */
/* ------------------------------------------------------------------ */
:root {
  --c-text:      #111;
  --c-text-2:    #555;
  --c-text-3:    #888;
  --c-border:    #e5e5e5;
  --c-bg:        #fff;
  --c-bg-2:      #f7f7f7;
  --c-critical:  #C53030;
  --c-high:      #B45309;
  --c-medium:    #D97706;
  --c-low:       #888;
  --c-pass:      #639922;
  --c-warn-dot:  #D97706;
  --c-block-dot: #C53030;
  --c-skip-dot:  #ccc;
  --c-pill-bg:   #f0f0f0;
  --c-pill-text: #555;
  --c-code-bg:   #f0f0f0;
  --c-code-text: #111;
  --c-hover:     #f7f7f7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --c-text:      #e6edf3;
    --c-text-2:    #8b949e;
    --c-text-3:    #484f58;
    --c-border:    #21262d;
    --c-bg:        #0d1117;
    --c-bg-2:      #161b22;
    --c-pill-bg:   #1c2128;
    --c-pill-text: #8b949e;
    --c-code-bg:   #1c2128;
    --c-code-text: #e6edf3;
    --c-hover:     #1c2128;
  }
}

/* ------------------------------------------------------------------ */
/* Reset / base                                                         */
/* ------------------------------------------------------------------ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 13px; color: var(--c-text); background: var(--c-bg); }
a { color: inherit; text-decoration: none; }

/* ------------------------------------------------------------------ */
/* App shell                                                            */
/* ------------------------------------------------------------------ */
.app { display: flex; height: 100vh; overflow: hidden; }

/* ------------------------------------------------------------------ */
/* Nav sidebar (leftmost strip)                                         */
/* ------------------------------------------------------------------ */
.nav-bar {
  width: 56px; flex-shrink: 0;
  background: var(--c-bg); border-right: 1px solid var(--c-border);
  display: flex; flex-direction: column; align-items: center;
}
.nav-logo {
  width: 56px; height: 52px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 800; letter-spacing: -0.5px;
  border-bottom: 1px solid var(--c-border); flex-shrink: 0;
}
.nav-items {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; padding: 6px 0; width: 100%;
}
.nav-item {
  width: 100%; display: flex; flex-direction: column;
  align-items: center; padding: 10px 0 8px; gap: 4px;
  cursor: pointer; user-select: none;
  color: var(--c-text-3); font-size: 10px; letter-spacing: 0.2px;
  border-left: 2px solid transparent;
}
.nav-item:hover { color: var(--c-text-2); background: var(--c-hover); }
.nav-item.active { color: var(--c-text); border-left-color: var(--c-text); }
.nav-icon { width: 18px; height: 18px; }

.nav-bottom {
  display: flex; flex-direction: column; align-items: center;
  padding: 12px 0; gap: 5px;
  border-top: 1px solid var(--c-border); width: 100%;
}
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--c-skip-dot); }
.live-dot.connected { background: var(--c-pass); }
.live-label-sm { font-size: 9px; color: var(--c-text-3); letter-spacing: 0.2px; }

/* ------------------------------------------------------------------ */
/* Content area (everything right of nav)                              */
/* ------------------------------------------------------------------ */
.content-area { flex: 1; display: flex; overflow: hidden; }
.panel { display: none; flex: 1; overflow: hidden; }
.panel.active { display: flex; }

/* ------------------------------------------------------------------ */
/* Sessions list sidebar                                                */
/* ------------------------------------------------------------------ */
.sidebar {
  width: 220px; flex-shrink: 0;
  border-right: 1px solid var(--c-border);
  display: flex; flex-direction: column; overflow: hidden;
}
.sidebar-header {
  padding: 12px 14px 8px;
  font-size: 10px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.6px; color: var(--c-text-3);
}
.sidebar-list { flex: 1; overflow-y: auto; }

.session-row {
  padding: 12px 16px; cursor: pointer;
  border-bottom: 1px solid var(--c-border);
}
.session-row:hover, .session-row.active { background: var(--c-hover); }
.session-row-top { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
.session-id { font-family: monospace; font-size: 13px; font-weight: 700; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.agent-tag {
  font-size: 11px; padding: 2px 6px; border-radius: 3px;
  background: var(--c-bg-2); border: 1px solid var(--c-border);
  color: var(--c-text-3); white-space: nowrap; flex-shrink: 0;
}
.session-row-bottom { font-size: 12px; color: var(--c-text-3); display: flex; gap: 6px; align-items: center; }

/* ------------------------------------------------------------------ */
/* Main feed area                                                       */
/* ------------------------------------------------------------------ */
.feed-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.feed-header {
  padding: 10px 20px 8px; border-bottom: 1px solid var(--c-border);
  display: flex; align-items: center; gap: 10px; flex-shrink: 0;
}
.feed-session-id { font-size: 12px; font-weight: 700; font-family: monospace; }
.feed-meta { font-size: 11px; color: var(--c-text-3); flex: 1; }
.feed-actions { display: flex; gap: 6px; }
.btn-sm {
  font-size: 11px; padding: 3px 10px; border-radius: 4px;
  background: var(--c-bg-2); border: 1px solid var(--c-border);
  color: var(--c-text-2); cursor: pointer;
}
.btn-sm:hover { color: var(--c-text); }

.feed { flex: 1; overflow-y: auto; padding: 16px 20px; }
.feed-empty { color: var(--c-text-3); font-size: 12px; padding: 20px 0; max-width: 860px; margin: 0 auto; }
.reconnecting-bar {
  background: var(--c-bg-2); border: 1px solid var(--c-border);
  padding: 6px 12px; margin: 0 auto 10px; font-size: 11px; color: var(--c-text-2);
  border-radius: 4px; max-width: 860px; width: 100%;
}

/* ------------------------------------------------------------------ */
/* Trace card                                                           */
/* ------------------------------------------------------------------ */
.card {
  border: 1px solid var(--c-border); border-radius: 6px;
  margin: 0 auto 8px; overflow: hidden; background: var(--c-bg-2);
  max-width: 860px; width: 100%;
}
.card-header {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; cursor: pointer; user-select: none;
}
.card-header:hover { background: var(--c-hover); }
.card-sev { font-size: 10px; font-weight: 700; width: 54px; flex-shrink: 0; }
.card-ts { font-family: monospace; font-size: 10px; color: var(--c-text-3); flex-shrink: 0; }
.card-prompt { font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--c-text-2); }
.card-verdict {
  font-size: 10px; padding: 2px 7px; border-radius: 3px;
  background: var(--c-pill-bg); color: var(--c-pill-text); flex-shrink: 0;
}
.card-dur { font-family: monospace; font-size: 10px; color: var(--c-text-3); flex-shrink: 0; }

.card-body { border-top: 1px solid var(--c-border); display: none; }
.card.expanded .card-body { display: block; }

.card-prompt-full {
  font-size: 13px; color: var(--c-text-2); line-height: 1.6;
  padding: 12px 14px; word-break: break-word;
}
.card-io {
  display: grid; grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid var(--c-border);
}
.card-io-block { padding: 10px 14px; }
.card-io-block + .card-io-block { border-left: 1px solid var(--c-border); }
.card-io-label {
  font-size: 10px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.5px; color: var(--c-text-3); margin-bottom: 5px;
}
.card-io-text {
  font-size: 13px; color: var(--c-text-2); line-height: 1.6;
  word-break: break-word; white-space: pre-wrap;
}
.card-io-empty { color: var(--c-text-3); font-style: italic; font-size: 12px; }

/* Expandable output */
.output-wrap { position: relative; }
.output-text { font-size: 13px; color: var(--c-text-2); line-height: 1.6; word-break: break-word; white-space: pre-wrap; }
.output-text.output-collapsed { max-height: 120px; overflow: hidden; -webkit-mask-image: linear-gradient(to bottom, black 55%, transparent 100%); mask-image: linear-gradient(to bottom, black 55%, transparent 100%); }
.btn-expand { display: block; width: 100%; margin-top: 6px; padding: 4px 0; background: var(--c-bg); border: 1px solid var(--c-border); border-radius: 3px; cursor: pointer; font-size: 11px; color: var(--c-text-3); }

/* ------------------------------------------------------------------ */
/* Step list                                                            */
/* ------------------------------------------------------------------ */
.step-list { padding: 6px 0; }
.step-item {
  display: flex; gap: 12px; padding: 5px 14px;
  border-top: 0.5px solid var(--c-border);
  position: relative;
}
.step-item:first-child { border-top: none; }
.step-item.step-skipped { opacity: 0.3; }

.step-left {
  display: flex; flex-direction: column; align-items: center;
  padding-top: 4px; width: 18px; flex-shrink: 0;
}
.dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.dot-pass    { background: #639922; }
.dot-warn    { background: #D97706; }
.dot-block   { background: #C53030; }
.dot-redact  { background: #C53030; }
.dot-skip    { background: #ccc; }
.dot-approval { background: #D97706; }
.connector { width: 1px; flex: 1; background: var(--c-border); margin-top: 3px; }

.step-right { flex: 1; min-width: 0; }
.step-name-row { display: flex; align-items: baseline; gap: 8px; }
.step-name { font-size: 14px; flex: 1; }
.step-dur { font-family: monospace; font-size: 10px; color: var(--c-text-3); flex-shrink: 0; }
.step-detail { font-size: 12px; color: var(--c-text-2); margin-top: 2px; word-break: break-word; font-family: monospace; }
.step-rules { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.rule-tag {
  font-family: monospace; font-size: 11px; padding: 1px 5px;
  background: var(--c-code-bg); color: var(--c-code-text); border: 1px solid var(--c-border);
  border-radius: 3px;
}

.card-footer {
  padding: 8px 14px; border-top: 0.5px solid var(--c-border);
  display: flex; align-items: center; font-size: 10px; color: var(--c-text-3);
}
.card-footer-right { margin-left: auto; font-family: monospace; }

/* Severity text colours */
.sev-Critical { color: #C53030; }
.sev-High     { color: #B45309; }
.sev-Medium   { color: #D97706; }
.sev-Low      { color: #888; }

/* ------------------------------------------------------------------ */
/* Network tab                                                          */
/* ------------------------------------------------------------------ */
.net-panel { padding: 24px 28px; max-width: 760px; overflow-y: auto; flex: 1; }
.net-section { margin-bottom: 28px; }
.net-title { font-size: 12px; font-weight: 700; margin-bottom: 4px; }
.net-desc { font-size: 11px; color: var(--c-text-3); margin-bottom: 10px; }
.net-add-row { display: flex; gap: 8px; margin-bottom: 10px; }
.net-input {
  flex: 1; padding: 5px 9px; border: 1px solid var(--c-border);
  border-radius: 4px; background: var(--c-bg); color: var(--c-text); font-size: 12px;
}
.net-input:focus { outline: none; border-color: var(--c-text-3); }
.btn-add {
  padding: 5px 14px; border: 1px solid var(--c-border);
  border-radius: 4px; background: var(--c-bg-2); cursor: pointer;
  font-size: 12px; color: var(--c-text);
}
.btn-add:hover { background: var(--c-hover); }
.net-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.net-table th {
  text-align: left; font-size: 10px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.5px; color: var(--c-text-3); padding: 4px 8px 6px;
  border-bottom: 1px solid var(--c-border);
}
.net-table td { padding: 6px 8px; border-bottom: 0.5px solid var(--c-border); }
.net-domain { font-family: monospace; }
.btn-remove { background: none; border: none; cursor: pointer; font-size: 11px; color: var(--c-text-3); }
.btn-remove:hover { color: #C53030; }
.net-always-blocked { opacity: 0.6; }
hr.net-hr { border: none; border-top: 0.5px solid var(--c-border); margin: 20px 0; }

/* No session selected */
.no-session {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: var(--c-text-3); font-size: 12px;
}
</style>
</head>
<body>
<div class="app">

  <!-- Nav sidebar -->
  <nav class="nav-bar">
    <div class="nav-logo">Ae</div>
    <div class="nav-items">

      <div class="nav-item active" id="nav-sessions" onclick="switchTab('sessions')" title="Sessions">
        <svg class="nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <line x1="6" y1="5" x2="14" y2="5"/>
          <line x1="6" y1="9" x2="14" y2="9"/>
          <line x1="6" y1="13" x2="14" y2="13"/>
          <circle cx="3.5" cy="5" r="1" fill="currentColor" stroke="none"/>
          <circle cx="3.5" cy="9" r="1" fill="currentColor" stroke="none"/>
          <circle cx="3.5" cy="13" r="1" fill="currentColor" stroke="none"/>
        </svg>
        Sessions
      </div>

      <div class="nav-item" id="nav-network" onclick="switchTab('network')" title="Network">
        <svg class="nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <circle cx="9" cy="9" r="6.5"/>
          <path d="M9 2.5c-2 2-3 4-3 6.5s1 4.5 3 6.5"/>
          <path d="M9 2.5c2 2 3 4 3 6.5s-1 4.5-3 6.5"/>
          <line x1="2.5" y1="9" x2="15.5" y2="9"/>
        </svg>
        Network
      </div>

    </div>
    <div class="nav-bottom">
      <div class="live-dot" id="live-dot"></div>
      <span class="live-label-sm" id="live-label">Off</span>
    </div>
  </nav>

  <!-- Content area -->
  <div class="content-area">

    <!-- Sessions panel -->
    <div class="panel active" id="panel-sessions">
      <div class="sidebar">
        <div class="sidebar-header">Sessions</div>
        <div class="sidebar-list" id="session-list"></div>
      </div>

      <div class="feed-area" id="feed-area">
        <div class="no-session" id="no-session">Select a session to view traces</div>

        <div id="feed-content" style="display:none; flex-direction:column; flex:1; overflow:hidden;">
          <div class="feed-header">
            <div class="feed-session-id" id="feed-sid"></div>
            <div class="feed-meta" id="feed-meta"></div>
            <div class="feed-actions">
              <button class="btn-sm" id="btn-pause" onclick="togglePause()">Pause</button>
              <button class="btn-sm" onclick="clearFeed()">Clear</button>
            </div>
          </div>
          <div class="feed" id="feed">
            <div class="feed-empty">No traces yet.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Network panel -->
    <div class="panel" id="panel-network">
      <div class="net-panel" id="net-panel">

        <div class="net-section">
          <div class="net-title">Allowlist</div>
          <div class="net-desc">Only these domains are permitted. Leave empty to allow all (except denylist).</div>
          <div class="net-add-row">
            <input class="net-input" id="allow-input" placeholder="example.com" onkeydown="if(event.key==='Enter')addDomain('allow')">
            <button class="btn-add" onclick="addDomain('allow')">Add</button>
          </div>
          <table class="net-table" id="allow-table">
            <thead><tr><th>Domain</th><th>Hits</th><th>Added</th><th></th></tr></thead>
            <tbody id="allow-body"></tbody>
          </table>
        </div>

        <hr class="net-hr">

        <div class="net-section">
          <div class="net-title">Denylist</div>
          <div class="net-desc">These domains are always blocked regardless of the allowlist.</div>
          <div class="net-add-row">
            <input class="net-input" id="deny-input" placeholder="malicious.example.com" onkeydown="if(event.key==='Enter')addDomain('deny')">
            <button class="btn-add" onclick="addDomain('deny')">Add</button>
          </div>
          <table class="net-table" id="deny-table">
            <thead><tr><th>Domain</th><th>Hits</th><th>Added</th><th></th></tr></thead>
            <tbody id="deny-body"></tbody>
          </table>
        </div>

        <hr class="net-hr">

        <div class="net-section net-always-blocked">
          <div class="net-title">Always blocked</div>
          <div class="net-desc">These addresses are blocked at the network layer and cannot be removed.</div>
          <table class="net-table">
            <thead><tr><th>Address / Range</th><th>Reason</th></tr></thead>
            <tbody>
              <tr><td class="net-domain">169.254.169.254</td><td>AWS / GCP / Azure IMDS</td></tr>
              <tr><td class="net-domain">10.0.0.0/8</td><td>Private network (RFC 1918)</td></tr>
              <tr><td class="net-domain">172.16.0.0/12</td><td>Private network (RFC 1918)</td></tr>
              <tr><td class="net-domain">192.168.0.0/16</td><td>Private network (RFC 1918)</td></tr>
              <tr><td class="net-domain">127.0.0.0/8</td><td>Loopback</td></tr>
              <tr><td class="net-domain">::1</td><td>IPv6 loopback</td></tr>
              <tr><td class="net-domain">fc00::/7</td><td>IPv6 unique local</td></tr>
            </tbody>
          </table>
        </div>

      </div>
    </div>

  </div><!-- .content-area -->
</div><!-- .app -->

<script>
/* ------------------------------------------------------------------ */
/* State                                                                */
/* ------------------------------------------------------------------ */
let activeSession = null;
let eventSource = null;
let paused = false;
let backoff = 500;
let reconnectTimer = null;
let sessionPollTimer = null;

const BASE = '/v1';

/* ------------------------------------------------------------------ */
/* Tab switching                                                        */
/* ------------------------------------------------------------------ */
function switchTab(name) {
  document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('nav-' + name).classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'network') loadNetwork();
}

/* ------------------------------------------------------------------ */
/* Sessions sidebar                                                     */
/* ------------------------------------------------------------------ */
async function loadSessions() {
  try {
    const sessions = await apiFetch(BASE + '/sessions');
    renderSessions(sessions);
  } catch (e) { /* ignore */ }
}

function renderSessions(sessions) {
  const list = document.getElementById('session-list');
  list.innerHTML = '';
  if (!sessions || !sessions.length) {
    list.innerHTML = '<div style="padding:12px;font-size:11px;color:var(--c-text-3)">No sessions yet</div>';
    return;
  }
  sessions.forEach(s => {
    const row = document.createElement('div');
    row.className = 'session-row' + (s.session_id === activeSession ? ' active' : '');
    row.onclick = () => selectSession(s.session_id, s);
    const shortId = (s.session_id || '').slice(0, 8);
    const sev = s.severity || 'Low';
    row.innerHTML =
      '<div class="session-row-top">' +
        '<span class="session-id">' + esc(shortId) + '</span>' +
        '<span class="agent-tag">' + esc(s.agent_type || 'general') + '</span>' +
      '</div>' +
      '<div class="session-row-bottom">' +
        '<span class="sev-' + esc(sev) + '">' + esc(sev) + '</span>' +
        '<span>' + (s.trace_count || 0) + ' traces &middot; risk ' + fmtRisk(s.cumulative_risk) + '</span>' +
      '</div>';
    list.appendChild(row);
  });
}

function selectSession(id, meta) {
  if (activeSession === id) return;
  activeSession = id;

  document.querySelectorAll('.session-row').forEach(r => r.classList.remove('active'));
  event && event.currentTarget && event.currentTarget.classList.add('active');

  document.getElementById('no-session').style.display = 'none';
  const fc = document.getElementById('feed-content');
  fc.style.display = 'flex';

  document.getElementById('feed-sid').textContent = id.slice(0, 8) + '...';
  document.getElementById('feed-meta').textContent =
    (meta && meta.agent_type ? meta.agent_type : '') +
    (meta && meta.environment ? ' · ' + meta.environment : '');

  clearFeed();
  connectSSE(id);
}

/* ------------------------------------------------------------------ */
/* SSE                                                                  */
/* ------------------------------------------------------------------ */
function setLive(connected) {
  const dot = document.getElementById('live-dot');
  const label = document.getElementById('live-label');
  if (connected) {
    dot.classList.add('connected');
    label.textContent = 'Live';
  } else {
    dot.classList.remove('connected');
    label.textContent = 'Off';
  }
}

function connectSSE(id) {
  if (eventSource) { eventSource.close(); eventSource = null; }
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }

  removeReconnectingBar();
  setLive(false);

  const es = new EventSource(BASE + '/sessions/' + id + '/events/stream');
  eventSource = es;

  es.onopen = () => { backoff = 500; setLive(true); };

  es.onmessage = (ev) => {
    if (!ev.data || ev.data.trim() === '') return;
    try {
      const trace = JSON.parse(ev.data);
      if (!paused) renderTrace(trace);
    } catch (e) { /* ignore malformed */ }
  };

  es.onerror = () => {
    es.close();
    eventSource = null;
    setLive(false);
    if (activeSession !== id) return;
    showReconnectingBar();
    reconnectTimer = setTimeout(() => connectSSE(id), backoff);
    backoff = Math.min(backoff * 2, 8000);
  };
}

function showReconnectingBar() {
  removeReconnectingBar();
  const bar = document.createElement('div');
  bar.className = 'reconnecting-bar';
  bar.id = 'reconnect-bar';
  bar.textContent = 'Reconnecting...';
  const feed = document.getElementById('feed');
  feed.prepend(bar);
}

function removeReconnectingBar() {
  const bar = document.getElementById('reconnect-bar');
  if (bar) bar.remove();
}

/* ------------------------------------------------------------------ */
/* Feed controls                                                        */
/* ------------------------------------------------------------------ */
function togglePause() {
  paused = !paused;
  document.getElementById('btn-pause').textContent = paused ? 'Resume' : 'Pause';
}

function clearFeed() {
  const feed = document.getElementById('feed');
  feed.innerHTML = '<div class="feed-empty">No traces yet.</div>';
}

/* ------------------------------------------------------------------ */
/* Trace rendering                                                      */
/* ------------------------------------------------------------------ */
function renderTrace(trace) {
  const feed = document.getElementById('feed');
  const empty = feed.querySelector('.feed-empty');
  if (empty) empty.remove();
  removeReconnectingBar();

  const tid = trace.trace_id;
  const existing = tid ? feed.querySelector('[data-trace-id="' + tid + '"]') : null;
  if (existing) {
    const updated = buildCard(trace, false);
    if (existing.classList.contains('expanded')) updated.classList.add('expanded');
    existing.replaceWith(updated);
    return;
  }

  if (!paused) {
    // Any previously-first card is no longer the latest — re-render its output label if pending
    const prevFirst = feed.querySelector('.card');
    if (prevFirst) {
      const prevTid = prevFirst.dataset.traceId;
      if (prevTid && prevFirst.dataset.finalized === 'false') {
        prevFirst.dataset.finalized = 'stale';
        const outEmpty = prevFirst.querySelector('.card-io-empty');
        if (outEmpty && outEmpty.textContent === 'Pending\u2026') outEmpty.textContent = '\u2014';
      }
    }
    feed.prepend(buildCard(trace, true));
  }
}

function buildCard(trace, isLatest) {
  const sev = trace.severity || 'Low';
  const verdict = trace.verdict || 'allowed';
  const dur = trace.duration_ms != null ? trace.duration_ms + 'ms' : '';
  const ts = trace.ts_readable || '';
  const prompt = (trace.prompt || '').slice(0, 120);

  const card = document.createElement('div');
  card.className = 'card';
  if (trace.trace_id) card.dataset.traceId = trace.trace_id;
  card.dataset.finalized = trace.finalized ? 'true' : 'false';

  const header = document.createElement('div');
  header.className = 'card-header';
  header.innerHTML =
    '<span class="card-sev sev-' + esc(sev) + '">' + esc(sev) + '</span>' +
    '<span class="card-ts">' + esc(ts) + '</span>' +
    '<span class="card-prompt">' + esc(prompt) + '</span>' +
    '<span class="card-verdict">' + esc(verdict) + '</span>' +
    '<span class="card-dur">' + esc(dur) + '</span>';
  header.onclick = () => card.classList.toggle('expanded');

  const body = document.createElement('div');
  body.className = 'card-body';

  // Input / Output side-by-side
  const io = document.createElement('div');
  io.className = 'card-io';

  const inBlock = document.createElement('div');
  inBlock.className = 'card-io-block';
  inBlock.innerHTML = '<div class="card-io-label">Input</div>';
  const inText = document.createElement('div');
  inText.className = 'card-io-text';
  inText.textContent = trace.prompt || '';
  inBlock.appendChild(inText);

  const outBlock = document.createElement('div');
  outBlock.className = 'card-io-block';
  outBlock.innerHTML = '<div class="card-io-label">Output</div>';
  if (trace.llm_output) {
    const COLLAPSE_THRESHOLD = 320;
    const text = trace.llm_output;
    const wrap = document.createElement('div');
    wrap.className = 'output-wrap';
    const outText = document.createElement('div');
    outText.className = 'output-text' + (text.length > COLLAPSE_THRESHOLD ? ' output-collapsed' : '');
    outText.textContent = text;
    wrap.appendChild(outText);
    if (text.length > COLLAPSE_THRESHOLD) {
      const btn = document.createElement('button');
      btn.className = 'btn-expand';
      btn.textContent = 'Show more';
      btn.onclick = (e) => {
        e.stopPropagation();
        const nowCollapsed = outText.classList.toggle('output-collapsed');
        btn.textContent = nowCollapsed ? 'Show more' : 'Show less';
      };
      wrap.appendChild(btn);
    }
    outBlock.appendChild(wrap);
  } else {
    const outText = document.createElement('div');
    outText.className = 'card-io-text card-io-empty';
    const isBlocked = (trace.verdict === 'blocked');
    const isPending = !trace.finalized && isLatest !== false;
    outText.textContent = isBlocked ? 'Blocked' : isPending ? 'Pending\u2026' : '\u2014';
    outBlock.appendChild(outText);
  }

  io.appendChild(inBlock);
  io.appendChild(outBlock);
  body.appendChild(io);

  body.appendChild(buildStepList(trace.spans || []));

  const footer = document.createElement('div');
  footer.className = 'card-footer';
  footer.innerHTML =
    'risk ' + fmtRisk(trace.risk_score) +
    '<span class="card-footer-right">trace ' + esc((trace.trace_id || '').slice(0, 8)) + '</span>';
  body.appendChild(footer);

  card.appendChild(header);
  card.appendChild(body);
  return card;
}

function buildStepList(spans) {
  const STEP_LABELS = {
    'input_received':   'Input received',
    'context_resolved': 'Context resolved',
    'network_firewall': 'Network firewall',
    'prellm_policy':    'Pre-hook · policy',
    'llm_call':         'LLM call',
    'postllm_policy':   'Post-hook · output',
    'tool_pre':         'Tool · pre-check',
    'tool_post':        'Tool · post-check',
    'approval_required':'Approval required',
  };

  const list = document.createElement('div');
  list.className = 'step-list';

  spans.forEach((span, idx) => {
    const item = document.createElement('div');
    item.className = 'step-item' + (span.status === 'skipped' ? ' step-skipped' : '');

    const name = STEP_LABELS[span.name] || span.name;
    const durStr = span.duration_ms != null ? span.duration_ms + 'ms' : '';
    const dc = dotClass(span.status);

    const leftHTML =
      '<div class="step-left">' +
        '<div class="dot ' + dc + '"></div>' +
        (idx < spans.length - 1 ? '<div class="connector"></div>' : '') +
      '</div>';

    let rulesHTML = '';
    if (span.rules && span.rules.length > 0 && span.status !== 'skipped') {
      rulesHTML = '<div class="step-rules">' +
        span.rules.map(r => '<span class="rule-tag">' + esc(r) + '</span>').join('') +
        '</div>';
    }

    let detailHTML = '';
    if (span.detail && span.status !== 'skipped') {
      detailHTML = '<div class="step-detail">' + esc(span.detail) + '</div>';
    }

    item.innerHTML =
      leftHTML +
      '<div class="step-right">' +
        '<div class="step-name-row">' +
          '<span class="step-name">' + esc(name) + '</span>' +
          '<span class="step-dur">' + esc(durStr) + '</span>' +
        '</div>' +
        detailHTML +
        rulesHTML +
      '</div>';

    list.appendChild(item);
  });

  return list;
}

function dotClass(status) {
  const map = {
    'pass': 'dot-pass',
    'warn': 'dot-warn',
    'block': 'dot-block',
    'redact': 'dot-redact',
    'skipped': 'dot-skip',
    'approval_required': 'dot-approval',
  };
  return map[status] || 'dot-skip';
}

/* ------------------------------------------------------------------ */
/* Network tab                                                          */
/* ------------------------------------------------------------------ */
async function loadNetwork() {
  try {
    const [al, dl] = await Promise.all([
      apiFetch(BASE + '/network/allowlist'),
      apiFetch(BASE + '/network/denylist'),
    ]);
    renderNetTable('allow-body', al.domains || [], 'allow');
    renderNetTable('deny-body', dl.domains || [], 'deny');
  } catch (e) { /* ignore */ }
}

function renderNetTable(tbodyId, entries, kind) {
  const tbody = document.getElementById(tbodyId);
  tbody.innerHTML = '';
  entries.forEach(e => {
    const domain = typeof e === 'string' ? e : e.domain;
    const hits = typeof e === 'object' ? (e.hits || 0) : 0;
    const added = typeof e === 'object' ? (e.added_at || '').slice(0, 10) : '';
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td class="net-domain">' + esc(domain) + '</td>' +
      '<td>' + hits + '</td>' +
      '<td>' + esc(added) + '</td>' +
      '<td><button class="btn-remove" onclick="removeDomain(\'' + kind + '\',\'' + esc(domain) + '\')">remove</button></td>';
    tbody.appendChild(tr);
  });
}

async function addDomain(kind) {
  const inputId = kind === 'allow' ? 'allow-input' : 'deny-input';
  const input = document.getElementById(inputId);
  const domain = input.value.trim();
  if (!domain) return;
  try {
    await apiFetch(BASE + '/network/' + kind + 'list', {
      method: 'POST',
      body: JSON.stringify({ domain }),
    });
    input.value = '';
    loadNetwork();
  } catch (e) { alert('Error: ' + e.message); }
}

async function removeDomain(kind, domain) {
  try {
    await apiFetch(BASE + '/network/' + kind + 'list/' + encodeURIComponent(domain), {
      method: 'DELETE',
    });
    loadNetwork();
  } catch (e) { alert('Error: ' + e.message); }
}

/* ------------------------------------------------------------------ */
/* Utilities                                                            */
/* ------------------------------------------------------------------ */
async function apiFetch(url, opts = {}) {
  const defaults = { headers: { 'Content-Type': 'application/json' } };
  const res = await fetch(url, { ...defaults, ...opts });
  if (!res.ok) throw new Error(res.status + ' ' + res.statusText);
  return res.json();
}

function esc(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function fmtRisk(v) {
  return v != null ? Number(v).toFixed(2) : '0.00';
}

/* ------------------------------------------------------------------ */
/* Init                                                                 */
/* ------------------------------------------------------------------ */
loadSessions();
sessionPollTimer = setInterval(loadSessions, 5000);
</script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(DASHBOARD_HTML)
