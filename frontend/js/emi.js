/* ===================================================================
   LoanWise AI — emi.js  v3.0
   EMI Calculator, Compare Loans, Financial Health pages
   Supports both slider-based (initEMICalculator) and
   form-submit-based (initEmiCalculatorPage) entry points.
=================================================================== */

/* ─── Core EMI Maths ─────────────────────────────────────────── */
function computeEMI(principal, annualRate, months) {
  if (!months || months <= 0 || !principal || principal <= 0) return 0;
  const r = (annualRate / 12) / 100;
  if (r === 0) return Math.round(principal / months);
  const factor = Math.pow(1 + r, months);
  return Math.round(principal * r * factor / (factor - 1));
}

function buildAmortSchedule(principal, annualRate, months) {
  const r = (annualRate / 12) / 100;
  const emi = computeEMI(principal, annualRate, months);
  const schedule = [];
  let balance = principal;
  for (let i = 1; i <= months; i++) {
    const interest = r === 0 ? 0 : Math.round(balance * r * 100) / 100;
    let princPart = parseFloat((emi - interest).toFixed(2));
    if (i === months) princPart = balance; // absorb rounding in final instalment
    const closing = Math.max(0, Math.round((balance - princPart) * 100) / 100);
    schedule.push({
      month: i,
      opening: balance,
      principal: princPart,
      interest,
      emi: princPart + interest,
      closing,
    });
    balance = closing;
  }
  return schedule;
}

/* ===================================================================
   ENTRY POINT A — Slider-based page (existing emi-calculator.html)
   Called as: initEMICalculator()
=================================================================== */
let emiPieChart = null;
let fullSchedule = [];

function initEMICalculator() {
  initPageLayout("emi-calculator", "EMI Calculator");

  const amt    = getQueryParam("amount");
  const rate   = getQueryParam("rate");
  const tenure = getQueryParam("tenure");

  if (amt)    { _setVal("emiAmount", "emiAmountSlider", amt); }
  if (rate)   { _setVal("emiRate",   "emiRateSlider",   rate); }
  if (tenure) { _setVal("emiTenure", "emiTenureSlider", tenure); }

  _syncSlider("emiAmount",  "emiAmountSlider");
  _syncSlider("emiRate",    "emiRateSlider");
  _syncSlider("emiTenure",  "emiTenureSlider");

  calculateEMI();
}

function _setVal(inputId, sliderId, val) {
  const inp = document.getElementById(inputId);
  const sld = document.getElementById(sliderId);
  if (inp) inp.value = val;
  if (sld) sld.value = val;
}

function _syncSlider(inputId, sliderId) {
  const input  = document.getElementById(inputId);
  const slider = document.getElementById(sliderId);
  if (!input || !slider) return;
  input.addEventListener("input",  () => { slider.value = input.value;  calculateEMI(); });
  slider.addEventListener("input", () => { input.value  = slider.value; calculateEMI(); });
}

function calculateEMI() {
  const principal  = parseFloat(document.getElementById("emiAmount")?.value  || 0);
  const annualRate = parseFloat(document.getElementById("emiRate")?.value    || 0);
  const months     = parseInt(document.getElementById("emiTenure")?.value    || 0);
  if (!principal || !annualRate || !months) return;

  const emi            = computeEMI(principal, annualRate, months);
  const totalRepayment = emi * months;
  const totalInterest  = totalRepayment - principal;
  const interestPct    = ((totalInterest / principal) * 100).toFixed(1);

  // Slider-based result card IDs
  const show = id => { const el = document.getElementById(id); if (el) el.style.display = ""; };
  show("emiResultCards"); show("emiChartCard"); show("amortCard");

  _setText("resultEMI",          formatCurrency(emi));
  _setText("resultInterest",     formatCurrency(totalInterest));
  _setText("resultTotal",        formatCurrency(totalRepayment));
  _setText("breakdownPrincipal", formatCurrency(principal));
  _setText("breakdownInterest",  formatCurrency(totalInterest));
  _setText("breakdownPercent",   interestPct + "%");

  // Form-based result card IDs (if on new page variant)
  _setText("resEMI",            formatCurrency(emi));
  _setText("resTotalInterest",  formatCurrency(totalInterest));
  _setText("resTotalRepayment", formatCurrency(totalRepayment));
  _setText("resInterestPct",    Math.round((totalInterest / totalRepayment) * 100) + "%");
  show("emiResultCard"); show("amortCard");

  _drawPieChart(principal, totalInterest);
  _buildAmortTable(principal, annualRate, months, emi);
}

