/* ===================================================================
   LoanWise AI — assessment.js  v2.0
   Handles: Assessment Report, What-If, Calculation Worksheet
=================================================================== */

let _appId = null;
let _currentAssessment = null;

/* ─── Page Init ──────────────────────────────────────────────── */
function initAssessmentPage() {
  initPageLayout("applications", "Assessment Report");

  _appId = getQueryParam("application_id") || sessionStorage.getItem("lw_last_app_id");
  if (!_appId) {
    showAlert("assessAlert", "No application selected. <a href='applications.html'>Go to Applications</a>.", "warning");
    document.getElementById("reportContent").innerHTML = "";
    return;
  }

  loadAssessment(_appId);

  // What-if modal
  document.getElementById("whatIfBtn")?.addEventListener("click", () => {
    new bootstrap.Modal(document.getElementById("whatIfModal")).show();
  });
  document.getElementById("runWhatIfBtn")?.addEventListener("click", runWhatIf);
}

/* ─── Load / Run Assessment ──────────────────────────────────── */
function loadAssessment(appId) {
  document.getElementById("reportContent").innerHTML =
    `<div class="text-center py-5"><span class="spinner-border spinner-la me-2"></span> Running assessment…</div>`;

  laAjax("POST", `/api/assessment/full/${appId}`)
    .then(data => {
      _currentAssessment = data;
      renderFullReport(data);
    })
    .catch(err => {
      showAlert("assessAlert", `Assessment error: ${err.message}`, "danger");
      document.getElementById("reportContent").innerHTML = "";
    });
}

/* ─── Main Report Renderer ───────────────────────────────────── */
function renderFullReport(data, isWhatIf = false) {
  const el = document.getElementById("reportContent");
  if (!el) return;

  const banner = isWhatIf
    ? `<div class="alert alert-info small mb-3">
        <strong>🔄 What-If Scenario</strong> — ${escapeHtml(data.scenario_label || "")}
        <br>${escapeHtml(data.scenario_note || "")}
        <button class="btn btn-sm btn-la-outline ms-2" onclick="renderFullReport(_currentAssessment)">← Back to Original</button>
       </div>` : "";

  el.innerHTML = banner
    + sectionOverview(data)
    + sectionApplicantProfile(data)
    + sectionEligibility(data)
    + sectionAffordability(data)
    + sectionCalculationWorksheet(data)
    + sectionRepaymentHistory(data)
    + sectionEligibleProducts(data)
    + sectionRecommendedProducts(data)
    + sectionNextSteps(data)
    + sectionDisclaimer(data);
}

/* ─── Section A: Overview ────────────────────────────────────── */
function sectionOverview(d) {
  const e = d.eligibility || {};
  const a = d.affordability || {};
  const s = d.applicant_summary || {};
  const ts = new Date(d.generated_at).toLocaleString("en-IN");

  const eColor = e.result === "Eligible" ? "success" : "danger";
  const aColor = a.result === "Manageable" ? "primary" : "warning";

  return `<div class="assess-section">
    <div class="assess-section-title">📋 Assessment Overview</div>
    <div class="row g-3 mb-3">
      <div class="col-md-6">
        <div class="text-muted small mb-1">Loan Category</div>
        <div class="fw-bold">${escapeHtml(s.loan_category || "—")}</div>
        <div class="text-muted small mt-2">Amount / Tenure</div>
        <div class="fw-bold">${formatCurrency(s.loan_amount)} / ${s.loan_tenure || "—"} months</div>
        <div class="text-muted small mt-2">Assessment Date</div>
        <div class="fw-bold">${ts}</div>
      </div>
      <div class="col-md-6">
        <div class="mb-2">
          <div class="text-muted small mb-1">Model 1 — Eligibility</div>
          <span class="verdict-badge ${e.result === 'Eligible' ? 'verdict-eligible' : 'verdict-not-eligible'}">
            ${escapeHtml(e.display_result || e.result || "—")}
          </span>
          <span class="small text-muted ms-2">Confidence: ${e.confidence_pct || 0}%</span>
        </div>
        <div>
          <div class="text-muted small mb-1">Model 2 — Affordability</div>
          <span class="verdict-badge ${a.result === 'Manageable' ? 'verdict-manageable' : 'verdict-not-manageable'}">
            ${escapeHtml(a.display_result || a.result || "—")}
          </span>
          <span class="small text-muted ms-2">Confidence: ${a.confidence_pct || 0}%</span>
        </div>
      </div>
    </div>
    <div class="row g-2">
      <div class="col-auto"><span class="badge bg-${eColor} bg-opacity-10 text-${eColor} border border-${eColor} border-opacity-25 px-3 py-2">✅ ${d.eligible_count || 0} Eligible Products</span></div>
      <div class="col-auto"><span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 px-3 py-2">⭐ ${d.recommended_count || 0} Recommended</span></div>
    </div>
    <p class="small text-muted mt-3 mb-0">⚠️ AI-based estimate only. Not a lender approval or financial advice.</p>
  </div>`;
}

