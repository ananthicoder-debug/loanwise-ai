/* ===================================================================
   LoanWise AI — loans.js v2.0
   Handles: Eligible Loans, Loan Search, Loan Categories
=================================================================== */

let lastApplicationId = null;

/* ─── Eligible Loans Page ────────────────────────────────────── */
function initEligibleLoansPage() {
  initPageLayout("eligible-loans", "Eligible Loans");

  // Pre-fill category from query string
  const cat = getQueryParam("category");
  if (cat) document.getElementById("loanCategory").value = cat;

  document.getElementById("eligibilityForm")?.addEventListener("submit", function(e) {
    e.preventDefault();
    submitLoanApplication();
  });

  // Restore last session result
  const savedAppId = sessionStorage.getItem("lw_last_app_id");
  if (savedAppId) {
    lastApplicationId = savedAppId;
    loadApplicationResults(savedAppId);
  }
}

function submitLoanApplication() {
  const loan_amount = parseFloat(document.getElementById("loanAmount").value);
  const loan_tenure = parseInt(document.getElementById("loanTenure").value);
  const loan_category = document.getElementById("loanCategory").value;
  const purpose = document.getElementById("loanPurpose")?.value.trim() || "";

  if (!loan_category) { showAlert("eligibilityAlert", "Please select a loan category.", "warning"); return; }
  if (!loan_amount || loan_amount < 1000) { showAlert("eligibilityAlert", "Enter a valid loan amount (minimum ₹1,000).", "warning"); return; }
  if (!loan_tenure || loan_tenure < 1) { showAlert("eligibilityAlert", "Enter a valid tenure in months.", "warning"); return; }

  const btn = document.getElementById("checkEligibilityBtn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Checking...';
  document.getElementById("resultsArea").innerHTML = "";

  laAjax("POST", "/api/applications", { loan_amount, loan_tenure, loan_category, purpose })
    .then(response => {
      lastApplicationId = response.application_id;
      sessionStorage.setItem("lw_last_app_id", response.application_id);
      renderEvaluationResponse(response);
    })
    .catch(err => showAlert("eligibilityAlert", err.message, "danger"))
    .finally(() => {
      btn.disabled = false;
      btn.textContent = "✅ Check My Eligibility";
    });
}

function loadApplicationResults(applicationId) {
  laAjax("GET", `/api/applications/${applicationId}`)
    .then(renderEvaluationResponse)
    .catch(() => {});
}

function renderEvaluationResponse(response) {
  const m1 = response.model_1 || {};
  const m1Class = m1.result === "Eligible" ? "badge-eligible" : "badge-not-eligible";

  const summaryHtml = `
    <div class="la-card mb-4">
      <div class="row align-items-center">
        <div class="col-md-8">
          <h5 class="fw-bold mb-2">You may match criteria for <span class="text-accent-la">${response.eligible_count}</span> loan product(s)</h5>
          <div class="d-flex flex-wrap gap-3">
            <div class="model-explanation flex-fill">
              <div class="model-title">Model 1 — Eligibility Assessment</div>
              <span class="${m1Class} model-result">${m1.result || "—"}</span>
              <span class="ms-2 small text-muted">Probability: ${Math.round((m1.probability || 0) * 100)}%</span>
              <div class="mt-1">
                <span class="factor-tag">Income</span><span class="factor-tag">CIBIL</span>
                <span class="factor-tag">Existing EMI</span><span class="factor-tag">Loan Amount</span>
              </div>
            </div>
          </div>
          <p class="small text-muted mt-2 mb-0">⚠️ This is an AI-assisted estimate. Not a guaranteed loan approval from any lender.</p>
        </div>
        <div class="col-md-4 text-md-end mt-3 mt-md-0">
          <a href="recommended-loans.html" class="btn btn-la-accent">⭐ View ${response.recommended_count} Recommended</a>
          <a href="assessment-report.html?application_id=${response.application_id}" class="btn btn-la-outline ms-1 mt-1">📊 Full Report</a>
        </div>
      </div>
    </div>
    ${renderEligibleGroups(response.eligible_products || {})}`;

  document.getElementById("resultsArea").innerHTML = summaryHtml;
  bindProductButtons();
}

function renderEligibleGroups(grouped) {
  const categories = Object.keys(grouped);
  if (!categories.length) {
    return `<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-msg">No products found in the catalogue for this category.</div><div class="empty-sub">The administrator may need to add products, or the catalogue may not be loaded.</div></div>`;
  }

  let html = "";
  // Summary counts per category
  html += `<div class="la-card mb-3"><div class="row g-2">`;
  categories.forEach(cat => {
    html += `<div class="col-6 col-md-3"><div class="text-center p-2 bg-light rounded"><div class="fw-bold text-primary-la">${grouped[cat].count}</div><div class="small text-muted">${cat}</div></div></div>`;
  });
  html += `</div></div>`;

  // Full hierarchy
  categories.forEach(cat => {
    const catData = grouped[cat];
    html += `<div class="category-heading">📂 ${escapeHtml(cat)} — ${catData.count} offer(s)</div>`;
    Object.keys(catData.lenders).forEach(lenderName => {
      const lenderData = catData.lenders[lenderName];
      html += `<div class="lender-heading">🏦 ${escapeHtml(lenderName)} — ${lenderData.count} product(s)</div>`;
      html += `<div class="row">`;
      lenderData.products.forEach(p => { html += renderProductCard(p, true); });
      html += `</div>`;
    });
  });
  return html;
}

function bindProductButtons() {
  $(".view-details-btn").off("click").on("click", function() {
    window.location.href = `loan-details.html?product_id=${$(this).data("id")}&application_id=${lastApplicationId || ""}`;
  });
  $(".add-compare-btn").off("click").on("click", function() {
    addToCompare($(this).data("id"), $(this).data("name"));
  });
}

/* ─── Compare shortlist (localStorage) ─────────────────────── */
function addToCompare(productId, productName) {
  let list = JSON.parse(localStorage.getItem("lw_compare") || "[]");
  if (list.length >= 4) { alert("You can compare up to 4 products. Remove one first."); return; }
  if (!list.find(p => p.id === productId)) {
    list.push({ id: productId, name: productName });
    localStorage.setItem("lw_compare", JSON.stringify(list));
  }
  if (confirm(`"${productName}" added to compare list (${list.length}/4). Go to Compare page now?`)) {
    window.location.href = "compare-loans.html";
  }
}

/* ─── Loan Search Page ───────────────────────────────────────── */
function initLoanSearchPage() {
  initPageLayout("loan-search", "Search Loans");

  // Pre-fill from query string
  const q = getQueryParam("q") || getQueryParam("category") || getQueryParam("lender") || "";
  if (q) {
    document.getElementById("searchInput").value = q;
    runSearch(q);
  }

  document.getElementById("searchForm")?.addEventListener("submit", function(e) {
    e.preventDefault();
    runSearch(document.getElementById("searchInput").value.trim());
  });

  document.querySelectorAll(".quick-filter").forEach(btn => {
    btn.addEventListener("click", function() {
      const q = this.dataset.q;
      document.getElementById("searchInput").value = q;
      runSearch(q);
    });
  });
}

function runSearch(q) {
  if (!q || q.length < 2) {
    showAlert("searchAlert", "Enter at least 2 characters to search.", "warning");
    return;
  }
  document.getElementById("searchResults").innerHTML = `<div class="text-center py-4"><span class="spinner-border spinner-la"></span> Searching...</div>`;

  laAjax("GET", `/api/loans/search?q=${encodeURIComponent(q)}`)
    .then(products => {
      if (!products.length) {
        document.getElementById("searchResults").innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-msg">No products found for "<strong>${escapeHtml(q)}</strong>".</div><div class="empty-sub">Try a different term — e.g. the lender name, category, or purpose.</div></div>`;
        return;
      }
      let html = `<div class="la-card-header mb-3">${products.length} product(s) found for "<strong>${escapeHtml(q)}</strong>"</div><div class="row">`;
      products.forEach(p => { html += renderProductCard(p, true); });
      html += `</div>`;
      document.getElementById("searchResults").innerHTML = html;
      bindProductButtons();
    })
    .catch(err => showAlert("searchAlert", err.message, "danger"));
}
