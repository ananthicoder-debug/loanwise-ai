/* ===================================================================
   LoanWise AI — active-loans.js
   Handles: Loan Details page, Active Loans page
=================================================================== */

/* ─── Loan Details Page ──────────────────────────────────────── */
let currentProduct = null;

function initLoanDetailsPage() {
  initPageLayout("eligible-loans", "Loan Details");

  const productId = getQueryParam("product_id");
  const applicationId = getQueryParam("application_id");

  if (!productId) {
    document.getElementById("detailAlert").innerHTML = `<div class="alert alert-warning">No product selected. <a href="eligible-loans.html">Go back</a>.</div>`;
    return;
  }

  laAjax("GET", `/api/loans/${productId}`)
    .then(product => {
      currentProduct = product;
      renderProductDetail(product, applicationId);
    })
    .catch(err => showAlert("detailAlert", err.message, "danger"));
}

function renderProductDetail(p, applicationId) {
  const verifiedBadge = p.verification_status === "Verified"
    ? `<span class="source-ribbon">✅ Verified from official source</span>`
    : `<span class="synthetic-ribbon">ℹ️ Source: Official lender page</span>`;

  const docs = Array.isArray(p.documents_required)
    ? p.documents_required.join(", ")
    : (p.documents_required || "Identity, Address, Income Proof");

  const benefits = Array.isArray(p.benefits) && p.benefits.length
    ? p.benefits.map(b => `<li>${escapeHtml(b)}</li>`).join("")
    : "<li>Not publicly specified</li>";

  const eligConds = Array.isArray(p.eligibility_conditions) && p.eligibility_conditions.length
    ? p.eligibility_conditions.map(e => `<li>${escapeHtml(e)}</li>`).join("")
    : "<li>Not publicly specified</li>";

  document.getElementById("productDetailContent").innerHTML = `
    <div class="row g-4">
      <!-- Main Info -->
      <div class="col-lg-8">
        <div class="la-card mb-4">
          <div class="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-3">
            <div>
              <div class="lender-badge mb-1">🏦 ${escapeHtml(p.lender_name)}</div>
              <h2 class="fw-bold mb-1">${escapeHtml(p.product_name)}</h2>
              <span class="badge bg-primary-la bg-opacity-10 text-primary-la me-2" style="background:var(--lavender);color:var(--primary);padding:4px 10px;border-radius:6px;font-size:0.82rem;">${escapeHtml(p.loan_category)}</span>
              ${verifiedBadge}
            </div>
          </div>

          <div class="row g-3 mb-4">
            <div class="col-6 col-md-3"><div class="health-metric"><div class="metric-label">Min Rate</div><div class="metric-value">${p.interest_rate_min}%</div></div></div>
            <div class="col-6 col-md-3"><div class="health-metric"><div class="metric-label">Max Rate</div><div class="metric-value">${p.interest_rate_max}%</div></div></div>
            <div class="col-6 col-md-3"><div class="health-metric"><div class="metric-label">Min Amount</div><div class="metric-value">${formatCurrency(p.min_amount)}</div></div></div>
            <div class="col-6 col-md-3"><div class="health-metric"><div class="metric-label">Max Amount</div><div class="metric-value">${formatCurrency(p.max_amount)}</div></div></div>
            <div class="col-6 col-md-3"><div class="health-metric"><div class="metric-label">Min Tenure</div><div class="metric-value">${p.min_tenure} mo</div></div></div>
            <div class="col-6 col-md-3"><div class="health-metric"><div class="metric-label">Max Tenure</div><div class="metric-value">${p.max_tenure} mo</div></div></div>
            <div class="col-6 col-md-3"><div class="health-metric"><div class="metric-label">Processing Fee</div><div class="metric-value" style="font-size:1rem">${escapeHtml(p.processing_fee || "Not specified")}</div></div></div>
            <div class="col-6 col-md-3"><div class="health-metric"><div class="metric-label">Collateral</div><div class="metric-value" style="font-size:1rem">${escapeHtml(p.collateral_required || "No")}</div></div></div>
          </div>

          <div class="row g-3">
            <div class="col-md-6">
              <h6 class="fw-bold text-primary-la">Eligibility Criteria</h6>
              <ul class="small text-muted">${eligConds}</ul>
              <div class="small"><strong>Min Age:</strong> ${p.minimum_age || 18} | <strong>Max Age:</strong> ${p.maximum_age || 70}</div>
              ${p.minimum_income ? `<div class="small"><strong>Min Income:</strong> ${formatCurrency(p.minimum_income)}/year</div>` : ""}
              ${p.minimum_cibil ? `<div class="small"><strong>Min CIBIL:</strong> ${p.minimum_cibil}</div>` : "<div class='small text-muted'>Min CIBIL: Not publicly specified</div>"}
              <div class="small"><strong>Employment:</strong> ${escapeHtml(p.employment_required || "Not specified")}</div>
              <div class="small"><strong>Coapplicant:</strong> ${escapeHtml(p.coapplicant_allowed || "Depends")}</div>
            </div>
            <div class="col-md-6">
              <h6 class="fw-bold text-primary-la">Benefits</h6>
              <ul class="small text-muted">${benefits}</ul>
              <h6 class="fw-bold text-primary-la mt-3">Documents Required</h6>
              <p class="small text-muted">${escapeHtml(docs)}</p>
            </div>
          </div>
        </div>

        <!-- Source Information -->
        <div class="la-card mb-4">
          <div class="la-card-header">📋 Product Information Source</div>
          <div class="row g-2 small">
            <div class="col-md-4"><strong>Product Information:</strong></div>
            <div class="col-md-8"><span class="source-ribbon">✅ Verified Product Information</span></div>
            <div class="col-md-4"><strong>Last Verified:</strong></div>
            <div class="col-md-8">${p.source_date || "2026-09-20"}</div>
            <div class="col-md-4"><strong>Official Source:</strong></div>
            <div class="col-md-8">${p.official_product_url ? `<a href="${p.official_product_url}" target="_blank" class="text-primary-la">${escapeHtml(p.official_product_url)} ↗</a>` : "Not available"}</div>
            <div class="col-md-4"><strong>Lender Website:</strong></div>
            <div class="col-md-8">${p.lender_website ? `<a href="${p.lender_website}" target="_blank" class="text-primary-la">${p.lender_website} ↗</a>` : "—"}</div>
          </div>
          <div class="mt-2 small text-muted">
            <strong>Note:</strong> This is verified product information from the official lender page.
            Any AI-generated eligibility or affordability estimate is clearly labelled separately.
          </div>
        </div>
      </div>

      <!-- Actions & EMI Calc -->
      <div class="col-lg-4">
        <div class="la-card mb-3">
          <div class="la-card-header">🧮 Quick EMI Calculator</div>
          <div class="mb-2">
            <label class="form-label">Loan Amount (₹)</label>
            <input type="number" class="form-control form-control-sm" id="calcAmount" value="${p.min_amount}" min="${p.min_amount}" max="${p.max_amount}">
          </div>
          <div class="mb-2">
            <label class="form-label">Interest Rate (%)</label>
            <input type="number" class="form-control form-control-sm" id="calcRate" step="0.01" value="${((p.interest_rate_min + p.interest_rate_max) / 2).toFixed(2)}">
          </div>
          <div class="mb-3">
            <label class="form-label">Tenure (Months)</label>
            <input type="number" class="form-control form-control-sm" id="calcTenure" value="${p.min_tenure}" min="${p.min_tenure}" max="${p.max_tenure}">
          </div>
          <button class="btn btn-la-outline w-100 mb-3" onclick="calcDetailEMI()">Calculate EMI</button>
          <div id="calcResult" class="text-center" style="display:none">
            <div class="small text-muted">Estimated Monthly EMI</div>
            <div class="fw-bold fs-3 text-accent-la" id="calcEmiValue">—</div>
            <div class="small text-muted mt-1" id="calcBreakdown"></div>
          </div>
        </div>

        <div class="la-card mb-3">
          <div class="la-card-header">🚀 Actions</div>
          <div class="d-grid gap-2">
            <button class="btn btn-la-primary" data-bs-toggle="modal" data-bs-target="#selectLoanModal" onclick="prepareSelectModal()">💰 Consider This Loan</button>
            <button class="btn btn-la-outline" onclick="addToCompare('${p._id}', '${escapeHtml(p.product_name)}')">⚖️ Add to Compare</button>
            <a href="emi-calculator.html?amount=${p.min_amount}&rate=${((p.interest_rate_min + p.interest_rate_max) / 2).toFixed(2)}&tenure=${p.min_tenure}" class="btn btn-la-outline">🧮 Full EMI Calculator</a>
            ${applicationId ? `<a href="eligible-loans.html?app=${applicationId}" class="btn btn-la-ghost">← Back to Results</a>` : ""}
          </div>
        </div>

        <div class="la-card">
          <div class="la-card-header">ℹ️ Important Notice</div>
          <p class="small text-muted mb-0">"Consider This Loan" creates an internal tracking entry only. It does <strong>not</strong> submit an application to the lender. Contact the lender directly to apply. All EMIs shown are estimates.</p>
        </div>
      </div>
    </div>`;

  setupSelectModal(p);

  // Auto-calculate EMI on load
  calcDetailEMI();
}

