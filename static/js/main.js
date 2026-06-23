/* ── main.js: RailWise AI Core JavaScript ── */
'use strict';

const API = '/api';
let token = localStorage.getItem('rw_token');
let currentPrediction = null;

/* ── Theme ── */
const root = document.documentElement;
const savedTheme = localStorage.getItem('rw_theme') || 'dark';
root.setAttribute('data-theme', savedTheme);

function toggleTheme() {
  const t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', t);
  localStorage.setItem('rw_theme', t);
}

/* ── Loader ── */
function showLoader() { const el = document.getElementById('loaderOverlay'); if (el) el.style.display = 'flex'; }
function hideLoader() { const el = document.getElementById('loaderOverlay'); if (el) el.style.display = 'none'; }

/* ── Toast ── */
function toast(msg, type = 'info') {
  const c = document.getElementById('toastContainer');
  if (!c) return;
  const id = 'toast-' + Date.now();
  const color = { info: 'var(--primary)', success: 'var(--accent)', danger: 'var(--danger)', warning: 'var(--warning)' }[type] || 'var(--primary)';
  c.insertAdjacentHTML('beforeend', `
    <div id="${id}" style="background:var(--bg-card);backdrop-filter:blur(20px);border:1px solid var(--border-glass);border-left:3px solid ${color};border-radius:12px;padding:14px 20px;min-width:260px;max-width:380px;color:var(--text-primary);box-shadow:var(--shadow-glow);animation:slideIn .3s ease;font-size:.9rem;">
      ${msg}
    </div>`);
  setTimeout(() => { const el = document.getElementById(id); if (el) el.style.animation = 'slideOut .3s ease forwards'; setTimeout(() => el?.remove(), 300); }, 3500);
}

/* ── Auth Helpers ── */
function authHeaders() {
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}
function isLoggedIn() { return !!token; }
function logout() { token = null; localStorage.removeItem('rw_token'); localStorage.removeItem('rw_user'); window.location.href = '/login'; }
function updateNavAuth() {
  const nav = document.getElementById('navAuthSection');
  if (!nav) return;
  const user = JSON.parse(localStorage.getItem('rw_user') || '{}');
  if (isLoggedIn()) {
    nav.innerHTML = `
      <a href="/profile" class="text-muted small me-3 text-decoration-none" style="transition:color 0.3s;" onmouseover="this.style.color='var(--text-primary)'" onmouseout="this.style.color='var(--text-muted)'">👤 ${user.first_name || 'User'}</a>
      <a href="/history" class="btn btn-glass btn-sm me-2">History</a>
      <button onclick="logout()" class="btn btn-glass btn-sm">Logout</button>`;
  } else {
    nav.innerHTML = `<a href="/login" class="btn btn-nav-cta btn-sm">Sign In</a>`;
  }
}

/* ── Populate Dropdowns ── */
async function loadStations() {
  const src = document.querySelector('[name="source_station"]');
  const dest = document.querySelector('[name="destination_station"]');
  if (!src && !dest) return;
  
  try {
    const res = await fetch(`${API}/stations`);
    if (!res.ok) {
      console.error(`[loadStations] API Error: Status ${res.status}`);
      return;
    }
    
    const body = await res.json();
    if (!body.success || !body.data || !Array.isArray(body.data.stations)) {
      console.error("[loadStations] Invalid JSON structure returned:", body);
      return;
    }
    
    if (body.data.stations.length === 0) {
      console.warn("[loadStations] Empty stations array returned.");
      const emptyOpt = `<option value="">No stations available</option>`;
      if (src) src.innerHTML = emptyOpt;
      if (dest) dest.innerHTML = emptyOpt;
      return;
    }

    const options = body.data.stations.map(s => {
      // Defensive programming: fallback to check both old hardcoded schema and new DB schema
      const code = s.station_code || s.code || '';
      const name = s.station_name || s.name || '';
      
      if (!code || !name) {
        console.warn("[loadStations] Station object missing required fields:", s);
      }
      
      return `<option value="${code}">${name} (${code})</option>`;
    }).join('');
    
    if (src) src.innerHTML = options;
    if (dest) dest.innerHTML = options;
    if (dest && dest.options.length > 1) {
      dest.selectedIndex = 1; // pick second by default
    }
    
    console.log(`[loadStations] Successfully loaded ${body.data.stations.length} stations.`);
  } catch (err) {
    console.error("[loadStations] Fetch exception:", err);
  }
}