/* ─── Section B: Applicant Profile ──────────────────────────── */
function sectionApplicantProfile(d) {
  const s = d.applicant_summary || {};
  const row = (label, val) => val != null && val !== ""
    ? `<tr><td class="text-muted">${label}</td><td class="fw-600">${val}</td></tr>` : "";

  return `<div class="assess-section">
    <div class="assess-section-title">👤 Applicant Financial Profile</div>
    <div class="table-responsive">
      <table class="input-feature-table w-100">
        <tbody>
          ${row("Monthly Income", formatCurrency(s.monthly_income))}
          ${row("Annual Income (derived)", formatCurrency(s.annual_income))}
          ${row("Existing Monthly EMI", formatCurrency(s.existing_emi))}
          ${row("Outstanding Debt", formatCurrency(s.outstanding_debt))}
          ${row("CIBIL Score", s.cibil_score)}
          ${row("Dependents", s.dependents)}
          ${row("Existing Loans", s.existing_loans)}
          ${row("Employment Type", s.employment_type)}
          ${row("Education", s.education)}
          ${row("Requested Amount", formatCurrency(s.loan_amount))}
          ${row("Requested Tenure", s.loan_tenure ? s.loan_tenure + " months" : null)}
          ${row("Applied Interest Rate", s.proposed_rate ? s.proposed_rate + "% p.a." : null)}
        </tbody>
      </table>
    </div>
  </div>`;
}

/* ─── Section C: Eligibility ─────────────────────────────────── */
function sectionEligibility(d) {
  const e = d.eligibility || {};
  const obs = e.observations || [];
  const explain = e.explanation || {};

  const inputTable = (e.input_features || []).map(f => `
    <tr>
      <td class="text-muted small">${escapeHtml(f.feature)}</td>
      <td class="fw-bold small">${f.value}</td>
      <td class="small text-muted">${escapeHtml(f.description || "")}</td>
    </tr>`).join("");

  const factors = (explain.top_factors || []).map(f => `
    <div class="factor-row">
      <div class="factor-dot ${f.direction || 'neutral'}"></div>
      <div>
        <div class="small fw-bold">${escapeHtml(f.display_name || f.feature)}</div>
        <div class="small text-muted">${escapeHtml(f.description || "")}</div>
        <div class="small">
          Value: <strong>${f.value}</strong> &nbsp;|&nbsp;
          Direction: <strong>${f.direction || "—"}</strong> &nbsp;|&nbsp;
          Strength: <strong>${f.strength || "—"}</strong>
          <span class="strength-bar-wrap"><span class="strength-bar" style="width:${Math.round((f.strength_score||0)*100)}%"></span></span>
        </div>
      </div>
    </div>`).join("");

  const obsHtml = obs.map(o => `
    <div class="obs-item">
      <div class="obs-icon">${o.type === 'positive' ? '✅' : o.type === 'warning' ? '⚠️' : o.type === 'neutral' ? '🔵' : 'ℹ️'}</div>
      <div class="obs-text">${escapeHtml(o.text || "")}</div>
    </div>`).join("");

  return `<div class="assess-section">
    <div class="assess-section-title">✅ Model 1 — Loan Eligibility Prediction</div>
    <div class="mb-3">
      <span class="verdict-badge ${e.result === 'Eligible' ? 'verdict-eligible' : 'verdict-not-eligible'}">${escapeHtml(e.display_result || "—")}</span>
      <span class="small text-muted ms-3">Model probability: ${e.confidence_pct || 0}%</span>
    </div>
    <div class="alert alert-info small mb-3">${escapeHtml(e.result_note || "")}</div>

    <div class="la-card-header mt-3 mb-2">Input Features Used by the Model</div>
    <div class="table-responsive mb-3">
      <table class="input-feature-table w-100 border">
        <thead><tr><th class="text-muted small px-2">Feature</th><th class="text-muted small px-2">Value</th><th class="text-muted small px-2">Description</th></tr></thead>
        <tbody>${inputTable}</tbody>
      </table>
    </div>

    <div class="la-card-header mb-2">Model Observations</div>
    ${obsHtml}

    <div class="la-card-header mt-3 mb-2">Top Contributing Factors
      <small class="fw-normal text-muted ms-2">(${escapeHtml(explain.explanation_method || "")})</small>
    </div>
    <div class="small text-muted mb-2">${escapeHtml(explain.method_note || "")}</div>
    ${factors || "<div class='text-muted small'>No factor data available.</div>"}

    <div class="small text-danger mt-3">⚠️ ${escapeHtml(e.disclaimer || "Trained on synthetic data.")}</div>
  </div>`;
}

