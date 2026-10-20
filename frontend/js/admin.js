/* ===================================================================
   LoanWise AI — admin.js  v2.0
   All admin page functions
=================================================================== */

/* ─── Admin Dashboard ────────────────────────────────────────── */
let adminCharts = {};

function initAdminDashboard() {
  initPageLayout("dashboard", "Admin Dashboard");
  laAjax("GET", "/api/admin/dashboard")
    .then(data => {
      document.getElementById("sTotalUsers").textContent     = data.total_users       ?? "—";
      document.getElementById("sTotalApps").textContent      = data.total_applications ?? "—";
      document.getElementById("sTotalLenders").textContent   = data.total_lenders      ?? "—";
      document.getElementById("sTotalProducts").textContent  = data.active_loan_products ?? "—";
      document.getElementById("sTotalPredictions").textContent = data.total_predictions ?? "—";
      document.getElementById("sTotalRecs").textContent      = data.total_recommendations ?? "—";
      document.getElementById("sTotalActiveLoans").textContent = data.active_loans     ?? "—";
      document.getElementById("sTotalOverdue").textContent   = data.overdue_payments   ?? "—";
      if (data.charts) {
        _drawAdminCatChart(data.charts.apps_by_category || {});
        _drawAdminLenderChart(data.charts.products_by_lender || []);
        _drawAdminPayChart(data.charts.payment_status || {});
      }
    })
    .catch(err => showAlert("adminDashAlert", err.message, "danger"));

  laAjax("GET", "/api/admin/datasets")
    .then(data => _renderAdminDatasetStatus(data))
    .catch(() => {});
}

function _renderAdminDatasetStatus(data) {
  const el = document.getElementById("adminDatasetStatus");
  if (!el) return;
  const counts = data.counts || {};
  const catalogue = data.catalogue_status || {};
  el.innerHTML = `
    <div class="dataset-status-row">
      <span class="small fw-bold">Dataset Version</span>
      <span class="badge-eligible">${data.dataset_version || "2.0"}</span>
    </div>
    <div class="dataset-status-row">
      <span class="small">Real Lenders Loaded</span>
      <span class="${catalogue.real_lenders_loaded ? 'badge-eligible' : 'badge-not-eligible'}">
        ${catalogue.real_lenders_loaded ? '✅ YES — ' + counts.lenders : '❌ NO'}
      </span>
    </div>
    <div class="dataset-status-row">
      <span class="small">Real Products Loaded</span>
      <span class="${catalogue.real_products_loaded ? 'badge-eligible' : 'badge-not-eligible'}">
        ${catalogue.real_products_loaded ? '✅ YES — ' + counts.loan_products : '❌ NO'}
      </span>
    </div>
    <div class="dataset-status-row">
      <span class="small">Users</span><span class="badge-manageable">${counts.users ?? 0}</span>
    </div>
    <div class="dataset-status-row">
      <span class="small">Applications</span><span class="badge-manageable">${counts.loan_applications ?? 0}</span>
    </div>
    <div class="dataset-status-row">
      <span class="small">Historical Loans</span><span class="badge-manageable">${counts.historical_loans ?? 0}</span>
    </div>
    <div class="dataset-status-row">
      <span class="small">Instalment Records</span><span class="badge-manageable">${counts.installment_payments ?? 0}</span>
    </div>`;
}

function _drawAdminCatChart(data) {
  const ctx = document.getElementById("adminCatChart")?.getContext("2d");
  if (!ctx || !Object.keys(data).length) return;
  if (adminCharts.cat) adminCharts.cat.destroy();
  adminCharts.cat = new Chart(ctx, {
    type: "bar",
    data: {
      labels: Object.keys(data),
      datasets: [{ data: Object.values(data), backgroundColor: "#6C4AB6", borderRadius: 6 }]
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
  });
}

function _drawAdminLenderChart(data) {
  const ctx = document.getElementById("adminLenderChart")?.getContext("2d");
  if (!ctx || !data.length) return;
  if (adminCharts.lender) adminCharts.lender.destroy();
  adminCharts.lender = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map(d => d.lender_name),
      datasets: [{ data: data.map(d => d.count), backgroundColor: "#F97316", borderRadius: 6 }]
    },
    options: { indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true } } }
  });
}