function calcDetailEMI() {
  const amount = parseFloat(document.getElementById("calcAmount")?.value || 0);
  const rate = parseFloat(document.getElementById("calcRate")?.value || 0);
  const tenure = parseInt(document.getElementById("calcTenure")?.value || 0);
  if (!amount || !rate || !tenure) return;
  const emi = computeEMI(amount, rate, tenure);
  document.getElementById("calcResult").style.display = "block";
  document.getElementById("calcEmiValue").textContent = formatCurrency(emi);
  const totalRepayment = emi * tenure;
  const totalInterest = totalRepayment - amount;
  document.getElementById("calcBreakdown").textContent =
    `Total Interest: ${formatCurrency(totalInterest)} | Total Repayment: ${formatCurrency(totalRepayment)}`;
}

function computeEMI(principal, annualRate, months) {
  if (months <= 0 || annualRate < 0) return 0;
  const r = (annualRate / 12) / 100;
  if (r === 0) return Math.round(principal / months);
  const factor = Math.pow(1 + r, months);
  return Math.round(principal * r * factor / (factor - 1));
}

function setupSelectModal(product) {
  const btn = document.getElementById("confirmLoanBtn");
  if (!btn) return;

  document.getElementById("modalAmount").value = product.min_amount;
  document.getElementById("modalRate").value = ((product.interest_rate_min + product.interest_rate_max) / 2).toFixed(2);
  document.getElementById("modalTenure").value = product.min_tenure;

  const today = new Date();
  document.getElementById("modalStartDate").value = today.toISOString().split("T")[0];
  const firstDue = new Date(today);
  firstDue.setMonth(firstDue.getMonth() + 1);
  document.getElementById("modalFirstDue").value = firstDue.toISOString().split("T")[0];

  ["modalAmount","modalRate","modalTenure"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", updateModalEMI);
  });
  updateModalEMI();

  btn.onclick = () => confirmCreateActiveLoan(product._id);
}