/* ─── Section D: Affordability ───────────────────────────────── */
function sectionAffordability(d) {
  const a = d.affordability || {};
  const obs = a.observations || [];
  const explain = a.explanation || {};

  const inputTable = (a.input_features || []).map(f => `
    <tr>
      <td class="text-muted small">${escapeHtml(f.feature)}</td>
      <td class="fw-bold small">${f.value}</td>
      <td class="small text-muted">${escapeHtml(f.description || "")}</td>
    </tr>`).join("");

  const factors = (explain.top_factors || []).map(f => `
    <div class="factor-row">
      <div class="factor-dot ${f.direction || 'neutral'}"></div>
      <div>
        <div class="small fw-bold">${escapeHtml(f.display_name || f.feature)}</div>
        <div class="small text-muted">${escapeHtml(f.description || "")}</div>
        <div class="small">
          Value: <strong>${f.value}</strong> &nbsp;|&nbsp;
          Direction: <strong>${f.direction || "—"}</strong> &nbsp;|&nbsp;
          Strength: <strong>${f.strength || "—"}</strong>
          <span class="strength-bar-wrap"><span class="strength-bar" style="width:${Math.round((f.strength_score||0)*100)}%"></span></span>
        </div>
      </div>
    </div>`).join("");

  const obsHtml = obs.map(o => `
    <div class="obs-item">
      <div class="obs-icon">${o.type === 'positive' ? '✅' : o.type === 'warning' ? '⚠️' : o.type === 'neutral' ? '🔵' : 'ℹ️'}</div>
      <div class="obs-text">${escapeHtml(o.text || "")}</div>
    </div>`).join("");

  return `<div class="assess-section">
    <div class="assess-section-title">💰 Model 2 — Loan Affordability and Repayment Feasibility</div>
    <div class="mb-3">
      <span class="verdict-badge ${a.result === 'Manageable' ? 'verdict-manageable' : 'verdict-not-manageable'}">${escapeHtml(a.display_result || "—")}</span>
      <span class="small text-muted ms-3">Model probability: ${a.confidence_pct || 0}%</span>
    </div>
    <div class="alert alert-info small mb-3">${escapeHtml(a.result_note || "")}</div>

    <div class="la-card-header mt-3 mb-2">Input Features Used by the Model</div>
    <div class="table-responsive mb-3">
      <table class="input-feature-table w-100 border">
        <thead><tr><th class="text-muted small px-2">Feature</th><th class="text-muted small px-2">Value</th><th class="text-muted small px-2">Description</th></tr></thead>
        <tbody>${inputTable}</tbody>
      </table>
    </div>

    <div class="la-card-header mb-2">Model Observations</div>
    ${obsHtml}

    <div class="la-card-header mt-3 mb-2">Top Contributing Factors
      <small class="fw-normal text-muted ms-2">(${escapeHtml(explain.explanation_method || "")})</small>
    </div>
    <div class="small text-muted mb-2">${escapeHtml(explain.method_note || "")}</div>
    ${factors || "<div class='text-muted small'>No factor data available.</div>"}

    <div class="small text-danger mt-3">⚠️ ${escapeHtml(a.disclaimer || "Trained on synthetic data.")}</div>
  </div>`;
}