function _drawAdminPayChart(data) {
  const ctx = document.getElementById("adminPayChart")?.getContext("2d");
  if (!ctx || !Object.keys(data).length) return;
  if (adminCharts.pay) adminCharts.pay.destroy();
  const colorMap = { PAID: "#16A34A", UPCOMING: "#6C4AB6", DUE: "#CA8A04", OVERDUE: "#DC2626" };
  adminCharts.pay = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: Object.keys(data),
      datasets: [{ data: Object.values(data), backgroundColor: Object.keys(data).map(k => colorMap[k] || "#ccc") }]
    },
    options: { plugins: { legend: { position: "bottom" } }, cutout: "60%" }
  });
}

/* ─── Admin Users ────────────────────────────────────────────── */
let allUsers = [];

function initAdminUsersPage() {
  initPageLayout("admin-users", "User Management");
  laAjax("GET", "/api/admin/users")
    .then(users => {
      allUsers = users;
      _renderUsers(users);
    })
    .catch(err => showAlert("usersAlert", err.message, "danger"));
  document.getElementById("userSearch")?.addEventListener("input", function() {
    const q = this.value.toLowerCase();
    _renderUsers(allUsers.filter(u =>
      (u.full_name || "").toLowerCase().includes(q) ||
      (u.email || "").toLowerCase().includes(q)
    ));
  });
}

function _renderUsers(users) {
  const tbody = document.getElementById("usersBody");
  if (!users.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">No users found.</td></tr>`;
    return;
  }
  tbody.innerHTML = users.map(u => `
    <tr>
      <td class="fw-bold">${escapeHtml(u.full_name || "—")}</td>
      <td class="small">${escapeHtml(u.email)}</td>
      <td class="small">${escapeHtml(u.phone || "—")}</td>
      <td class="small">${escapeHtml(u.address?.city || "—")}</td>
      <td><span class="badge-manageable">${u.application_count ?? 0}</span></td>
      <td class="small">${formatDate(u.created_at)}</td>
      <td><span class="${u.status === 'inactive' ? 'badge-not-eligible' : 'badge-eligible'}">${u.status || "active"}</span></td>
      <td>
        <button class="btn btn-sm btn-la-outline" onclick="toggleUserStatus('${u._id}', '${escapeHtml(u.full_name)}')">
          ${u.status === "inactive" ? "Activate" : "Deactivate"}
        </button>
      </td>
    </tr>`).join("");
}

function toggleUserStatus(userId, name) {
  if (!confirm(`Toggle status for ${name}?`)) return;
  laAjax("PUT", `/api/admin/users/${userId}/status`)
    .then(() => { initAdminUsersPage(); showAlert("usersAlert", "User status updated.", "success"); })
    .catch(err => showAlert("usersAlert", err.message, "danger"));
}