/* ── Prediction Form Submit ── */
async function submitPrediction(e) {
  e?.preventDefault();
  const form = document.getElementById('predictForm');
  if (!form) return;

  const data = {
    train_number:       form.train_number?.value?.trim(),
    source_station:     form.source_station?.value?.trim(),
    destination_station:form.destination_station?.value?.trim(),
    journey_date:       form.journey_date?.value,
    booking_date:       form.booking_date?.value,
    class_type:         form.class_type?.value,
    quota_type:         form.quota_type?.value,
    booking_wl:         parseInt(form.booking_wl?.value),
    current_wl:         parseInt(form.current_wl?.value),
    current_rac:        parseInt(form.current_rac?.value) || 0,
  };

  showLoader();
  try {
    const res = await fetch(`${API}/predict`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data),
    });
    const resultJson = await res.json();
    hideLoader();
    if (!res.ok || !resultJson.success) { 
      toast(resultJson.error || resultJson.message || 'Prediction failed', 'danger'); 
      return; 
    }
    currentPrediction = { input: data, result: resultJson.data };
    sessionStorage.setItem('rw_prediction', JSON.stringify(currentPrediction));
    window.location.href = '/result';
  } catch (err) {
    hideLoader();
    toast('Network error. Please try again.', 'danger');
  }
}

/* ── Render Result Page ── */
function renderResult() {
  const stored = sessionStorage.getItem('rw_prediction');
  if (!stored) { window.location.href = '/dashboard'; return; }
  const { input, result } = JSON.parse(stored);

  // Normalize probabilities to 100%
  let pCnf = parseFloat(result.probability_cnf) || 0;
  let pRac = parseFloat(result.probability_rac) || 0;
  let pWl = parseFloat(result.probability_wl) || 0;
  
  let total = pCnf + pRac + pWl;
  if (total > 0 && Math.abs(total - 100) > 0.01) {
    let diff = 100 - total;
    if (pCnf >= pRac && pCnf >= pWl) pCnf += diff;
    else if (pRac >= pCnf && pRac >= pWl) pRac += diff;
    else pWl += diff;
  }
  
  pCnf = parseFloat(pCnf.toFixed(2));
  pRac = parseFloat(pRac.toFixed(2));
  pWl = parseFloat(pWl.toFixed(2));

  // Primary probability based on prediction
  let maxProb = pCnf;
  if (result.prediction === 'RAC') maxProb = pRac;
  else if (result.prediction === 'WL') maxProb = pWl;

  // Dynamic Risk Level
  let dynRisk = 'HIGH';
  if (maxProb >= 80) dynRisk = 'LOW';
  else if (maxProb >= 50) dynRisk = 'MEDIUM';

  // Confidence Meter
  let confText = 'Low Confidence';
  let confClass = 'conf-low';
  if (maxProb >= 90) { confText = 'Very High Confidence'; confClass = 'conf-very-high'; }
  else if (maxProb >= 75) { confText = 'High Confidence'; confClass = 'conf-high'; }
  else if (maxProb >= 50) { confText = 'Medium Confidence'; confClass = 'conf-medium'; }

  setText('res-status', result.prediction);
  setText('res-risk', dynRisk);
  setText('res-main-pct', maxProb + '%');
  setText('res-confidence', confText);

  const confEl = document.getElementById('res-confidence');
  if (confEl) confEl.className = 'confidence-meter ' + confClass;

  setText('res-cnf-pct2', pCnf + '%');
  setText('res-rac-pct', pRac + '%');
  setText('res-wl-pct',  pWl  + '%');
  setText('res-days',    result.booking_days_before + ' days');
  setText('res-train',   input.train_number);
  setText('res-route',   `${input.source_station} → ${input.destination_station}`);
  setText('res-class',   input.class_type);
  setText('res-quota',   input.quota_type);
  setText('res-wl-num',  'WL ' + input.current_wl);

  const statusEl = document.getElementById('res-status');
  if (statusEl) {
    statusEl.className = result.prediction === 'CNF' ? 'badge-cnf' : result.prediction === 'RAC' ? 'badge-rac' : 'badge-wl';
    statusEl.style.cssText = 'font-size:1rem;padding:6px 18px;display:inline-block;margin-top:4px;';
  }
  const riskEl = document.getElementById('res-risk');
  if (riskEl) riskEl.className = `risk-${dynRisk.toLowerCase()}`;

  setTimeout(() => {
    setBar('bar-cnf', pCnf);
    setBar('bar-rac', pRac);
    setBar('bar-wl',  pWl);
  }, 300);

  drawGauge(maxProb, result.prediction);

  if (result.recommendations?.length) {
    renderRecommendations(result.recommendations);
    const hc = document.getElementById('highConfSection');
    if (hc) hc.style.display = 'none';
    const rc = document.getElementById('recommendSection');
    if (rc) rc.style.display = 'block';
  } else {
    const rc = document.getElementById('recommendSection');
    if (rc) rc.style.display = 'none';
    const hc = document.getElementById('highConfSection');
    if (hc) hc.style.display = 'block';
  }

  // Explainable AI
  if (result.explanation) {
    const explainSec = document.getElementById('explainSection');
    if (explainSec) explainSec.style.display = 'block';
    
    const posList = result.explanation.why_positive.map(p => `<div style="margin-bottom:8px;"><i class="fa fa-check-circle me-2" style="color:var(--accent);"></i> ${p}</div>`).join('');
    const negList = result.explanation.why_negative.map(n => `<div style="margin-bottom:8px;"><i class="fa fa-exclamation-circle me-2" style="color:var(--warning);"></i> ${n}</div>`).join('');
    
    const posEl = document.getElementById('xai-pos-list');
    if (posEl) posEl.innerHTML = posList || '';
    
    const negEl = document.getElementById('xai-neg-list');
    if (negEl) negEl.innerHTML = negList || '';
  }
}