/* ─── Section E: Calculation Worksheet ──────────────────────── */
function sectionCalculationWorksheet(d) {
  const ws = d.calculations || {};
  const s  = ws.summary || {};

  const calcCard = (calc, title) => {
    if (!calc || !calc.trace) return "";
    const t = calc.trace;
    const steps = (t.steps || []).map(st => `<li class="small">${escapeHtml(st)}</li>`).join("");
    return `<div class="calc-box">
      <div class="calc-name">${title}</div>
      <div class="calc-formula">${escapeHtml(t.formula || "")}</div>
      <ul class="mb-1 ps-3">${steps}</ul>
      <div class="calc-result">${t.result != null ? (typeof t.result === 'number' ? t.result.toLocaleString('en-IN', {maximumFractionDigits:2}) : t.result) : "N/A"} <span class="text-muted fw-normal" style="font-size:.8rem">${escapeHtml(t.unit || "")}</span></div>
      ${t.note ? `<div class="small text-muted mt-1">Note: ${escapeHtml(t.note)}</div>` : ""}
    </div>`;
  };

  const summaryRows = [
    ["Monthly Income",        formatCurrency(s.monthly_income)],
    ["Annual Income",         formatCurrency(s.annual_income)],
    ["Existing EMI",          formatCurrency(s.existing_emi)],
    ["Proposed EMI",          formatCurrency(s.proposed_emi)],
    ["Total EMI",             formatCurrency(s.total_emi)],
    ["EMI Burden (existing)", s.existing_emi_burden_pct != null ? s.existing_emi_burden_pct.toFixed(1) + "%" : "—"],
    ["Total EMI-to-Income",   s.total_emi_ratio_pct != null ? s.total_emi_ratio_pct.toFixed(1) + "%" : "—"],
    ["Monthly Surplus",       formatCurrency(s.monthly_surplus)],
    ["Debt-to-Income",        s.debt_to_income_pct != null ? s.debt_to_income_pct.toFixed(1) + "%" : "—"],
    ["Total Repayment",       formatCurrency(s.total_scheduled_repayment)],
    ["Total Interest",        formatCurrency(s.total_estimated_interest)],
  ].map(([l, v]) => `<tr><td class="text-muted small">${l}</td><td class="fw-bold small">${v}</td></tr>`).join("");

  return `<div class="assess-section">
    <div class="assess-section-title">🧮 Financial Calculations Summary</div>
    <div class="row g-3 mb-3">
      <div class="col-md-4">
        <div class="table-responsive">
          <table class="w-100"><tbody>${summaryRows}</tbody></table>
        </div>
      </div>
      <div class="col-md-8">
        <div class="alert alert-info small">
          ℹ️ Proposed EMI uses the standard reducing-balance formula at ${escapeHtml(String(s.applied_rate_pct || 12))}% p.a.
          Total repayment and interest are estimates. Actual charges vary by lender.
        </div>
      </div>
    </div>

    <button class="collapse-btn" type="button" data-bs-toggle="collapse" data-bs-target="#calcDetails">
      🔍 View Internal Calculation Trace ▼
    </button>
    <div class="collapse mt-3" id="calcDetails">
      ${calcCard(ws.annual_income,        "Annual Income")}
      ${calcCard(ws.proposed_emi,         "Proposed EMI (Reducing Balance)")}
      ${calcCard(ws.existing_emi_burden,  "Existing EMI Burden")}
      ${calcCard(ws.total_emi_ratio,      "Total EMI-to-Income Ratio")}
      ${calcCard(ws.monthly_surplus,      "Estimated Monthly Surplus")}
      ${calcCard(ws.debt_to_income_ratio, "Debt-to-Income Ratio")}
    </div>
  </div>`;
}