/* ─── Admin Applications ─────────────────────────────────────── */
function initAdminApplicationsPage() {
  initPageLayout("admin-applications", "Applications");
  laAjax("GET", "/api/admin/applications")
    .then(apps => {
      const tbody = document.getElementById("adminAppsBody");
      if (!apps.length) { tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No applications.</td></tr>`; return; }
      tbody.innerHTML = apps.map(a => `<tr>
        <td class="small text-muted">${a._id.slice(-8).toUpperCase()}</td>
        <td>${escapeHtml(a.applicant_name || "—")}</td>
        <td><span class="badge-manageable">${escapeHtml(a.loan_category)}</span></td>
        <td class="fw-bold">${formatCurrency(a.loan_amount)}</td>
        <td>${a.loan_tenure} mo</td>
        <td class="small">${formatDate(a.application_date)}</td>
        <td><span class="badge-eligible">${escapeHtml(a.status || "evaluated")}</span></td>
      </tr>`).join("");
    })
    .catch(err => showAlert("adminAppsAlert", err.message, "danger"));
}

/* ─── Admin Lenders ──────────────────────────────────────────── */
let allAdminLenders = [];

function initAdminLendersPage() {
  initPageLayout("admin-lenders", "Lenders");
  loadAdminLenders();

  document.getElementById("saveLenderBtn")?.addEventListener("click", () => {
    const name = document.getElementById("newLenderName")?.value.trim();
    if (!name) { showAlert("addLenderAlert", "Lender name is required.", "warning"); return; }
    laAjax("POST", "/api/admin/lenders", {
      lender_name: name,
      lender_type: document.getElementById("newLenderType")?.value,
      official_website: document.getElementById("newLenderWebsite")?.value.trim(),
      headquarters_city: document.getElementById("newLenderCity")?.value.trim(),
      state: document.getElementById("newLenderState")?.value.trim(),
      verification_status: "Not_Publicly_Specified",
    })
    .then(() => {
      bootstrap.Modal.getInstance(document.getElementById("addLenderModal"))?.hide();
      loadAdminLenders();
      showAlert("lenderMgmtAlert", "Lender added.", "success");
    })
    .catch(err => showAlert("addLenderAlert", err.message, "danger"));
  });
}

function loadAdminLenders() {
  laAjax("GET", "/api/admin/lenders")
    .then(lenders => {
      allAdminLenders = lenders;
      const tbody = document.getElementById("adminLendersBody");
      if (!lenders.length) { tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No lenders found.</td></tr>`; return; }
      tbody.innerHTML = lenders.map(l => `<tr>
        <td class="small text-muted">${escapeHtml(l.lender_code || "—")}</td>
        <td class="fw-bold">${escapeHtml(l.lender_name)}</td>
        <td>${escapeHtml(l.lender_type || "—")}</td>
        <td class="small">${escapeHtml(l.headquarters_city || "—")}</td>
        <td class="small">${l.official_website ? `<a href="${l.official_website}" target="_blank" class="text-primary-la">↗</a>` : "—"}</td>
        <td><span class="badge-manageable">${l.product_count ?? 0}</span></td>
        <td><span class="badge-verified">${escapeHtml(l.verification_status || "—")}</span></td>
        <td><span class="${l.status === 'inactive' ? 'badge-not-eligible' : 'badge-eligible'}">${l.status || "active"}</span></td>
        <td><button class="btn btn-sm btn-la-outline text-danger" onclick="deactivateLender('${l._id}','${escapeHtml(l.lender_name)}')" ${l.status === 'inactive' ? 'disabled' : ''}>Deactivate</button></td>
      </tr>`).join("");
    })
    .catch(err => showAlert("lenderMgmtAlert", err.message, "danger"));
}

function deactivateLender(id, name) {
  if (!confirm(`Deactivate ${name} and all its products? This cannot be undone easily.`)) return;
  laAjax("DELETE", `/api/admin/lenders/${id}`)
    .then(() => { loadAdminLenders(); showAlert("lenderMgmtAlert", `${name} deactivated.`, "warning"); })
    .catch(err => showAlert("lenderMgmtAlert", err.message, "danger"));
}

/* ─── Admin Products ─────────────────────────────────────────── */
let allAdminProducts = [];

function initAdminProductsPage() {
  initPageLayout("admin-products", "Products");
  laAjax("GET", "/api/admin/products")
    .then(products => {
      allAdminProducts = products;
      _renderAdminProducts(products);
    })
    .catch(err => showAlert("prodMgmtAlert", err.message, "danger"));
  document.getElementById("prodSearch")?.addEventListener("input", _filterAdminProducts);
  document.getElementById("prodCatFilter")?.addEventListener("change", _filterAdminProducts);
  document.getElementById("prodStatusFilter")?.addEventListener("change", _filterAdminProducts);
}