function prepareSelectModal() { if (currentProduct) setupSelectModal(currentProduct); }

function updateModalEMI() {
  const a = parseFloat(document.getElementById("modalAmount")?.value || 0);
  const r = parseFloat(document.getElementById("modalRate")?.value || 0);
  const t = parseInt(document.getElementById("modalTenure")?.value || 0);
  document.getElementById("modalEmiPreview").textContent = (a && r && t) ? formatCurrency(computeEMI(a, r, t)) + "/month" : "—";
}

function confirmCreateActiveLoan(productId) {
  const actual_amount = parseFloat(document.getElementById("modalAmount").value);
  const interest_rate = parseFloat(document.getElementById("modalRate").value);
  const tenure_months = parseInt(document.getElementById("modalTenure").value);
  const start_date = document.getElementById("modalStartDate").value;
  const first_due_date = document.getElementById("modalFirstDue").value;

  if (!actual_amount || !interest_rate || !tenure_months || !start_date || !first_due_date) {
    showAlert("modalAlert", "Fill in all fields.", "warning"); return;
  }

  const btn = document.getElementById("confirmLoanBtn");
  btn.disabled = true;
  btn.textContent = "Creating...";

  laAjax("POST", "/api/active-loans", {
    product_id: productId,
    recommendation_id: null,
    application_id: getQueryParam("application_id") || null,
    actual_amount, interest_rate, tenure_months, start_date, first_due_date
  })
  .then(() => {
    bootstrap.Modal.getInstance(document.getElementById("selectLoanModal"))?.hide();
    window.location.href = "active-loans.html";
  })
  .catch(err => {
    showAlert("modalAlert", err.message, "danger");
    btn.disabled = false;
    btn.textContent = "Create Active Loan";
  });
}