/* ─── Section F: Repayment History ──────────────────────────── */
function sectionRepaymentHistory(d) {
  const r = d.repayment_history || {};
  if (!r || r.previous_loans === 0) {
    return `<div class="assess-section">
      <div class="assess-section-title">📅 Historical Repayment Analysis</div>
      <div class="text-muted small">No sufficient historical repayment data is available for this assessment.</div>
    </div>`;
  }
  const qualityIcon = { positive: "✅", warning: "⚠️", caution: "🟡", neutral: "ℹ️" }[r.quality_label] || "ℹ️";
  const pcr = r.payment_completion;

  return `<div class="assess-section">
    <div class="assess-section-title">📅 Historical Repayment Analysis</div>
    <div class="row g-3">
      <div class="col-6 col-md-3 text-center">
        <div style="font-size:1.6rem;font-weight:800;color:var(--primary)">${r.previous_loans}</div>
        <div class="small text-muted">Historical Loans</div>
      </div>
      <div class="col-6 col-md-3 text-center">
        <div style="font-size:1.6rem;font-weight:800;color:var(--accent)">${r.missed_payments}</div>
        <div class="small text-muted">Missed Payments</div>
      </div>
      <div class="col-6 col-md-3 text-center">
        <div style="font-size:1.6rem;font-weight:800;color:#F59E0B">${r.late_payments}</div>
        <div class="small text-muted">Late Payments</div>
      </div>
      <div class="col-6 col-md-3 text-center">
        <div style="font-size:1.6rem;font-weight:800;color:#6B7280">${r.average_days_late || 0}</div>
        <div class="small text-muted">Avg Days Late</div>
      </div>
    </div>
    ${pcr ? `
    <div class="mt-3 small">
      <strong>Payment Completion Ratio:</strong> ${pcr.ratio_pct}%
      <span class="text-muted ms-2">(${pcr.paid_est} paid / ${pcr.total_due} due — approximate proxy)</span>
    </div>` : ""}
    <div class="mt-3 obs-item">
      <div class="obs-icon">${qualityIcon}</div>
      <div class="obs-text">${escapeHtml(r.summary || "")}</div>
    </div>
    ${r.note ? `<div class="small text-muted mt-2">${escapeHtml(r.note)}</div>` : ""}
  </div>`;
}

/* ─── Section G: Eligible Products ──────────────────────────── */
function sectionEligibleProducts(d) {
  const all = (d.eligible_products || []).filter(p => p.eligibility_status === "Potentially Eligible");
  const notElig = (d.eligible_products || []).filter(p => p.eligibility_status !== "Potentially Eligible");

  if (!all.length && !notElig.length) {
    return `<div class="assess-section">
      <div class="assess-section-title">🏦 Eligible Loan Products</div>
      <div class="text-muted small">No products found for this loan category. Ensure the product catalogue is seeded.</div>
    </div>`;
  }

  const eligCards = all.map(p => productCard(p, false)).join("");
  const notCards  = notElig.length
    ? `<button class="collapse-btn mt-2" type="button" data-bs-toggle="collapse" data-bs-target="#notEligProducts">
        Show ${notElig.length} products that don't match criteria ▼
       </button>
       <div class="collapse mt-2" id="notEligProducts">
         ${notElig.map(p => productCard(p, false)).join("")}
       </div>` : "";

  return `<div class="assess-section">
    <div class="assess-section-title">🏦 Eligible Loan Products <span class="badge bg-success ms-2">${all.length}</span></div>
    <p class="small text-muted mb-3">Products that match configured eligibility criteria and the AI model estimate. Potentially eligible — verify directly with the lender.</p>
    ${eligCards || '<div class="text-muted small">No potentially eligible products found.</div>'}
    ${notCards}
  </div>`;
}

/* ─── Section H: Recommended Products ───────────────────────── */
function sectionRecommendedProducts(d) {
  const recs = d.recommended_products || [];
  if (!recs.length) {
    return `<div class="assess-section">
      <div class="assess-section-title">⭐ Recommended Products</div>
      <div class="text-muted small">No products currently match both the eligibility and affordability criteria. Adjust the loan amount or tenure, or review the financial profile.</div>
    </div>`;
  }

  return `<div class="assess-section">
    <div class="assess-section-title">⭐ Recommended Products <span class="badge bg-primary ms-2">${recs.length}</span></div>
    <p class="small text-muted mb-3">Products that are both potentially eligible AND assessed as manageable by the affordability model.</p>
    ${recs.map(p => productCard(p, true)).join("")}
  </div>`;
}