function _setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function _drawPieChart(principal, interest) {
  const canvas = document.getElementById("emiPieChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (emiPieChart) emiPieChart.destroy();
  emiPieChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Principal", "Interest"],
      datasets: [{
        data: [principal, interest],
        backgroundColor: ["#6C4AB6", "#F97316"],
        borderWidth: 2,
      }],
    },
    options: {
      cutout: "65%",
      plugins: { legend: { position: "bottom" } },
    },
  });
}

function _buildAmortTable(principal, annualRate, months, emi) {
  fullSchedule = buildAmortSchedule(principal, annualRate, months);
  renderAmortRows(fullSchedule.slice(0, 12));

  // Toggle controls for slider-based page
  const more   = document.getElementById("amortMore");
  const toggle = document.getElementById("toggleAmort");
  if (more)   more.style.display   = fullSchedule.length > 12 ? "" : "none";
  if (toggle) toggle.style.display = fullSchedule.length > 12 ? "" : "none";

  // Show-All button for form-based page
  const showAll = document.getElementById("showAllAmort");
  if (showAll) showAll.style.display = fullSchedule.length > 12 ? "inline-block" : "none";
}

function renderAmortRows(rows) {
  // Slider-based page uses #amortBody
  const tbody = document.getElementById("amortBody");
  if (!tbody) return;
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${r.month}</td>
      <td>${formatCurrency(r.opening)}</td>
      <td class="fw-bold">${formatCurrency(r.emi)}</td>
      <td>${formatCurrency(r.principal)}</td>
      <td class="text-accent-la">${formatCurrency(r.interest)}</td>
      <td>${formatCurrency(r.closing)}</td>
    </tr>`).join("");
}

function showFullAmort() {
  renderAmortRows(fullSchedule);
  const more = document.getElementById("amortMore");
  if (more) more.style.display = "none";
}

function toggleAmortTable() {
  const btn  = document.getElementById("toggleAmort");
  const tbody = document.getElementById("amortBody");
  if (!btn || !tbody) return;
  if (fullSchedule.length > 12 && tbody.children.length <= 12) {
    renderAmortRows(fullSchedule);
    btn.textContent = "Show Preview";
  } else {
    renderAmortRows(fullSchedule.slice(0, 12));
    btn.textContent = "Show Full Table";
  }
}

/* ===================================================================
   ENTRY POINT B — Form-submit-based page variant
   Called as: initEmiCalculatorPage()
=================================================================== */
function initEmiCalculatorPage() {
  initPageLayout("emi-calculator", "EMI Calculator");

  // Pre-fill from query params
  const amt    = getQueryParam("amount");
  const rate   = getQueryParam("rate");
  const tenure = getQueryParam("tenure");
  if (amt)    { const el = document.getElementById("emiAmount");  if (el) el.value = amt; }
  if (rate)   { const el = document.getElementById("emiRate");    if (el) el.value = rate; }
  if (tenure) { const el = document.getElementById("emiTenure");  if (el) el.value = tenure; }

  // Auto-calculate if query params were provided
  if (amt && rate && tenure) calculateEMI();

  document.getElementById("emiForm")?.addEventListener("submit", e => {
    e.preventDefault();
    calculateEMI();
  });

  document.getElementById("showAllAmort")?.addEventListener("click", () => {
    renderAmortRows(fullSchedule);
    const btn = document.getElementById("showAllAmort");
    if (btn) btn.style.display = "none";
  });
}

/* ===================================================================
   ENTRY POINT C — Compare Loans page
   Called as: initCompareLoansPage()
=================================================================== */
function initCompareLoansPage() {
  initPageLayout("compare-loans", "Compare Loans");
  _loadCompareList();

  document.getElementById("loadCompareBtn")?.addEventListener("click", _loadCompareData);
  document.getElementById("clearCompareBtn")?.addEventListener("click", () => {
    localStorage.removeItem("lw_compare");
    _loadCompareList();
    const tableWrap = document.getElementById("compareTableWrap");
    if (tableWrap) tableWrap.style.display = "none";
  });
}

function _loadCompareList() {
  const list = JSON.parse(localStorage.getItem("lw_compare") || "[]");
  const listBar    = document.getElementById("compareListBar");
  const noItems    = document.getElementById("compareNoItems");
  const tableWrap  = document.getElementById("compareTableWrap");

  if (!list.length) {
    if (listBar)   listBar.style.display   = "none";
    if (noItems)   noItems.style.display   = "block";
    if (tableWrap) tableWrap.style.display = "none";
    return;
  }

  if (noItems)  noItems.style.display  = "none";
  if (listBar)  listBar.style.display  = "block";

  const chips = document.getElementById("compareChips");
  if (chips) {
    chips.innerHTML = list.map((item, i) =>
      `<span class="badge-manageable d-inline-flex align-items-center gap-2">
        ${escapeHtml(item.name)}
        <button class="btn-close" style="font-size:0.6rem" onclick="_removeFromCompare(${i})"></button>
      </span>`
    ).join("");
  }

  const loadBtn = document.getElementById("loadCompareBtn");
  if (loadBtn) loadBtn.disabled = list.length < 2;
}

function _removeFromCompare(index) {
  let list = JSON.parse(localStorage.getItem("lw_compare") || "[]");
  list.splice(index, 1);
  localStorage.setItem("lw_compare", JSON.stringify(list));
  _loadCompareList();
  const tableWrap = document.getElementById("compareTableWrap");
  if (tableWrap) tableWrap.style.display = "none";
}

function _loadCompareData() {
  const list = JSON.parse(localStorage.getItem("lw_compare") || "[]");
  if (list.length < 2) {
    showAlert("compareAlert", "Add at least 2 products to compare.", "warning");
    return;
  }
  const ids = list.map(p => p.id).join(",");
  laAjax("GET", `/api/loans/compare?ids=${encodeURIComponent(ids)}`)
    .then(products => _renderCompareTable(products))
    .catch(err => showAlert("compareAlert", err.message, "danger"));
}

function _renderCompareTable(products) {
  if (!products || !products.length) return;

  // Pre-compute EMI for each product
  products.forEach(p => {
    const midRate = (p.interest_rate_min + p.interest_rate_max) / 2;
    p._emi         = computeEMI(p.min_amount, midRate, p.min_tenure);
    p._total       = p._emi * p.min_tenure;
    p._interest    = p._total - p.min_amount;
  });

  const minRate   = Math.min(...products.map(p => p.interest_rate_min));
  const maxAmt    = Math.max(...products.map(p => p.max_amount));
  const minEMI    = Math.min(...products.map(p => p._emi));
  const maxTenure = Math.max(...products.map(p => p.max_tenure));

  // Table head
  let headHtml = "<tr><th>Attribute</th>";
  products.forEach(p => {
    headHtml += `<th class="text-center">${escapeHtml(p.lender_name)}<br><small class="fw-normal text-muted">${escapeHtml(p.product_name)}</small></th>`;
  });
  headHtml += "</tr>";

  const rowDefs = [
    ["Category",       p => escapeHtml(p.loan_category)],
    ["Min Rate",       p => {
      const v = `${p.interest_rate_min}%`;
      return p.interest_rate_min === minRate ? `<span class="better">${v} ★</span>` : v;
    }],
    ["Max Rate",       p => `${p.interest_rate_max}%`],
    ["Min Amount",     p => formatCurrency(p.min_amount)],
    ["Max Amount",     p => {
      const v = formatCurrency(p.max_amount);
      return p.max_amount === maxAmt ? `<span class="better">${v} ★</span>` : v;
    }],
    ["Min Tenure",     p => `${p.min_tenure} mo`],
    ["Max Tenure",     p => {
      const v = `${p.max_tenure} mo`;
      return p.max_tenure === maxTenure ? `<span class="better">${v} ★</span>` : v;
    }],
    ["Processing Fee", p => escapeHtml(p.processing_fee || "Not specified")],
    ["Est. EMI (min amount, min tenure, mid rate)", p => {
      const v = formatCurrency(p._emi);
      return p._emi === minEMI ? `<span class="better fw-bold">${v} ★</span>` : `<span class="fw-bold">${v}</span>`;
    }],
    ["Total Interest (est.)",   p => formatCurrency(p._interest)],
    ["Total Repayment (est.)",  p => formatCurrency(p._total)],
    ["Collateral",     p => escapeHtml(p.collateral_required || "No")],
    ["Verification",   p => `<span class="badge-verified">${escapeHtml(p.verification_status || "Verified")}</span>`],
    ["Source Date",    p => escapeHtml(p.source_date || "—")],
    ["Official Source",p => p.official_product_url
      ? `<a href="${p.official_product_url}" target="_blank" class="text-primary-la small">Official ↗</a>`
      : "—"],
    ["",               p => `<a href="loan-details.html?product_id=${p._id}" class="btn btn-sm btn-la-primary">Details</a>`],
  ];

  let bodyHtml = "";
  rowDefs.forEach(([label, fn]) => {
    bodyHtml += `<tr><td class="fw-bold small text-muted">${label}</td>`;
    products.forEach(p => { bodyHtml += `<td class="text-center small">${fn(p)}</td>`; });
    bodyHtml += "</tr>";
  });

  const head = document.getElementById("compareHead");
  const body = document.getElementById("compareBody");
  const wrap = document.getElementById("compareTableWrap");
  if (head) head.innerHTML = headHtml;
  if (body) body.innerHTML = bodyHtml;
  if (wrap) wrap.style.display = "block";
}

/* ===================================================================
   ENTRY POINT D — Financial Health page
   Called as: initFinancialHealthPage()
=================================================================== */
function initFinancialHealthPage() {
  initPageLayout("financial-health", "Financial Profile");
  laAjax("GET", "/api/credit-profile")
    .then(cp => {
      if (!cp || !Object.keys(cp).length) {
        document.getElementById("healthContent").innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">📊</div>
            <div class="empty-msg">No financial profile found.</div>
            <div class="empty-sub">
              <a href="profile.html">Complete your profile</a> to see your financial summary.
            </div>
          </div>`;
        return;
      }
      _renderFinancialHealth(cp);
    })
    .catch(err => showAlert("healthAlert", err.message, "danger"));
}