function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }

function setBar(id, pct) { const el = document.getElementById(id); if (el) el.style.width = pct + '%'; }

function drawGauge(pct, prediction) {
  const canvas = document.getElementById('gaugeCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H - 10;
  const r = Math.min(cx, cy) - 10;

  ctx.clearRect(0, 0, W, H);

  // Background arc
  ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI, 0);
  ctx.lineWidth = 14; ctx.strokeStyle = 'rgba(255,255,255,0.08)'; ctx.lineCap = 'round'; ctx.stroke();

  // Value arc
  const ratio = pct / 100;
  let color = '#06d6a0'; // CNF
  if (prediction === 'RAC') color = '#ffd166';
  else if (prediction === 'WL') color = '#ff6b6b';

  ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI, Math.PI + ratio * Math.PI);
  ctx.strokeStyle = color; ctx.lineWidth = 14; ctx.lineCap = 'round'; ctx.stroke();

  // Glow
  ctx.shadowBlur = 16; ctx.shadowColor = color;
  ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI + ratio * Math.PI - 0.02, Math.PI + ratio * Math.PI);
  ctx.strokeStyle = color; ctx.lineWidth = 14; ctx.stroke();
  ctx.shadowBlur = 0;
}

function renderRecommendations(recs) {
  const container = document.getElementById('recContainer');
  if (!container) return;
  container.innerHTML = recs.map(r => {
    let icon = r.type.includes('date') ? 'fa-calendar-alt' : 'fa-train';
    let cardTitle = r.type.includes('date') ? 'Alternative Date' : 'Alternative Class';
    return `
    <div class="col-12 col-md-6">
      <div class="glass-card rec-card h-100" style="border-left-color: var(--accent);">
        <div class="rec-type" style="color:var(--accent);"><i class="fa ${icon} me-1"></i> ${cardTitle}</div>
        <div class="rec-title mt-2">Train ${r.train_number}</div>
        <div class="rec-meta">Class: <strong style="color:var(--text-primary);">${r.class}</strong> &nbsp;|&nbsp; Date: <strong style="color:var(--text-primary);">${r.journey_date}</strong></div>
        <div class="mt-3">
          <span class="badge-cnf"><i class="fa fa-check me-1"></i>${r.availability}</span>
        </div>
        ${r.note ? `<p class="mt-3 mb-0 prob-explanation"><i class="fa fa-info-circle me-1"></i>${r.note}</p>` : ''}
      </div>
    </div>`
  }).join('');
}