function productCard(p, isRec) {
  const eligBadge = p.eligibility_status === "Potentially Eligible"
    ? `<span class="badge-eligible">Potentially Eligible</span>`
    : `<span class="badge-not-eligible">Not Eligible</span>`;
  const aff = p.affordability_result
    ? `<span class="ms-1 ${p.affordability_result === 'Manageable' ? 'badge-status-paid' : 'badge-status-overdue'}">${p.affordability_result}</span>`
    : "";
  const matchScore = p.match_score
    ? `<span class="match-score-badge ms-2">Match ${p.match_score}%</span>` : "";
  const reason = p.recommendation_reason
    ? `<div class="small text-success mt-1">✅ ${escapeHtml(p.recommendation_reason)}</div>` : "";
  const ruleWarnings = (p.rule_reasons || []).length
    ? `<div class="small text-danger mt-1">${p.rule_reasons.slice(0,2).map(r => '⚠️ ' + escapeHtml(r)).join('<br>')}</div>` : "";

  return `<div class="product-match-card ${isRec ? 'recommended' : ''}">
    <div class="d-flex flex-wrap justify-content-between align-items-start gap-2">
      <div>
        <div class="fw-bold">🏦 ${escapeHtml(p.lender_name)}</div>
        <div class="fw-semibold small mt-1">${escapeHtml(p.product_name)}</div>
      </div>
      <div>${eligBadge}${aff}${matchScore}</div>
    </div>
    <div class="d-flex flex-wrap gap-3 mt-2 small text-muted">
      <span>Rate: ${p.interest_rate_min}%–${p.interest_rate_max}%</span>
      <span>Amount: ${formatCurrency(p.min_amount)}–${formatCurrency(p.max_amount)}</span>
      <span>Tenure: ${p.min_tenure}–${p.max_tenure} mo</span>
      ${p.estimated_emi ? `<span>Est. EMI: <strong>${formatCurrency(p.estimated_emi)}/mo</strong></span>` : ""}
      <span>Fee: ${escapeHtml(p.processing_fee || "Not specified")}</span>
    </div>
    ${p.official_product_url ? `<div class="small mt-1"><a href="${escapeHtml(p.official_product_url)}" target="_blank" rel="noopener">🔗 Official Source</a> ${p.verification_status === 'Verified' ? '✅ Verified' : ''}</div>` : ""}
    ${reason}${ruleWarnings}
  </div>`;
}

/* ─── Section I: Next Steps ──────────────────────────────────── */
function sectionNextSteps(d) {
  const steps = d.next_steps || [];
  return `<div class="assess-section">
    <div class="assess-section-title">🚀 Personalized Next Steps</div>
    ${steps.map((s, i) => `
      <div class="step-item">
        <div class="step-num">${i + 1}</div>
        <div class="small">${escapeHtml(s)}</div>
      </div>`).join("")}
  </div>`;
}

function sectionDisclaimer(d) {
  const text = d.disclaimer || "LoanWise AI model outputs are estimates. Final eligibility and approval are determined by the lender.";
  return `<div class="disclaimer-box mt-3">
    <strong>⚠️ Important Notice</strong><br>
    ${escapeHtml(text)}
  </div>`;
}

/* ─── What-If ─────────────────────────────────────────────────── */
function runWhatIf() {
  const amount  = parseFloat(document.getElementById("wiAmount").value) || null;
  const rate    = parseFloat(document.getElementById("wiRate").value)   || null;
  const tenure  = parseInt(document.getElementById("wiTenure").value)   || null;
  const body    = {};
  if (amount)  body.loan_amount   = amount;
  if (rate)    body.proposed_rate = rate;
  if (tenure)  body.loan_tenure   = tenure;

  if (!Object.keys(body).length) {
    showAlert("wiAlert", "Enter at least one value to recalculate.", "warning");
    return;
  }

  const btn = document.getElementById("runWhatIfBtn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Calculating…';

  laAjax("POST", `/api/assessment/what-if/${_appId}`, body)
    .then(data => {
      bootstrap.Modal.getInstance(document.getElementById("whatIfModal"))?.hide();
      renderFullReport(data, true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    })
    .catch(err => showAlert("wiAlert", err.message, "danger"))
    .finally(() => {
      btn.disabled = false;
      btn.textContent = "Recalculate Scenario";
    });
}