function _filterAdminProducts() {
  const q = (document.getElementById("prodSearch")?.value || "").toLowerCase();
  const cat = document.getElementById("prodCatFilter")?.value || "";
  const status = document.getElementById("prodStatusFilter")?.value;
  _renderAdminProducts(allAdminProducts.filter(p =>
    (!q || (p.product_name || "").toLowerCase().includes(q) || (p.lender_name || "").toLowerCase().includes(q)) &&
    (!cat || p.loan_category === cat) &&
    (status === "" || String(p.is_active) === status)
  ));
}

function _renderAdminProducts(products) {
  const tbody = document.getElementById("adminProductsBody");
  if (!products.length) { tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">No products found.</td></tr>`; return; }
  tbody.innerHTML = products.map(p => `<tr>
    <td class="fw-bold small">${escapeHtml(p.lender_name || "—")}</td>
    <td class="small">${escapeHtml(p.product_name)}</td>
    <td><span class="badge-manageable small">${escapeHtml(p.loan_category)}</span></td>
    <td class="small">${formatCurrency(p.min_amount)} – ${formatCurrency(p.max_amount)}</td>
    <td class="small">${p.interest_rate_min}%–${p.interest_rate_max}%</td>
    <td><span class="badge-verified small">${escapeHtml(p.verification_status || "—")}</span></td>
    <td><span class="${p.is_active ? 'badge-eligible' : 'badge-not-eligible'}">${p.is_active ? "Active" : "Inactive"}</span></td>
    <td>
      ${p.is_active
        ? `<button class="btn btn-sm btn-la-outline text-danger" onclick="deactivateProduct('${p._id}','${escapeHtml(p.product_name)}')">Deactivate</button>`
        : '<span class="small text-muted">Inactive</span>'}
    </td>
  </tr>`).join("");
}

function deactivateProduct(id, name) {
  if (!confirm(`Deactivate "${name}"?`)) return;
  laAjax("DELETE", `/api/admin/products/${id}`)
    .then(() => initAdminProductsPage())
    .catch(err => showAlert("prodMgmtAlert", err.message, "danger"));
}

/* ─── Admin Predictions ──────────────────────────────────────── */
function initAdminPredictionsPage() {
  initPageLayout("admin-predictions", "Predictions & Model Performance");
  _loadModelPerformance();
  _loadPredictionRecords();
}

function switchTab(tab) {
  ["performance", "records"].forEach(t => {
    document.getElementById("tab-" + t).style.display = t === tab ? "" : "none";
  });
  document.querySelectorAll("#predsTabs .nav-link").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
}

function _loadModelPerformance() {
  const el = document.getElementById("modelPerfContent");
  if (!el) return;
  laAjax("GET", "/api/admin/model-performance")
    .then(records => {
      if (!records.length) {
        el.innerHTML = `<div class="alert alert-warning">No model performance data. Run training first: <code>python ml/train_eligibility.py && python ml/train_affordability.py</code></div>`;
        return;
      }
      el.innerHTML = records.map(r => _renderModelMetricsCard(r)).join("");
    })
    .catch(err => {
      el.innerHTML = `<div class="alert alert-info">Model performance endpoint not reachable: ${escapeHtml(err.message)}. Ensure MongoDB is running and training has been completed.</div>`;
    });
}

function _renderModelMetricsCard(r) {
  const m  = r.metrics || {};
  const cm = m.confusion_matrix || [[0,0],[0,0]];
  const fi = r.feature_importance || {};

  const fiRows = Object.entries(fi).sort((a,b) => b[1]-a[1]).slice(0,8).map(([feat, imp]) => {
    const pct = Math.round(imp * 100);
    return `<tr>
      <td class="small">${escapeHtml(feat.replace(/_enc$/,"").replace(/_/g," "))}</td>
      <td><span class="feat-bar-wrap"><span class="feat-bar" style="width:${pct}%"></span></span></td>
      <td class="small text-muted">${(imp*100).toFixed(1)}%</td>
    </tr>`;
  }).join("");

  return `<div class="model-section">
    <div class="model-section-title">${escapeHtml(r.model_name || "Model")}
      <span class="small fw-normal text-muted ms-2">v${r.model_version || "2.0"} · ${escapeHtml(r.algorithm || "")} · Trained ${escapeHtml(r.training_date || "")}</span>
    </div>
    <div class="alert alert-warning small mb-3">⚠️ ${escapeHtml(r.disclaimer || "Metrics from synthetic test data only.")}</div>

    <!-- Metrics -->
    <div class="row g-3 mb-4">
      ${[["Accuracy",  (m.accuracy||0)*100,  "% (overall correct)"],
         ["Precision", (m.precision||0)*100, "% (of predicted positives)"],
         ["Recall",    (m.recall||0)*100,    "% (of actual positives)"],
         ["F1 Score",  (m.f1_score||0)*100,  "% (harmonic mean)"],
         ["ROC-AUC",   (m.roc_auc||0)*100,   "% (discrimination)"]].map(([lbl, val, unit]) =>
        `<div class="col-6 col-md-2">
          <div class="metric-card">
            <div class="metric-val">${val.toFixed(1)}%</div>
            <div class="metric-label">${lbl}</div>
            <div class="metric-label" style="font-size:.7rem">${unit}</div>
          </div>
        </div>`).join("")}
    </div>

    <div class="row g-4">
      <!-- Confusion Matrix -->
      <div class="col-md-5">
        <div class="la-card-header mb-2">Confusion Matrix (Test Set)</div>
        <table class="cm-table w-100">
          <thead><tr><th></th><th>Predicted +</th><th>Predicted −</th></tr></thead>
          <tbody>
            <tr><td class="fw-bold">Actual +</td>
                <td class="cm-tp">TP = ${cm[1]?.[1] ?? "—"}</td>
                <td class="cm-fn">FN = ${cm[1]?.[0] ?? "—"}</td></tr>
            <tr><td class="fw-bold">Actual −</td>
                <td class="cm-fp">FP = ${cm[0]?.[1] ?? "—"}</td>
                <td class="cm-tn">TN = ${cm[0]?.[0] ?? "—"}</td></tr>
          </tbody>
        </table>
        <div class="small text-muted mt-2">TP=True Pos  TN=True Neg  FP=False Pos  FN=False Neg</div>
      </div>

      <!-- Feature Importance -->
      ${fiRows ? `<div class="col-md-7">
        <div class="la-card-header mb-2">Feature Importance / Coefficient Strength</div>
        <table class="w-100">
          <tbody>${fiRows}</tbody>
        </table>
      </div>` : ""}
    </div>

    <div class="mt-3 small text-muted">
      Dataset: ${escapeHtml(r.dataset_name || "")} &nbsp;|&nbsp;
      Train: ${r.training_records ?? "—"} records &nbsp;|&nbsp;
      Test: ${r.testing_records ?? "—"} records &nbsp;|&nbsp;
      Features: ${(r.features || []).length}
    </div>
  </div>`;
}

function _loadPredictionRecords() {
  laAjax("GET", "/api/admin/predictions")
    .then(preds => {
      const tbody = document.getElementById("predsBody");
      if (!preds || !tbody) return;
      if (!preds.length) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No predictions yet.</td></tr>`;
        return;
      }
      tbody.innerHTML = preds.map(p => `<tr>
        <td class="small text-muted">${(p.application_id||"").slice(-8).toUpperCase()}</td>
        <td><span class="${(p.model_1?.result||"") === 'Eligible' ? 'badge-eligible' : 'badge-not-eligible'}">${p.model_1?.result || "—"}</span></td>
        <td class="small">${p.model_1?.probability != null ? Math.round(p.model_1.probability * 100) + "%" : "—"}</td>
        <td><span class="${(p.model_2?.result||"") === 'Manageable' ? 'badge-manageable' : 'badge-not-manageable'}">${p.model_2?.result || "—"}</span></td>
        <td class="small">${p.model_2?.probability != null ? Math.round(p.model_2.probability * 100) + "%" : "—"}</td>
        <td class="small">${p.eligible_count ?? 0}</td>
        <td class="small">${p.recommended_count ?? 0}</td>
        <td class="small">${escapeHtml(p.model_version || "—")}</td>
        <td class="small">${formatDate(p.created_at)}</td>
      </tr>`).join("");
    })
    .catch(() => {});
}

/* ─── Admin Recommendations ──────────────────────────────────── */
function initAdminRecommendationsPage() {
  initPageLayout("admin-recommendations", "Recommendations");
  laAjax("GET", "/api/admin/recommendations")
    .then(recs => {
      const tbody = document.getElementById("recsAdminBody");
      if (!recs.length) { tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No recommendations yet.</td></tr>`; return; }
      tbody.innerHTML = recs.map(r => `<tr>
        <td class="small text-muted">${r.application_id?.slice(-8).toUpperCase() || "—"}</td>
        <td class="small text-muted">${r.product_id?.slice(-8).toUpperCase() || "—"}</td>
        <td><span class="badge-eligible">${r.eligibility_result || "—"}</span></td>
        <td><span class="badge-manageable">${r.affordability_result || "—"}</span></td>
        <td>${r.match_score ?? "—"}%</td>
        <td>${r.recommended_emi ? formatCurrency(r.recommended_emi) : "—"}</td>
        <td class="small">${formatDate(r.created_at)}</td>
      </tr>`).join("");
    })
    .catch(err => showAlert("recsAdminAlert", err.message, "danger"));
}