/* ── Login / Register ── */
async function handleLogin(e) {
  e?.preventDefault();
  const email = document.getElementById('loginEmail')?.value;
  const password = document.getElementById('loginPass')?.value;
  showLoader();
  try {
    const res = await fetch(`${API}/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
    const resJson = await res.json();
    hideLoader();
    if (!res.ok || !resJson.success) { toast(resJson.error || resJson.message || 'Login failed', 'danger'); return; }
    token = resJson.data.token;
    localStorage.setItem('rw_token', token);
    localStorage.setItem('rw_user', JSON.stringify(resJson.data.user));
    toast('Welcome back! 🎉', 'success');
    setTimeout(() => window.location.href = '/dashboard', 800);
  } catch { hideLoader(); toast('Network error', 'danger'); }
}

async function handleRegister(e) {
  e?.preventDefault();
  const payload = {
    email:      document.getElementById('regEmail')?.value,
    password:   document.getElementById('regPass')?.value,
    first_name: document.getElementById('regFirst')?.value,
    last_name:  document.getElementById('regLast')?.value,
  };
  showLoader();
  try {
    const res = await fetch(`${API}/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const resJson = await res.json();
    hideLoader();
    if (!res.ok || !resJson.success) { toast(resJson.error || resJson.message || 'Registration failed', 'danger'); return; }
    toast('Account created! Please log in.', 'success');
    setTimeout(() => document.getElementById('loginTab')?.click(), 900);
  } catch { hideLoader(); toast('Network error', 'danger'); }
}

/* ── History ── */
async function loadHistory() {
  if (!isLoggedIn()) { window.location.href = '/login'; return; }
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;
  showLoader();
  try {
    const res = await fetch(`${API}/history`, { headers: authHeaders() });
    const resJson = await res.json();
    hideLoader();
    if (!res.ok || !resJson.success) { 
      console.error('[loadHistory] API Error:', resJson);
      toast('Failed to load history', 'danger'); 
      return; 
    }
    
    const records = resJson.data.history || [];
    console.log(`[loadHistory] Retrieved ${records.length} history records.`);
    
    tbody.innerHTML = records.map((p, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>${p.train_number}</td>
        <td>${p.source_station} → ${p.destination_station}</td>
        <td>${p.journey_date}</td>
        <td>${p.class_type}</td>
        <td>WL ${p.current_wl}</td>
        <td><span class="badge-${p.predicted_status.toLowerCase()}">${p.predicted_status}</span></td>
        <td class="risk-${p.risk_level.toLowerCase()}">${p.risk_level}</td>
        <td style="font-size:.82rem;color:var(--text-muted);">${new Date(p.created_at).toLocaleDateString()}</td>
      </tr>`).join('') || '<tr><td colspan="9" class="text-center py-4" style="color:var(--text-muted);">No predictions yet.</td></tr>';
  } catch (err) { 
    hideLoader(); 
    console.error('[loadHistory] Network Error:', err);
    toast('Error loading history', 'danger'); 
  }
}

/* ── Admin (Removed old stats to avoid conflicts) ── */

/* ── Profile ── */
async function loadProfile() {
  if (!isLoggedIn()) { window.location.href = '/login'; return; }
  showLoader();
  try {
    const [profRes, statsRes, actRes] = await Promise.all([
      fetch(`${API}/profile`, { headers: authHeaders() }),
      fetch(`${API}/profile/stats`, { headers: authHeaders() }),
      fetch(`${API}/profile/recent-activity`, { headers: authHeaders() })
    ]);
    const profJson = await profRes.json();
    const statsJson = await statsRes.json();
    const actJson = await actRes.json();
    hideLoader();

    if (profJson.success) {
      const p = profJson.data;
      setText('prof-fullname', p.full_name);
      setText('prof-email', p.email);
      setText('prof-role', p.role);
      setText('prof-created', p.created_at ? new Date(p.created_at).toLocaleDateString() : 'N/A');
      setText('prof-login', p.last_login ? new Date(p.last_login).toLocaleString() : 'N/A');
      
      const editFirst = document.getElementById('editFirstName');
      const editLast = document.getElementById('editLastName');
      if (editFirst) editFirst.value = p.first_name;
      if (editLast) editLast.value = p.last_name;
    }

    if (statsJson.success) {
      const s = statsJson.data;
      setText('stat-total', s.total_predictions);
      setText('stat-avg-cnf', s.avg_probability_cnf + '%');
      setText('stat-cnf', s.cnf_predictions);
      setText('stat-rac', s.rac_predictions);
      setText('stat-wl', s.wl_predictions);
    }

    if (actJson.success) {
      const acts = actJson.data.recent_activity || [];
      const actBody = document.getElementById('recentActivityBody');
      if (actBody) {
        actBody.innerHTML = acts.map(a => `
          <tr>
            <td class="fw-bold text-white">${a.train_number}</td>
            <td style="color:var(--text-muted);font-size:0.85rem;">${a.route}</td>
            <td style="color:var(--text-primary);font-size:0.85rem;">${a.journey_date}</td>
            <td><span class="badge-${a.predicted_status.toLowerCase()}">${a.predicted_status}</span></td>
            <td style="color:var(--text-muted);font-size:0.8rem;">${new Date(a.prediction_date).toLocaleDateString()}</td>
          </tr>
        `).join('') || '<tr><td colspan="5" class="text-center py-4" style="color:var(--text-muted);">No recent activity.</td></tr>';
      }
    }
  } catch (err) {
    hideLoader();
    console.error('[loadProfile] Error:', err);
    toast('Error loading profile', 'danger');
  }
}

async function handleEditProfile(e) {
  e.preventDefault();
  const first_name = document.getElementById('editFirstName').value;
  const last_name = document.getElementById('editLastName').value;
  showLoader();
  try {
    const res = await fetch(`${API}/profile/update`, {
      method: 'PUT', headers: authHeaders(), body: JSON.stringify({ first_name, last_name })
    });
    const resJson = await res.json();
    hideLoader();
    if (!res.ok || !resJson.success) { toast(resJson.error || 'Failed to update profile', 'danger'); return; }
    toast('Profile updated successfully', 'success');
    
    let user = JSON.parse(localStorage.getItem('rw_user') || '{}');
    user.first_name = first_name;
    user.last_name = last_name;
    localStorage.setItem('rw_user', JSON.stringify(user));
    
    updateNavAuth();
    loadProfile();
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
    if (modal) modal.hide();
  } catch { hideLoader(); toast('Network error', 'danger'); }
}

async function handleChangePassword(e) {
  e.preventDefault();
  const current_password = document.getElementById('currentPassword').value;
  const new_password = document.getElementById('newPassword').value;
  showLoader();
  try {
    const res = await fetch(`${API}/profile/change-password`, {
      method: 'PUT', headers: authHeaders(), body: JSON.stringify({ current_password, new_password })
    });
    const resJson = await res.json();
    hideLoader();
    if (!res.ok || !resJson.success) { toast(resJson.error || 'Failed to change password', 'danger'); return; }
    toast('Password changed successfully', 'success');
    
    document.getElementById('changePasswordForm').reset();
    const modal = bootstrap.Modal.getInstance(document.getElementById('changePasswordModal'));
    if (modal) modal.hide();
  } catch { hideLoader(); toast('Network error', 'danger'); }
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => {
  updateNavAuth();

  const themeBtn = document.getElementById('themeToggleBtn');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  const pForm = document.getElementById('predictForm');
  if (pForm) {
    loadStations();
    pForm.addEventListener('submit', submitPrediction);
  }

  const loginForm = document.getElementById('loginForm');
  if (loginForm) loginForm.addEventListener('submit', handleLogin);

  const regForm = document.getElementById('registerForm');
  if (regForm) regForm.addEventListener('submit', handleRegister);

  const editProfileForm = document.getElementById('editProfileForm');
  if (editProfileForm) editProfileForm.addEventListener('submit', handleEditProfile);

  const changePasswordForm = document.getElementById('changePasswordForm');
  if (changePasswordForm) changePasswordForm.addEventListener('submit', handleChangePassword);

  if (document.getElementById('res-status')) renderResult();
  if (document.getElementById('historyTableBody')) loadHistory();
  if (document.getElementById('prof-fullname')) loadProfile();
});