function _renderFinancialHealth(cp) {
  const monthly      = cp.monthly_income || 0;
  const existingEmi  = cp.existing_emi || cp.current_emi || 0;
  const debt         = cp.outstanding_debt || 0;
  const annualIncome = cp.annual_income || monthly * 12;
  const dti          = annualIncome > 0 ? Math.round((debt / annualIncome) * 100) : 0;
  const eti          = monthly > 0 ? Math.round((existingEmi / monthly) * 100) : 0;
  const cibil        = cp.cibil_score || 0;

  const cibilLabel = cibil >= 750 ? "Excellent" : cibil >= 700 ? "Good" : cibil >= 650 ? "Fair"
    : cibil >= 600 ? "Below Average" : "Low";
  const cibilColor = cibil >= 750 ? "var(--success)" : cibil >= 700 ? "#2563EB"
    : cibil >= 650 ? "var(--warning)" : "var(--danger)";

  const etiClass = eti > 50 ? "text-danger" : eti > 35 ? "text-warning" : "text-success";
  const etiMsg   = eti <= 35 ? "Within typical manageable range"
    : eti <= 50 ? "Approaching high obligation zone"
    : "High EMI burden relative to income";

  const dtiClass = dti > 40 ? "text-danger" : dti > 25 ? "text-warning" : "text-success";
  const dtiMsg   = dti <= 25 ? "Within typical manageable range"
    : dti <= 40 ? "Moderate debt level"
    : "High debt relative to income";

  document.getElementById("healthContent").innerHTML = `
    <div class="row g-4">
      <div class="col-md-4">
        <div class="la-card h-100">
          <div class="la-card-header">💰 Income Summary</div>
          <div class="health-metric"><div class="metric-label">Monthly Income</div><div class="metric-value">${formatCurrency(monthly)}</div></div>
          <div class="health-metric"><div class="metric-label">Annual Income</div><div class="metric-value">${formatCurrency(annualIncome)}</div></div>
          <div class="health-metric"><div class="metric-label">Employment Type</div><div class="metric-value" style="font-size:1rem">${escapeHtml(cp.employment_type || "—")}</div></div>
          <div class="health-metric"><div class="metric-label">Years Employed</div><div class="metric-value" style="font-size:1rem">${cp.years_of_employment || "—"}</div></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="la-card h-100">
          <div class="la-card-header">📋 Current Obligations</div>
          <div class="health-metric"><div class="metric-label">Existing EMI/Month</div><div class="metric-value">${formatCurrency(existingEmi)}</div><div class="metric-desc">${eti}% of monthly income</div></div>
          <div class="health-metric"><div class="metric-label">Outstanding Debt</div><div class="metric-value">${formatCurrency(debt)}</div><div class="metric-desc">Debt-to-Income: ${dti}%</div></div>
          <div class="health-metric"><div class="metric-label">Existing Loans</div><div class="metric-value" style="font-size:1rem">${cp.existing_loans || 0}</div></div>
          <div class="health-metric"><div class="metric-label">Dependents</div><div class="metric-value" style="font-size:1rem">${cp.dependents || 0}</div></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="la-card h-100">
          <div class="la-card-header">📊 Credit Profile</div>
          <div class="health-metric">
            <div class="metric-label">CIBIL Score</div>
            <div class="metric-value" style="color:${cibilColor}">${cibil} <small style="font-size:0.8rem">(${cibilLabel})</small></div>
            <div class="match-score-bar mt-2">
              <div class="match-score-fill" style="width:${Math.round(((cibil - 300) / 600) * 100)}%;background:${cibilColor}"></div>
            </div>
          </div>
          <div class="health-metric"><div class="metric-label">Missed Payments</div><div class="metric-value" style="font-size:1rem;color:${(cp.missed_payments || 0) > 0 ? 'var(--danger)' : 'var(--success)'}">${cp.missed_payments || 0}</div></div>
          <div class="health-metric"><div class="metric-label">Late Payments</div><div class="metric-value" style="font-size:1rem;color:${(cp.late_payments || 0) > 0 ? 'var(--warning)' : 'var(--success)'}">${cp.late_payments || 0}</div></div>
          <div class="health-metric"><div class="metric-label">Previous Loans</div><div class="metric-value" style="font-size:1rem">${cp.previous_loans || 0}</div></div>
        </div>
      </div>
      <div class="col-12">
        <div class="la-card">
          <div class="la-card-header">📈 Obligation Ratios Summary</div>
          <div class="row g-3">
            <div class="col-md-6">
              <p class="small text-muted mb-2">
                <strong>EMI-to-Income Ratio: ${eti}%</strong><br>
                <span class="${etiClass}">${etiMsg}</span>
              </p>
              <p class="small text-muted mb-0">
                <strong>Debt-to-Income Ratio: ${dti}%</strong><br>
                <span class="${dtiClass}">${dtiMsg}</span>
              </p>
            </div>
            <div class="col-md-6">
              <div class="alert alert-info small mb-0">
                <strong>Note:</strong> These are neutral financial summary metrics based on the information you provided.
                They are not a financial health score or assessment. Thresholds shown are general reference ranges only.
                Consult a qualified financial advisor for personalised guidance.
              </div>
            </div>
          </div>
          <div class="mt-3">
            <a href="eligible-loans.html" class="btn btn-la-primary me-2">✅ Check Loan Eligibility</a>
            <a href="profile.html" class="btn btn-la-outline">✏️ Update Profile</a>
          </div>
        </div>
      </div>
    </div>`;
}
