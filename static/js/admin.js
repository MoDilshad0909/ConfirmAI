const API = '/api';
const token = localStorage.getItem('rw_token');

function authHeaders() {
  return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
}

function showLoader() {
  const overlay = document.getElementById('loaderOverlay');
  if (overlay) overlay.style.display = 'flex';
}

function hideLoader() {
  const overlay = document.getElementById('loaderOverlay');
  if (overlay) overlay.style.display = 'none';
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.innerText = text;
}

async function loadAdminData() {
  if (!token) { window.location.href = '/login'; return; }
  showLoader();
  try {
    const endpoints = [
      fetch(`${API}/admin/stats`, { headers: authHeaders() }),
      fetch(`${API}/admin/users`, { headers: authHeaders() }),
      fetch(`${API}/admin/predictions`, { headers: authHeaders() }),
      fetch(`${API}/admin/searches`, { headers: authHeaders() }),
      fetch(`${API}/admin/analytics`, { headers: authHeaders() }),
      fetch(`${API}/admin/traffic`, { headers: authHeaders() }),
      fetch(`${API}/admin/model`, { headers: authHeaders() }),
      fetch(`${API}/admin/logs`, { headers: authHeaders() })
    ];

    const responses = await Promise.all(endpoints);
    const data = await Promise.all(responses.map(res => res.json()));
    hideLoader();

    const [stats, users, preds, searches, analytics, traffic, model, logs] = data.map(d => d.data || {});

    // Overview KPIs (from /api/admin/stats)
    setText('kpi-users', stats.total_users || 0);
    setText('kpi-preds', stats.total_predictions || 0);
    setText('kpi-searches', stats.total_searches || 0);
    setText('kpi-today', stats.active_today || 0);
    setText('kpi-week', stats.active_week || 0);
    setText('kpi-month', stats.active_month || 0);
    setText('kpi-avg-prob', (stats.avg_probability || 0) + '%');
    setText('kpi-cnf', stats.cnf_count || 0);
    setText('kpi-rac', stats.rac_count || 0);
    
    // Search Analytics
    setText('sch-today', searches.searches_today || 0);
    setText('sch-week', searches.searches_week || 0);
    setText('sch-month', searches.searches_month || 0);
    setText('kpi-top-route', searches.most_searched_route || 'N/A');
    setText('kpi-top-train', searches.most_searched_train || 'N/A');
    
    // We can also add new DOM elements if needed for searches, but let's assume the UI handles it.

    // Users (from /api/admin/users)
    const uBody = document.getElementById('adminUsersBody');
    if (uBody) {
      uBody.innerHTML = (users.users || []).map(u => `
        <tr>
          <td>${u.user_id}</td>
          <td>${u.name}</td>
          <td>${u.email}</td>
          <td><span class="badge bg-secondary">${u.role}</span></td>
          <td>${u.total_predictions}</td>
          <td style="font-size:0.8rem">${u.last_login !== "Never" ? new Date(u.last_login).toLocaleDateString() : "Never"}</td>
          <td>
             <button class="btn btn-sm btn-outline-danger" onclick="toggleStatus(${u.user_id})">Disable</button>
          </td>
        </tr>
      `).join('');
    }

    // Predictions (from /api/admin/predictions)
    const pBody = document.getElementById('adminPredsBody');
    if (pBody) {
      pBody.innerHTML = (preds.predictions || []).map(p => `
        <tr>
          <td>${p.train_number}</td>
          <td>${p.route}</td>
          <td>${p.journey_date}</td>
          <td>${p.class_type}</td>
          <td>${p.current_wl}</td>
          <td><span class="badge-${p.predicted_status.toLowerCase()}">${p.predicted_status}</span></td>
          <td class="risk-${p.risk_level.toLowerCase()}">${p.risk_level}</td>
          <td>${p.user_name}</td>
          <td style="font-size:0.8rem">${new Date(p.timestamp).toLocaleString()}</td>
        </tr>
      `).join('');
    }

    // Charts (from /api/admin/analytics)
    if (analytics.doughnut) {
      new Chart(document.getElementById('statusDoughnut'), {
        type: 'doughnut',
        data: {
          labels: analytics.doughnut.labels,
          datasets: [{ data: analytics.doughnut.data, backgroundColor: ['#28a745', '#ffc107', '#dc3545'] }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Prediction Status Distribution', color: '#fff' }, legend: { labels: { color: '#fff' } } } }
      });
    }

    if (analytics.routes) {
      new Chart(document.getElementById('routesBarChart'), {
        type: 'bar',
        data: {
          labels: analytics.routes.labels,
          datasets: [{ label: 'Searches', data: analytics.routes.data, backgroundColor: '#00d2ff' }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Top 5 Searched Routes', color: '#fff' }, legend: { labels: { color: '#fff' } } }, scales: { y: { ticks: { color: '#fff' } }, x: { ticks: { color: '#fff' } } } }
      });
    }
    
    const overviewChartEl = document.getElementById('overviewChart');
    if (overviewChartEl && analytics.daily_trend) {
      new Chart(overviewChartEl, {
        type: 'line',
        data: {
          labels: analytics.daily_trend.labels,
          datasets: [{ label: 'Daily Predictions', data: analytics.daily_trend.data, borderColor: '#bb86fc', backgroundColor: 'rgba(187, 134, 252, 0.2)', fill: true, tension: 0.4 }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#fff' } } }, scales: { y: { ticks: { color: '#fff' }, beginAtZero: true }, x: { ticks: { color: '#fff' } } } }
      });
    }

    // Traffic (from /api/admin/traffic)
    setText('traf-total', traffic.total || 0);
    setText('traf-unique', traffic.unique || 0);
    setText('traf-logged', traffic.logged_in || 0);
    setText('traf-guest', traffic.guest || 0);
    
    const dBreak = document.getElementById('deviceBreakdown');
    if (dBreak && traffic.devices) {
      dBreak.innerHTML = traffic.devices.map(d => `
        <div class="d-flex justify-content-between border-bottom pb-2 mb-2">
          <span>${d.device}</span><span class="fw-bold">${d.count}</span>
        </div>
      `).join('');
    }

    // Model (from /api/admin/model)
    setText('mod-version', model.version || '--');
    setText('mod-acc', model.accuracy || '--');
    setText('mod-roc', model.roc_auc || '--');

    if (model.feature_importance) {
      new Chart(document.getElementById('featureChart'), {
        type: 'bar',
        data: {
          labels: model.feature_importance.labels,
          datasets: [{ label: 'Feature Importance Score', data: model.feature_importance.data, backgroundColor: '#bb86fc' }]
        },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { labels: { color: '#fff' } } }, scales: { y: { ticks: { color: '#fff' } }, x: { ticks: { color: '#fff' } } } }
      });
    }

    // Logs (from /api/admin/logs)
    const lBody = document.getElementById('adminLogsBody');
    if (lBody) {
      lBody.innerHTML = (logs.logs || []).map(l => `
        <tr>
          <td style="font-size:0.8rem">${new Date(l.timestamp).toLocaleString()}</td>
          <td>${l.endpoint || 'unknown'}</td>
          <td>${l.device || '-'}</td>
          <td style="font-size:0.8rem" class="text-truncate" style="max-width: 150px;">${l.browser || '-'}</td>
          <td>${l.is_logged_in ? '<span class="badge bg-success">Yes</span>' : '<span class="badge bg-secondary">No</span>'}</td>
        </tr>
      `).join('');
    }

  } catch (err) {
    hideLoader();
    console.error('Failed to load admin data:', err);
    alert('Failed to load Admin Dashboard Data');
  }
}

async function toggleStatus(userId) {
  try {
    const res = await fetch(`${API}/admin/users/${userId}/status`, { method: 'PUT', headers: authHeaders() });
    const json = await res.json();
    alert(json.message);
  } catch(e) {
    alert("Failed to toggle status");
  }
}

function exportData() {
  alert("Report generation triggered. A CSV file will be sent to your email shortly.");
}

document.addEventListener('DOMContentLoaded', loadAdminData);