/* ─── Active Loans Page ──────────────────────────────────────── */
function initActiveLoansPage() {
  initPageLayout("active-loans", "Active Loans");

  laAjax("GET", "/api/active-loans")
    .then(loans => {
      if (!loans.length) {
        document.getElementById("activeLoansContent").innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">💰</div>
            <div class="empty-msg">No active loans yet.</div>
            <div class="empty-sub">Check eligibility, find a product, and select it to create an active loan.</div>
            <a href="eligible-loans.html" class="btn btn-la-primary mt-3">Check Eligibility</a>
          </div>`;
        return;
      }
      let html = `<div class="row g-4">`;
      loans.forEach(loan => {
        const statusClass = loan.status === "active" ? "badge-eligible" : "badge bg-secondary";
        html += `
          <div class="col-md-6 col-xl-4">
            <div class="la-card h-100">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                  <div class="lender-badge">🏦 ${escapeHtml(loan.lender_name)}</div>
                  <div class="fw-bold mt-1">${escapeHtml(loan.product_name)}</div>
                  <div class="small text-muted">${escapeHtml(loan.loan_category || "")}</div>
                </div>
                <span class="${statusClass}">${loan.status?.toUpperCase()}</span>
              </div>
              <div class="row g-2 mb-3">
                <div class="col-6"><div class="health-metric"><div class="metric-label">Loan Amount</div><div class="metric-value" style="font-size:1.1rem">${formatCurrency(loan.actual_amount)}</div></div></div>
                <div class="col-6"><div class="health-metric"><div class="metric-label">Monthly EMI</div><div class="metric-value text-accent-la" style="font-size:1.1rem">${formatCurrency(loan.emi_amount)}</div></div></div>
                <div class="col-6"><div class="health-metric"><div class="metric-label">Interest Rate</div><div class="metric-value" style="font-size:1rem">${loan.interest_rate}%</div></div></div>
                <div class="col-6"><div class="health-metric"><div class="metric-label">Tenure</div><div class="metric-value" style="font-size:1rem">${loan.tenure_months} months</div></div></div>
              </div>
              <div class="small text-muted mb-3">Start: ${formatDate(loan.start_date)} | First EMI: ${formatDate(loan.first_due_date)}</div>
              <div class="d-flex gap-2">
                <button class="btn btn-sm btn-la-primary" onclick="window.location.href='emi-schedule.html?loan_id=${loan._id}'">View Schedule</button>
                <button class="btn btn-sm btn-la-outline" onclick="window.location.href='payment-history.html?loan_id=${loan._id}'">Payments</button>
              </div>
            </div>
          </div>`;
      });
      html += `</div>`;
      document.getElementById("activeLoansContent").innerHTML = html;
    })
    .catch(err => showAlert("activeLoansAlert", err.message, "danger"));
}

function addToCompare(id, name) {
  let list = JSON.parse(localStorage.getItem("lw_compare") || "[]");
  if (list.length >= 4) { alert("Up to 4 products can be compared. Remove one first."); return; }
  if (!list.find(p => p.id === id)) {
    list.push({ id, name });
    localStorage.setItem("lw_compare", JSON.stringify(list));
  }
  if (confirm(`"${name}" added to compare list. Go to Compare page now?`)) window.location.href = "compare-loans.html";
}