/* ─── Admin Active Loans ─────────────────────────────────────── */
function initAdminActiveLoansPage() {
  initPageLayout("admin-active-loans", "Active Loans");
  laAjax("GET", "/api/admin/active-loans")
    .then(loans => {
      const tbody = document.getElementById("adminActiveLoansBody");
      if (!loans.length) { tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No active loans.</td></tr>`; return; }
      tbody.innerHTML = loans.map(l => `<tr>
        <td>${escapeHtml(l.applicant_name || "—")}</td>
        <td class="small">${escapeHtml(l.product_name || "—")}</td>
        <td class="small">${escapeHtml(l.lender_name || "—")}</td>
        <td class="fw-bold">${formatCurrency(l.actual_amount)}</td>
        <td>${formatCurrency(l.emi_amount)}</td>
        <td>${l.interest_rate}%</td>
        <td>${l.tenure_months} mo</td>
        <td><span class="${l.status === 'active' ? 'badge-eligible' : 'badge bg-secondary text-white'}">${l.status}</span></td>
        <td class="small">${formatDate(l.start_date)}</td>
      </tr>`).join("");
    })
    .catch(err => showAlert("adminActiveLoansAlert", err.message, "danger"));
}

/* ─── Admin Payments ─────────────────────────────────────────── */
function initAdminPaymentsPage() {
  initPageLayout("admin-payments", "Payments");
  laAjax("GET", "/api/admin/payments")
    .then(payments => {
      const tbody = document.getElementById("adminPaymentsBody");
      if (!payments.length) { tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No payments found.</td></tr>`; return; }
      tbody.innerHTML = payments.map(p => `<tr>
        <td class="small text-muted">${p.active_loan_id?.slice(-8).toUpperCase() || "—"}</td>
        <td>${p.emi_number}</td>
        <td class="small">${formatDate(p.due_date)}</td>
        <td class="fw-bold">${formatCurrency(p.amount_due)}</td>
        <td>${p.amount_paid > 0 ? formatCurrency(p.amount_paid) : "—"}</td>
        <td>${statusBadgeHtml(p.payment_status)}</td>
        <td class="small">${p.payment_date ? formatDate(p.payment_date) : "—"}</td>
        <td class="small">${p.days_overdue > 0 ? `<span class="text-danger">${p.days_overdue}</span>` : "—"}</td>
        <td class="small">${p.late_charge > 0 ? `<span class="text-danger">${formatCurrency(p.late_charge)}</span>` : "—"}</td>
      </tr>`).join("");
    })
    .catch(err => showAlert("adminPaymentsAlert", err.message, "danger"));
}

