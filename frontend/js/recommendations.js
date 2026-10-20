/* ===================================================================
   LoanWise AI — recommendations.js
=================================================================== */

function initRecommendedLoansPage() {
  initPageLayout("recommended-loans", "Recommended Loans");

  const savedAppId = sessionStorage.getItem("lw_last_app_id");
  if (savedAppId) {
    loadRecommendationsForApp(savedAppId);
  } else {
    loadAllRecommendations();
  }
}

function loadRecommendationsForApp(appId) {
  document.getElementById("recContent").innerHTML = `<div class="text-center py-4"><span class="spinner-border spinner-la"></span></div>`;
  laAjax("GET", `/api/applications/${appId}`)
    .then(response => renderRecommendations(response))
    .catch(() => loadAllRecommendations());
}

function loadAllRecommendations() {
  laAjax("GET", "/api/recommendations")
    .then(recs => {
      if (!recs.length) {
        document.getElementById("recContent").innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">⭐</div>
            <div class="empty-msg">No recommendations yet.</div>
            <div class="empty-sub">Run an eligibility check first to generate recommendations.</div>
            <a href="eligible-loans.html" class="btn btn-la-primary mt-3">Check Eligibility</a>
          </div>`;
        return;
      }
      let html = `<div class="alert alert-info small mb-4">Showing recommendations from all your past applications. <a href="eligible-loans.html">Run a new check</a> for updated results.</div>`;
      html += `<div class="row">`;
      recs.forEach(rec => {
        if (!rec.product) return;
        html += renderRecCard(rec);
      });
      html += `</div>`;
      document.getElementById("recContent").innerHTML = html;
      bindRecButtons();
    })
    .catch(err => showAlert("recAlert", err.message, "danger"));
}

function renderRecommendations(response) {
  const recs = response.recommended_products || [];
  const m1 = response.model_1 || {};
  const m2 = response.model_2 || {};

  let html = `
    <div class="la-card mb-4">
      <div class="row g-3">
        <div class="col-md-6">
          <div class="model-explanation">
            <div class="model-title">Model 1 — Eligibility Assessment</div>
            <div class="model-result ${m1.result === 'Eligible' ? 'text-success' : 'text-danger'}">${m1.result || '—'}</div>
            <div class="small text-muted mt-1">Probability: ${Math.round((m1.probability || 0) * 100)}%</div>
            <div class="mt-1"><span class="factor-tag">Income</span><span class="factor-tag">CIBIL</span><span class="factor-tag">Existing Loans</span><span class="factor-tag">Requested Amount</span></div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="model-explanation">
            <div class="model-title">Model 2 — Affordability Assessment</div>
            <div class="model-result ${m2.result === 'Manageable' ? 'text-success' : 'text-danger'}">${m2.result || '—'}</div>
            <div class="small text-muted mt-1">Probability: ${Math.round((m2.probability || 0) * 100)}%</div>
            <div class="mt-1"><span class="factor-tag">Monthly Income</span><span class="factor-tag">Existing EMI</span><span class="factor-tag">Debt</span><span class="factor-tag">Payment History</span></div>
          </div>
        </div>
      </div>
      <div class="mt-3 d-flex gap-3 align-items-center">
        <div><span class="fw-bold">${response.eligible_count}</span> <span class="text-muted">Eligible Products</span></div>
        <div>→</div>
        <div><span class="fw-bold text-accent-la">${response.recommended_count}</span> <span class="text-muted">Recommended (Eligible + Manageable)</span></div>
      </div>
    </div>`;

  if (!recs.length) {
    html += `<div class="empty-state"><div class="empty-icon">⭐</div><div class="empty-msg">No recommended products for this profile.</div><div class="empty-sub">This may be because the requested EMI appears too high relative to income, or existing obligations are significant. <a href="profile.html">Update your profile</a> and try again.</div></div>`;
  } else {
    html += `<div class="row">`;
    recs.forEach(product => {
      html += renderProductRecCard(product);
    });
    html += `</div>`;
  }

  document.getElementById("recContent").innerHTML = html;
  bindRecButtons();
}

function renderProductRecCard(product) {
  const m2Badge = product.affordability_result === "Manageable"
    ? `<span class="badge-manageable">Manageable ✓</span>`
    : `<span class="badge-not-manageable">Not Manageable</span>`;
  const matchScore = product.match_score || 0;
  const reason = product.recommendation_reason || "";

  return `<div class="col-md-6 col-xl-4 mb-3">
    <div class="loan-product-card h-100 d-flex flex-column">
      <div class="lender-badge">🏦 ${escapeHtml(product.lender_name)}</div>
      <div class="product-name">${escapeHtml(product.product_name)}</div>
      <div class="mb-2">
        <span class="badge-eligible me-1">Potentially Eligible ✓</span>
        ${m2Badge}
      </div>
      <div class="small text-muted mb-1">Rate: ${product.interest_rate_min}%–${product.interest_rate_max}%</div>
      <div class="small text-muted mb-1">Amount: ${formatCurrency(product.min_amount)} – ${formatCurrency(product.max_amount)}</div>
      ${product.estimated_emi ? `<div class="emi-highlight mt-1">Est. EMI: ${formatCurrency(product.estimated_emi)}/mo</div>` : ""}
      <div class="mt-2">
        <div class="match-score-label">AI Match Score: ${matchScore}%</div>
        <div class="match-score-bar"><div class="match-score-fill" style="width:${matchScore}%"></div></div>
      </div>
      ${reason ? `<div class="model-explanation mt-2"><div class="model-title">Model-Based Explanation</div><div class="small">${escapeHtml(reason)}</div></div>` : ""}
      <div class="source-tag">✅ Verified • ${escapeHtml(product.source_date || "")} • <a href="${product.official_product_url || '#'}" target="_blank">Official Source ↗</a></div>
      <div class="mt-auto pt-2 d-flex gap-2">
        <button class="btn btn-sm btn-la-primary view-rec-btn" data-id="${product._id}">View Details</button>
        <button class="btn btn-sm btn-la-accent add-compare-btn" data-id="${product._id}" data-name="${escapeHtml(product.product_name)}">Compare</button>
      </div>
    </div>
  </div>`;
}

function renderRecCard(rec) {
  const p = rec.product || {};
  return `<div class="col-md-6 col-xl-4 mb-3">
    <div class="loan-product-card h-100 d-flex flex-column">
      <div class="lender-badge">🏦 ${escapeHtml(p.lender_name || "—")}</div>
      <div class="product-name">${escapeHtml(p.product_name || "—")}</div>
      <div class="mb-1"><span class="badge-eligible">Eligible ✓</span> <span class="badge-manageable">Manageable ✓</span></div>
      ${p.interest_rate_min ? `<div class="small text-muted">Rate: ${p.interest_rate_min}%–${p.interest_rate_max}%</div>` : ""}
      ${rec.recommended_emi ? `<div class="emi-highlight mt-1">Est. EMI: ${formatCurrency(rec.recommended_emi)}/mo</div>` : ""}
      ${rec.reason ? `<div class="model-explanation mt-2"><div class="model-title">Explanation</div><div class="small">${escapeHtml(rec.reason)}</div></div>` : ""}
      <div class="mt-auto pt-2">
        <button class="btn btn-sm btn-la-primary view-rec-btn" data-id="${p._id}">View Details</button>
      </div>
    </div>
  </div>`;
}

function bindRecButtons() {
  document.querySelectorAll(".view-rec-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      window.location.href = `loan-details.html?product_id=${btn.dataset.id}`;
    });
  });
  document.querySelectorAll(".add-compare-btn").forEach(btn => {
    btn.addEventListener("click", () => addToCompare(btn.dataset.id, btn.dataset.name));
  });
}

function addToCompare(id, name) {
  let list = JSON.parse(localStorage.getItem("lw_compare") || "[]");
  if (list.length >= 4) { alert("Up to 4 products can be compared. Remove one first."); return; }
  if (!list.find(p => p.id === id)) {
    list.push({ id, name });
    localStorage.setItem("lw_compare", JSON.stringify(list));
  }
  if (confirm(`"${name}" added. Go to Compare page now?`)) window.location.href = "compare-loans.html";
}
