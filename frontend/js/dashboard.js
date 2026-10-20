/* ===================================================================
   LoanWise AI — dashboard.js
=================================================================== */

function initDashboard() {
  initPageLayout("dashboard", "Dashboard");

  laAjax("GET", "/api/dashboard")
    .then(data => {
      document.getElementById("welcomeTitle").textContent = `Welcome, ${data.welcome_name} 👋`;
      const cards = data.cards || {};

      document.getElementById("statEligible").textContent = cards.eligible_loans || 0;
      document.getElementById("statRecommended").textContent = cards.recommended_loans || 0;
      document.getElementById("statActiveLoans").textContent = cards.active_loans || 0;
      document.getElementById("statNextEMI").textContent = cards.next_emi
        ? `${formatDate(cards.next_emi.due_date)}`
        : "None";

      renderNotifications(data.notifications || []);
      renderRecentActivity(data.recent_activity || []);
      renderCategoryChart(data.charts?.eligible_by_category || {});
      renderPaymentChart(data.charts?.payment_status || {});
      renderCatalogueSummary(data.charts?.eligible_by_category || {});
    })
    .catch(err => showAlert("dashAlert", err.message, "danger"));
}

function renderNotifications(notifications) {
  const el = document.getElementById("notificationsPanel");
  if (!notifications.length) {
    el.innerHTML = `<div class="empty-state small"><div class="empty-icon">🔔</div><div>No pending notifications</div></div>`;
    return;
  }
  let html = "";
  notifications.slice(0, 5).forEach(n => {
    const cls = n.type === "overdue" ? "overdue" : "upcoming";
    html += `<div class="notification-item ${cls}">
      <div class="small fw-bold">${n.type === "overdue" ? "⚠️ Overdue EMI" : "📅 Upcoming EMI"}</div>
      <div class="small">${escapeHtml(n.message)}</div>
      ${n.estimated_late_charge ? `<div class="small text-danger">Est. Late Charge: ${formatCurrency(n.estimated_late_charge)}</div>` : ""}
    </div>`;
  });
  el.innerHTML = html;
}

function renderRecentActivity(activity) {
  const el = document.getElementById("recentActivity");
  if (!activity.length) {
    el.innerHTML = `<div class="empty-state small"><div>No recent activity. <a href="eligible-loans.html">Check eligibility</a> to get started.</div></div>`;
    return;
  }
  let html = '<ul class="list-unstyled mb-0">';
  activity.forEach(a => {
    html += `<li class="py-2 border-bottom small">
      <span class="fw-bold">${escapeHtml(a.message)}</span>
      <span class="text-muted float-end">${formatDate(a.date)}</span>
    </li>`;
  });
  html += "</ul>";
  el.innerHTML = html;
}

function renderCatalogueSummary(categories) {
  const el = document.getElementById("catalogueSummary");
  if (!Object.keys(categories).length) {
    el.innerHTML = `<div class="text-muted small">No catalogue data available.</div>`;
    return;
  }
  let html = '';
  Object.entries(categories).forEach(([cat, count]) => {
    html += `<div class="dataset-status-row">
      <span class="small">${cat}</span>
      <span class="badge-manageable">${count} products</span>
    </div>`;
  });
  el.innerHTML = html;
}

let catChart = null, payChart = null;

function renderCategoryChart(data) {
  const ctx = document.getElementById("categoryChart")?.getContext("2d");
  if (!ctx) return;
  if (catChart) catChart.destroy();
  const labels = Object.keys(data);
  const values = Object.values(data);
  if (!labels.length) return;
  catChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: ["#6C4AB6","#F97316","#16A34A","#2563EB","#CA8A04","#9333EA","#0891B2"] }]
    },
    options: { plugins: { legend: { position: "bottom", labels: { font: { size: 11 } } } }, cutout: "65%" }
  });
}

function renderPaymentChart(data) {
  const ctx = document.getElementById("paymentChart")?.getContext("2d");
  if (!ctx) return;
  if (payChart) payChart.destroy();
  const colorMap = { PAID: "#16A34A", UPCOMING: "#6C4AB6", DUE: "#CA8A04", OVERDUE: "#DC2626" };
  const labels = Object.keys(data);
  const values = Object.values(data);
  if (!labels.length || values.every(v => v === 0)) {
    document.getElementById("paymentChart").parentElement.innerHTML += `<p class="text-muted small text-center mt-2">No payment data yet. <a href="active-loans.html">Create an active loan</a>.</p>`;
    return;
  }
  payChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: labels.map(l => colorMap[l] || "#ccc"), borderRadius: 6 }]
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
  });
}