/* ─── Admin Datasets ─────────────────────────────────────────── */
function initAdminDatasetsPage() {
  initPageLayout("admin-datasets", "Datasets");
  laAjax("GET", "/api/admin/datasets")
    .then(data => _renderDatasetsPage(data))
    .catch(err => showAlert("datasetsAlert", err.message, "danger"));

  laAjax("GET", "/api/admin/lender-stats")
    .then(stats => {
      document.getElementById("lenderProductCounts").innerHTML = stats.map(s =>
        `<tr><td class="fw-bold">${escapeHtml(s.lender_name)}</td><td><span class="badge-manageable">${s.product_count}</span></td></tr>`
      ).join("");
    }).catch(() => {});

  laAjax("GET", "/api/admin/category-stats")
    .then(stats => {
      document.getElementById("categoryProductCounts").innerHTML = stats.map(s =>
        `<tr><td class="fw-bold">${escapeHtml(s.category)}</td><td>${s.product_count}</td><td>${s.lender_count}</td></tr>`
      ).join("");
    }).catch(() => {});
}

function _renderDatasetsPage(data) {
  const counts = data.counts || {};
  const versionCards = document.getElementById("datasetVersionCards");
  if (versionCards) {
    versionCards.innerHTML = `
      <div class="col-6 col-md-3"><div class="la-stat-card text-center"><div class="stat-value">${data.dataset_version || "2.0"}</div><div class="stat-label">Dataset Version</div></div></div>
      <div class="col-6 col-md-3"><div class="la-stat-card orange text-center"><div class="stat-value">${data.product_catalogue_version || "—"}</div><div class="stat-label">Catalogue Version</div></div></div>
      <div class="col-6 col-md-3"><div class="la-stat-card green text-center"><div class="stat-value">${data.updated_at || "—"}</div><div class="stat-label">Last Updated</div></div></div>
      <div class="col-6 col-md-3"><div class="la-stat-card navy text-center"><div class="stat-value">${counts.loan_products || 0}</div><div class="stat-label">Active Products</div></div></div>`;
  }

  const collEl = document.getElementById("collectionCounts");
  if (collEl) {
    const rows = [
      ["Users", counts.users], ["Applications", counts.loan_applications],
      ["Lenders", counts.lenders], ["Loan Products", counts.loan_products],
      ["Predictions", counts.predictions], ["Recommendations", counts.recommendations],
      ["Active Loans", counts.active_loans], ["Payments", counts.payments],
      ["Historical Loans", counts.historical_loans], ["Instalment Payments", counts.installment_payments],
      ["Notifications", counts.notifications], ["Documents", counts.documents],
      ["Feedback", counts.feedback],
    ];
    collEl.innerHTML = rows.map(([label, val]) =>
      `<div class="dataset-status-row"><span class="small">${label}</span><span class="badge-manageable">${val ?? 0}</span></div>`
    ).join("");
  }

  const catEl = document.getElementById("catalogueStatus");
  if (catEl) {
    const cs = data.catalogue_status || {};
    catEl.innerHTML = `
      <div class="dataset-status-row">
        <span class="small">Real Lenders Loaded</span>
        <span class="${cs.real_lenders_loaded ? 'badge-eligible' : 'badge-not-eligible'}">${cs.real_lenders_loaded ? 'YES ✅' : 'NO ❌'}</span>
      </div>
      <div class="dataset-status-row">
        <span class="small">Real Products Loaded</span>
        <span class="${cs.real_products_loaded ? 'badge-eligible' : 'badge-not-eligible'}">${cs.real_products_loaded ? 'YES ✅' : 'NO ❌'}</span>
      </div>
      <div class="dataset-status-row">
        <span class="small">Historical Data Loaded</span>
        <span class="${cs.historical_data_loaded ? 'badge-eligible' : 'badge-manageable'}">${cs.historical_data_loaded ? 'YES ✅' : 'NOT YET (optional)'}</span>
      </div>
      <div class="mt-3 small text-muted">Borrower dataset: ${data.borrower_dataset_version || "—"}<br>Historical dataset: ${data.historical_dataset_version || "—"}</div>`;
  }
}

/* ─── Admin Data Quality ─────────────────────────────────────── */
function initAdminDataQualityPage() {
  initPageLayout("admin-data-quality", "Data Quality");
  document.getElementById("runDqBtn")?.addEventListener("click", runDataQualityCheck);
}

function runDataQualityCheck() {
  const btn = document.getElementById("runDqBtn");
  btn.disabled = true;
  btn.textContent = "Running...";

  laAjax("GET", "/api/admin/data-quality")
    .then(result => {
      const statusClass = result.status === "PASS" ? "alert-success" : "alert-danger";
      let html = `
        <div class="alert ${statusClass} mb-4">
          <strong>Status: ${result.status}</strong> — Checked at ${result.checked_at}
        </div>
        <div class="row g-3 mb-4">
          <div class="col-md-3"><div class="la-stat-card text-center"><div class="stat-value">${result.total_products}</div><div class="stat-label">Total Products</div></div></div>
          <div class="col-md-3"><div class="la-stat-card green text-center"><div class="stat-value">${result.active_products}</div><div class="stat-label">Active Products</div></div></div>
          <div class="col-md-3"><div class="la-stat-card orange text-center"><div class="stat-value">${result.total_lenders}</div><div class="stat-label">Lenders</div></div></div>
          <div class="col-md-3"><div class="la-stat-card ${result.errors?.length ? 'red' : 'green'} text-center"><div class="stat-value">${result.errors?.length || 0}</div><div class="stat-label">Errors</div></div></div>
        </div>`;

      if (result.errors?.length) {
        html += `<div class="la-card mb-3"><div class="la-card-header text-danger">❌ Errors (${result.errors.length})</div>`;
        result.errors.forEach(e => { html += `<div class="alert alert-danger py-2 mb-2 small">⚠️ ${escapeHtml(e)}</div>`; });
        html += `</div>`;
      }
      if (result.warnings?.length) {
        html += `<div class="la-card mb-3"><div class="la-card-header text-warning">⚠️ Warnings (${result.warnings.length})</div>`;
        result.warnings.forEach(w => { html += `<div class="alert alert-warning py-2 mb-2 small">⚠️ ${escapeHtml(w)}</div>`; });
        html += `</div>`;
      }
      if (!result.errors?.length && !result.warnings?.length) {
        html += `<div class="alert alert-success">✅ No errors or warnings found. Catalogue data is valid.</div>`;
      }
      document.getElementById("dqContent").innerHTML = html;
    })
    .catch(err => showAlert("dqAlert", err.message, "danger"))
    .finally(() => { btn.disabled = false; btn.textContent = "🔄 Run Quality Check"; });
}

/* ─── Admin Feedback ─────────────────────────────────────────── */
function initAdminFeedbackPage() {
  initPageLayout("admin-feedback", "Feedback");
  laAjax("GET", "/api/admin/feedback")
    .then(items => {
      const tbody = document.getElementById("adminFbBody");
      if (!items.length) { tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No feedback yet.</td></tr>`; return; }
      tbody.innerHTML = items.map(f => `<tr>
        <td>${escapeHtml(f.user_name || "—")}</td>
        <td>${"⭐".repeat(f.rating || 1)}</td>
        <td><span class="badge-manageable">${escapeHtml(f.category || "General")}</span></td>
        <td class="small">${escapeHtml(f.comments || "—")}</td>
        <td class="small">${formatDate(f.created_at)}</td>
      </tr>`).join("");
    })
    .catch(err => showAlert("adminFbAlert", err.message, "danger"));
}
